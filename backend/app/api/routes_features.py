"""
API routes for features service
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import date
from typing import Optional, List, Dict, Any
from app.services.features import build_features, get_store_sku_velocity, get_all_features

router = APIRouter()


@router.post("/features/build")
def build_features_endpoint(snapshot_date: date) -> Dict[str, Any]:
    """
    Build velocity and volatility features for all store-SKU combinations
    
    This endpoint processes sales data and calculates:
    - v7: 7-day rolling average velocity
    - v14: 14-day rolling average velocity  
    - v30: 30-day rolling average velocity
    - volatility: Standard deviation of daily sales over 30 days
    """
    try:
        result = build_features(snapshot_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build features: {str(e)}")


@router.get("/features/velocity/{store_id}/{sku_id}")
def get_velocity(
    store_id: str, 
    sku_id: str, 
    snapshot_date: Optional[date] = Query(None, description="Specific date for features, defaults to most recent")
) -> Dict[str, Any]:
    """
    Get velocity metrics for a specific store-SKU combination
    
    Answers the question: "How fast does this SKU sell in this store?"
    """
    try:
        result = get_store_sku_velocity(store_id, sku_id, snapshot_date)
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"No velocity data found for store {store_id}, SKU {sku_id}"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get velocity data: {str(e)}")


@router.get("/features")
def list_features(
    snapshot_date: Optional[date] = Query(None, description="Filter by specific date"),
    store_id: Optional[str] = Query(None, description="Filter by store ID"),
    sku_id: Optional[str] = Query(None, description="Filter by SKU ID"),
    limit: int = Query(100, description="Maximum number of results", le=1000)
) -> List[Dict[str, Any]]:
    """
    List features with optional filtering
    
    Returns velocity and volatility metrics for store-SKU combinations
    """
    try:
        results = get_all_features(snapshot_date, store_id, sku_id)
        
        # Apply limit
        if limit and len(results) > limit:
            results = results[:limit]
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list features: {str(e)}")


@router.get("/features/summary")
def features_summary(snapshot_date: Optional[date] = Query(None)) -> Dict[str, Any]:
    """
    Get summary statistics for features
    """
    try:
        features = get_all_features(snapshot_date)
        
        if not features:
            return {
                "total_store_sku_combinations": 0,
                "snapshot_date": snapshot_date.isoformat() if snapshot_date else None
            }
        
        # Calculate summary statistics
        velocities_v14 = [f["v14"] for f in features]
        volatilities = [f["volatility"] for f in features]
        
        summary = {
            "total_store_sku_combinations": len(features),
            "snapshot_date": features[0]["date"] if features else None,
            "velocity_stats": {
                "avg_v14": sum(velocities_v14) / len(velocities_v14),
                "max_v14": max(velocities_v14),
                "min_v14": min(velocities_v14)
            },
            "volatility_stats": {
                "avg_volatility": sum(volatilities) / len(volatilities),
                "max_volatility": max(volatilities),
                "min_volatility": min(volatilities)
            },
            "top_performers": features[:5]  # Top 5 by v14
        }
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get features summary: {str(e)}")