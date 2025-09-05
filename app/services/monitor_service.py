from typing import List, cast
from fastapi import Response
from sqlalchemy import func
from app.models.monitor_check import MonitorCheck
from app.models.monitor import Monitor, MonitorParams, MonitorQueryParams
from sqlmodel import Session, select
from app.utils.http import fetch_with_retries, raise_404
from time import perf_counter
from sqlalchemy.sql.elements import ColumnElement
from datetime import datetime

def fetch_monitors(query_params: MonitorQueryParams, session: Session) -> List[Monitor]:
  query = select(Monitor)

  if query_params.url:
    query = query.where(func.lower(Monitor.url).contains(query_params.url.lower()))
  if query_params.name:
    query = query.where(Monitor.name.ilike(f"%{query_params.name}%")) # type: ignore

  if query_params.is_active is not None:
    query = query.where(Monitor.is_active == query_params.is_active)

  if query_params.last_status_code:
    query = query.where(Monitor.last_status_code == query_params.last_status_code)

  monitors = list(session.exec(query).all())
  return monitors

def update_monitor(monitor_id: int, monitor_params: MonitorParams, session: Session):
  monitor = session.get(Monitor, monitor_id)
  if not monitor:
    raise_404(f"Monitor with id={monitor_id} not found")

  updated_data = monitor_params.model_dump(exclude_unset=True)
  for field, value in updated_data.items():
    setattr(monitor, field, value)
  
  session.add(monitor)
  session.commit()
  session.refresh(monitor)
  return monitor

def delete(monitor_id: int, session: Session):
  try:
    monitor = session.get(Monitor, monitor_id)
    if not monitor:
      raise_404(f"Monitor with id={monitor_id} not found")
    session.delete(monitor)
    session.commit()
    return Response(status_code=204)
  except Exception as e:
    session.rollback()
    print(f"An unexpected error occurred: {e}")

async def check_all_monitors(session: Session):
  """
  Loop through all monitors in DB and check them.
  """
  monitors = session.exec(select(Monitor)).all()
  for monitor in monitors:
    await check_monitor(session, monitor)

async def check_monitor(session: Session, monitor: Monitor):
  """
  Check the health of a monitor by pinging its URL with retries.
  Update monitor status in DB.
  """
  start_time = perf_counter()
  query = select(MonitorCheck).where(Monitor.id == monitor.id)
  check = session.exec(query).one()
  if not check:
    raise_404(f"MonitorCheck with monitor_id={monitor.id} not found")

  try:
    response = await fetch_with_retries(monitor.url)
    check.status_code = response.status_code
    check.success = True
  except Exception as e:
    check.success = False
    check.error_message = str(e)
  finally:
    elapsed_time = (perf_counter() - start_time) * 1000 
    check.response_time_ms = elapsed_time
    session.add(check)
    session.commit()

def get_monitor_history(session: Session, monitor_id: int, limit: int) -> List[MonitorCheck]:
  monitor = session.get(Monitor, monitor_id)
  if not monitor:
    raise_404(f'Monitor not found with id: {monitor_id}')
  
  mc_timestamp = cast("ColumnElement[datetime]", MonitorCheck.checked_at)

  query = (
    select(MonitorCheck)
    .where(MonitorCheck.monitor_id == monitor_id)
    .order_by(mc_timestamp.desc())
    .limit(limit)
  )
  
  monitor_checks = session.exec(query).all()

  return list(monitor_checks)

def get_monitor_summary(session: Session, monitor_id: int) -> dict[str, float]:
  monitor = session.get(Monitor, monitor_id)
  if not monitor:
    raise_404(f'Monitor not found with id: {monitor_id}')

  checks = session.exec(
    select(MonitorCheck).where(MonitorCheck.monitor_id == monitor_id)
  ).all()

  total = len(checks)
  if total == 0:
    return {
      "total_checks": 0,
      "success_checks": 0,
      "failed_checks": 0,
      "success_rate": 0.0,
      "average_response_time_ms": 0.0,
    }

  success_checks = sum(1 for c in checks if c.success)
  failed_checks = total - success_checks
  avg_response_time = sum(c.response_time_ms for c in checks if c.response_time_ms) / total

  return {
    "total_checks": total,
    "success_checks": success_checks,
    "failed_checks": failed_checks,
    "success_rate": (success_checks / total) * 100,
    "average_response_time_ms": avg_response_time,
  }