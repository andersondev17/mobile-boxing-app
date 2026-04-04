from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
import traceback
import sys
from typing import List
from config import get_db
from models import Exercise
from schemas import ExerciseBase

router = APIRouter(prefix="/exercises", tags=["exercises"])

@router.get("/", response_model=List[ExerciseBase])
def get_exercises(db: Session = Depends(get_db)):
    try:
        exercises = db.query(Exercise).options(
            joinedload(Exercise.category),
            joinedload(Exercise.difficulty)
        ).all()
        return exercises
    except Exception as e:
        print("❌ [BACKEND-ERROR] Detailed traceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{exercise_id}", response_model=ExerciseBase)
def get_exercise(exercise_id: str, db: Session = Depends(get_db)):
    try:
        exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        return exercise
    except Exception as e:
        print("❌ [BACKEND-ERROR] Detailed traceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))
