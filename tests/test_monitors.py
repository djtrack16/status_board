import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import SQLModel, Session, create_engine, delete, select
from app.main import app
from app.models.monitor import Monitor
from app.models.monitor_check import MonitorCheck
from app.database import get_session
from tests.factories.monitor_factory import MonitorFactory, MonitorCheckFactory
from tests.config import(
  create_engine,
  client,
  monitor_factory,
  monitor_params_factory,
  monitor_check_factory,
  session_fixture,
  engine_fixture
)

def test_create_monitor(client, session_fixture):
  payload = {
    "url": "https://example.com",
    "name": "Example",
  }
  response = client.post(
    "/monitors/",
    json=payload
  )
  assert response.status_code == 200
  data = response.json()
  assert data["url"] == "https://example.com"
  assert data["name"] == "Example"
  assert "id" in data

  monitor = session_fixture.get(Monitor, data["id"])
  assert monitor is not None
  assert monitor.url == payload["url"]
  assert monitor.name == payload["name"]

def test_update_monitor(client, monitor_factory, session_fixture):
  payload = {
    "url": "https://example.com",
    "is_active": True,
    "expected_status_code": 500,
    "name": "fake_name"
  }

  mc = monitor_factory.create(url="gmail.com",is_active=False)
  session_fixture.commit()

  response = client.patch(
    f'/monitors/{mc.id}',
    json=payload
  )
  data = response.json()

  session_fixture.refresh(mc)

  assert response.status_code == 200
  assert mc.id == data['id']

  m = session_fixture.get(Monitor, data['id'])
  assert m is not None
  assert m.url == payload['url']
  assert m.name == payload['name']
  assert m.expected_status_code == payload['expected_status_code']

def test_delete_monitor(client, session_fixture, monitor_factory):
  mf = monitor_factory.create(url="gmail.com")
  session_fixture.commit()
  assert session_fixture.get(Monitor, mf.id) is not None
  deleted_id = mf.id

  response = client.delete(f"/monitors/{mf.id}")
  assert response.status_code == 204
  session_fixture.expire_all() # expire cached objects so we always query fresh from the db
  deleted_monitor = session_fixture.get(Monitor, deleted_id)

  assert deleted_monitor is None


def test_create_monitor_with_factory(monitor_factory):
  fake_url = "https://example.com",
  fake_name = "Example"
  monitor = monitor_factory.build(url=fake_url, name=fake_name)
  assert monitor is not None
  assert monitor.url == fake_url
  assert monitor.name == fake_name

def test_monitor_check_factory_creates_record(monitor_check_factory):
  mc = monitor_check_factory.build(status_code=204, success=True, response_time_ms=560)
  assert mc is not None
  assert mc.status_code == 204
  assert mc.success is True
  assert mc.response_time_ms == 560

def test_monitor_factory_creates_record(monitor_factory, session_fixture):
  monitor = monitor_factory.create(url="https://google.com")

  db_monitor = session_fixture.get(type(monitor), monitor.id)
  assert db_monitor is not None
  assert db_monitor.url == "https://google.com"
