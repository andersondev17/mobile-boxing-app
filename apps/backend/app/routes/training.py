from sqlalchemy.orm import Column, String, ForeingKey, TIMESTAMP
from config import Base

class Training(Base):
    __table__="training"

    id = Column(String, primary_key=True)
    