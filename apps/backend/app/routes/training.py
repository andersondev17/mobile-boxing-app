from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
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
        raise HTTPException(status_code=404, detail="Training not found")
    return result

@router.post("/", response_model=TrainingBase, status_code=status.HTTP_201_CREATED)
async def add_training(training: TrainingBase, db: db_dependency) -> TrainingBase:
    result = db.query(TrainingBase).filter(TrainingBase.id == training.id).first()
    if result:
        raise HTTPException(status_code=404, detail="Training already existed")
    
    db_training = Training(**training.model_dump())

    try:
        db.add(db_training)
        db.commit()
        db.refresh(db_training)
        return db_training
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    
@router.put("/{training_id}", response_model=TrainingBase, status_code=status.HTTP_200_OK)
async def update_training(training_id: str, training: TrainingBase, db: db_dependency) -> TrainingBase:
    result = db.query(Training).filter(Training.id == training_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Training not found") 

    for field, value in training.model_dump().items():
        if value is not None:
            setattr(result, field, value)

    try:
        db.commit()
        db.refresh(result)
        return result
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=f"Database error: {e}")
    
@router.delete("/{training_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_training(training_id: str, db: db_dependency) -> dict:
    result = db.query(Training).filter(Training.id == training_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Training not found")
    
    try:
        db.delete(result)
        db.commit()
        return {"message":"training deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=f"Database error: {e}")