from sqlalchemy.orm import Session
from . import models

def create_user(db: Session, username: str, password: str) -> models.User:
    # Для мини-проекта нам не нужна криптография паролей — это можно добавить позже (JWT/bcrypt)
    user = models.User(
        username=username,
        hashed_password="test"  # фиксированно, чтобы не было bcrypt-ограничений
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_task(db: Session, title: str, user_id: int, completed: bool = False) -> models.Task:
    task = models.Task(title=title, completed=completed, owner_id=user_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_tasks(db: Session, user_id: int):
    return db.query(models.Task).filter(models.Task.owner_id == user_id).all()
