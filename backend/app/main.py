# app/main.py
from datetime import date

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import schemas, crud, models
from app.database import Base, engine
from app.dependencies import get_db, get_current_user
from app.auth import verify_password, create_access_token

app = FastAPI(title="Habit Tracker API")

Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- AUTH ----------

@app.post("/auth/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_username(db, username=payload.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    user = crud.create_user(db, username=payload.username, password=payload.password)
    return user


# ВАЖНО: теперь login принимает form-data (OAuth2PasswordRequestForm),
# чтобы Swagger Authorize работал.
@app.post("/auth/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


# ---------- HABITS (JWT PROTECTED) ----------

@app.get("/habits", response_model=list[schemas.HabitOut])
def list_habits(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return crud.get_habits(db, owner_id=user.id)


@app.post("/habits", response_model=schemas.HabitOut, status_code=201)
def create_habit(
    payload: schemas.HabitCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return crud.create_habit(db, name=payload.name, owner_id=user.id)


@app.delete("/habits/{habit_id}", status_code=204)
def delete_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    habit = crud.get_habit(db, habit_id=habit_id, owner_id=user.id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    crud.delete_habit(db, habit)
    return None


# ---------- CHECKINS (JWT PROTECTED) ----------

@app.post("/habits/{habit_id}/checkins", response_model=schemas.CheckinOut, status_code=201)
def create_checkin(
    habit_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    habit = crud.get_habit(db, habit_id=habit_id, owner_id=user.id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    return crud.add_checkin(db, habit_id=habit_id, checkin_date=date.today())


@app.get("/habits/{habit_id}/checkins", response_model=list[schemas.CheckinOut])
def list_checkins(
    habit_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    habit = crud.get_habit(db, habit_id=habit_id, owner_id=user.id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    return crud.list_checkins(db, habit_id=habit_id)
