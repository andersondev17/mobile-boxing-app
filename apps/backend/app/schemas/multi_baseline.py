"""
Multi-baseline analysis schemas for hybrid RF + DTW pipeline.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class MultiBaselineRequest(BaseModel):
    """Request schema for multi-baseline analysis."""
    features: List[Dict[str, Any]] = Field(
        ..., 
        description="List of feature dictionaries from user sequence"
    )
    threshold: float = Field(
        default=15.0, 
        ge=0.0, 
        le=50.0,
        description="DTW score threshold for valid punch detection"
    )

class MultiBaselineResponse(BaseModel):
    """Response schema for multi-baseline analysis."""
    success: bool
    punch_type: str
    dtw_score: float
    is_valid: bool
    rf_predictions: List[Dict[str, Any]] = []
    all_scores: Dict[str, float] = {}
    threshold_used: float
    system_status: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    class Config:
        json_encoders = {
            float: lambda v: float(v) if v is not None else None
        }

class SystemStatusResponse(BaseModel):
    """System status for multi-baseline analyzer."""
    baselines_loaded: bool
    model_loaded: bool
    punch_types: List[str]
    total_baselines: int
