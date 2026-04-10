"""
Consent management endpoints (Ley 1581 Colombia).

Users must grant explicit consent before any biometric data
(landmarks, movement metrics, technique scores) is persisted.
"""

from fastapi import APIRouter, HTTPException, Request
from typing import List

from models import Consent
from schemas import ConsentCreate, ConsentResponse

router = APIRouter(prefix="/consent", tags=["consent"])


@router.post("/", response_model=ConsentResponse)
async def grant_consent(
    consent: ConsentCreate,
    request: Request,
    user_id: str = None,
):
    """Record explicit user consent for data processing.

    Must be called from the mobile app's consent screen
    before the user accesses technique analysis features.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    # Upsert: update existing consent or create new
    existing = await Consent.find_one(
        Consent.user_id == user_id,
        Consent.consent_type == consent.consent_type,
    )

    client_ip = request.client.host if request.client else None

    if existing:
        existing.granted = consent.granted
        existing.ip_address = client_ip
        if not consent.granted:
            from datetime import datetime, timezone
            existing.revoked_at = datetime.now(timezone.utc)
        await existing.save()
        doc = existing
    else:
        doc = Consent(
            user_id=user_id,
            consent_type=consent.consent_type,
            granted=consent.granted,
            ip_address=client_ip,
        )
        await doc.insert()

    return ConsentResponse(
        user_id=doc.user_id,
        consent_type=doc.consent_type,
        granted=doc.granted,
        granted_at=doc.granted_at,
        policy_version=doc.policy_version,
    )


@router.get("/{user_id}", response_model=List[ConsentResponse])
async def get_user_consents(user_id: str) -> List[ConsentResponse]:
    """Get all consent records for a user."""
    consents = await Consent.find(Consent.user_id == user_id).to_list()
    return [
        ConsentResponse(
            user_id=c.user_id,
            consent_type=c.consent_type,
            granted=c.granted,
            granted_at=c.granted_at,
            policy_version=c.policy_version,
        )
        for c in consents
    ]


@router.get("/{user_id}/check")
async def check_consent(user_id: str, consent_type: str = "biometric_data") -> dict:
    """Quick check: does the user have active consent for a given type?

    Used by the WebSocket handler and technique analysis endpoints
    to gate access to biometric processing.
    """
    consent = await Consent.find_one(
        Consent.user_id == user_id,
        Consent.consent_type == consent_type,
        Consent.granted == True,
    )
    return {
        "user_id": user_id,
        "consent_type": consent_type,
        "has_consent": consent is not None,
    }
