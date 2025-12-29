from fastapi import APIRouter, HTTPException, Query
from datetime import date
from typing import Optional, List, Dict, Any
from app.db.session import SessionLocal
from app.db.models import BatchRisk
from app.services.scoring import compute_batch_risk, get_risk_summary

router = APIRouter()


@router.post("/risk/compute")
def compute_risk_scores(snapshot_date: date) -> Dict[str, Any]:
    """
    Compute risk scores for all inventory batches on a given snapshot date
    
    This endpoint processes inventory batches and calculates:
    - Days to expiry
    - Expected sales to expiry (using v14 velocity)
    - At-risk units and value
    - Risk score (0-100) based on urgency and financial impact
    """
    try:
        result = compute_batch_risk(snapshot_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute risk scores: {str(e)}")


@router.get("/risk")
def get_risk_inbox(
    snapshot_date: date,
    store_id: Optional[str] = Query(None, description="Filter by store ID"),
    min_risk_score: Optional[float] = Query(None, description="Minimum risk score (0-100)", ge=0, le=100),
    max_days_to_expiry: Optional[int] = Query(None, description="Maximum days to expiry", ge=0),
    limit: int = Query(100, description="Maximum number of results", le=1000)
) -> List[Dict[str, Any]]:
    """
    Get Risk Inbox - list of at-risk inventory batches
    
    Returns batches ordered by risk score (highest first) with optional filtering
    """
    try:
        db = SessionLocal()
        
        # Build query with filters
        query = db.query(BatchRisk).filter(BatchRisk.snapshot_date == snapshot_date)
        
        if store_id:
            query = query.filter(BatchRisk.store_id == store_id)
        
        if min_risk_score is not None:
            query = query.filter(BatchRisk.risk_score >= min_risk_score)
        
        if max_days_to_expiry is not None:
            query = query.filter(BatchRisk.days_to_expiry <= max_days_to_expiry)
        
        # Order by risk score (highest first) and apply limit
        risks = query.order_by(BatchRisk.risk_score.desc()).limit(limit).all()
        
        if not risks:
            return []
        
        # Format response
        return [
            {
                "store_id": r.store_id,
                "sku_id": r.sku_id,
                "batch_id": r.batch_id,
                "days_to_expiry": r.days_to_expiry,
                "expected_sales_to_expiry": float(r.expected_sales_to_expiry),
                "at_risk_units": r.at_risk_units,
                "at_risk_value": float(r.at_risk_value),
                "risk_score": float(r.risk_score),
                "risk_level": (
                    "HIGH" if r.risk_score >= 70 else
                    "MEDIUM" if r.risk_score >= 30 else
                    "LOW"
                )
            }
            for r in risks
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get risk data: {str(e)}")
    finally:
        db.close()


@router.get("/risk/summary")
def get_risk_summary_endpoint(snapshot_date: date) -> Dict[str, Any]:
    """
    Get risk summary statistics for a snapshot date
    
    Returns distribution of risk levels, financial impact, and key metrics
    """
    try:
        summary = get_risk_summary(snapshot_date)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get risk summary: {str(e)}")


@router.get("/risk/stores")
def get_risk_by_store(
    snapshot_date: date,
    min_risk_score: Optional[float] = Query(50.0, description="Minimum risk score threshold")
) -> List[Dict[str, Any]]:
    """
    Get risk summary grouped by store
    
    Useful for identifying which stores have the most at-risk inventory
    """
    try:
        db = SessionLocal()
        
        # Query risks above threshold
        query = db.query(BatchRisk).filter(
            BatchRisk.snapshot_date == snapshot_date,
            BatchRisk.risk_score >= min_risk_score
        )
        
        risks = query.all()
        
        if not risks:
            return []
        
        # Group by store
        store_risks = {}
        for risk in risks:
            store_id = risk.store_id
            if store_id not in store_risks:
                store_risks[store_id] = {
                    "store_id": store_id,
                    "total_batches": 0,
                    "total_at_risk_units": 0,
                    "total_at_risk_value": 0.0,
                    "avg_risk_score": 0.0,
                    "max_risk_score": 0.0,
                    "risk_scores": []
                }
            
            store_data = store_risks[store_id]
            store_data["total_batches"] += 1
            store_data["total_at_risk_units"] += risk.at_risk_units
            store_data["total_at_risk_value"] += float(risk.at_risk_value)
            store_data["risk_scores"].append(float(risk.risk_score))
            store_data["max_risk_score"] = max(store_data["max_risk_score"], float(risk.risk_score))
        
        # Calculate averages and format response
        result = []
        for store_data in store_risks.values():
            store_data["avg_risk_score"] = round(
                sum(store_data["risk_scores"]) / len(store_data["risk_scores"]), 2
            )
            store_data["total_at_risk_value"] = round(store_data["total_at_risk_value"], 2)
            del store_data["risk_scores"]  # Remove intermediate data
            result.append(store_data)
        
        # Sort by total at-risk value (highest first)
        result.sort(key=lambda x: x["total_at_risk_value"], reverse=True)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get store risk data: {str(e)}")
    finally:
        db.close()


@router.get("/risk/urgent")
def get_urgent_risks(
    snapshot_date: date,
    max_days: int = Query(7, description="Maximum days to expiry for urgent items", ge=1, le=30)
) -> List[Dict[str, Any]]:
    """
    Get urgent risks - items expiring soon with high risk scores
    
    Focuses on items that need immediate attention
    """
    try:
        db = SessionLocal()
        
        # Query urgent items (expiring soon with high risk)
        urgent_risks = db.query(BatchRisk).filter(
            BatchRisk.snapshot_date == snapshot_date,
            BatchRisk.days_to_expiry <= max_days,
            BatchRisk.risk_score >= 50.0  # Only medium-high risk items
        ).order_by(
            BatchRisk.days_to_expiry.asc(),  # Most urgent first
            BatchRisk.risk_score.desc()      # Then by risk score
        ).limit(50).all()
        
        return [
            {
                "store_id": r.store_id,
                "sku_id": r.sku_id,
                "batch_id": r.batch_id,
                "days_to_expiry": r.days_to_expiry,
                "at_risk_units": r.at_risk_units,
                "at_risk_value": float(r.at_risk_value),
                "risk_score": float(r.risk_score),
                "urgency": "CRITICAL" if r.days_to_expiry <= 3 else "HIGH"
            }
            for r in urgent_risks
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get urgent risks: {str(e)}")
    finally:
        db.close()
