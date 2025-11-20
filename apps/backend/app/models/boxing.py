import uuid
from sqlalchemy import Boolean, Column, Integer, JSON, String, TIMESTAMP, func

from config import Base


class BoxingSession(Base):
    __tablename__ = "boxing_session"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, unique=True, nullable=False)
    processed_filename = Column(String, nullable=False)
    frames_analyzed = Column(Integer, nullable=False, default=0)
    baseline_used = Column(Boolean, nullable=False, default=False)
    feedback_summary = Column(JSON, nullable=False, default=list)
    metrics_path = Column(String, nullable=True)
    session_file = Column(String, nullable=True)
    session_rows = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

