# StatusBoard API

StatusBoard is a lightweight health monitoring service that tracks the uptime and response of your websites or services. It stores historical monitor checks, calculates success/failure rates, and provides an API for creating, updating, and fetching monitor data.

---

## Features (MVP)

- Add monitors with URL, name, expected status code, and active/inactive status.
- Automatic background monitoring with retry logic.
- Store monitor check history with response time and success/failure.
- Retrieve monitor summaries including success rate and average response time.
- Fetch monitor history with limits.
- Update or delete monitors.
- Fully tested endpoints and background jobs.

---

## Technology Stack

- **Python 3.12**
- **FastAPI** — API framework
- **SQLModel** (SQLAlchemy + Pydantic) — database models
- **SQLite** — in-memory or file-based database for MVP
- **Async HTTP requests** with `httpx`
- **Pytest** — for tests

---

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd status_board

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run database migrations (for MVP with SQLModel, create tables)
python -m app.database  # or run `create_all` in your main app

# Start the server
uvicorn app.main:app --reload
```

The API will be available at:

```bash
http://127.0.0.1:8000
```

Docs:

```bash
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc
```

# API Endpoints

## Monitors

Create a Monitor
```bash
POST /monitors/
```

### Request body (JSON)

```bash
{
  "url": "https://example.com",
  "name": "Example",
  "is_active": true,
  "expected_status_code": 200
}
```

### Response

```bash
{
  "id": 1,
  "url": "https://example.com",
  "name": "Example",
  "is_active": true,
  "expected_status_code": 200,
  "last_status_code": null,
  "last_error": null,
  "is_online": null,
  "last_checked_at": null,
  "response_time_ms": null,
  "created_at": "2025-09-06T00:00:00",
  "updated_at": "2025-09-06T00:00:00"
}
```

### Get All Monitors
GET /monitors/


Query parameters

* is_active (optional, boolean)
* url (optional, string)
* name (optional, string)

### Response

```bash
[
  {
    "id": 1,
    "url": "https://example.com",
    "name": "Example",
    "is_active": true,
    "expected_status_code": 200,
    "last_status_code": 200,
    "is_online": true
  }
]
```

### Update a Monitor

```bash
PATCH /monitors/{id}/
```

Request body (any subset of fields)

```bash
{
  "url": "https://example.org",
  "name": "New Name"
}
```

### Response

Updated monitor object (same format as create).

## Get Monitor History

```
GET /monitors/{id}/history?limit=10
```


* Returns the last limit monitor checks (default limit is configured in app)
* Each check includes timestamp, response time, success/failure, and error message if any.

## Get Monitor Summary

```
GET /monitors/{id}/summary
```

### Response

```
{
  "total_checks": 10,
  "success_checks": 8,
  "failed_checks": 2,
  "success_rate": 80.0,
  "average_response_time_ms": 120.5
}
```

## Testing

* Tests use pytest and factories.
* Run tests with:

  ```
  pytest tests/ -v
  ```

  * Includes tests for:
    - CRUD operations on monitors
    - Fetching history and summary
    - Background task logic
    - Retry behavior

### Background Monitoring

* Monitors are checked automatically in a background loop every 60 seconds.
* Uses async HTTP requests with retries.
* Stores results in the MonitorCheck table.
* Historical data is used to calculate success rate and average response time.

## Next Steps / Enhancements (Future)

* Email or Slack notifications on monitor failure.
* Configurable check intervals per monitor.
* Authentication and multi-user support.
* Dashboard UI for monitoring history.
* Persistent database with PostgreSQL or MySQL.

## Notes

This MVP is designed to give a working, testable monitoring API. The code is fully async-ready, making it easy to scale with more monitors or more frequent check intervals in the future.
