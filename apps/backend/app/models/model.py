from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from config import Base

class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True)
    email = Column(String)
    name = Column(String)
    role = Column(String)
    email_verified = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
