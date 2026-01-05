# Mini Task Manager – Backend

Small backend service built with FastAPI and PostgreSQL.

## Tech stack
- Python 3.10+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Docker
- Pytest

## Run locally (without Docker)
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r ../requirements.txt
python -m uvicorn app.main:app --reload

RUN
cd backend
docker compose up -d

Health check

Open in browser:

http://127.0.0.1:8000/health
Tests

From project root:

pytest
