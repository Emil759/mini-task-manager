from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, UniqueConstraint, func
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    habits = relationship("Habit", back_populates="owner", cascade="all, delete")


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="habits")

    checkins = relationship("CheckIn", back_populates="habit", cascade="all, delete")


class CheckIn(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    habit = relationship("Habit", back_populates="checkins")

    __table_args__ = (
        UniqueConstraint("habit_id", "date", name="uq_checkin_habit_date"),
    )
