"""
Training CRUD endpoints using SQLAlchemy / PostgreSQL.
"""

import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Training
from app.schemas import TrainingBase, TrainingCreate
from app.config.database import get_pg_session

router = APIRouter(prefix="/training", tags=["training"])


def _training_to_response(t: Training) -> TrainingBase:
    """Convert SQLAlchemy model to response schema."""
    return TrainingBase(
        id=str(t.id),
        user_id=str(t.user_id),
        title=t.title,
        status=t.status,
        started_at=t.started_at,
        ended_at=t.ended_at,
    )


@router.get("/", response_model=List[TrainingBase], status_code=status.HTTP_200_OK)
async def get_trainings(db: AsyncSession = Depends(get_pg_session)) -> List[TrainingBase]:
    """List all training sessions (limited to 10)."""
    stmt = select(Training).limit(10)
    result = await db.execute(stmt)
    trainings = result.scalars().all()
    if not trainings:
        raise HTTPException(status_code=404, detail="Trainings not found")
    return [_training_to_response(t) for t in trainings]


@router.get("/{training_id}", response_model=TrainingBase, status_code=status.HTTP_200_OK)
async def get_training(training_id: str, db: AsyncSession = Depends(get_pg_session)) -> TrainingBase:
    """Get a single training session by ID."""
    try:
        training_uuid = uuid.UUID(training_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    training = await db.get(Training, training_uuid)
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    return _training_to_response(training)


@router.post("/", response_model=TrainingBase, status_code=status.HTTP_201_CREATED)
async def add_training(training: TrainingCreate, db: AsyncSession = Depends(get_pg_session)) -> TrainingBase:
    """Create a new training session."""
    try:
        user_uuid = uuid.UUID(training.user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id UUID format")

    new_training = Training(
        user_id=user_uuid,
        title=training.title,
    )
    db.add(new_training)
    await db.commit()
    await db.refresh(new_training)
    return _training_to_response(new_training)


@router.put("/{training_id}", response_model=TrainingBase, status_code=status.HTTP_200_OK)
async def update_training(training_id: str, training: TrainingCreate, db: AsyncSession = Depends(get_pg_session)) -> TrainingBase:
    """Update an existing training session."""
    try:
        training_uuid = uuid.UUID(training_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    existing = await db.get(Training, training_uuid)
    if not existing:
        raise HTTPException(status_code=404, detail="Training not found")

    existing.user_id = uuid.UUID(training.user_id)
    existing.title = training.title
    await db.commit()
    await db.refresh(existing)
    return _training_to_response(existing)


@router.delete("/{training_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_training(training_id: str, db: AsyncSession = Depends(get_pg_session)) -> dict:
    """Delete a training session by ID."""
    try:
        training_uuid = uuid.UUID(training_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    training = await db.get(Training, training_uuid)
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")

    await db.delete(training)
    await db.commit()
    return {"message": "Training deleted successfully"}
