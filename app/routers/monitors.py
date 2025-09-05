from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.models.monitor import Monitor, MonitorParams, MonitorQueryParams
from app.models.monitor_check import MonitorCheck
from app.services import monitor_service
from app.database import get_session

router = APIRouter()

DEFAULT_MONITOR_HISTORY_LIMIT = 20

@router.post("/", response_model=Monitor)
def create_monitor(monitor: Monitor, session: Session = Depends(get_session)) -> Monitor:
  session.add(monitor)
  session.commit()
  session.refresh(monitor)
  return monitor

@router.patch('/{id}', response_model=Monitor)
def update_monitor(
  id: int, monitor_params: MonitorParams, session: Session = Depends(get_session)
):
  return monitor_service.update_monitor(id, monitor_params, session)

@router.get('/', response_model=List[Monitor])
def fetch_monitor(
  query_params: MonitorQueryParams = Depends(),
  session: Session = Depends(get_session)
) -> List[Monitor]:
  return monitor_service.fetch_monitors(query_params, session)

@router.delete('/{id}', response_model=None)
def delete_monitor(id: int, session: Session = Depends(get_session)):
  return monitor_service.delete(id, session)

@router.get('/{monitor_id}/history', response_model=List[MonitorCheck]) # should id be monitor_id?
def monitor_history(
  monitor_id: int,
  limit: int = DEFAULT_MONITOR_HISTORY_LIMIT,
  session: Session = Depends()
) -> List[MonitorCheck]:
  return monitor_service.get_monitor_history(session, monitor_id, limit)

@router.get("/{monitor_id}/summary")
def get_monitor_summary(
    monitor_id: int,
    session: Session = Depends(get_session),
) -> dict[str, float]:
  return monitor_service.get_monitor_summary(session, monitor_id)
