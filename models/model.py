"""
MongoDB document models using Beanie ODM.

Each class maps to a MongoDB collection. Beanie handles
serialization, validation (via Pydantic), and async CRUD.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from beanie import Document
from pydantic import Field


def _utcnow() -> datetime:
    """Timezone-aware UTC now."""
    return datetime.now(timezone.utc)


class User(Document):
    """Registered application user."""

    email: str
    name: str = ""
    role: Optional[str] = None
    email_verified: bool = False
    hashed_password: Optional[str] = None
    provider: Optional[str] = None  # "email" | "google"
    created_at: datetime = Field(default_factory=_utcnow)

    class Settings:
        name = "users"
        indexes = [
            "email",
        ]


class Role(Document):
    """Application role (admin, trainer, user)."""

    name: str

    class Settings:
        name = "roles"
        indexes = [
            "name",
        ]


class Training(Document):
    """Training session record."""

    user_id: str
    title: str
    status: bool = False
    started_at: datetime = Field(default_factory=_utcnow)
    ended_at: Optional[datetime] = None

    class Settings:
        name = "trainings"
        indexes = [
            "user_id",
        ]


class Exercise(Document):
    """Boxing exercise definition."""

    title: str
    poster_url: Optional[str] = None
    video_url: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    duration_min: int = 5
    description: Optional[str] = None
    technique: Optional[str] = None
    muscles: list[str] = Field(default_factory=list)
    equipment: Optional[str] = None

    class Settings:
        name = "exercises"
        indexes = [
            "title",
            "category",
        ]


class Category(Document):
    """Exercise category."""

    name: str
    description: str = ""

    class Settings:
        name = "categories"


class Difficulty(Document):
    """Exercise difficulty level."""

    name: str
    description: str = ""

    class Settings:
        name = "difficulties"


class AuthCode(Document):
    """Temporary OAuth authorization code for token exchange."""

    code: str
    user_email: str
    expires_at: datetime = Field(
        default_factory=lambda: _utcnow() + timedelta(minutes=2)
    )

    class Settings:
        name = "auth_codes"
        indexes = [
            "code",
        ]






