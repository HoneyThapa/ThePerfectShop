from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db.session import SessionLocal
from app.db.models import UserPreferences

router = APIRouter(prefix="/preferences", tags=["User Preferences"])

class PreferencesRequest(BaseModel):
    optimize_for: str = "balanced"  # stability, profit, waste_min, balanced
    service_level_priority: str = "medium"  # low, medium, high
    multi_location_aggressiveness: str = "medium"  # low, medium, high

class PreferencesResponse(BaseModel):
    optimize_for: str
    service_level_priority: str
    multi_location_aggressiveness: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@router.get("/", response_model=PreferencesResponse)
async def get_user_preferences():
    """Get current user preferences"""
    try:
        db = SessionLocal()
        prefs = db.query(UserPreferences).filter(UserPreferences.user_id == "default").first()
        db.close()
        
        if not prefs:
            # Return defaults if no preferences set
            return PreferencesResponse(
                optimize_for="balanced",
                service_level_priority="medium",
                multi_location_aggressiveness="medium"
            )
        
        return PreferencesResponse(
            optimize_for=prefs.optimize_for,
            service_level_priority=prefs.service_level_priority,
            multi_location_aggressiveness=prefs.multi_location_aggressiveness,
            created_at=prefs.created_at.isoformat() if prefs.created_at else None,
            updated_at=prefs.updated_at.isoformat() if prefs.updated_at else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching preferences: {str(e)}")

@router.post("/", response_model=PreferencesResponse)
async def update_user_preferences(request: PreferencesRequest):
    """Update user preferences"""
    try:
        # Validate input values
        valid_optimize = ["stability", "profit", "waste_min", "balanced"]
        valid_priority = ["low", "medium", "high"]
        
        if request.optimize_for not in valid_optimize:
            raise HTTPException(status_code=400, detail=f"optimize_for must be one of: {valid_optimize}")
        
        if request.service_level_priority not in valid_priority:
            raise HTTPException(status_code=400, detail=f"service_level_priority must be one of: {valid_priority}")
        
        if request.multi_location_aggressiveness not in valid_priority:
            raise HTTPException(status_code=400, detail=f"multi_location_aggressiveness must be one of: {valid_priority}")
        
        db = SessionLocal()
        
        # Check if preferences exist
        prefs = db.query(UserPreferences).filter(UserPreferences.user_id == "default").first()
        
        if prefs:
            # Update existing preferences
            prefs.optimize_for = request.optimize_for
            prefs.service_level_priority = request.service_level_priority
            prefs.multi_location_aggressiveness = request.multi_location_aggressiveness
        else:
            # Create new preferences
            prefs = UserPreferences(
                user_id="default",
                optimize_for=request.optimize_for,
                service_level_priority=request.service_level_priority,
                multi_location_aggressiveness=request.multi_location_aggressiveness
            )
            db.add(prefs)
        
        db.commit()
        
        response = PreferencesResponse(
            optimize_for=prefs.optimize_for,
            service_level_priority=prefs.service_level_priority,
            multi_location_aggressiveness=prefs.multi_location_aggressiveness,
            created_at=prefs.created_at.isoformat() if prefs.created_at else None,
            updated_at=prefs.updated_at.isoformat() if prefs.updated_at else None
        )
        
        db.close()
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating preferences: {str(e)}")

@router.get("/options")
async def get_preference_options():
    """Get available preference options"""
    return {
        "optimize_for": {
            "stability": "Long-term inventory stability and predictable operations",
            "profit": "Short-term profit maximization and margin protection", 
            "waste_min": "Waste minimization and sustainability focus",
            "balanced": "Balanced approach across all objectives"
        },
        "service_level_priority": {
            "low": "Accept some stockouts to minimize waste",
            "medium": "Balance service level with waste reduction",
            "high": "Maintain high service levels, accept higher waste risk"
        },
        "multi_location_aggressiveness": {
            "low": "Conservative store-to-store transfers",
            "medium": "Moderate transfer recommendations",
            "high": "Aggressive rebalancing across locations"
        }
    }