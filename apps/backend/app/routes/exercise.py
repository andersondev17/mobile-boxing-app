"""
Exercise endpoints using Beanie ODM.
"""

from fastapi import APIRouter, HTTPException
from typing import List

from models import Exercise
from schemas import ExerciseBase

router = APIRouter(prefix="/exercises", tags=["exercises"])


def _exercise_to_response(ex: Exercise) -> ExerciseBase:
    """Convert Beanie document to response schema."""
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
async def get_exercises() -> List[ExerciseBase]:
    """List all exercises."""
    exercises = await Exercise.find_all().to_list()
    return [_exercise_to_response(ex) for ex in exercises]


@router.get("/{exercise_id}", response_model=ExerciseBase)
async def get_exercise(exercise_id: str) -> ExerciseBase:
    """Get a single exercise by ID."""
    exercise = await Exercise.get(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return _exercise_to_response(exercise)
