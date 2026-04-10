"""
Authentication service: login, register, token refresh.
Uses Beanie ODM for MongoDB operations.
"""

from fastapi import HTTPException
from models import User, Role
from auth import create_token, verify_password, hash_password
from schemas import UserCreate


async def login_user(email: str, password: str) -> dict | None:
    """Authenticate user with email/password and return JWT tokens."""
    user = await User.find_one(User.email == email)
    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        return None
    payload = {"sub": str(user.id), "email": user.email, "role": user.role or "user"}
    return {
        "access_token": create_token(payload, "access"),
        "refresh_token": create_token(payload, "refresh"),
    }


async def register_user(user_data: UserCreate) -> User | None:
    """Register a new user with email/password."""
    existing = await User.find_one(User.email == user_data.email)
    if existing:
        return None

    hashed = hash_password(user_data.password)
    role = await Role.find_one(Role.name == "user")

    new_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed,
        role=str(role.id) if role else None,
        email_verified=True,
        provider="email",
    )
    await new_user.insert()
    return new_user


def refresh_user_token(payload: dict) -> dict:
    """Generate new token pair from a valid refresh token payload."""
    return {
        "access_token": create_token(
            {"sub": payload["sub"], "email": payload.get("email"), "role": payload.get("role")},
        ),
        "refresh_token": create_token(
            {"sub": payload["sub"], "email": payload.get("email"), "role": payload.get("role")},
            "refresh",
        ),
    }
