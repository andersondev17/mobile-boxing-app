from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated, List
from config import get_db
from models import User
from schemas import UserBase

router = APIRouter(prefix="/user", tags=["user"])

db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/", response_model=List[UserBase])
async def get_users(db: db_dependency) -> List[UserBase]:
    result = db.query(User).all()
    if not result:
        raise HTTPException(status_code=404, detail="Users not found")
    return result