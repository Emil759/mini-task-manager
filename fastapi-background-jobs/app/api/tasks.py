from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.models import Task
from app.db.session import get_db
from app.workers.tasks import process_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    payload: str | None = None


class TaskOut(BaseModel):
    id: int
    status: str
    payload: str | None = None
    result: str | None = None

    class Config:
        from_attributes = True


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    task = Task(payload=data.payload, status="pending")
    db.add(task)
    db.commit()
    db.refresh(task)

    # 🔴 ВОТ ЭТА СТРОКА БЫЛА НУЖНА
    process_task.delay(task.id)

    return task


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
