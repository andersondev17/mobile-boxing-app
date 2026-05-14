from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Consent
from app.schemas import ConsentCreate, ConsentResponse
from app.config.database import get_pg_session

router = APIRouter(prefix="/consent", tags=["consent"])

def _clerk_id_to_uuid(clerk_id: str) -> uuid.UUID:
    """Convert Clerk user ID (user_1234567890abcdef) to UUID format."""
    # If it's already a UUID, return as-is
    try:
        return uuid.UUID(clerk_id)
    except ValueError:
        pass
    
    # Convert Clerk user ID (user_1234567890abcdef) to UUID format
    # Remove 'user_' prefix and pad/truncate to create a valid UUID
    clean_id = clerk_id.replace('user_', '')
    padded_id = clean_id.ljust(32, '0')[:32]
    formatted_uuid = f"{padded_id[0:8]}-{padded_id[8:12]}-{padded_id[12:16]}-{padded_id[16:20]}-{padded_id[20:32]}"
    
    return uuid.UUID(formatted_uuid)


@router.post("/", response_model=ConsentResponse)
async def grant_consent(
    consent: ConsentCreate,
    request: Request,
    user_id: str,
    db: AsyncSession = Depends(get_pg_session),
):
    """Record explicit user consent for data processing."""
    try:
        user_uuid = _clerk_id_to_uuid(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    # Upsert: update existing consent or create new
    stmt = select(Consent).where(
        Consent.user_id == user_uuid,
        Consent.consent_type == consent.consent_type
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    client_ip = request.client.host if request.client else None

    if existing:
        existing.granted = consent.granted
        existing.ip_address = client_ip
        if not consent.granted:
            existing.revoked_at = datetime.now(timezone.utc)
        else:
            existing.revoked_at = None
        doc = existing
    else:
        doc = Consent(
            user_id=user_uuid,
            consent_type=consent.consent_type,
            granted=consent.granted,
            ip_address=client_ip,
        )
        db.add(doc)

    await db.commit()
    await db.refresh(doc)

    return ConsentResponse(
        user_id=str(doc.user_id),
        consent_type=doc.consent_type,
        granted=doc.granted,
        granted_at=doc.granted_at,
        policy_version=doc.policy_version,
    )


@router.get("/{user_id}", response_model=List[ConsentResponse])
async def get_user_consents(user_id: str, db: AsyncSession = Depends(get_pg_session)) -> List[ConsentResponse]:
    """Get all consent records for a user."""
    try:
        user_uuid = _clerk_id_to_uuid(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    stmt = select(Consent).where(Consent.user_id == user_uuid)
    result = await db.execute(stmt)
    consents = result.scalars().all()

    return [
        ConsentResponse(
            user_id=str(c.user_id),
            consent_type=c.consent_type,
            granted=c.granted,
            granted_at=c.granted_at,
            policy_version=c.policy_version,
        )
        for c in consents
    ]


@router.get("/{user_id}/check")
async def check_consent(
    user_id: str, 
    consent_type: str = "biometric_data", 
    db: AsyncSession = Depends(get_pg_session)
) -> dict:
    """Quick check: does the user have active consent for a given type?"""
    try:
        user_uuid = _clerk_id_to_uuid(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    stmt = select(Consent).where(
        Consent.user_id == user_uuid,
        Consent.consent_type == consent_type,
        Consent.granted == True
    )
    result = await db.execute(stmt)
    consent = result.scalar_one_or_none()

    return {
        "user_id": user_id,
        "consent_type": consent_type,
        "has_consent": consent is not None,
    }






