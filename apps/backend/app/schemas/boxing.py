from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class BaselineResponse(BaseModel):
    status: str
    rows: int


class SessionSaveResponse(BaseModel):
    status: str
    file: str
    rows: int


class BoxingStatusResponse(BaseModel):
    success: bool
    baseline_loaded: bool
    sessions: Dict[str, int]


class CleanupResponse(BaseModel):
    message: str
    temp_files_deleted: int
    output_files_deleted: int
    uploads_deleted: int
    metrics_deleted: int


class BoxingSessionSchema(BaseModel):
    id: str
    session_id: str
    processed_filename: str
    frames_analyzed: int
    baseline_used: bool
    feedback_summary: List[str]
    metrics_path: Optional[str] = None
    session_file: Optional[str] = None
    session_rows: int
    created_at: datetime

    class Config:
        from_attributes = True
