from sqlalchemy import Column, Integer, String, DateTime
from config import Base
from datetime import datetime

class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, index=True)
    name = Column(String, index=True)
    role = Column(String, index=True)
    email_verified = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
