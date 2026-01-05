import time
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.db.models import Task
from app.db.session import SessionLocal


@celery_app.task(name="process_task")
def process_task(task_id: int) -> None:
    db: Session = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if not task:
            return

        task.status = "processing"
        db.commit()

        time.sleep(2)

        task.result = (task.payload or "").upper()
        task.status = "done"
        db.commit()
    except Exception:
        task = db.get(Task, task_id)
        if task:
            task.status = "failed"
            db.commit()
        raise
    finally:
        db.close()
