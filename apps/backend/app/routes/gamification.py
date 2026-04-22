"""
Gamification Routes

Endpoints for XP, achievements, levels, and reward management.
Integrates with smartwatch data and punch analysis for real-time progress.
"""

from typing import List, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from config.database import get_pg_session
from sqlalchemy.ext.asyncio import AsyncSession
from auth import get_current_user
from services.gamification_service import GamificationService

router = APIRouter(prefix="/gamification", tags=["Gamification"])

# Request/Response Models
class XPResponse(BaseModel):
    """Response for XP addition."""
    user_id: str
    xp_added: int
    xp_total: int
    level_old: int
    level_new: int
    level_up: bool
    xp_for_next_level: int
    reason: str

class PunchActivityRequest(BaseModel):
    """Request to track punch activity."""
    punch_type: str = Field(..., description="Type of punch: jab, cross, hook, uppercut")
    count: int = Field(1, description="Number of punches", ge=1)

class CalorieActivityRequest(BaseModel):
    """Request to track calorie burning."""
    calories_burned: float = Field(..., description="Calories burned in session", ge=0)
    session_id: Optional[str] = Field(None, description="Training session ID")

class UserStatsResponse(BaseModel):
    """Comprehensive user gamification stats."""
    user_id: str
    xp: int
    level: int
    xp_for_next_level: int
    achievements_count: int
    achievements: List[Dict]
    ad_eligibility: Dict

class AchievementResponse(BaseModel):
    """Achievement information."""
    id: str
    name: str
    condition: str
    unlocked_at: Optional[str]

class AdEligibilityResponse(BaseModel):
    """Ad eligibility status."""
    eligible: bool
    reason: str
    ad_reduction: Optional[float] = None
    level: Optional[int] = None
    achievements: Optional[int] = None

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    db: AsyncSession = Depends(get_pg_session),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get comprehensive gamification stats for the current user.
    Includes XP, level, achievements, and ad eligibility.
    """
    user_id = UUID(current_user["sub"])
    gamification = GamificationService(db)
    
    try:
        stats = await gamification.get_user_stats(user_id)
        return UserStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user stats: {str(e)}"
        )

@router.post("/track-punch", response_model=XPResponse)
async def track_punch_activity(
    request: PunchActivityRequest,
    db: AsyncSession = Depends(get_pg_session),
    current_user: Dict = Depends(get_current_user)
):
    """
    Track punch activity and award XP.
    
    Commonly called from punch analysis results or manual logging.
    """
    user_id = UUID(current_user["sub"])
    gamification = GamificationService(db)
    
    # Validate punch type
    valid_punches = ["jab", "cross", "hook", "uppercut"]
    if request.punch_type not in valid_punches:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid punch type. Must be one of: {valid_punches}"
        )
    
    try:
        result = await gamification.track_punch_activity(
            user_id, 
            request.punch_type, 
            request.count
        )
        return XPResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to track punch activity: {str(e)}"
        )

@router.post("/track-calories", response_model=XPResponse)
async def track_calorie_activity(
    request: CalorieActivityRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_pg_session),
    current_user: Dict = Depends(get_current_user)
):
    """
    Track calorie burning and award XP with bonus for milestones.
    
    This endpoint is typically called from smartwatch data processing
    or session completion events.
    """
    user_id = UUID(current_user["sub"])
    gamification = GamificationService(db)
    
    try:
        result = await gamification.track_calorie_activity(
            user_id, 
            request.calories_burned
        )
        
        # Check for new achievements in background
        background_tasks.add_task(
            _check_and_notify_achievements,
            user_id,
            {"daily_calories": request.calories_burned},
            db
        )
        
        return XPResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to track calorie activity: {str(e)}"
        )

@router.get("/achievements", response_model=List[AchievementResponse])
async def get_user_achievements(
    db: AsyncSession = Depends(get_pg_session),
    current_user: Dict = Depends(get_current_user)
):
    """Get all achievements unlocked by the user."""
    user_id = UUID(current_user["sub"])
    gamification = GamificationService(db)
    
    try:
        achievements = await gamification.get_user_achievements(user_id)
        return [
            AchievementResponse(
                id=str(a.id),
                name=a.name,
                condition=a.condition,
                unlocked_at=None  # This would come from UserAchievement join
            )
            for a in achievements
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get achievements: {str(e)}"
        )

@router.get("/ad-eligibility", response_model=AdEligibilityResponse)
async def check_ad_eligibility(
    db: AsyncSession = Depends(get_pg_session),
    current_user: Dict = Depends(get_current_user)
):
    """
    Check if user is eligible for ad-free or reduced-ad experience.
    
    Rules:
    - Burn ≥100 kcal today → ad-free analysis
    - Level 5+ → 50% fewer ads
    - Calorie achievements → 30% fewer ads
    """
    user_id = UUID(current_user["sub"])
    gamification = GamificationService(db)
    
    try:
        eligibility = await gamification.check_ad_eligibility(user_id)
        return AdEligibilityResponse(**eligibility)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check ad eligibility: {str(e)}"
        )

@router.post("/initialize-achievements")
async def initialize_achievements(
    db: AsyncSession = Depends(get_pg_session),
    current_user: Dict = Depends(get_current_user)
):
    """
    Initialize default achievements in the system.
    
    This is an admin-level endpoint to set up the achievement system.
    In production, this would be protected by admin permissions.
    """
    # Check if user is admin (simplified check)
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    gamification = GamificationService(db)
    
    try:
        await gamification.create_default_achievements()
        return {"message": "Default achievements initialized successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize achievements: {str(e)}"
        )

@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_pg_session)
):
    """
    Get leaderboard of top users by XP and level.
    
    This is a public endpoint for competitive gamification.
    """
    from sqlalchemy import select, func
    from models.postgres import UserProgress, User
    
    try:
        # Query top users by XP
        query = (
            select(
                User.id,
                User.name,
                UserProgress.xp,
                UserProgress.level,
                func.row_number().over(
                    order_by=UserProgress.xp.desc()
                ).label('rank')
            )
            .join(UserProgress, User.id == UserProgress.user_id)
            .order_by(UserProgress.xp.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(query)
        leaderboard = result.all()
        
        return {
            "leaderboard": [
                {
                    "rank": row.rank,
                    "user_id": str(row.id),
                    "name": row.name or "Anonymous",
                    "xp": row.xp,
                    "level": row.level
                }
                for row in leaderboard
            ],
            "total": len(leaderboard),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get leaderboard: {str(e)}"
        )

async def _check_and_notify_achievements(
    user_id: UUID, 
    activity_data: Dict, 
    db: AsyncSession
):
    """
    Background task to check for new achievements and send notifications.
    
    This runs asynchronously to avoid blocking the main response.
    """
    try:
        gamification = GamificationService(db)
        new_achievements = await gamification.check_and_unlock_achievements(
            user_id, 
            activity_data
        )
        
        if new_achievements:
            # Here you would typically send push notifications,
            # update Firebase, or trigger other notification systems
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"User {user_id} unlocked {len(new_achievements)} achievements")
            
            # TODO: Send to Firebase/Notification service
            # await notification_service.send_achievement_unlocked(user_id, new_achievements)
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to check achievements for user {user_id}: {e}")
