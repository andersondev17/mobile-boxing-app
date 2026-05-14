"""
Hybrid ML Analysis Routes

Endpoints for punch classification using the Random Forest + DTW hybrid approach.
This provides fast, accurate punch type detection with confidence scoring.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from app.config.database import get_pg_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import get_current_user
from services.ml.models.hybrid_classifier import get_hybrid_classifier
from app.routes.consent import check_consent
from services.events.technique_producer import TechniqueProducer

router = APIRouter(prefix="/analysis", tags=["Hybrid Analysis"])

# Request/Response Models
class LandmarkFrame(BaseModel):
    """Single frame of landmark data."""
    timestamp: float
    landmarks: List[Dict]

class PunchAnalysisRequest(BaseModel):
    """Request for punch type analysis."""
    session_id: str = Field(..., description="Training session identifier")
    landmarks: List[LandmarkFrame] = Field(..., description="Sequence of landmark frames")
    user_id: Optional[str] = Field(None, description="User ID (if authenticated)")

class PunchAnalysisResponse(BaseModel):
    """Response from punch analysis."""
    punch_type: str
    confidence: float
    method: str
    details: Dict
    session_id: str

class FeatureImportanceResponse(BaseModel):
    """Response with feature importance from RF model."""
    feature_importance: Dict[str, float]

@router.post("/punch-classify", response_model=PunchAnalysisResponse)
async def classify_punch(
    request: PunchAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_pg_session),
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Classify punch type using hybrid RF + DTW approach.
    
    Process:
    1. Check biometric consent (Ley 1581)
    2. Extract features from landmark sequence
    3. RF filtering -> top-k predictions
    4. DTW validation against selected baselines
    5. Return final classification with confidence
    """
    
    # Get user ID from app.authentication or request
    user_id = current_user.get("sub") if current_user else request.user_id
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check biometric consent (Ley 1581 compliance)
    consent_check = await check_consent(user_id, "biometric_data")
    if not consent_check.get("has_consent", False):
        raise HTTPException(
            status_code=403, 
            detail="Biometric consent required for punch analysis"
        )
    
    try:
        # Convert landmark frames to list of dictionaries
        landmark_sequence = []
        for frame in request.landmarks:
            frame_data = {"timestamp": frame.timestamp}
            if frame.landmarks:
                frame_data.update(frame.landmarks[0])
            landmark_sequence.append(frame_data)
        
        # Get hybrid classifier
        classifier = get_hybrid_classifier()
        
        # Perform classification
        result = classifier.classify_punch(landmark_sequence)
        
        # Add session info
        result["session_id"] = request.session_id
        
        # Publish result to Kafka for analytics (async)
        background_tasks.add_task(
            _publish_analysis_result,
            user_id=user_id,
            session_id=request.session_id,
            result=result
        )
        
        return PunchAnalysisResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@router.get("/feature-importance", response_model=FeatureImportanceResponse)
async def get_feature_importance(
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Get feature importance from the Random Forest model.
    Useful for understanding which biomechanical features matter most.
    """
    classifier = get_hybrid_classifier()
    importance = classifier.get_feature_importance()
    
    if importance is None:
        raise HTTPException(
            status_code=503,
            detail="Feature importance not available - model not loaded"
        )
    
    return FeatureImportanceResponse(feature_importance=importance)

@router.post("/batch-classify")
async def batch_classify_punches(
    requests: List[PunchAnalysisRequest],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_pg_session),
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Classify multiple punch sequences in batch.
    Useful for processing recorded training sessions.
    """
    user_id = current_user.get("sub") if current_user else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check consent once for all requests
    consent_check = await check_consent(user_id, "biometric_data")
    if not consent_check.get("has_consent", False):
        raise HTTPException(
            status_code=403, 
            detail="Biometric consent required for punch analysis"
        )
    
    classifier = get_hybrid_classifier()
    results = []
    
    for request in requests:
        try:
            # Convert landmark frames
            landmark_sequence = []
            for frame in request.landmarks:
                frame_data = {"timestamp": frame.timestamp}
                if frame.landmarks:
                    frame_data.update(frame.landmarks[0])
                landmark_sequence.append(frame_data)
            
            # Classify
            result = classifier.classify_punch(landmark_sequence)
            result["session_id"] = request.session_id
            
            results.append(PunchAnalysisResponse(**result))
            
            # Publish to Kafka
            background_tasks.add_task(
                _publish_analysis_result,
                user_id=user_id,
                session_id=request.session_id,
                result=result
            )
            
        except Exception as e:
            # Add error result but continue processing others
            results.append(PunchAnalysisResponse(
                punch_type="error",
                confidence=0.0,
                method="error",
                details={"error": str(e)},
                session_id=request.session_id
            ))
    
    return {"results": results, "processed": len(results), "total": len(requests)}

async def _publish_analysis_result(user_id: str, session_id: str, result: Dict):
    """
    Publish analysis result to Kafka for analytics and gamification.
    
    This runs in background to avoid blocking the response.
    """
    try:
        producer = TechniqueProducer()
        
        # Publish punch detection event
        await producer.send_punch_detected(
            user_id=user_id,
            session_id=session_id,
            punch_type=result["punch_type"],
            dtw_score=result["confidence"],
            metadata={
                "method": result["method"],
                "feature_count": result["details"].get("feature_count", 0)
            }
        )
        
        # If confidence is high, publish quality score
        if result["confidence"] > 0.7:
            await producer.send_dtw_score(
                user_id=user_id,
                session_id=session_id,
                punch_type=result["punch_type"],
                dtw_score=result["confidence"],
                feedback_details=result["details"]
            )
            
    except Exception as e:
        # Log error but don't fail the main request
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to publish analysis result to Kafka: {e}")






