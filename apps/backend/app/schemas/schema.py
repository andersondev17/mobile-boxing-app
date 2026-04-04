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

class UserCreate(BaseModel):
    email: str
    name: str
    password: str

class TrainingBase(BaseModel):
    id: str
    user_id: str
    title: str
    status: bool
    started_at: datetime
    ended_at: datetime

    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    id: str
    description: str
    class Config:
        from_attributes = True

class DifficultyBase(BaseModel):
    id: str
    description: str
    class Config:
        from_attributes = True

class ExerciseBase(BaseModel):
    id: str
    title: str
    poster_url: str | None = None
    video_url: str | None = None
    category_id: str | None = None
    difficulty_id: str | None = None
    duration_min: int
    description: str | None = None
    technique: str | None = None
    muscles: list[str] | None = None
    equipment: str | None = None
    
    category: CategoryBase | None = None
    difficulty: DifficultyBase | None = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: str
    role: str | None = None

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleUser(BaseModel):
    email: str
    name: str