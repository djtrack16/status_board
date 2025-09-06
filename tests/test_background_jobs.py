from contextlib import suppress
from httpx import ASGITransport, AsyncClient
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.main import app
from app.models.monitor_check import MonitorCheck
from app.services import monitor_service
from app.main import monitor_loop
from tests.config import(
  monitor_factory,
  monitor_check_factory,
  session_fixture,
  engine_fixture
)

@pytest.mark.asyncio
async def test_check_monitor_success(session_fixture, monitor_factory, monitor_check_factory):
  # Arrange: create monitor and monitor check
  monitor = monitor_factory.create()
  check = monitor_check_factory.create(monitor=monitor)

  # Patch fetch_with_retries to always return a mock response
  mock_response = AsyncMock()
  mock_response.status_code = 200
  with patch("app.services.monitor_service.fetch_with_retries", return_value=mock_response):
    # Act
    await monitor_service.check_monitor(session_fixture, monitor)
  
  # Assert
  session_fixture.refresh(check)
  assert check.success is True
  assert check.status_code == 200
  assert check.response_time_ms > 0


@pytest.mark.asyncio
async def test_check_monitor_failure(session_fixture, monitor_factory, monitor_check_factory):
  monitor = monitor_factory.create()
  check = monitor_check_factory.create(monitor=monitor)

  # Patch fetch_with_retries to raise an exception
  with patch("app.services.monitor_service.fetch_with_retries", side_effect=Exception("fail")):
    await monitor_service.check_monitor(session_fixture, monitor)

  session_fixture.refresh(check)
  assert check.success is False
  assert check.error_message == "fail"
  assert check.response_time_ms > 0


@pytest.mark.asyncio
async def test_check_all_monitors_calls_check_monitor(session_fixture, monitor_factory, monitor_check_factory):
  # Arrange: create multiple monitors
  monitors = [monitor_factory.create() for _ in range(2)]
  for m in monitors:
    monitor_check_factory.create(monitor=m)

  # Patch check_monitor so we just track calls
  with patch("app.services.monitor_service.check_monitor", new_callable=AsyncMock) as mock_check:
    await monitor_service.check_all_monitors(session_fixture)
  
  # Assert that check_monitor was called once per monitor
  assert mock_check.call_count == len(monitors)

@pytest.mark.asyncio
async def test_monitor_loop_calls_check_all_once():
  # Patch check_all_monitors
  with patch("app.main.check_all_monitors", new_callable=AsyncMock) as mock_check:
    # Patch asyncio.sleep to exit immediately after first iteration
    async def fake_sleep(duration):
      raise asyncio.CancelledError()  # stops the loop after first sleep

    with patch("asyncio.sleep", new=fake_sleep):
      # Run monitor_loop
      with suppress(asyncio.CancelledError):
        await monitor_loop()
    
    # check_all_monitors should have been called exactly once
    assert mock_check.call_count == 1

@pytest.mark.asyncio
async def test_monitor_loop_handles_exceptions_gracefully():
  # Patch check_all_monitors to raise an exception
  with patch("app.main.check_all_monitors", new_callable=AsyncMock) as mock_check:
    mock_check.side_effect = Exception("Boom!")
    
    async def fake_sleep(duration):
      raise asyncio.CancelledError()  # exit after first iteration

    with patch("asyncio.sleep", new=fake_sleep):
      # Run monitor_loop
      with suppress(asyncio.CancelledError):
        await monitor_loop()

    # Loop should have tried to call check_all_monitors once, even with exception
    assert mock_check.call_count == 1
'''
@pytest.mark.asyncio
async def test_monitor_loop_runs_multiple_iterations():
  mock_check = AsyncMock()

  # Save original asyncio.sleep
  original_sleep = asyncio.sleep

  async def fake_sleep(seconds):
    await original_sleep(0)  # yield control to event loop

  with patch.object(monitor_service, "check_all_monitors", mock_check):
    with patch("asyncio.sleep", new=fake_sleep):
      task = asyncio.create_task(monitor_loop())

      # Allow loop to run a few iterations
      for _ in range(3):
        await original_sleep(0)

      # Cancel the loop
      task.cancel()
      with suppress(asyncio.CancelledError):
        await task

  assert mock_check.call_count >= 3
'''
