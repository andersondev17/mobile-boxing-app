# auth/services/auth_service.py
from sqlalchemy.orm import Session
from models import User
from auth import create_token, verify_password, hash_password

def login_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    payload = {"sub": user.id, "role": "user"}
    return {
        "access_token": create_token(payload, "access"),
        "refresh_token": create_token(payload, "refresh")
    }

def refresh_user_token(payload: dict):
    return {
        "access_token": create_token({"sub": payload["sub"], "role": payload.get("role")}),
        "refresh_token": create_token({"sub": payload["sub"], "role": payload.get("role")}, "refresh")
    }
