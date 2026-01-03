from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .database import SessionLocal, engine, Base
from . import models, schemas, crud

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mini Task Manager")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/tasks", response_model=schemas.TaskOut)
def add_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).first()
    if not user:
        user = crud.create_user(db, "test", "test")

    return crud.create_task(db, title=task.title, user_id=user.id, completed=task.completed)


@app.get("/tasks", response_model=list[schemas.TaskOut])
def read_tasks(db: Session = Depends(get_db)):
    user = db.query(models.User).first()
    if not user:
        return []
    return crud.get_tasks(db, user.id)
