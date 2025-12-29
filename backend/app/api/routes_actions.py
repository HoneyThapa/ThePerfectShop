from datetime import date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Action, ActionOutcome
from app.services.actions import ActionEngine

router = APIRouter(prefix="/actions", tags=["actions"])


class ActionGenerateRequest(BaseModel):
    snapshot_date: date
    min_risk_score: Optional[float] = 50.0
    include_transfers: Optional[bool] = True
    include_markdowns: Optional[bool] = True
    include_liquidations: Optional[bool] = True


class ActionResponse(BaseModel):
    action_id: int
    action_type: str
    from_store: str
    to_store: Optional[str]
    sku_id: str
    batch_id: str
    qty: int
    discount_pct: Optional[float]
    expected_savings: float
    status: str
    created_at: str
    
    class Config:
        from_attributes = True


class ActionApprovalRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


class ActionCompletionRequest(BaseModel):
    recovered_value: float
    cleared_units: int
    notes: Optional[str] = None


@router.post("/generate")
async def generate_action_recommendations(
    request: ActionGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate action recommendations for at-risk inventory.
    
    Requirements 3.4:
    - Rank all recommendations by expected savings
    - Implement POST /actions/generate endpoint
    """
    try:
        action_engine = ActionEngine(db)
        
        # Generate all recommendations
        recommendations = action_engine.generate_all_recommendations(request.snapshot_date)
        
        # Filter based on request preferences
        filtered_recommendations = []
        for rec in recommendations:
            if (rec['action_type'] == 'TRANSFER' and request.include_transfers) or \
               (rec['action_type'] == 'MARKDOWN' and request.include_markdowns) or \
               (rec['action_type'] == 'LIQUIDATE' and request.include_liquidations):
                filtered_recommendations.append(rec)
        
        # Save to database
        action_ids = action_engine.save_recommendations_to_db(filtered_recommendations)
        
        return {
            "message": f"Generated {len(action_ids)} action recommendations",
            "action_ids": action_ids,
            "recommendations": filtered_recommendations[:20]  # Return top 20 for preview
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.get("/", response_model=List[ActionResponse])
async def list_actions(
    status: Optional[str] = Query(None, description="Filter by status: PROPOSED, APPROVED, DONE, REJECTED"),
    action_type: Optional[str] = Query(None, description="Filter by type: TRANSFER, MARKDOWN, LIQUIDATE"),
    store_id: Optional[str] = Query(None, description="Filter by store ID"),
    limit: int = Query(100, description="Maximum number of actions to return"),
    db: Session = Depends(get_db)
):
    """
    List action recommendations with optional filtering.
    
    Requirements 3.4:
    - Add GET /actions for listing recommendations
    """
    try:
        query = db.query(Action)
        
        if status:
            query = query.filter(Action.status == status.upper())
        
        if action_type:
            query = query.filter(Action.action_type == action_type.upper())
        
        if store_id:
            query = query.filter(Action.from_store == store_id)
        
        actions = query.order_by(Action.expected_savings.desc()).limit(limit).all()
        
        return [ActionResponse(
            action_id=action.action_id,
            action_type=action.action_type,
            from_store=action.from_store,
            to_store=action.to_store,
            sku_id=action.sku_id,
            batch_id=action.batch_id,
            qty=action.qty,
            discount_pct=float(action.discount_pct) if action.discount_pct else None,
            expected_savings=float(action.expected_savings),
            status=action.status,
            created_at=action.created_at.isoformat()
        ) for action in actions]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing actions: {str(e)}")


@router.post("/{action_id}/approve")
async def approve_action(
    action_id: int,
    request: ActionApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Approve or reject an action recommendation.
    
    Requirements 3.5:
    - Create approval and completion endpoints
    """
    try:
        action = db.query(Action).filter(Action.action_id == action_id).first()
        
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        if action.status != 'PROPOSED':
            raise HTTPException(status_code=400, detail="Action is not in PROPOSED status")
        
        action.status = 'APPROVED' if request.approved else 'REJECTED'
        db.commit()
        
        return {
            "message": f"Action {action_id} {'approved' if request.approved else 'rejected'}",
            "action_id": action_id,
            "new_status": action.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating action: {str(e)}")


@router.post("/{action_id}/complete")
async def complete_action(
    action_id: int,
    request: ActionCompletionRequest,
    db: Session = Depends(get_db)
):
    """
    Mark an action as completed and record outcomes.
    
    Requirements 3.5:
    - Create approval and completion endpoints
    """
    try:
        action = db.query(Action).filter(Action.action_id == action_id).first()
        
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        if action.status != 'APPROVED':
            raise HTTPException(status_code=400, detail="Action must be approved before completion")
        
        # Update action status
        action.status = 'DONE'
        
        # Record outcome
        outcome = ActionOutcome(
            action_id=action_id,
            recovered_value=request.recovered_value,
            cleared_units=request.cleared_units,
            notes=request.notes
        )
        
        db.add(outcome)
        db.commit()
        
        return {
            "message": f"Action {action_id} marked as completed",
            "action_id": action_id,
            "recovered_value": request.recovered_value,
            "cleared_units": request.cleared_units
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing action: {str(e)}")


@router.get("/{action_id}")
async def get_action_details(
    action_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific action."""
    try:
        action = db.query(Action).filter(Action.action_id == action_id).first()
        
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        # Get outcome if exists
        outcome = db.query(ActionOutcome).filter(ActionOutcome.action_id == action_id).first()
        
        response = {
            "action_id": action.action_id,
            "action_type": action.action_type,
            "from_store": action.from_store,
            "to_store": action.to_store,
            "sku_id": action.sku_id,
            "batch_id": action.batch_id,
            "qty": action.qty,
            "discount_pct": float(action.discount_pct) if action.discount_pct else None,
            "expected_savings": float(action.expected_savings),
            "status": action.status,
            "created_at": action.created_at.isoformat(),
            "outcome": None
        }
        
        if outcome:
            response["outcome"] = {
                "recovered_value": float(outcome.recovered_value),
                "cleared_units": outcome.cleared_units,
                "notes": outcome.notes,
                "measured_at": outcome.measured_at.isoformat()
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving action: {str(e)}")