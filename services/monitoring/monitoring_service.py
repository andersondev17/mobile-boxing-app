"""
Monitoring and Metrics Service

Provides comprehensive monitoring for:
- ML model performance and accuracy
- API response times and error rates
- Kafka message processing
- User engagement and gamification metrics
- System health and resource usage
"""

import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import defaultdict, deque
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from models.postgres import SessionAnalytics, UserMetrics, TestRun
from app.schemas import settings

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: datetime
    value: float
    tags: Dict[str, str]

@dataclass
class MLModelMetrics:
    """ML model performance metrics."""
    accuracy: float
    precision: Dict[str, float]  # per punch type
    recall: Dict[str, float]     # per punch type
    confusion_matrix: Dict[str, Dict[str, int]]
    avg_response_time_ms: float
    total_predictions: int

class MonitoringService:
    """
    Central monitoring service for all application metrics.
    
    Features:
    - Real-time metric collection
    - Historical trend analysis
    - Alerting on threshold breaches
    - Performance dashboards
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._metrics_cache = defaultdict(lambda: deque(maxlen=1000))
        self._alerts = []
        
    async def record_ml_prediction(self, 
                              predicted_type: str, 
                              actual_type: Optional[str] = None,
                              confidence: float = 0.0,
                              response_time_ms: float = 0.0) -> None:
        """
        Record ML prediction for performance tracking.
        
        Args:
            predicted_type: Predicted punch type
            actual_type: Ground truth (if available)
            confidence: Model confidence score
            response_time_ms: Prediction response time
        """
        timestamp = datetime.now(timezone.utc)
        
        # Store prediction metrics
        self._metrics_cache["ml_predictions"].append(
            MetricPoint(timestamp, 1.0, {
                "predicted": predicted_type,
                "actual": actual_type or "unknown",
                "confidence_bucket": self._get_confidence_bucket(confidence)
            })
        )
        
        # Store response time metrics
        self._metrics_cache["ml_response_time"].append(
            MetricPoint(timestamp, response_time_ms, {"model": "hybrid_rf_dtw"})
        )
        
        # If we have ground truth, update accuracy metrics
        if actual_type:
            await self._update_ml_accuracy(predicted_type, actual_type, timestamp)
    
    async def record_api_call(self, 
                           endpoint: str, 
                           method: str,
                           status_code: int,
                           response_time_ms: float,
                           user_id: Optional[str] = None) -> None:
        """
        Record API call metrics.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: Response status code
            response_time_ms: Response time in milliseconds
            user_id: User identifier (if available)
        """
        timestamp = datetime.now(timezone.utc)
        
        self._metrics_cache["api_calls"].append(
            MetricPoint(timestamp, 1.0, {
                "endpoint": endpoint,
                "method": method,
                "status": str(status_code),
                "error": str(status_code >= 400)
            })
        )
        
        self._metrics_cache["api_response_time"].append(
            MetricPoint(timestamp, response_time_ms, {
                "endpoint": endpoint,
                "method": method
            })
        )
        
        # Check for slow endpoints
        if response_time_ms > 2000:  # 2 second threshold
            await self._create_alert(
                "slow_api",
                f"Slow API response: {endpoint} took {response_time_ms}ms",
                severity="warning"
            )
    
    async def record_kafka_message(self, 
                                topic: str,
                                message_type: str,
                                processing_time_ms: float = 0.0,
                                success: bool = True) -> None:
        """
        Record Kafka message processing metrics.
        
        Args:
            topic: Kafka topic name
            message_type: Type of message
            processing_time_ms: Time to process message
            success: Whether processing succeeded
        """
        timestamp = datetime.now(timezone.utc)
        
        self._metrics_cache["kafka_messages"].append(
            MetricPoint(timestamp, 1.0, {
                "topic": topic,
                "message_type": message_type,
                "success": str(success)
            })
        )
        
        if processing_time_ms > 0:
            self._metrics_cache["kafka_processing_time"].append(
                MetricPoint(timestamp, processing_time_ms, {
                    "topic": topic,
                    "message_type": message_type
                })
            )
    
    async def record_user_activity(self, 
                                user_id: str,
                                activity_type: str,
                                metadata: Optional[Dict] = None) -> None:
        """
        Record user activity for engagement tracking.
        
        Args:
            user_id: User identifier
            activity_type: Type of activity (login, workout, achievement, etc.)
            metadata: Additional activity data
        """
        timestamp = datetime.now(timezone.utc)
        
        self._metrics_cache["user_activity"].append(
            MetricPoint(timestamp, 1.0, {
                "user_id": user_id,
                "activity_type": activity_type,
                **(metadata or {})
            })
        )
    
    async def get_ml_metrics(self, 
                          time_range: timedelta = timedelta(hours=24)) -> MLModelMetrics:
        """
        Get ML model performance metrics.
        
        Args:
            time_range: Time window for metrics
            
        Returns:
            MLModelMetrics with performance data
        """
        cutoff_time = datetime.now(timezone.utc) - time_range
        
        # Get recent predictions with ground truth
        recent_predictions = [
            m for m in self._metrics_cache["ml_predictions"]
            if m.timestamp > cutoff_time and m.tags.get("actual") != "unknown"
        ]
        
        if not recent_predictions:
            return MLModelMetrics(0.0, {}, {}, {}, 0.0, 0)
        
        # Calculate confusion matrix
        punch_types = ["jab", "cross", "hook", "uppercut"]
        confusion_matrix = {pt: {pt2: 0 for pt2 in punch_types} for pt in punch_types}
        
        correct_predictions = 0
        for pred in recent_predictions:
            predicted = pred.tags["predicted"]
            actual = pred.tags["actual"]
            
            if predicted in confusion_matrix and actual in confusion_matrix[predicted]:
                confusion_matrix[predicted][actual] += 1
                
            if predicted == actual:
                correct_predictions += 1
        
        # Calculate overall accuracy
        accuracy = correct_predictions / len(recent_predictions)
        
        # Calculate precision and recall per class
        precision = {}
        recall = {}
        
        for punch_type in punch_types:
            # Precision = TP / (TP + FP)
            tp = confusion_matrix[punch_type][punch_type]
            fp = sum(confusion_matrix[punch_type][other] for other in punch_types if other != punch_type)
            precision[punch_type] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            
            # Recall = TP / (TP + FN)
            fn = sum(confusion_matrix[other][punch_type] for other in punch_types if other != punch_type)
            recall[punch_type] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        # Average response time
        response_times = [
            m.value for m in self._metrics_cache["ml_response_time"]
            if m.timestamp > cutoff_time
        ]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        return MLModelMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            confusion_matrix=confusion_matrix,
            avg_response_time_ms=avg_response_time,
            total_predictions=len(recent_predictions)
        )
    
    async def get_api_metrics(self, 
                           time_range: timedelta = timedelta(hours=24)) -> Dict:
        """Get API performance metrics."""
        cutoff_time = datetime.now(timezone.utc) - time_range
        
        # Filter recent API calls
        recent_calls = [
            m for m in self._metrics_cache["api_calls"]
            if m.timestamp > cutoff_time
        ]
        
        recent_response_times = [
            m for m in self._metrics_cache["api_response_time"]
            if m.timestamp > cutoff_time
        ]
        
        if not recent_calls:
            return {"total_calls": 0, "error_rate": 0.0, "avg_response_time": 0.0}
        
        # Calculate error rate
        error_calls = [m for m in recent_calls if m.tags.get("error") == "True"]
        error_rate = len(error_calls) / len(recent_calls)
        
        # Calculate average response time
        avg_response_time = (
            sum(m.value for m in recent_response_times) / len(recent_response_times)
            if recent_response_times else 0.0
        )
        
        # Group by endpoint
        endpoint_stats = defaultdict(lambda: {"calls": 0, "errors": 0, "total_time": 0})
        
        for call in recent_calls:
            endpoint = call.tags["endpoint"]
            endpoint_stats[endpoint]["calls"] += 1
            if call.tags.get("error") == "True":
                endpoint_stats[endpoint]["errors"] += 1
        
        for rt in recent_response_times:
            endpoint = rt.tags["endpoint"]
            endpoint_stats[endpoint]["total_time"] += rt.value
        
        # Calculate per-endpoint metrics
        endpoint_metrics = {}
        for endpoint, stats in endpoint_stats.items():
            endpoint_metrics[endpoint] = {
                "calls": stats["calls"],
                "errors": stats["errors"],
                "error_rate": stats["errors"] / stats["calls"] if stats["calls"] > 0 else 0.0,
                "avg_response_time": stats["total_time"] / stats["calls"] if stats["calls"] > 0 else 0.0
            }
        
        return {
            "total_calls": len(recent_calls),
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "endpoint_breakdown": endpoint_metrics,
            "time_range_hours": time_range.total_seconds() / 3600
        }
    
    async def get_user_engagement_metrics(self, 
                                     time_range: timedelta = timedelta(days=7)) -> Dict:
        """Get user engagement and gamification metrics."""
        cutoff_time = datetime.now(timezone.utc) - time_range
        
        # Get recent user activities
        recent_activities = [
            m for m in self._metrics_cache["user_activity"]
            if m.timestamp > cutoff_time
        ]
        
        # Group by activity type
        activity_counts = defaultdict(int)
        daily_active_users = defaultdict(set)
        
        for activity in recent_activities:
            activity_type = activity.tags["activity_type"]
            activity_counts[activity_type] += 1
            
            # Track daily active users
            date_key = activity.timestamp.date().isoformat()
            user_id = activity.tags["user_id"]
            daily_active_users[date_key].add(user_id)
        
        # Calculate DAU (Daily Active Users)
        dau_values = [len(users) for users in daily_active_users.values()]
        avg_dau = sum(dau_values) / len(dau_values) if dau_values else 0
        
        # Get database metrics for more comprehensive view
        db_metrics = await self._get_database_engagement_metrics(time_range)
        
        return {
            "time_range_days": time_range.total_seconds() / 86400,
            "total_activities": len(recent_activities),
            "activity_breakdown": dict(activity_counts),
            "avg_daily_active_users": avg_dau,
            "daily_active_users": {
                date: len(users) for date, users in daily_active_users.items()
            },
            **db_metrics
        }
    
    async def get_system_health(self) -> Dict:
        """Get overall system health status."""
        health_status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "healthy",
            "checks": {}
        }
        
        # Check ML model health
        ml_metrics = await self.get_ml_metrics(timedelta(minutes=30))
        if ml_metrics.total_predictions == 0:
            health_status["checks"]["ml_model"] = {
                "status": "warning",
                "message": "No recent predictions"
            }
        elif ml_metrics.accuracy < 0.7:
            health_status["checks"]["ml_model"] = {
                "status": "critical",
                "message": f"Low accuracy: {ml_metrics.accuracy:.2%}"
            }
        else:
            health_status["checks"]["ml_model"] = {
                "status": "healthy",
                "accuracy": ml_metrics.accuracy
            }
        
        # Check API health
        api_metrics = await self.get_api_metrics(timedelta(minutes=30))
        if api_metrics["error_rate"] > 0.1:  # 10% error rate threshold
            health_status["checks"]["api"] = {
                "status": "critical",
                "message": f"High error rate: {api_metrics['error_rate']:.2%}"
            }
        elif api_metrics["avg_response_time"] > 1000:  # 1 second threshold
            health_status["checks"]["api"] = {
                "status": "warning",
                "message": f"Slow responses: {api_metrics['avg_response_time']:.0f}ms"
            }
        else:
            health_status["checks"]["api"] = {
                "status": "healthy",
                "avg_response_time": api_metrics["avg_response_time"]
            }
        
        # Check Kafka health (simplified)
        recent_kafka = [
            m for m in self._metrics_cache["kafka_messages"]
            if m.timestamp > datetime.now(timezone.utc) - timedelta(minutes=5)
        ]
        
        if len(recent_kafka) == 0:
            health_status["checks"]["kafka"] = {
                "status": "warning",
                "message": "No recent Kafka activity"
            }
        else:
            success_rate = sum(1 for m in recent_kafka if m.tags.get("success") == "True") / len(recent_kafka)
            health_status["checks"]["kafka"] = {
                "status": "healthy" if success_rate > 0.95 else "warning",
                "success_rate": success_rate
            }
        
        # Overall status
        critical_checks = [c for c in health_status["checks"].values() if c.get("status") == "critical"]
        warning_checks = [c for c in health_status["checks"].values() if c.get("status") == "warning"]
        
        if critical_checks:
            health_status["status"] = "critical"
        elif warning_checks:
            health_status["status"] = "warning"
        
        return health_status
    
    async def _update_ml_accuracy(self, predicted: str, actual: str, timestamp: datetime) -> None:
        """Update ML accuracy tracking metrics."""
        # This would typically update a dedicated metrics table
        # For now, we store in memory cache
        pass
    
    def _get_confidence_bucket(self, confidence: float) -> str:
        """Categorize confidence score into buckets."""
        if confidence >= 0.9:
            return "high"
        elif confidence >= 0.7:
            return "medium"
        else:
            return "low"
    
    async def _create_alert(self, alert_type: str, message: str, severity: str = "info") -> None:
        """Create and store an alert."""
        alert = {
            "id": len(self._alerts) + 1,
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "acknowledged": False
        }
        
        self._alerts.append(alert)
        logger.warning(f"ALERT [{severity.upper()}]: {message}")
        
        # In production, this would send to Sentry, Slack, etc.
    
    async def _get_database_engagement_metrics(self, time_range: timedelta) -> Dict:
        """Get engagement metrics from database."""
        cutoff_date = datetime.now(timezone.utc) - time_range
        
        try:
            # Get session analytics
            session_result = await self.db.execute(
                select(
                    func.count(SessionAnalytics.session_id).label('total_sessions'),
                    func.sum(SessionAnalytics.punch_count).label('total_punches'),
                    func.avg(SessionAnalytics.avg_score).label('avg_score')
                ).where(SessionAnalytics.created_at >= cutoff_date)
            )
            session_data = session_result.first()
            
            # Get user metrics
            user_result = await self.db.execute(
                select(
                    func.count(UserMetrics.user_id).label('active_users'),
                    func.avg(UserMetrics.fatigue_index).label('avg_fatigue')
                ).where(UserMetrics.last_updated >= cutoff_date)
            )
            user_data = user_result.first()
            
            return {
                "total_sessions": session_data.total_sessions or 0,
                "total_punches": session_data.total_punches or 0,
                "avg_technique_score": float(session_data.avg_score or 0),
                "active_users": user_data.active_users or 0,
                "avg_fatigue_index": float(user_data.avg_fatigue or 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get database engagement metrics: {e}")
            return {
                "total_sessions": 0,
                "total_punches": 0,
                "avg_technique_score": 0.0,
                "active_users": 0,
                "avg_fatigue_index": 0.0
            }
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts."""
        return sorted(self._alerts, key=lambda x: x["timestamp"], reverse=True)[:limit]

# Global monitoring instance
_monitoring_service = None

def get_monitoring_service(db: AsyncSession) -> MonitoringService:
    """Get or create monitoring service instance."""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService(db)
    return _monitoring_service






