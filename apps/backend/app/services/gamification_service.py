"""
Gamification Service

Manages XP, achievements, levels, and rewards for the boxing training application.
Integrates with smartwatch data for calorie-based rewards and punch tracking.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from models.postgres import User, UserProgress, Achievement, UserAchievement
from schemas import settings
import logging

logger = logging.getLogger(__name__)

class GamificationService:
    """
    Core gamification engine handling:
    - XP calculation and level progression
    - Achievement unlocking logic
    - Calorie-based reward eligibility
    - Ad-free access determination
    """
    
    # XP values for different activities
    XP_VALUES = {
        "punch_jab": 5,
        "punch_cross": 7,
        "punch_hook": 10,
        "punch_uppercut": 12,
        "calorie_burn_100": 50,  # Bonus for burning 100+ calories
        "session_complete": 25,
        "perfect_technique": 15,
        "daily_streak": 100,
    }
    
    # Level progression thresholds
    LEVEL_THRESHOLDS = {
        1: 0,
        2: 100,
        3: 250,
        4: 500,
        5: 1000,
        6: 2000,
        7: 3500,
        8: 6000,
        9: 10000,
        10: 15000,
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_progress(self, user_id: uuid.UUID) -> Optional[UserProgress]:
        """Get current user progress including XP and level."""
        result = await self.db.execute(
            select(UserProgress).where(UserProgress.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def ensure_user_progress(self, user_id: uuid.UUID) -> UserProgress:
        """Ensure user has progress record, create if needed."""
        progress = await self.get_user_progress(user_id)
        if not progress:
            progress = UserProgress(
                user_id=user_id,
                xp=0,
                level=1,
                last_updated=datetime.now(timezone.utc)
            )
            self.db.add(progress)
            await self.db.commit()
            await self.db.refresh(progress)
            logger.info(f"Created progress record for user {user_id}")
        return progress
    
    def calculate_level(self, xp: int) -> int:
        """Calculate level based on XP."""
        for level, threshold in sorted(self.LEVEL_THRESHOLDS.items(), reverse=True):
            if xp >= threshold:
                return level
        return 1
    
    def get_xp_for_next_level(self, current_level: int) -> int:
        """Get XP needed to reach next level."""
        next_level = current_level + 1
        if next_level in self.LEVEL_THRESHOLDS:
            return self.LEVEL_THRESHOLDS[next_level]
        return self.LEVEL_THRESHOLDSDS.get(max(self.LEVEL_THRESHOLDS.keys())) + 1000
    
    async def add_xp(self, user_id: uuid.UUID, xp_amount: int, reason: str) -> Dict:
        """
        Add XP to user and handle level progression.
        
        Args:
            user_id: User identifier
            xp_amount: Amount of XP to add
            reason: Description of XP source
            
        Returns:
            Dict with updated progress and level-up info
        """
        progress = await self.ensure_user_progress(user_id)
        old_level = progress.level
        old_xp = progress.xp
        
        # Add XP
        progress.xp += xp_amount
        progress.last_updated = datetime.now(timezone.utc)
        
        # Check for level up
        new_level = self.calculate_level(progress.xp)
        progress.level = new_level
        
        await self.db.commit()
        await self.db.refresh(progress)
        
        level_up = new_level > old_level
        
        if level_up:
            logger.info(f"User {user_id} leveled up from {old_level} to {new_level}")
        
        return {
            "user_id": str(user_id),
            "xp_added": xp_amount,
            "xp_total": progress.xp,
            "level_old": old_level,
            "level_new": new_level,
            "level_up": level_up,
            "xp_for_next_level": self.get_xp_for_next_level(new_level),
            "reason": reason
        }
    
    async def track_punch_activity(self, user_id: uuid.UUID, punch_type: str, count: int = 1) -> Dict:
        """
        Track punch activity and award XP.
        
        Args:
            user_id: User identifier
            punch_type: Type of punch (jab, cross, hook, uppercut)
            count: Number of punches
            
        Returns:
            Dict with XP awarded and progress
        """
        xp_key = f"punch_{punch_type}"
        xp_per_punch = self.XP_VALUES.get(xp_key, 5)
        total_xp = xp_per_punch * count
        
        result = await self.add_xp(
            user_id, 
            total_xp, 
            f"{count}x {punch_type} punches"
        )
        
        # Check for punch count achievements
        await self._check_punch_achievements(user_id, punch_type, count)
        
        return result
    
    async def track_calorie_activity(self, user_id: uuid.UUID, calories_burned: float) -> Dict:
        """
        Track calorie burning and award bonus XP for milestones.
        
        Args:
            user_id: User identifier
            calories_burned: Calories burned in session
            
        Returns:
            Dict with XP awarded and ad eligibility
        """
        xp_awarded = 0
        
        # Bonus XP for calorie milestones
        if calories_burned >= 100:
            xp_awarded += self.XP_VALUES["calorie_burn_100"]
        
        # Small XP for general activity
        xp_awarded += int(calories_burned * 0.1)  # 1 XP per 10 calories
        
        result = await self.add_xp(
            user_id,
            xp_awarded,
            f"Calorie burn: {calories_burned:.1f} kcal"
        )
        
        # Add ad eligibility info
        result["ad_free_eligible"] = calories_burned >= 100
        result["calories_burned"] = calories_burned
        
        return result
    
    async def check_ad_eligibility(self, user_id: uuid.UUID) -> Dict:
        """
        Check if user is eligible for ad-free experience.
        
        Rules:
        - Burned ≥100 kcal today → ad-free analysis
        - High level users → reduced ads
        - Achievement holders → special privileges
        
        Returns:
            Dict with ad eligibility status and reasons
        """
        # This would typically check today's activity
        # For now, we'll base it on user level and recent achievements
        progress = await self.get_user_progress(user_id)
        
        if not progress:
            return {"eligible": False, "reason": "no_progress"}
        
        # High-level users get reduced ads
        if progress.level >= 5:
            return {
                "eligible": True,
                "reason": "high_level",
                "ad_reduction": 0.5,  # 50% fewer ads
                "level": progress.level
            }
        
        # Check for specific achievements
        achievements = await self.get_user_achievements(user_id)
        calorie_achievements = [a for a in achievements if "calorie" in a.name.lower()]
        
        if calorie_achievements:
            return {
                "eligible": True,
                "reason": "calorie_achievement",
                "ad_reduction": 0.3,  # 30% fewer ads
                "achievements": len(calorie_achievements)
            }
        
        return {
            "eligible": False,
            "reason": "insufficient_activity",
            "level": progress.level,
            "suggestion": "Burn 100+ calories or reach level 5 for ad benefits"
        }
    
    async def create_default_achievements(self) -> None:
        """Create default achievements if they don't exist."""
        default_achievements = [
            {
                "name": "First Jab",
                "condition": "punch_jab_count >= 1",
                "description": "Throw your first jab"
            },
            {
                "name": "Jab Master", 
                "condition": "punch_jab_count >= 100",
                "description": "Throw 100 jabs"
            },
            {
                "name": "Calorie Crusher",
                "condition": "daily_calories >= 100",
                "description": "Burn 100+ calories in a day"
            },
            {
                "name": "Technique Perfectionist",
                "condition": "perfect_technique_count >= 10",
                "description": "Achieve perfect technique 10 times"
            },
            {
                "name": "Week Warrior",
                "condition": "weekly_sessions >= 5",
                "description": "Complete 5 training sessions in a week"
            },
            {
                "name": "Level 5 Champion",
                "condition": "level >= 5",
                "description": "Reach level 5"
            }
        ]
        
        for achievement_data in default_achievements:
            # Check if achievement already exists
            existing = await self.db.execute(
                select(Achievement).where(Achievement.name == achievement_data["name"])
            ).scalar_one_or_none()
            
            if not existing:
                achievement = Achievement(
                    id=uuid.uuid4(),
                    name=achievement_data["name"],
                    condition=achievement_data["condition"]
                )
                self.db.add(achievement)
        
        await self.db.commit()
        logger.info("Default achievements created/verified")
    
    async def get_user_achievements(self, user_id: uuid.UUID) -> List[Achievement]:
        """Get all achievements unlocked by user."""
        result = await self.db.execute(
            select(Achievement)
            .join(UserAchievement)
            .where(UserAchievement.user_id == user_id)
        )
        return result.scalars().all()
    
    async def check_and_unlock_achievements(self, user_id: uuid.UUID, activity_data: Dict) -> List[Dict]:
        """
        Check if user qualifies for new achievements based on activity.
        
        Args:
            user_id: User identifier
            activity_data: Dict with recent activity metrics
            
        Returns:
            List of newly unlocked achievements
        """
        # Get all achievements
        result = await self.db.execute(select(Achievement))
        all_achievements = result.scalars().all()
        
        # Get user's current achievements
        user_achievements = await self.get_user_achievements(user_id)
        user_achievement_ids = {a.id for a in user_achievements}
        
        newly_unlocked = []
        
        for achievement in all_achievements:
            if achievement.id in user_achievement_ids:
                continue
            
            # Evaluate achievement condition
            if await self._evaluate_achievement_condition(achievement.condition, user_id, activity_data):
                # Unlock achievement
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    unlocked_at=datetime.now(timezone.utc)
                )
                self.db.add(user_achievement)
                
                newly_unlocked.append({
                    "id": str(achievement.id),
                    "name": achievement.name,
                    "condition": achievement.condition,
                    "unlocked_at": user_achievement.unlocked_at.isoformat()
                })
                
                # Award XP for achievement
                await self.add_xp(user_id, 25, f"Achievement: {achievement.name}")
        
        if newly_unlocked:
            await self.db.commit()
            logger.info(f"User {user_id} unlocked {len(newly_unlocked)} achievements")
        
        return newly_unlocked
    
    async def _evaluate_achievement_condition(self, condition: str, user_id: uuid.UUID, activity_data: Dict) -> bool:
        """
        Evaluate achievement condition.
        
        This is a simplified version - in production you'd want a more robust
        condition evaluation system with proper parsing and safety checks.
        """
        # Simple condition evaluation for common patterns
        if "punch_jab_count >= 1" in condition:
            return activity_data.get("jab_count", 0) >= 1
        
        if "punch_jab_count >= 100" in condition:
            return activity_data.get("total_jab_count", 0) >= 100
        
        if "daily_calories >= 100" in condition:
            return activity_data.get("daily_calories", 0) >= 100
        
        if "level >= 5" in condition:
            progress = await self.get_user_progress(user_id)
            return progress and progress.level >= 5
        
        # Add more condition evaluations as needed
        return False
    
    async def _check_punch_achievements(self, user_id: uuid.UUID, punch_type: str, count: int) -> None:
        """Check for punch-specific achievements."""
        activity_data = {
            "jab_count": count if punch_type == "jab" else 0,
            "total_jab_count": count if punch_type == "jab" else 0
        }
        
        await self.check_and_unlock_achievements(user_id, activity_data)
    
    async def get_user_stats(self, user_id: uuid.UUID) -> Dict:
        """Get comprehensive user gamification stats."""
        progress = await self.get_user_progress(user_id)
        achievements = await self.get_user_achievements(user_id)
        ad_eligibility = await self.check_ad_eligibility(user_id)
        
        return {
            "user_id": str(user_id),
            "xp": progress.xp if progress else 0,
            "level": progress.level if progress else 1,
            "xp_for_next_level": self.get_xp_for_next_level(progress.level if progress else 1),
            "achievements_count": len(achievements),
            "achievements": [
                {
                    "id": str(a.id),
                    "name": a.name,
                    "unlocked_at": a.unlocked_at.isoformat() if hasattr(a, 'unlocked_at') else None
                }
                for a in achievements
            ],
            "ad_eligibility": ad_eligibility
        }
