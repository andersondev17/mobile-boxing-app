# auth/services/auth_service.py
from sqlalchemy.orm import Session
from models import User, Role
from auth import create_token, verify_password, hash_password
from schemas import UserCreate, LoginRequest
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

def login_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        return None
    payload = {"sub": user.id, "role": "user"}
    return {
        "access_token": create_token(payload, "access"),
        "refresh_token": create_token(payload, "refresh")
    }

def register_user(db: Session, user: UserCreate):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        return None

    hashed = hash_password(user.password)

    role = db.query(Role).filter(Role.name=="user").one_or_none()

    new_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed,
        role=role.id if role else None,
        email_verified=True
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(404, detail=f"Database Error: {e}")
    

def refresh_user_token(payload: dict):
    return {
        "access_token": create_token({"sub": payload["sub"], "role": payload.get("role")}),
        "refresh_token": create_token({"sub": payload["sub"], "role": payload.get("role")}, "refresh")
    }
