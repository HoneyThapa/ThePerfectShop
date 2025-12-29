from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.kpis import KPIService, AuditTrailService

router = APIRouter(prefix="/kpis", tags=["KPIs"])


@router.get("/dashboard")
async def get_dashboard_metrics(
    as_of_date: Optional[date] = Query(None, description="Date for metrics calculation (defaults to today)"),
    db: Session = Depends(get_db)
):
    """
    Get main dashboard KPI metrics.
    
    Requirements 4.4:
    - Implement GET /kpis/dashboard for main metrics
    
    Returns:
    - Total at-risk inventory values
    - Recovered value from completed actions
    - Write-off reduction metrics
    - Inventory turnover improvement
    - Action counts and ROI
    """
    try:
        kpi_service = KPIService(db)
        metrics = kpi_service.calculate_dashboard_metrics(as_of_date)
        
        return {
            "status": "success",
            "data": {
                "as_of_date": as_of_date or date.today(),
                "total_at_risk_value": metrics.total_at_risk_value,
                "recovered_value": metrics.recovered_value,
                "write_off_reduction": metrics.write_off_reduction,
                "inventory_turnover_improvement": metrics.inventory_turnover_improvement,
                "cash_freed": metrics.cash_freed,
                "actions_completed": metrics.actions_completed,
                "actions_pending": metrics.actions_pending,
                "roi_percentage": metrics.roi_percentage
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating dashboard metrics: {str(e)}")


@router.get("/savings")
async def get_savings_tracking(
    start_date: date = Query(..., description="Start date for savings tracking"),
    end_date: date = Query(..., description="End date for savings tracking"),
    period_type: str = Query("monthly", description="Period type: daily, weekly, or monthly"),
    db: Session = Depends(get_db)
):
    """
    Get savings tracking over time.
    
    Requirements 4.4:
    - Add GET /kpis/savings for savings tracking
    
    Returns:
    - Time-series data for savings by period
    - Breakdown by action type (transfer, markdown, liquidation)
    - Prevented writeoffs and action counts
    """
    try:
        if period_type not in ['daily', 'weekly', 'monthly']:
            raise HTTPException(status_code=400, detail="period_type must be 'daily', 'weekly', or 'monthly'")
        
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")
        
        kpi_service = KPIService(db)
        savings_data = kpi_service.calculate_savings_over_time(start_date, end_date, period_type)
        
        # Format response data
        formatted_data = []
        for period in savings_data:
            formatted_data.append({
                "period_start": period.period_start,
                "period_end": period.period_end,
                "total_savings": period.total_savings,
                "transfer_savings": period.transfer_savings,
                "markdown_savings": period.markdown_savings,
                "liquidation_savings": period.liquidation_savings,
                "prevented_writeoffs": period.prevented_writeoffs,
                "actions_count": period.actions_count
            })
        
        # Calculate summary statistics
        total_savings = sum(p.total_savings for p in savings_data)
        total_actions = sum(p.actions_count for p in savings_data)
        avg_savings_per_period = total_savings / len(savings_data) if savings_data else 0
        
        return {
            "status": "success",
            "data": {
                "period_type": period_type,
                "start_date": start_date,
                "end_date": end_date,
                "summary": {
                    "total_savings": total_savings,
                    "total_actions": total_actions,
                    "average_savings_per_period": avg_savings_per_period,
                    "periods_count": len(savings_data)
                },
                "periods": formatted_data
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating savings tracking: {str(e)}")


@router.get("/inventory")
async def get_inventory_health_metrics(
    as_of_date: Optional[date] = Query(None, description="Date for inventory health calculation (defaults to today)"),
    db: Session = Depends(get_db)
):
    """
    Get inventory health metrics.
    
    Requirements 4.4:
    - Create GET /kpis/inventory for inventory health
    
    Returns:
    - Total inventory value and at-risk percentages
    - Risk distribution (high/medium/low risk batches)
    - Average days to expiry
    - Inventory turnover rate
    """
    try:
        kpi_service = KPIService(db)
        health_metrics = kpi_service.calculate_inventory_health_metrics(as_of_date)
        
        return {
            "status": "success",
            "data": {
                "as_of_date": as_of_date or date.today(),
                "total_inventory_value": health_metrics.total_inventory_value,
                "at_risk_inventory_value": health_metrics.at_risk_inventory_value,
                "at_risk_percentage": health_metrics.at_risk_percentage,
                "risk_distribution": {
                    "high_risk_batches": health_metrics.high_risk_batches,
                    "medium_risk_batches": health_metrics.medium_risk_batches,
                    "low_risk_batches": health_metrics.low_risk_batches,
                    "total_batches": (
                        health_metrics.high_risk_batches + 
                        health_metrics.medium_risk_batches + 
                        health_metrics.low_risk_batches
                    )
                },
                "avg_days_to_expiry": health_metrics.avg_days_to_expiry,
                "inventory_turnover_rate": health_metrics.inventory_turnover_rate
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating inventory health metrics: {str(e)}")


@router.get("/audit/{action_id}")
async def get_action_audit_trail(
    action_id: int,
    db: Session = Depends(get_db)
):
    """
    Get complete audit trail for a specific action.
    
    Requirements 4.5:
    - Provide audit trail access via API
    """
    try:
        audit_service = AuditTrailService(db)
        audit_trail = audit_service.get_action_audit_trail(action_id)
        
        if not audit_trail:
            raise HTTPException(status_code=404, detail=f"No audit trail found for action {action_id}")
        
        # Format audit trail data
        formatted_trail = []
        for entry in audit_trail:
            formatted_trail.append({
                "timestamp": entry.timestamp,
                "event_type": entry.event_type,
                "user_id": entry.user_id,
                "details": entry.details,
                "financial_impact": entry.financial_impact
            })
        
        return {
            "status": "success",
            "data": {
                "action_id": action_id,
                "audit_trail": formatted_trail
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving audit trail: {str(e)}")


@router.post("/outcomes/{action_id}")
async def record_action_outcome(
    action_id: int,
    recovered_value: float,
    cleared_units: int,
    notes: str = "",
    db: Session = Depends(get_db)
):
    """
    Record the outcome of a completed action.
    
    Requirements 4.5:
    - Provide API endpoint for recording action outcomes
    """
    try:
        audit_service = AuditTrailService(db)
        outcome = audit_service.record_action_outcome(
            action_id=action_id,
            recovered_value=recovered_value,
            cleared_units=cleared_units,
            notes=notes,
            user_id=None  # Would come from authentication context
        )
        
        return {
            "status": "success",
            "message": f"Outcome recorded for action {action_id}",
            "data": {
                "action_id": action_id,
                "recovered_value": float(outcome.recovered_value),
                "cleared_units": outcome.cleared_units,
                "measured_at": outcome.measured_at,
                "notes": outcome.notes
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording action outcome: {str(e)}")


@router.get("/financial-impact")
async def get_financial_impact_summary(
    start_date: Optional[date] = Query(None, description="Start date for financial impact analysis"),
    end_date: Optional[date] = Query(None, description="End date for financial impact analysis"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive financial impact summary.
    
    Requirements 4.5:
    - Provide financial impact analysis via API
    """
    try:
        audit_service = AuditTrailService(db)
        impact_summary = audit_service.get_financial_impact_summary(start_date, end_date)
        
        return {
            "status": "success",
            "data": impact_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating financial impact: {str(e)}")


@router.get("/outcomes/{action_id}")
async def get_action_outcome_details(
    action_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed outcome data for a specific action.
    
    Requirements 4.5:
    - Provide detailed outcome information via API
    """
    try:
        audit_service = AuditTrailService(db)
        outcome_data = audit_service.get_action_outcome_data(action_id)
        
        if not outcome_data:
            raise HTTPException(status_code=404, detail=f"No outcome data found for action {action_id}")
        
        return {
            "status": "success",
            "data": {
                "action_id": outcome_data.action_id,
                "action_type": outcome_data.action_type,
                "expected_savings": outcome_data.expected_savings,
                "actual_recovered_value": outcome_data.actual_recovered_value,
                "cleared_units": outcome_data.cleared_units,
                "completion_date": outcome_data.completion_date,
                "variance": outcome_data.variance,
                "variance_percentage": outcome_data.variance_percentage,
                "notes": outcome_data.notes
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving outcome details: {str(e)}")