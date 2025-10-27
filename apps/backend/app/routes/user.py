from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List
from config import get_db
from models import User
from schemas import UserBase
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/user", tags=["user"])

#dependencia de sesión de base datos
db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/", response_model=List[UserBase])
async def get_users(db: db_dependency) -> List[UserBase]:
    result = db.query(User).limit(10).all()
    if not result:
        raise HTTPException(status_code=404, detail="Users not found")
    
    return result

@router.get("/{user_id}", response_model=UserBase)
async def get_user(user_id: str, db: db_dependency) -> UserBase:
    result = db.query(User).filter(User.id == user_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    return result

@router.post("/", response_model=UserBase, status_code=status.HTTP_201_CREATED)
async def add_user(user: UserBase, db: db_dependency) -> UserBase:
    existing_user = db.query(User).filter(User.id == user.id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this ID already exists")

    db_user = User(**user.model_dump())

    try: 
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
                    
@router.put("/{user_id}", response_model=UserBase, status_code=status.HTTP_200_OK)
async def update_user(user_id: str, user: UserBase, db: db_dependency) -> UserBase:
    result = db.query(User).filter(User.id == user_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    for field, value in user.model_dump().items():
        if value is not None:
            setattr(result, field, value)

    try:
        db.commit()
        db.refresh(result)
        return result
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/{user_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_user(user_id: str, db: db_dependency) -> dict:
    result = db.query(User).filter(User.id == user_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        db.delete(result)
        db.commit()
        return {"message":"User deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")