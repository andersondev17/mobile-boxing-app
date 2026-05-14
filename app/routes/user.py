from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from app.schemas import UserBase
from app.config.database import get_pg_session

router = APIRouter(prefix="/user", tags=["user"])


def _user_to_response(user: User) -> UserBase:
    """Convert SQLAlchemy model to response schema."""
    return UserBase(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        email_verified=user.email_verified,
        created_at=user.created_at,
    )


@router.get("/", response_model=List[UserBase])
async def get_users(db: AsyncSession = Depends(get_pg_session)) -> List[UserBase]:
    """List all users (limited to 10)."""
    stmt = select(User).limit(10)
    result = await db.execute(stmt)
    users = result.scalars().all()
    if not users:
        raise HTTPException(status_code=404, detail="Users not found")
    return [_user_to_response(u) for u in users]


@router.get("/{user_id}", response_model=UserBase)
async def get_user(user_id: str, db: AsyncSession = Depends(get_pg_session)) -> UserBase:
    """Get a single user by ID."""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id UUID format")

    user = await db.get(User, user_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


@router.delete("/{user_id}", response_model=dict)
async def delete_user(user_id: str, db: AsyncSession = Depends(get_pg_session)) -> dict:
    """Delete a user by ID."""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id UUID format")

    user = await db.get(User, user_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted successfully"}

