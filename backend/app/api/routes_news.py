from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from app.db.session import SessionLocal
from app.db.models import NewsEvents

router = APIRouter(prefix="/news", tags=["News Events"])

class NewsEventRequest(BaseModel):
    event_date: date
    event_type: str  # demand_spike, supplier_delay, seasonal, weather, etc.
    description: str
    impact_stores: Optional[List[str]] = None
    impact_skus: Optional[List[str]] = None
    score_modifier: float = 0.0  # -0.2 to +0.2

class NewsEventResponse(BaseModel):
    id: int
    event_date: str
    event_type: str
    description: str
    impact_stores: Optional[List[str]]
    impact_skus: Optional[List[str]]
    score_modifier: float
    created_at: str

@router.get("/", response_model=List[NewsEventResponse])
async def get_news_events(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    event_type: Optional[str] = None
):
    """Get news events with optional filtering"""
    try:
        db = SessionLocal()
        query = db.query(NewsEvents)
        
        if start_date:
            query = query.filter(NewsEvents.event_date >= start_date)
        if end_date:
            query = query.filter(NewsEvents.event_date <= end_date)
        if event_type:
            query = query.filter(NewsEvents.event_type == event_type)
        
        events = query.order_by(NewsEvents.event_date.desc()).all()
        db.close()
        
        return [
            NewsEventResponse(
                id=event.id,
                event_date=event.event_date.isoformat(),
                event_type=event.event_type,
                description=event.description,
                impact_stores=event.impact_stores,
                impact_skus=event.impact_skus,
                score_modifier=float(event.score_modifier),
                created_at=event.created_at.isoformat()
            )
            for event in events
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news events: {str(e)}")

@router.post("/", response_model=NewsEventResponse)
async def create_news_event(request: NewsEventRequest):
    """Create a new news event"""
    try:
        # Validate score modifier range
        if not -0.5 <= request.score_modifier <= 0.5:
            raise HTTPException(
                status_code=400, 
                detail="score_modifier must be between -0.5 and 0.5"
            )
        
        db = SessionLocal()
        
        event = NewsEvents(
            event_date=request.event_date,
            event_type=request.event_type,
            description=request.description,
            impact_stores=request.impact_stores,
            impact_skus=request.impact_skus,
            score_modifier=request.score_modifier
        )
        
        db.add(event)
        db.commit()
        
        response = NewsEventResponse(
            id=event.id,
            event_date=event.event_date.isoformat(),
            event_type=event.event_type,
            description=event.description,
            impact_stores=event.impact_stores,
            impact_skus=event.impact_skus,
            score_modifier=float(event.score_modifier),
            created_at=event.created_at.isoformat()
        )
        
        db.close()
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating news event: {str(e)}")

@router.delete("/{event_id}")
async def delete_news_event(event_id: int):
    """Delete a news event"""
    try:
        db = SessionLocal()
        event = db.query(NewsEvents).filter(NewsEvents.id == event_id).first()
        
        if not event:
            raise HTTPException(status_code=404, detail="News event not found")
        
        db.delete(event)
        db.commit()
        db.close()
        
        return {"status": "success", "message": "News event deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting news event: {str(e)}")

@router.get("/types")
async def get_event_types():
    """Get available event types"""
    return {
        "event_types": [
            "demand_spike",
            "supplier_delay", 
            "seasonal",
            "weather",
            "promotion",
            "competitor_action",
            "supply_shortage",
            "logistics_issue",
            "market_trend",
            "other"
        ]
    }