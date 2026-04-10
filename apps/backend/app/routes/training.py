"""
Training CRUD endpoints using Beanie ODM.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List

from models import Training
from schemas import TrainingBase, TrainingCreate

router = APIRouter(prefix="/training", tags=["training"])


def _training_to_response(t: Training) -> TrainingBase:
    """Convert Beanie document to response schema."""
    return TrainingBase(
        id=str(t.id),
        user_id=t.user_id,
        title=t.title,
        status=t.status,
        started_at=t.started_at,
        ended_at=t.ended_at,
    )


@router.get("/", response_model=List[TrainingBase], status_code=status.HTTP_200_OK)
async def get_trainings() -> List[TrainingBase]:
    """List all training sessions (limited to 10)."""
    trainings = await Training.find_all().limit(10).to_list()
    if not trainings:
        raise HTTPException(status_code=404, detail="Trainings not found")
    return [_training_to_response(t) for t in trainings]


@router.get("/{training_id}", response_model=TrainingBase, status_code=status.HTTP_200_OK)
async def get_training(training_id: str) -> TrainingBase:
    """Get a single training session by ID."""
    training = await Training.get(training_id)
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    return _training_to_response(training)


@router.post("/", response_model=TrainingBase, status_code=status.HTTP_201_CREATED)
async def add_training(training: TrainingCreate) -> TrainingBase:
    """Create a new training session."""
    new_training = Training(
        user_id=training.user_id,
        title=training.title,
    )
    await new_training.insert()
    return _training_to_response(new_training)


@router.put("/{training_id}", response_model=TrainingBase, status_code=status.HTTP_200_OK)
async def update_training(training_id: str, training: TrainingCreate) -> TrainingBase:
    """Update an existing training session."""
    existing = await Training.get(training_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Training not found")

    existing.user_id = training.user_id
    existing.title = training.title
    await existing.save()
    return _training_to_response(existing)


@router.delete("/{training_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_training(training_id: str) -> dict:
    """Delete a training session by ID."""
    training = await Training.get(training_id)
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    await training.delete()
    return {"message": "Training deleted successfully"}