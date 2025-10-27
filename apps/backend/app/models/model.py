from sqlalchemy import Column, Integer, String, TIMESTAMP, func, ForeignKey, Boolean, Json
from config import Base

class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True)
    email = Column(String)
    name = Column(String)
    role = Column(String, ForeignKey("role.id"))
    email_verified = Column(Boolean)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Role(Base):
    __table__ = "role"

    id = Column(String, primary_key=True)
    description = Column(String)

class Training(Base):
    __tablename__ = "training"

    id = Column(String, primary_key=True)
    user_id= Column(String, ForeignKey("user.id"))
    title = Column(String)
    status = Column(Boolean)
    started_at = Column(TIMESTAMP(timezone=True), server_Default=func.now())
    ended_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Exercise(Base):
    __table__ = "exercise"

    id = Column(String, primary_key=True)
    title = Column(String)
    poster_url = Column(String, ForeignKey("poster_url.id"))
    category = Column(String, ForeignKey("category.id"))
    difficulty = Column(String, ForeignKey("difficulty.id"))
    duration_min = Column(String)
    description = Column(String)
    technique = Column(String)
    muscles = Column(Json)
    equipment = Column(String)

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