from sqlmodel import SQLModel, Field, Relationship
from datetime import UTC, datetime
from typing import List, Optional

#from app.models.monitor_check import MonitorCheck

class Monitor(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	url: str
	name: Optional[str] = None
	is_active: bool = Field(default=True)
	last_status_code: Optional[int] = None
	last_error: Optional[str] = None
	is_online: Optional[bool] = None
	last_checked_at: Optional[datetime] = None
	response_time_ms: Optional[float] = None # in milliseconds
	expected_status_code: int = 200
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	checks: List["MonitorCheck"] = Relationship(back_populates="monitor") # type: ignore


