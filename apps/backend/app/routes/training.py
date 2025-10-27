from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exec import SQLAlchemyError
from config import get_db
from models import Training
from schemas import TrainingBase
from typing import Annotated, List

router = APIRouter(prefix="/training", tags=["training"])

#dependencia sesion local
db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/", response_model=List[TrainingBase], status_code=status.HTTP_200_OK)
async def get_trainings(db: db_dependency) -> List[TrainingBase]:
    result = db.query(Training).limit(10).all()
    if not result:
        raise HTTPException(status_code=404, detail="Trainings not found")
    return result

@router.get("/{training_id}", response_model=TrainingBase, status_code=status.HTTP_200_OK)
async def get_training(training_id: str, db: db_dependency) -> TrainingBase:
    result = db.query(Training).filter(Training.id == training_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Trainings not found")
    return result