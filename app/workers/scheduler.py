'''
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx
from datetime import UTC, datetime
from sqlmodel import Session, select
from models.monitor import Monitor
from database import engine

SCHEDULER = AsyncIOScheduler()

RETRY_CONFIG = Retry(
  max_retries=3,
  backoff_factor=0.5,
  status_force_list=[500, 502, 503, 504],
  allowed_methods=["GET"]
)

HTTP_REQUEST_TIMEOUT_LIMIT_SECONDS=10

HEALTH_CHECK_INTERVAL_IN_MINUTES=5

import httpx
import asyncio

async def fetch_with_retries(url: str, retries: int = 3, delay: float = 1.0):
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                response.raise_for_status()
                return response
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            if attempt == retries - 1:
                raise  # Give up on final attempt
            await asyncio.sleep(delay * 2**attempt)  # Exponential backoff


async def check_monitor(session: Session, monitor: Monitor):
  start_time = datetime.now(UTC)
  try:
    async with httpx.AsyncClient(
      transport = TRANSPORT,
      timeout=HTTP_REQUEST_TIMEOUT_LIMIT_SECONDS
    ) as client:
      await client.get(monitor.url)

    end_time = datetime.now(UTC)
    monitor.last_response_time = (end_time - start_time).total_seconds()
    monitor.last_checked_at = end_time
  except Exception as e:
    failure_time = datetime.now(UTC)
    monitor.last_failure_at = failure_time
    monitor.last_error_message = f"{e}"
    monitor.last_response_time = None
    monitor.last_checked_at = failure_time

  session.add(monitor)
  session.commit()

def schedule_jobs():
  SCHEDULER.add_job(run_all_checks, 'interval', minutes=HEALTH_CHECK_INTERVAL_IN_MINUTES)
  SCHEDULER.start()

async def run_all_checks():
  with Session(engine) as session:
    monitors = session.exec(select(Monitor)).all()
    for monitor in monitors:
      await check_monitor(session, monitor)
'''