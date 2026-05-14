from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Exercise
from app.schemas import ExerciseBase
from app.config.database import get_pg_session

router = APIRouter(prefix="/exercises", tags=["exercises"])


def _exercise_to_response(ex: Exercise) -> ExerciseBase:
    """Convert SQLAlchemy model to response schema."""
    return ExerciseBase(
        id=str(ex.id),
        title=ex.title,
        poster_url=ex.poster_url,
        video_url=ex.video_url,
        category=ex.category,
        difficulty=ex.difficulty,
        duration_min=ex.duration_min,
        description=ex.description,
        technique=ex.technique,
        muscles=ex.muscles,
        equipment=ex.equipment,
    )


@router.get("/", response_model=List[ExerciseBase])
async def get_exercises(db: AsyncSession = Depends(get_pg_session)) -> List[ExerciseBase]:
    """List all exercises."""
    result = await db.execute(select(Exercise))
    exercises = result.scalars().all()
    return [_exercise_to_response(ex) for ex in exercises]


@router.get("/{exercise_id}", response_model=ExerciseBase)
async def get_exercise(exercise_id: str, db: AsyncSession = Depends(get_pg_session)) -> ExerciseBase:
    """Get a single exercise by ID."""
    import uuid
    try:
        ex_uuid = uuid.UUID(exercise_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    exercise = await db.get(Exercise, ex_uuid)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return _exercise_to_response(exercise)






