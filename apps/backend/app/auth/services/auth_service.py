"""
Authentication service: login, register, token refresh.
Uses PostgreSQL for user management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.postgres import User
from auth import create_token, verify_password, hash_password
from schemas import UserCreate


async def login_user(email: str, password: str, db: AsyncSession) -> dict | None:
    """Authenticate user with email/password and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        return None
        
    payload = {"sub": str(user.id), "email": user.email, "role": user.role or "user"}
    return {
        "access_token": create_token(payload, "access"),
        "refresh_token": create_token(payload, "refresh"),
    }


async def register_user(user_data: UserCreate, db: AsyncSession) -> User | None:
    """Register a new user with email/password."""
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing = result.scalar_one_or_none()
    
    if existing:
        return None

    hashed = hash_password(user_data.password)
    
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed,
        role="user",
        email_verified=True,
        provider="email",
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
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
