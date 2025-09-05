from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import field_validator


class MonitorQueryParams(SQLModel):
	is_active: Optional[bool] = None

	@field_validator("is_active", mode="before")
	@classmethod
	def normalize_bool(cls, v):
		if isinstance(v, bool):
			return v
		if isinstance(v, str):
			v_lower = v.lower()
			if v_lower in {"true", "1", "yes", "on"}:
				return True
			if v_lower in {"false", "0", "no", "off"}:
				return False
		return v