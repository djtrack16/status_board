from datetime import UTC, datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

#from app.models.monitor import Monitor

class MonitorCheck(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  monitor_id: int = Field(foreign_key="monitor.id", index=True)
  checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
  status_code: Optional[int] = None
  success: bool = False
  response_time_ms: Optional[float] = None
  error_message: Optional[str] = None
  monitor: "Monitor" = Relationship(back_populates="checks") # type: ignore
