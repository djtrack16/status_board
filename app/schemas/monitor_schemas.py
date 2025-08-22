from pydantic import BaseModel, HttpUrl
from typing import Optional

class URLCreate(BaseModel):
  url: HttpUrl
  name: Optional[str] = None

class URLUpdate(BaseModel):
  name: Optional[str]
  url: Optional[HttpUrl]

class URLStatus(BaseModel):
  id: int
  url: HttpUrl
  status_code: Optional[int]
  response_time_ms: Optional[float]
  last_checked: Optional[str]