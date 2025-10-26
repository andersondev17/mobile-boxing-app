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
        orm_mode = True
