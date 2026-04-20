"""
Google OAuth service: user creation and auth code management.
Uses PostgreSQL for user management and MongoDB for temporary auth codes.
"""

import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.postgres import User
from models.model import AuthCode


async def get_or_create_google_user(google_user, db: AsyncSession) -> User:
    """Find existing user by email or create a new Google-authenticated user."""
    result = await db.execute(select(User).where(User.email == google_user.email))
    user_db = result.scalar_one_or_none()

    if not user_db:
        user_db = User(
            email=google_user.email,
            name=google_user.name,
            role="user",
            email_verified=True,
            provider="google",
            provider_id=google_user.sub if hasattr(google_user, "sub") else None
        )
        db.add(user_db)
        await db.commit()
        await db.refresh(user_db)

    return user_db


async def create_auth_code(user: User) -> str:
    """Create a temporary auth code for OAuth token exchange in MongoDB."""
    code = str(uuid.uuid4())
    auth_code = AuthCode(
        code=code,
        user_email=user.email,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=2),
    )
    await auth_code.insert()
    return code
