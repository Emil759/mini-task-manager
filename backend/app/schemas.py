# app/schemas.py
from datetime import date
from pydantic import BaseModel, Field


# ---------- AUTH ----------

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    # bcrypt ограничение: 72 bytes (важно!)
    password: str = Field(min_length=6, max_length=72)


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str = Field(min_length=6, max_length=72)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- HABITS ----------

class HabitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class HabitOut(BaseModel):
    id: int
    name: str
    owner_id: int

    class Config:
        from_attributes = True


# ---------- CHECKINS ----------

class CheckinOut(BaseModel):
    id: int
    habit_id: int
    date: date

    class Config:
        from_attributes = True
