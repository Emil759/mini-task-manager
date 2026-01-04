from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from . import models
from .auth import hash_password


# -------- Users --------
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, username: str, password: str) -> models.User:
    user = models.User(username=username, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# -------- Habits --------
def create_habit(db: Session, name: str, owner_id: int) -> models.Habit:
    habit = models.Habit(name=name, owner_id=owner_id)
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


def get_habits(db: Session, owner_id: int):
    return db.query(models.Habit).filter(models.Habit.owner_id == owner_id).order_by(models.Habit.id.desc()).all()


def get_habit(db: Session, habit_id: int, owner_id: int):
    return db.query(models.Habit).filter(and_(models.Habit.id == habit_id, models.Habit.owner_id == owner_id)).first()


def delete_habit(db: Session, habit: models.Habit):
    db.delete(habit)
    db.commit()


# -------- Check-ins --------
def add_checkin(db: Session, habit_id: int, checkin_date: date) -> models.CheckIn:
    checkin = models.CheckIn(habit_id=habit_id, date=checkin_date)
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin


def list_checkins(db: Session, habit_id: int, date_from: date | None = None, date_to: date | None = None):
    q = db.query(models.CheckIn).filter(models.CheckIn.habit_id == habit_id).order_by(models.CheckIn.date.desc())
    if date_from:
        q = q.filter(models.CheckIn.date >= date_from)
    if date_to:
        q = q.filter(models.CheckIn.date <= date_to)
    return q.all()
