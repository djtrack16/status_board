from pydantic import ConfigDict, BaseModel
from sqlmodel import Field
from typing import Optional

class MonitorParams(BaseModel):
	id: Optional[int] = Field(default=None, primary_key=True)
	url: str
	is_active: bool = Field(default=True)
	expected_status_code: int = 200
	name: Optional[str] = None