"""
Boxing session and consent document models.
"""

from datetime import datetime, timezone
from typing import Optional

from beanie import Document
from pydantic import Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BoxingSession(Document):
    """Record of a boxing analysis session."""

    session_id: str
    user_id: Optional[str] = None
    processed_filename: str = ""
    frames_analyzed: int = 0
    baseline_used: bool = False
    feedback_summary: list[str] = Field(default_factory=list)
    metrics_path: Optional[str] = None
    session_file: Optional[str] = None
    session_rows: int = 0
    created_at: datetime = Field(default_factory=_utcnow)
    
    # New fields for punch type confirmation
    punch_type_detected: Optional[str] = None  # Tipo detectado automáticamente
    punch_type_confirmed: Optional[str] = None  # Tipo confirmado por usuario
    user_corrected: bool = False  # Si el usuario corrigió la detección

    class Settings:
        name = "boxing_sessions"
        indexes = [
            "session_id",
            "user_id",
        ]


class Consent(Document):
    """Explicit user consent record (Ley 1581 Colombia).

    Must be obtained before persisting any biometric data
    (landmarks, movement metrics, technique scores).
    """

    user_id: str
    consent_type: str  # "biometric_data" | "technique_analysis" | "health_metrics"
    granted: bool = False
    granted_at: datetime = Field(default_factory=_utcnow)
    revoked_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    policy_version: str = "1.0"

    class Settings:
        name = "consents"
        indexes = [
            "user_id",
            "consent_type",
        ]
