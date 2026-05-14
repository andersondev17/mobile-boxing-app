"""
Monitoring and Metrics Routes

Endpoints for system monitoring, performance metrics, and health checks.
Provides real-time insights into ML model performance, API health, and user engagement.
"""

from typing import Dict, List, Optional
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.config.database import get_pg_session
from sqlalchemy.ext.asyncio import AsyncSession
from services.monitoring.monitoring_service import get_monitoring_service, MLModelMetrics
from app.auth import get_current_user

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

# Response Models
class HealthCheckResponse(BaseModel):
    """System health check response."""
    timestamp: str
    status: str
    checks: Dict[str, Dict]

class MLMetricsResponse(BaseModel):
    """ML model performance metrics."""
    accuracy: float
    precision: Dict[str, float]
    recall: Dict[str, float]
    confusion_matrix: Dict[str, Dict[str, int]]
    avg_response_time_ms: float
    total_predictions: int

class APIMetricsResponse(BaseModel):
    """API performance metrics."""
    total_calls: int
    error_rate: float
    avg_response_time: float
    endpoint_breakdown: Dict[str, Dict]
    time_range_hours: float

class UserEngagementResponse(BaseModel):
    """User engagement and activity metrics."""
    time_range_days: float
    total_activities: int
    activity_breakdown: Dict[str, int]
    avg_daily_active_users: float
    daily_active_users: Dict[str, int]
    total_sessions: int
    total_punches: int
    avg_technique_score: float
    active_users: int

class AlertResponse(BaseModel):
    """Alert information."""
    id: int
    type: str
    message: str
    severity: str
    timestamp: str
    acknowledged: bool

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    db: AsyncSession = Depends(get_pg_session)
):
    """
    Comprehensive system health check.
    
    Checks:
    - ML model accuracy and recent activity
    - API response times and error rates
    - Kafka message processing
    - Database connectivity
    
    Returns overall system status and individual component health.
    """
    try:
        monitoring = get_monitoring_service(db)
        health = await monitoring.get_system_health()
        return HealthCheckResponse(**health)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/health/simple")
async def simple_health_check() -> Dict:
    """
    Simple health check for load balancers and monitoring systems.
    
    Returns minimal status information for quick health verification.
    """
    return {
        "status": "healthy",
        "timestamp": "datetime.now(timezone.utc).isoformat()",
        "version": "1.0.0"
    }

@router.get("/metrics/ml", response_model=MLMetricsResponse)
async def get_ml_metrics(
    hours: int = Query(24, description="Time range in hours", ge=1, le=168),
    db: AsyncSession = Depends(get_pg_session),
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Get ML model performance metrics.
    
    Provides:
    - Overall accuracy
    - Precision and recall per punch type
    - Confusion matrix
    - Average response time
    - Total prediction count
    
    Requires authentication for detailed metrics.
    """
    try:
        monitoring = get_monitoring_service(db)
        time_range = timedelta(hours=hours)
        metrics = await monitoring.get_ml_metrics(time_range)
        
        return MLMetricsResponse(
            accuracy=metrics.accuracy,
            precision=metrics.precision,
            recall=metrics.recall,
            confusion_matrix=metrics.confusion_matrix,
            avg_response_time_ms=metrics.avg_response_time_ms,
            total_predictions=metrics.total_predictions
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ML metrics: {str(e)}"
        )

@router.get("/metrics/api", response_model=APIMetricsResponse)
async def get_api_metrics(
    hours: int = Query(24, description="Time range in hours", ge=1, le=168),
    db: AsyncSession = Depends(get_pg_session),
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Get API performance metrics.
    
    Provides:
    - Total API calls
    - Error rate percentage
    - Average response time
    - Per-endpoint breakdown
    - Request distribution
    
    Requires authentication for detailed metrics.
    """
    try:
        monitoring = get_monitoring_service(db)
        time_range = timedelta(hours=hours)
        metrics = await monitoring.get_api_metrics(time_range)
        
        return APIMetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get API metrics: {str(e)}"
        )

@router.get("/metrics/engagement", response_model=UserEngagementResponse)
async def get_engagement_metrics(
    days: int = Query(7, description="Time range in days", ge=1, le=30),
    db: AsyncSession = Depends(get_pg_session),
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Get user engagement and activity metrics.
    
    Provides:
    - Daily active users
    - Activity breakdown by type
    - Session statistics
    - Punch counts and technique scores
    - User retention indicators
    
    Requires authentication for detailed metrics.
    """
    try:
        monitoring = get_monitoring_service(db)
        time_range = timedelta(days=days)
        metrics = await monitoring.get_user_engagement_metrics(time_range)
        
        return UserEngagementResponse(**metrics)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get engagement metrics: {str(e)}"
        )

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    limit: int = Query(50, description="Maximum number of alerts", ge=1, le=1000),
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, critical"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    db: AsyncSession = Depends(get_pg_session),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get system alerts and notifications.
    
    Returns:
    - Recent system alerts
    - Performance warnings
    - Error notifications
    - Health check failures
    
    Requires authentication.
    """
    try:
        monitoring = get_monitoring_service(db)
        alerts = monitoring.get_recent_alerts(limit)
        
        # Apply filters
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        
        if acknowledged is not None:
            alerts = [a for a in alerts if a["acknowledged"] == acknowledged]
        
        return [AlertResponse(**alert) for alert in alerts]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alerts: {str(e)}"
        )

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_pg_session),
    current_user: Dict = Depends(get_current_user)
):
    """
    Acknowledge a system alert.
    
    Marks the alert as acknowledged to prevent repeated notifications.
    Requires authentication.
    """
    try:
        monitoring = get_monitoring_service(db)
        alerts = monitoring.get_recent_alerts(1000)
        
        # Find and update the alert
        for alert in alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_by"] = current_user.get("sub")
                alert["acknowledged_at"] = "datetime.now(timezone.utc).isoformat()"
                return {"message": f"Alert {alert_id} acknowledged"}
        
        raise HTTPException(
            status_code=404,
            detail=f"Alert {alert_id} not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to acknowledge alert: {str(e)}"
        )

@router.get("/dashboard")
async def get_dashboard_data(
    db: AsyncSession = Depends(get_pg_session),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get comprehensive dashboard data.
    
    Combines health, metrics, and alerts into a single response
    for dashboard applications.
    Requires authentication.
    """
    try:
        monitoring = get_monitoring_service(db)
        
        # Get all dashboard components
        health = await monitoring.get_system_health()
        ml_metrics = await monitoring.get_ml_metrics(timedelta(hours=24))
        api_metrics = await monitoring.get_api_metrics(timedelta(hours=24))
        engagement = await monitoring.get_user_engagement_metrics(timedelta(days=7))
        alerts = monitoring.get_recent_alerts(10)
        
        return {
            "health": health,
            "ml_metrics": {
                "accuracy": ml_metrics.accuracy,
                "total_predictions": ml_metrics.total_predictions,
                "avg_response_time_ms": ml_metrics.avg_response_time_ms
            },
            "api_metrics": {
                "total_calls": api_metrics["total_calls"],
                "error_rate": api_metrics["error_rate"],
                "avg_response_time": api_metrics["avg_response_time"]
            },
            "engagement": {
                "total_sessions": engagement["total_sessions"],
                "active_users": engagement["active_users"],
                "avg_daily_active_users": engagement["avg_daily_active_users"]
            },
            "recent_alerts": alerts[:5],  # Top 5 recent alerts
            "timestamp": "datetime.now(timezone.utc).isoformat()"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard data: {str(e)}"
        )

# Middleware for automatic metric collection
async def monitoring_middleware(request, call_next):
    """
    FastAPI middleware for automatic API metric collection.
    
    This middleware would be added to the FastAPI app to automatically
    track all API calls for monitoring purposes.
    """
    import time
    from services.monitoring_service import get_monitoring_service
    
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000
    
    # Record metrics (in production, this would be async)
    try:
        # Get monitoring service (would need DB session)
        # monitoring = get_monitoring_service(db_session)
        # await monitoring.record_api_call(
        #     endpoint=request.url.path,
        #     method=request.method,
        #     status_code=response.status_code,
        #     response_time_ms=response_time_ms
        # )
        pass  # Placeholder for now
    except Exception:
        # Don't let monitoring errors break the API
        pass
    
    return response






