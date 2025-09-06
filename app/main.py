import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from app.routers.monitors import router
from sqlmodel import SQLModel, Session
from app.database import engine
from contextlib import asynccontextmanager
#from workers import scheduler
from app.services.monitor_service import check_all_monitors

@asynccontextmanager
async def lifespan(app: FastAPI):
  # Startup: create DB tables
  SQLModel.metadata.create_all(engine)

  # Startup: launch background loop
  task = asyncio.create_task(monitor_loop())
  yield
  # Shutdown: cancel background loop
  task.cancel()
  try:
    await task
  except asyncio.CancelledError:
    print("Background monitor loop stopped.")

app = FastAPI(lifespan=lifespan)
app.include_router(router, prefix="/monitors", tags=["monitors"])

@app.get("/")
def root():
  return {"hooray": "StatusBoard API is running"}

# 🔁 background task
async def monitor_loop():
  while True:
    try:
      with Session(engine) as session:
        await check_all_monitors(session)
    except Exception as e:
      print(f"[Monitor Loop] Error: {e}")
    await asyncio.sleep(60)  # run every 60s