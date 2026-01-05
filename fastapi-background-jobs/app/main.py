from fastapi import FastAPI
from sqlalchemy import text

from app.api.tasks import router as tasks_router
from app.db.session import engine

app = FastAPI(title="FastAPI Background Jobs")

app.include_router(tasks_router)


@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
