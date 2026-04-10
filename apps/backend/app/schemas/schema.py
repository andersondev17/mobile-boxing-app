"""
Pydantic schemas for request/response validation.

These are separate from the Beanie Document models.
Documents = database shape, Schemas = API shape.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── User ─────────────────────────────────────────────────────

class UserBase(BaseModel):
    """User response schema."""
    id: str
    email: str
    name: str
    role: Optional[str] = None
    email_verified: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """User registration request."""
    email: str
    name: str
    password: str


# ── Training ─────────────────────────────────────────────────

class TrainingBase(BaseModel):
    """Training session schema."""
    id: str
    user_id: str
    title: str
    status: bool = False
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrainingCreate(BaseModel):
    """Create training request."""
    user_id: str
    title: str


# ── Exercise ─────────────────────────────────────────────────

class ExerciseBase(BaseModel):
    """Exercise response schema."""
    id: str
    title: str
    poster_url: Optional[str] = None
    video_url: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    duration_min: int = 5
    description: Optional[str] = None
    technique: Optional[str] = None
    muscles: list[str] = []
    equipment: Optional[str] = None

    class Config:
        from_attributes = True


# ── Auth ─────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: str
    role: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleUser(BaseModel):
    email: str
    name: str


# ── Consent ──────────────────────────────────────────────────

class ConsentCreate(BaseModel):
    """Consent grant request (Ley 1581 Colombia)."""
    consent_type: str  # "biometric_data" | "technique_analysis" | "health_metrics"
    granted: bool


class ConsentResponse(BaseModel):
    """Consent status response."""
    user_id: str
    consent_type: str
    granted: bool
    granted_at: Optional[datetime] = None
    policy_version: str = "1.0"