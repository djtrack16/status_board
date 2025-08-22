import pytest
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_session  # your dependency
from tests.factories.monitor_factory import MonitorFactory, MonitorCheckFactory

# Use in-memory SQLite with StaticPool so all sessions share the same connection
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
  TEST_DATABASE_URL,
  connect_args={"check_same_thread": False},
  poolclass=StaticPool,
)

# Fixture to create tables once per test session
@pytest.fixture(scope="session", autouse=True)
def create_test_db():
  SQLModel.metadata.create_all(engine)
  yield
  SQLModel.metadata.drop_all(engine)


# Override dependency for FastAPI
def override_get_session():
  with Session(engine) as session:
    yield session

app.dependency_overrides[get_session] = override_get_session

# Fixture for TestClient
@pytest.fixture
def client():
  with TestClient(app) as c:
    yield c

# Test DB SQLite
@pytest.fixture
def session_fixture(engine_fixture):
  
  # setup
  SQLModel.metadata.create_all(engine_fixture)
  with Session(engine_fixture) as session:
    yield session

  # teardown
  session.close()
  SQLModel.metadata.drop_all(engine_fixture)

@pytest.fixture(scope="function")
def engine_fixture():
  # each unit test gets an isolated db
  yield engine
  engine.dispose()

@pytest.fixture
def monitor_factory(session_fixture):
  # Bind factory to the session for this test run
  MonitorFactory._meta.sqlalchemy_session =  session_fixture# type: ignore
  return MonitorFactory

@pytest.fixture
def monitor_check_factory(session_fixture):
  # Bind factory to the session for this test run
  MonitorCheckFactory._meta.sqlalchemy_session =  session_fixture# type: ignore
  return MonitorCheckFactory