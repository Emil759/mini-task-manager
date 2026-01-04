# app/auth.py
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import HTTPException
from jose import jwt
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "secret123")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _ensure_bcrypt_password_limit(password: str) -> None:
    # bcrypt: максимум 72 байта
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password too long (bcrypt max 72 bytes)")


def hash_password(password: str) -> str:
    _ensure_bcrypt_password_limit(password)
    try:
        return pwd_context.hash(password)
    except Exception as e:
        # вместо 500 без объяснений — понятный текст
        raise HTTPException(status_code=500, detail=f"Password hashing error: {type(e).__name__}")


def verify_password(password: str, hashed: str) -> bool:
    _ensure_bcrypt_password_limit(password)
    return pwd_context.verify(password, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
