from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
    id: str
    email: str
    name: str
    role: str
    email_verified: int
    created_at: datetime
