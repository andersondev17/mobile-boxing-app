"""
Google AdMob API Routes

Endpoints for managing ad configurations, tracking impressions,
and integrating with Firebase Analytics and gamification system.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from database.postgres import get_pg_session
from services.ads_service import admob_service
from services.firebase_service import services.firebase_service

router = APIRouter(prefix="/ads", tags=["ads"])

# Pydantic models for request/response
class AdConfigRequest(BaseModel):
    ad_type: str
    placement: str

class AdConfigResponse(BaseModel):
    user_id: str
    ad_type: str
    placement: str
    ad_unit_id: str
    eligible: bool
    ad_reduction: float
    reason: str
    show_ad: bool
    frequency_remaining: int
    next_available: Optional[str]

class AdImpressionRequest(BaseModel):
    ad_type: str
    placement: str
    ad_unit_id: str
    revenue: float = 0.0

class AdClickRequest(BaseModel):
    ad_type: str
    placement: str
    ad_unit_id: str

class RewardedAdRequest(BaseModel):
    reward_type: str
    reward_amount: int

class AdMetricsResponse(BaseModel):
    user_id: str
    period_days: int
    total_impressions: int
    total_clicks: int
    total_revenue: float
    ctr: float
    rpm: float
    rewarded_ads_completed: int
    rewards_granted: Dict[str, int]
    ad_breakdown: Dict[str, Dict[str, Any]]

@router.get("/config", response_model=AdConfigResponse)
async def get_ad_config(
    ad_type: str = Query(..., description="Type of ad (banner, interstitial, rewarded, native)"),
    placement: str = Query(..., description="Placement identifier"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get ad configuration for user based on eligibility and frequency limits.
    
    This endpoint determines if an ad should be shown based on:
    - User's gamification eligibility (ad-free rewards)
    - Frequency limits for the ad type
    - User's recent ad viewing history
    
    Args:
        ad_type: Type of ad requested
        placement: Where the ad will be displayed
        current_user: Authenticated user
        
    Returns:
        Ad configuration with unit ID and eligibility status
    """
    user_id = current_user["sub"]
    
    try:
        config = await admob_service.get_ad_config(user_id, ad_type, placement)
        return AdConfigResponse(**config)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ad config: {str(e)}"
        )

@router.post("/impression")
async def track_ad_impression(
    request: AdImpressionRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Track ad impression for analytics and revenue tracking.
    
    Call this endpoint when an ad is successfully displayed to the user.
    This updates frequency tracking and logs the impression to Firebase Analytics.
    
    Args:
        request: Ad impression details
        current_user: Authenticated user
        
    Returns:
        Success status
    """
    user_id = current_user["sub"]
    
    try:
        success = await admob_service.track_ad_impression(
            user_id=user_id,
            ad_type=request.ad_type,
            placement=request.placement,
            ad_unit_id=request.ad_unit_id,
            revenue=request.revenue
        )
        
        if success:
            return {"success": True, "message": "Ad impression tracked"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to track ad impression"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to track ad impression: {str(e)}"
        )

@router.post("/click")
async def track_ad_click(
    request: AdClickRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Track ad click for analytics.
    
    Call this endpoint when a user clicks on an ad.
    This logs the click event to Firebase Analytics.
    
    Args:
        request: Ad click details
        current_user: Authenticated user
        
    Returns:
        Success status
    """
    user_id = current_user["sub"]
    
    try:
        success = await admob_service.track_ad_clicked(
            user_id=user_id,
            ad_type=request.ad_type,
            placement=request.placement,
            ad_unit_id=request.ad_unit_id
        )
        
        if success:
            return {"success": True, "message": "Ad click tracked"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to track ad click"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to track ad click: {str(e)}"
        )

@router.post("/rewarded-completed")
async def track_rewarded_ad_completed(
    request: RewardedAdRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Track completion of rewarded video ad and grant rewards.
    
    Call this endpoint when a user successfully watches a rewarded video ad.
    This grants the appropriate reward (XP, energy boost, etc.) and tracks the event.
    
    Args:
        request: Rewarded ad completion details
        current_user: Authenticated user
        
    Returns:
        Success status and reward details
    """
    user_id = current_user["sub"]
    
    try:
        success = await admob_service.track_rewarded_ad_completed(
            user_id=user_id,
            reward_type=request.reward_type,
            reward_amount=request.reward_amount
        )
        
        if success:
            return {
                "success": True, 
                "message": "Rewarded ad completed and reward granted",
                "reward_type": request.reward_type,
                "reward_amount": request.reward_amount
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to process rewarded ad"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to track rewarded ad: {str(e)}"
        )

@router.get("/metrics", response_model=AdMetricsResponse)
async def get_ad_metrics(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get ad performance metrics for the current user.
    
    Returns comprehensive analytics about ad impressions, clicks, revenue,
    and rewarded ads completed over the specified time period.
    
    Args:
        days: Number of days to include in analysis
        current_user: Authenticated user
        
    Returns:
        Ad performance metrics
    """
    user_id = current_user["sub"]
    
    try:
        metrics = await admob_service.get_ad_performance_metrics(user_id, days)
        return AdMetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ad metrics: {str(e)}"
        )

@router.get("/banner/{placement}")
async def get_banner_ad(
    placement: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get banner ad configuration for specific placement.
    
    Convenience endpoint for banner ads.
    
    Args:
        placement: Banner placement identifier
        current_user: Authenticated user
        
    Returns:
        Banner ad configuration
    """
    user_id = current_user["sub"]
    
    try:
        config = await admob_service.get_ad_config(user_id, "banner", placement)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get banner ad: {str(e)}"
        )

@router.get("/interstitial/{placement}")
async def get_interstitial_ad(
    placement: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get interstitial ad configuration for specific placement.
    
    Convenience endpoint for interstitial ads.
    
    Args:
        placement: Interstitial placement identifier
        current_user: Authenticated user
        
    Returns:
        Interstitial ad configuration
    """
    user_id = current_user["sub"]
    
    try:
        config = await admob_service.get_ad_config(user_id, "interstitial", placement)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get interstitial ad: {str(e)}"
        )

@router.get("/rewarded/{placement}")
async def get_rewarded_ad(
    placement: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get rewarded video ad configuration for specific placement.
    
    Convenience endpoint for rewarded video ads.
    
    Args:
        placement: Rewarded ad placement identifier
        current_user: Authenticated user
        
    Returns:
        Rewarded ad configuration
    """
    user_id = current_user["sub"]
    
    try:
        config = await admob_service.get_ad_config(user_id, "rewarded", placement)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get rewarded ad: {str(e)}"
        )

@router.get("/native/{placement}")
async def get_native_ad(
    placement: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get native ad configuration for specific placement.
    
    Convenience endpoint for native ads.
    
    Args:
        placement: Native ad placement identifier
        current_user: Authenticated user
        
    Returns:
        Native ad configuration
    """
    user_id = current_user["sub"]
    
    try:
        config = await admob_service.get_ad_config(user_id, "native", placement)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get native ad: {str(e)}"
        )

@router.get("/ad-units")
async def get_ad_units():
    """
    Get all available ad unit configurations.
    
    Returns the list of all configured ad unit IDs for different
    ad types and placements. This is useful for frontend configuration.
    
    Returns:
        Dictionary of ad units by type and placement
    """
    try:
        return {
            "ad_units": admob_service.ad_units,
            "frequency_limits": admob_service.ad_frequency_limits
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ad units: {str(e)}"
        )

@router.get("/eligibility-summary")
async def get_ad_eligibility_summary(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get comprehensive ad eligibility summary for the user.
    
    Combines gamification eligibility with current ad frequency status
    to provide a complete picture of the user's ad experience.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Ad eligibility summary with all ad types
    """
    user_id = current_user["sub"]
    
    try:
        ad_types = ["banner", "interstitial", "rewarded", "native"]
        summary = {"user_id": user_id, "ad_types": {}}
        
        for ad_type in ad_types:
            # Get config for a standard placement
            config = await admob_service.get_ad_config(user_id, ad_type, "default")
            summary["ad_types"][ad_type] = {
                "eligible": config.get("eligible", False),
                "ad_reduction": config.get("ad_reduction", 0),
                "frequency_remaining": config.get("frequency_remaining", 0),
                "next_available": config.get("next_available")
            }
        
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get eligibility summary: {str(e)}"
        )






