"""
Google OAuth service: user creation and auth code management.
Uses Beanie ODM for MongoDB operations.
"""

import uuid
from datetime import datetime, timezone, timedelta

from models import User, Role, AuthCode


async def get_or_create_google_user(google_user) -> User:
    """Find existing user by email or create a new Google-authenticated user."""
    role = await Role.find_one(Role.name == "user")
    user_db = await User.find_one(User.email == google_user.email)

    if not user_db:
        user_db = User(
            email=google_user.email,
            name=google_user.name,
            role=str(role.id) if role else None,
            email_verified=True,
            provider="google",
        )
        await user_db.insert()

    return user_db


async def create_auth_code(user: User) -> str:
    """Create a temporary auth code for OAuth token exchange."""
    code = str(uuid.uuid4())
    auth_code = AuthCode(
        code=code,
        user_email=user.email,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=2),
    )
    await auth_code.insert()
    return code
