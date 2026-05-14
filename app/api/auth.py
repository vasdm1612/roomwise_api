"""Authentication routes."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, verify_password
from app.schemas import Token, UserCreate, UserLogin, UserRead
from app.services.crud import create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: sqlite3.Connection = Depends(get_db)) -> dict:
    """Register a new user."""

    if get_user_by_email(db, user.email):
        raise HTTPException(status_code=409, detail="User with this email already exists")
    return create_user(db, user)


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: sqlite3.Connection = Depends(get_db)) -> Token:
    """Validate credentials and return a JWT token."""

    user = get_user_by_email(db, credentials.email)
    if user is None or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="User is inactive")
    return Token(access_token=create_access_token(str(user["id"])))


@router.get("/me", response_model=UserRead)
def read_me(current_user: dict = Depends(get_current_user)) -> dict:
    """Return information about the authenticated user."""

    return current_user
