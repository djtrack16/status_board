from datetime import datetime, timedelta, timezone
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


def test_get_monitors_by_url(client, monitor_factory):
  url = "www.google.com"
  mf = monitor_factory.create(url=url)
  response = client.get(f"/monitors/?url={url}")

  assert response.status_code == 200
  data = response.json()
  assert len(data) == 1
  assert mf.url == data[0]['url']

def test_get_monitors_by_is_active(client, monitor_factory):
  #is_active = false
  monitor_factory.create(is_active=False)
  monitor_factory.create(is_active=True)
  response = client.get(f"/monitors/?is_active=False")

  assert response.status_code == 200
  data = response.json()
  assert len(data) == 1
  for mf in data:
    assert mf['is_active'] == False

def test_get_monitors_by_last_status_code(client, monitor_factory):
  last_status_code = 500
  monitor_factory.create(last_status_code=last_status_code)
  monitor_factory.create(last_status_code=last_status_code)
  monitor_factory.create(last_status_code=404)
  response = client.get(f"/monitors/?last_status_code={last_status_code}")

  assert response.status_code == 200
  data = response.json()
  assert len(data) == 2
  for mf in data:
    assert 500 == mf['last_status_code']

def test_get_monitor_history_not_found_with_factories(client, monitor_factory):
  monitor_factory.create(url="123")
  response = client.get("/monitors/999/history?limit=2")
  assert response.status_code == 404
  data = response.json()
  assert "Monitor not found" in data["detail"]

def test_get_monitor_history_with_factories(client, session_fixture, monitor_factory, monitor_check_factory):
  # Create a monitor with factory
  m = monitor_factory.create()

  # Create 3 monitor checks in reverse chronological order
  for i in range(3):
    monitor_check_factory.create(
      monitor= m,
      checked_at= datetime.now(timezone.utc) - timedelta(minutes=i),
    )

  response = client.get(f"/monitors/{m.id}/history?limit=2")
  assert response.status_code == 200
  data = response.json()

  assert len(data) == 2
  assert data[0]["checked_at"] > data[1]["checked_at"]

def test_get_monitor_summary_happy_path(client, session_fixture, monitor_factory, monitor_check_factory):
  monitor = monitor_factory.create()

  # 2 successes, 1 failure
  monitor_check_factory.create(monitor=monitor, success=True, response_time_ms=100, checked_at=datetime.now(timezone.utc))
  monitor_check_factory.create(monitor=monitor, success=True, response_time_ms=200, checked_at=datetime.now(timezone.utc) - timedelta(minutes=1))
  monitor_check_factory.create(monitor=monitor, success=False, response_time_ms=150, checked_at=datetime.now(timezone.utc) - timedelta(minutes=2))

  session_fixture.commit()

  response = client.get(f"/monitors/{monitor.id}/summary")
  assert response.status_code == 200
  data = response.json()

  assert data["total_checks"] == 3
  assert data["success_checks"] == 2
  assert data["failed_checks"] == 1
  assert data["success_rate"] == pytest.approx(66.6666, 0.1)  # ~66.67%
  assert data["average_response_time_ms"] == pytest.approx((100+200+150)/3)

def test_get_monitor_summary_no_checks(client, session_fixture, monitor_factory):
  # Create a monitor with no checks
  monitor = monitor_factory.create()
  session_fixture.commit()

  # Call the API
  response = client.get(f"/monitors/{monitor.id}/summary")
  assert response.status_code == 200
  data = response.json()

  assert data["total_checks"] == 0
  assert data["success_checks"] == 0
  assert data["failed_checks"] == 0
  assert data["success_rate"] == 0.0
  assert data["average_response_time_ms"] == 0.0


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
