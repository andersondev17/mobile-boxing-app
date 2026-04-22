"""
Firebase Service Integration

Handles Firebase Analytics, Cloud Messaging, and Authentication
for the boxing-app project using the google-services.json configuration.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, messaging
from schemas.env import settings

logger = logging.getLogger(__name__)

class FirebaseService:
    """Firebase service for analytics, messaging, and user data."""
    
    def __init__(self):
        self._app = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize Firebase Admin SDK."""
        if self._initialized:
            return True
            
        try:
            # Load service account from google-services.json
            service_account_path = Path(__file__).parent / "firebase" / "google-services.json"
            
            if not service_account_path.exists():
                logger.warning("Firebase service account file not found at %s", service_account_path)
                return False
                
            # Extract service account info from google-services.json
            with open(service_account_path, 'r') as f:
                google_services = json.load(f)
                
            # Convert google-services.json format to service account format
            service_account = {
                "type": "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "private_key_id": google_services["client"][0]["oauth_client"][0]["client_id"],
                "private_key": google_services["client"][0]["oauth_client"][0]["client_secret"].replace("\\n", "\n"),
                "client_email": f"{settings.FIREBASE_PROJECT_ID}@appspot.gserviceaccount.com",
                "client_id": settings.FIREBASE_PROJECT_ID,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
            
            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(service_account)
            self._app = firebase_admin.initialize_app(cred, {
                'projectId': settings.FIREBASE_PROJECT_ID,
                'storageBucket': f'{settings.FIREBASE_PROJECT_ID}.appspot.com'
            })
            
            self._initialized = True
            logger.info("Firebase Admin SDK initialized for project: %s", settings.FIREBASE_PROJECT_ID)
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            return False
    
    async def log_analytics_event(self, user_id: str, event_name: str, 
                              parameters: Optional[Dict[str, Any]] = None) -> bool:
        """Log analytics event to Firebase."""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Firebase Admin SDK doesn't have direct analytics logging
            # Events are typically logged client-side or via Firebase Analytics SDK
            # For now, we'll log locally and integrate with custom analytics
            logger.info(f"Analytics event: {event_name} for user {user_id}, params: {parameters}")
            
            # TODO: Implement custom analytics tracking or use Firebase Analytics REST API
            return True
            
        except Exception as e:
            logger.error(f"Failed to log analytics event: {e}")
            return False
    
    async def send_push_notification(self, user_id: str, title: str, body: str, 
                                 data: Optional[Dict[str, Any]] = None) -> bool:
        """Send push notification via Firebase Cloud Messaging."""
        if not self._initialized:
            await self.initialize()
            
        try:
            # In a real implementation, you would get the user's FCM token
            # For now, we'll simulate this
            fcm_token = await self._get_user_fcm_token(user_id)
            
            if not fcm_token:
                logger.warning(f"No FCM token found for user {user_id}")
                return False
            
            # Create message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                token=fcm_token,
                data=data or {}
            )
            
            # Send message
            response = messaging.send(message)
            logger.info(f"Push notification sent to {user_id}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False
    
    async def _get_user_fcm_token(self, user_id: str) -> Optional[str]:
        """Get user's FCM token from database."""
        # In a real implementation, this would query your database
        # For demonstration, return a mock token
        return f"mock_fcm_token_{user_id}"
    
    async def track_user_engagement(self, user_id: str, engagement_data: Dict[str, Any]) -> bool:
        """Track user engagement metrics."""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Track engagement events
            events = [
                ("user_login", {"method": engagement_data.get("login_method", "unknown")}),
                ("workout_completed", {"duration": engagement_data.get("workout_duration", 0)}),
                ("punch_analyzed", {"punch_type": engagement_data.get("punch_type", "unknown")}),
                ("achievement_unlocked", {"achievement": engagement_data.get("achievement", "unknown")}),
            ]
            
            for event_name, params in events:
                await self.log_analytics_event(user_id, event_name, params)
            
            logger.info(f"Engagement tracked for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track engagement: {e}")
            return False

# Global Firebase service instance
firebase_service = FirebaseService()

# Convenience functions for easy access
async def log_user_login(user_id: str, method: str = "email") -> bool:
    """Log user login event."""
    return await firebase_service.log_analytics_event(
        user_id=user_id,
        event_name="user_login",
        parameters={"method": method}
    )

async def log_workout_completed(user_id: str, duration: int, punch_count: int) -> bool:
    """Log workout completion."""
    return await firebase_service.log_analytics_event(
        user_id=user_id,
        event_name="workout_completed",
        parameters={
            "duration_seconds": duration,
            "punch_count": punch_count,
            "completion_rate": min(punch_count / 100, 1.0)  # Assuming 100 punches target
        }
    )

async def log_achievement_unlocked(user_id: str, achievement_name: str, achievement_type: str) -> bool:
    """Log achievement unlock."""
    return await firebase_service.log_analytics_event(
        user_id=user_id,
        event_name="achievement_unlocked",
        parameters={
            "achievement_name": achievement_name,
            "achievement_type": achievement_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

async def send_achievement_notification(user_id: str, achievement_name: str) -> bool:
    """Send achievement notification."""
    return await firebase_service.send_push_notification(
        user_id=user_id,
        title="Achievement Unlocked!",
        body=f"Congratulations! You've unlocked: {achievement_name}",
        data={"type": "achievement", "name": achievement_name}
    )

async def track_punch_performance(user_id: str, punch_type: str, score: float, feedback: List[str]) -> bool:
    """Track punch performance metrics."""
    return await firebase_service.log_analytics_event(
        user_id=user_id,
        event_name="punch_performance",
        parameters={
            "punch_type": punch_type,
            "technique_score": score,
            "feedback_count": len(feedback),
            "avg_feedback_score": sum([f.count("excellent") for f in feedback]) / len(feedback) if feedback else 0
        }
    )
