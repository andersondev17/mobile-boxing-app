from sqlalchemy import Column, Integer, String, DateTime, TIMESTAMP, func, ForeignKey, Boolean, JSON
from config import Base
import uuid
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    role = Column(String, ForeignKey("role.id"))  # relación directa
    role_rel = relationship("Role", back_populates="users")
    email_verified = Column(Boolean, default=False)
    hashed_password = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Role(Base):
    __tablename__ = "role"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    users = relationship("User", back_populates="role_rel")

class Training(Base):
    __tablename__ = "training"

    id = Column(String, primary_key=True)
    user_id= Column(String, ForeignKey("user.id"))
    title = Column(String)
    status = Column(Boolean)
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    ended_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Exercise(Base):
    __tablename__ = "exercise"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    poster_url = Column(String) # URL string
    video_url = Column(String)  # URL string for demonstration
    category_id = Column("category", String, ForeignKey("category.id"))
    difficulty_id = Column("difficulty", String, ForeignKey("difficulty.id"))
    duration_min = Column(Integer, default=5)
    description = Column(String)
    technique = Column(String)
    muscles = Column(JSON) # Array of strings
    equipment = Column(String)

    category = relationship("Category")
    difficulty = relationship("Difficulty")

class PosterUrl(Base):
    __tablename__ = "poster_url"
    
    id = Column(String, primary_key=True)
    url = Column(String)

class Category(Base):
    __tablename__ = "category"

    id = Column(String, primary_key=True)
    description = Column(String)

class Difficulty(Base):
    __tablename__ = "difficulty"

    id = Column(String, primary_key = True)
    description = Column(String)
    
class AuthCode(Base):
    __tablename__ = "auth_codes"
    code = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_email = Column(String, nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=2))
