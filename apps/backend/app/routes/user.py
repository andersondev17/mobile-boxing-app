"""
User CRUD endpoints using Beanie ODM.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List

from models import User
from schemas import UserBase

router = APIRouter(prefix="/user", tags=["user"])


def _user_to_response(user: User) -> UserBase:
    """Convert Beanie document to response schema."""
    return UserBase(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        email_verified=user.email_verified,
        created_at=user.created_at,
    )


@router.get("/", response_model=List[UserBase])
async def get_users() -> List[UserBase]:
    """List all users (limited to 10)."""
    users = await User.find_all().limit(10).to_list()
    if not users:
        raise HTTPException(status_code=404, detail="Users not found")
    return [_user_to_response(u) for u in users]


@router.get("/{user_id}", response_model=UserBase)
async def get_user(user_id: str) -> UserBase:
    """Get a single user by ID."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


@router.delete("/{user_id}", response_model=dict)
async def delete_user(user_id: str) -> dict:
    """Delete a user by ID."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user.delete()
    return {"message": "User deleted successfully"}