from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    id: str
    email: str
    name: str
    role: str
    email_verified: int
    created_at: datetime
    
    class Config:
        from_attributes  = True

class TrainingBase(BaseModel):
    id: str
    user_id: str
    title: str
    status: bool
    started_at: datetime
    ended_at: datetime

    class Config:
        from_attributes = True

class ExerciseBase(BaseModel):
    id: str
    title: str
    poster_url: str
    category: str
    difficulty: str
    duration_min: str
    description: str
    technique: str
    muscles: dict
    equipment: str

    class Config:
        from_attributes = True