import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Boolean, DateTime, UUID, Enum, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    """Registered application user stored in PostgreSQL."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, default="")
    hashed_password: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    provider: Mapped[str] = mapped_column(String, default="email")  # "email" | "google"
    provider_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, default="user")
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    birth_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    height: Mapped[Optional[float]] = mapped_column(nullable=True) # in cm
    weight: Mapped[Optional[float]] = mapped_column(nullable=True) # in kg
    sex: Mapped[Optional[str]] = mapped_column(String, nullable=True) # "M", "F", "Other"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class Exercise(Base):
    """Boxing exercise definition."""
    __tablename__ = "exercises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String, index=True)
    poster_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, index=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String, index=True)
    duration_min: Mapped[int] = mapped_column(default=5)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    technique: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    muscles: Mapped[list[str]] = mapped_column(JSON, default=list)
    equipment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Training(Base):
    """Training session record."""
    __tablename__ = "trainings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String)
    status: Mapped[bool] = mapped_column(default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class BoxingSession(Base):
    """Record of a boxing analysis session."""
    __tablename__ = "boxing_sessions"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    processed_filename: Mapped[str] = mapped_column(String, default="")
    frames_analyzed: Mapped[int] = mapped_column(default=0)
    baseline_used: Mapped[bool] = mapped_column(default=False)
    feedback_summary: Mapped[list[str]] = mapped_column(JSON, default=list)
    metrics_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    session_file: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    session_rows: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Punch type confirmation
    punch_type_detected: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    punch_type_confirmed: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_corrected: Mapped[bool] = mapped_column(default=False)


class Consent(Base):
    """Explicit user consent record (Ley 1581 Colombia)."""
    __tablename__ = "consents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    consent_type: Mapped[str] = mapped_column(String, index=True) # "biometric_data" | "technique_analysis" | "health_metrics"
    granted: Mapped[bool] = mapped_column(default=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    policy_version: Mapped[str] = mapped_column(String, default="1.0")


class UserMetrics(Base):
    """Aggregated biomechanical metrics per user."""
    __tablename__ = "user_metrics"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    avg_speed: Mapped[float] = mapped_column(default=0.0)
    fatigue_index: Mapped[float] = mapped_column(default=0.0)
    improvement_rate: Mapped[float] = mapped_column(default=0.0)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class SessionAnalytics(Base):
    """High-level summary of analysis sessions."""
    __tablename__ = "session_analytics"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    punch_count: Mapped[int] = mapped_column(default=0)
    duration_sec: Mapped[int] = mapped_column(default=0)
    avg_score: Mapped[float] = mapped_column(default=0.0)
    drop_off_point: Mapped[Optional[int]] = mapped_column(nullable=True) # frame_index where technique failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class TestRun(Base):
    """Web testing session record."""
    __tablename__ = "test_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    video_name: Mapped[str] = mapped_column(String, nullable=False)
    total_frames: Mapped[int] = mapped_column(default=0)
    scored_frames: Mapped[int] = mapped_column(default=0)
    avg_score: Mapped[float] = mapped_column(default=0.0)
    min_score: Mapped[float] = mapped_column(default=0.0)
    max_score: Mapped[float] = mapped_column(default=0.0)
    punch_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # JSON array as string
    processing_ms: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class UserProgress(Base):
    """Gamification: tracks XP and levels over time."""
    __tablename__ = "user_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    xp: Mapped[int] = mapped_column(default=0)
    level: Mapped[int] = mapped_column(default=1)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class Achievement(Base):
    """Gamification: Definition of rule-based achievements."""
    __tablename__ = "achievements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    condition: Mapped[str] = mapped_column(String, nullable=False)


class UserAchievement(Base):
    """Gamification: Unlocked achievements by users."""
    __tablename__ = "user_achievements"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    achievement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), primary_key=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)







