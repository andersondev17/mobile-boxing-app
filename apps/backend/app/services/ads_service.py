"""
Google AdMob Integration Service

Manages banner ads, video ads, and rewarded ads integration with Firebase Analytics.
Tracks ad revenue and user ad preferences based on gamification eligibility.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID

from schemas.env import settings
from services.firebase_service import firebase_service

logger = logging.getLogger(__name__)

class AdMobService:
    """Google AdMob integration service for banner and video ads."""
    
    def __init__(self):
        self.ad_units = {
            # Banner ad units
            "banner_home": "ca-app-pub-XXXXXXXXXXXXXXXXX/YYYYYYYYYY",
            "banner_workout": "ca-app-pub-XXXXXXXXXXXXXXXXX/YYYYYYYYYY",
            "banner_profile": "ca-app-pub-XXXXXXXXXXXXXXXXX/YYYYYYYYYY",
            
            # Interstitial ad units
            "interstitial_workout_end": "ca-app-pub-XXXXXXXXXXXXXXXXX/YYYYYYYYYY",
            "interstitial_session_start": "ca-app-pub-XXXXXXXXXXXXXXXXX/YYYYYYYYYY",
            
            # Rewarded video ad units
            "rewarded_xp_bonus": "ca-app-pub-XXXXXXXXXXXXXXXXX/YYYYYYYYYY",
            "rewarded_energy_boost": "ca-app-pub-XXXXXXXXXXXXXXXXX/YYYYYYYYYY",
            "rewarded_premium_analysis": "ca-app-pub-XXXXXXXXXXXXXXXXX/YYYYYYYYYY",
            
            # Native ad units
            "native_workout_tips": "ca-app-pub-XXXXXXXXXXXXXXXXX/YYYYYYYYYY",
            "native_achievements": "ca-app-pub-XXXXXXXXXXXXXXXXX/YYYYYYYYYY"
        }
        
        self.ad_frequency_limits = {
            "banner": 3,  # max 3 banner impressions per minute
            "interstitial": 1,  # max 1 interstitial per 5 minutes
            "rewarded": 5,  # max 5 rewarded videos per hour
        }
    
    async def get_ad_config(self, user_id: str, ad_type: str, placement: str) -> Dict[str, Any]:
        """
        Get ad configuration for user based on eligibility and frequency limits.
        
        Args:
            user_id: User identifier
            ad_type: Type of ad (banner, interstitial, rewarded, native)
            placement: Where the ad will be shown
            
        Returns:
            Ad configuration with unit ID, eligibility, and metadata
        """
        try:
            # Check user's ad eligibility from gamification
            from services.gamification_service import GamificationService
            
            # Note: In real implementation, you'd inject this dependency
            # gamification = GamificationService(db)
            # eligibility = await gamification.check_ad_eligibility(UUID(user_id))
            
            # For now, simulate eligibility check
            eligibility = await self._simulate_ad_eligibility(user_id)
            
            # Check frequency limits
            can_show = await self._check_frequency_limits(user_id, ad_type)
            
            # Get appropriate ad unit
            ad_unit_key = f"{ad_type}_{placement}"
            ad_unit_id = self.ad_units.get(ad_unit_key, "")
            
            config = {
                "user_id": user_id,
                "ad_type": ad_type,
                "placement": placement,
                "ad_unit_id": ad_unit_id,
                "eligible": not eligibility.get("eligible", False) and can_show,
                "ad_reduction": eligibility.get("ad_reduction", 0),
                "reason": eligibility.get("reason", "standard_ad_display"),
                "show_ad": not eligibility.get("eligible", False) and can_show,
                "frequency_remaining": await self._get_frequency_remaining(user_id, ad_type),
                "next_available": await self._get_next_available_time(user_id, ad_type)
            }
            
            # Log ad request to Firebase
            await firebase_service.log_analytics_event(
                user_id=user_id,
                event_name="ad_request",
                parameters={
                    "ad_type": ad_type,
                    "placement": placement,
                    "eligible": config["eligible"],
                    "show_ad": config["show_ad"]
                }
            )
            
            return config
            
        except Exception as e:
            logger.error(f"Error getting ad config: {e}")
            return {"error": str(e)}
    
    async def track_ad_impression(self, user_id: str, ad_type: str, placement: str, 
                                ad_unit_id: str, revenue: float = 0.0) -> bool:
        """
        Track ad impression for analytics and revenue tracking.
        
        Args:
            user_id: User identifier
            ad_type: Type of ad shown
            placement: Where ad was shown
            ad_unit_id: Ad unit identifier
            revenue: Estimated revenue from impression
        """
        try:
            # Update frequency tracking
            await self._update_frequency_tracking(user_id, ad_type)
            
            # Track impression in Firebase
            await firebase_service.log_analytics_event(
                user_id=user_id,
                event_name="ad_impression",
                parameters={
                    "ad_type": ad_type,
                    "placement": placement,
                    "ad_unit_id": ad_unit_id,
                    "revenue": revenue,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Track revenue
            if revenue > 0:
                await self._track_ad_revenue(user_id, revenue, ad_type)
            
            logger.info(f"Ad impression tracked: {ad_type} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking ad impression: {e}")
            return False
    
    async def track_ad_clicked(self, user_id: str, ad_type: str, placement: str,
                             ad_unit_id: str) -> bool:
        """Track ad click for analytics."""
        try:
            await firebase_service.log_analytics_event(
                user_id=user_id,
                event_name="ad_clicked",
                parameters={
                    "ad_type": ad_type,
                    "placement": placement,
                    "ad_unit_id": ad_unit_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Ad click tracked: {ad_type} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking ad click: {e}")
            return False
    
    async def track_rewarded_ad_completed(self, user_id: str, reward_type: str, 
                                        reward_amount: int) -> bool:
        """
        Track completion of rewarded video ad and grant rewards.
        
        Args:
            user_id: User identifier
            reward_type: Type of reward (xp_bonus, energy_boost, premium_analysis)
            reward_amount: Amount of reward granted
        """
        try:
            # Grant reward based on type
            if reward_type == "xp_bonus":
                from services.gamification_service import GamificationService
                # gamification = GamificationService(db)
                # await gamification.add_xp(user_id, reward_amount)
                pass  # Implementation would go here
            
            # Track rewarded ad completion
            await firebase_service.log_analytics_event(
                user_id=user_id,
                event_name="rewarded_ad_completed",
                parameters={
                    "reward_type": reward_type,
                    "reward_amount": reward_amount,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Rewarded ad completed: {reward_type} ({reward_amount}) for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking rewarded ad: {e}")
            return False
    
    async def get_ad_performance_metrics(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get ad performance metrics for a user."""
        try:
            # In real implementation, this would query your analytics database
            # For now, return mock data
            return {
                "user_id": user_id,
                "period_days": days,
                "total_impressions": 45,
                "total_clicks": 3,
                "total_revenue": 0.12,
                "ctr": 0.067,  # Click-through rate
                "rpm": 0.0027,  # Revenue per mille
                "rewarded_ads_completed": 8,
                "rewards_granted": {
                    "xp_bonus": 5,
                    "energy_boost": 3
                },
                "ad_breakdown": {
                    "banner": {"impressions": 35, "revenue": 0.08},
                    "interstitial": {"impressions": 8, "revenue": 0.03},
                    "rewarded": {"impressions": 2, "revenue": 0.01}
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting ad metrics: {e}")
            return {}
    
    async def _simulate_ad_eligibility(self, user_id: str) -> Dict[str, Any]:
        """Simulate ad eligibility check (in real implementation, use gamification service)."""
        # Mock implementation - replace with actual gamification service call
        return {
            "eligible": False,  # User gets ad-free experience
            "reason": "daily_calorie_goal",
            "ad_reduction": 0.0
        }
    
    async def _check_frequency_limits(self, user_id: str, ad_type: str) -> bool:
        """Check if user has reached frequency limits for ad type."""
        # In real implementation, check Redis or database for recent impressions
        return True  # Allow for demo
    
    async def _get_frequency_remaining(self, user_id: str, ad_type: str) -> int:
        """Get remaining ads user can see based on frequency limits."""
        limit = self.ad_frequency_limits.get(ad_type, 1)
        # In real implementation, check current count
        return limit
    
    async def _get_next_available_time(self, user_id: str, ad_type: str) -> Optional[str]:
        """Get when user can see next ad of this type."""
        # In real implementation, calculate based on last impression time
        return None
    
    async def _update_frequency_tracking(self, user_id: str, ad_type: str):
        """Update frequency tracking for user."""
        # In real implementation, update Redis or database
        pass
    
    async def _track_ad_revenue(self, user_id: str, revenue: float, ad_type: str):
        """Track ad revenue for analytics."""
        await firebase_service.log_analytics_event(
            user_id=user_id,
            event_name="ad_revenue",
            parameters={
                "revenue": revenue,
                "ad_type": ad_type,
                "currency": "USD",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Global ad service instance
admob_service = AdMobService()

# Convenience functions for easy access
async def should_show_ad(user_id: str, ad_type: str, placement: str) -> bool:
    """Check if ad should be shown to user."""
    config = await admob_service.get_ad_config(user_id, ad_type, placement)
    return config.get("show_ad", False)

async def get_banner_ad_config(user_id: str, placement: str) -> Dict[str, Any]:
    """Get banner ad configuration."""
    return await admob_service.get_ad_config(user_id, "banner", placement)

async def get_interstitial_ad_config(user_id: str, placement: str) -> Dict[str, Any]:
    """Get interstitial ad configuration."""
    return await admob_service.get_ad_config(user_id, "interstitial", placement)

async def get_rewarded_ad_config(user_id: str, placement: str) -> Dict[str, Any]:
    """Get rewarded video ad configuration."""
    return await admob_service.get_ad_config(user_id, "rewarded", placement)

async def get_native_ad_config(user_id: str, placement: str) -> Dict[str, Any]:
    """Get native ad configuration."""
    return await admob_service.get_ad_config(user_id, "native", placement)
