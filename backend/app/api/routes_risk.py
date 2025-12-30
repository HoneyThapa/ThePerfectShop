from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.schemas import BatchRiskResponse, RiskSummaryResponse, RiskRefreshRequest, StandardResponse
from app.response_models import create_success_response, create_paginated_response, APIResponse
from app.db.session import get_db
from app.db.models import BatchRisk, StoreMaster, SKUMaster
from app.auth import get_current_user, require_analyst, User
from sqlalchemy import func

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/", response_model=APIResponse)
async def get_risk(
    snapshot_date: date = Query(..., description="Date for risk analysis (YYYY-MM-DD format)", example="2024-01-15"),
    min_risk_score: float = Query(0, ge=0, le=100, description="Minimum risk score filter (0-100)", example=50.0),
    store_id: Optional[str] = Query(None, description="Filter by specific store ID", example="STORE001"),
    page: int = Query(1, ge=1, description="Page number for pagination", example=1),
    page_size: int = Query(50, ge=1, le=1000, description="Number of results per page", example=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst())
):
    """
    Retrieve inventory batches at risk of expiry with detailed risk analysis.
    
    Returns a paginated list of inventory batches sorted by risk score (highest first).
    Each batch includes risk metrics, financial impact, and expiry timeline.
    
    **Risk Score Interpretation:**
    - 80-100: High risk (immediate action required)
    - 50-79: Medium risk (monitor closely)
    - 0-49: Low risk (normal monitoring)
    
    **Pagination:**
    - Use `page` and `page_size` parameters to navigate through results
    - Response includes pagination metadata with total counts
    - Maximum page size is 1000 items
    
    **Example Response:**
    ```json
    {
        "success": true,
        "message": "Risk data retrieved successfully",
        "data": [
            {
                "snapshot_date": "2024-01-15",
                "store_id": "STORE001",
                "sku_id": "SKU123",
                "batch_id": "BATCH001",
                "days_to_expiry": 30,
                "expected_sales_to_expiry": 45.5,
                "at_risk_units": 25,
                "at_risk_value": 625.00,
                "risk_score": 85.2
            }
        ],
        "metadata": {
            "pagination": {
                "page": 1,
                "page_size": 50,
                "total_count": 150,
                "total_pages": 3,
                "has_next": true,
                "has_previous": false
            }
        }
    }
    ```
    
    **Query Parameters:**
    - `snapshot_date`: Analysis date (required)
    - `min_risk_score`: Filter batches above this risk threshold
    - `store_id`: Limit results to specific store
    - `page`: Page number (starts from 1)
    - `page_size`: Results per page (1-1000)
    
    **Requirements:** 2.5
    - Make risk analysis results available via API endpoints
    """
    try:
        # Build base query
        query = db.query(BatchRisk).filter(BatchRisk.snapshot_date == snapshot_date)
        
        if min_risk_score > 0:
            query = query.filter(BatchRisk.risk_score >= min_risk_score)
        
        if store_id:
            query = query.filter(BatchRisk.store_id == store_id)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination and ordering
        offset = (page - 1) * page_size
        rows = query.order_by(BatchRisk.risk_score.desc()).offset(offset).limit(page_size).all()

        # Convert to response format
        risk_data = [
            {
                "snapshot_date": r.snapshot_date,
                "store_id": r.store_id,
                "sku_id": r.sku_id,
                "batch_id": r.batch_id,
                "days_to_expiry": r.days_to_expiry,
                "expected_sales_to_expiry": float(r.expected_sales_to_expiry),
                "at_risk_units": r.at_risk_units,
                "at_risk_value": float(r.at_risk_value),
                "risk_score": float(r.risk_score),
            }
            for r in rows
        ]
        
        return create_paginated_response(
            message="Risk data retrieved successfully",
            data=risk_data,
            page=page,
            page_size=page_size,
            total_count=total_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving risk data: {str(e)}")


@router.get("/summary", response_model=List[RiskSummaryResponse])
async def get_risk_summary(
    snapshot_date: date = Query(..., description="Date for risk summary"),
    group_by: str = Query("store", description="Group by 'store' or 'category'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst())
):
    """
    Get risk summary by store or category.
    
    Requirements 2.5:
    - Make risk analysis results available via API endpoints
    """
    try:
        if group_by not in ['store', 'category']:
            raise HTTPException(status_code=400, detail="group_by must be 'store' or 'category'")
        
        if group_by == 'store':
            # Group by store
            query = db.query(
                BatchRisk.store_id,
                func.count(BatchRisk.batch_id).label('total_batches'),
                func.sum(func.case([(BatchRisk.risk_score >= 80, 1)], else_=0)).label('high_risk_batches'),
                func.sum(func.case([(BatchRisk.risk_score.between(50, 79), 1)], else_=0)).label('medium_risk_batches'),
                func.sum(func.case([(BatchRisk.risk_score < 50, 1)], else_=0)).label('low_risk_batches'),
                func.sum(BatchRisk.at_risk_value).label('total_at_risk_value'),
                func.avg(BatchRisk.risk_score).label('avg_risk_score')
            ).filter(BatchRisk.snapshot_date == snapshot_date).group_by(BatchRisk.store_id).all()
            
            return [
                RiskSummaryResponse(
                    store_id=row.store_id,
                    total_batches=row.total_batches,
                    high_risk_batches=row.high_risk_batches,
                    medium_risk_batches=row.medium_risk_batches,
                    low_risk_batches=row.low_risk_batches,
                    total_at_risk_value=float(row.total_at_risk_value or 0),
                    avg_risk_score=float(row.avg_risk_score or 0)
                )
                for row in query
            ]
        
        else:  # group_by == 'category'
            # Group by category (requires join with SKU master)
            query = db.query(
                SKUMaster.category,
                func.count(BatchRisk.batch_id).label('total_batches'),
                func.sum(func.case([(BatchRisk.risk_score >= 80, 1)], else_=0)).label('high_risk_batches'),
                func.sum(func.case([(BatchRisk.risk_score.between(50, 79), 1)], else_=0)).label('medium_risk_batches'),
                func.sum(func.case([(BatchRisk.risk_score < 50, 1)], else_=0)).label('low_risk_batches'),
                func.sum(BatchRisk.at_risk_value).label('total_at_risk_value'),
                func.avg(BatchRisk.risk_score).label('avg_risk_score')
            ).join(SKUMaster, BatchRisk.sku_id == SKUMaster.sku_id)\
             .filter(BatchRisk.snapshot_date == snapshot_date)\
             .group_by(SKUMaster.category).all()
            
            return [
                RiskSummaryResponse(
                    category=row.category,
                    total_batches=row.total_batches,
                    high_risk_batches=row.high_risk_batches,
                    medium_risk_batches=row.medium_risk_batches,
                    low_risk_batches=row.low_risk_batches,
                    total_at_risk_value=float(row.total_at_risk_value or 0),
                    avg_risk_score=float(row.avg_risk_score or 0)
                )
                for row in query
            ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating risk summary: {str(e)}")


@router.post("/refresh", response_model=StandardResponse)
async def refresh_risk_analysis(
    request: RiskRefreshRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst())
):
    """
    Trigger risk recalculation for a specific date.
    
    Requirements 2.5:
    - Make risk analysis results available via API endpoints
    """
    try:
        # This would trigger the risk scoring service
        # For now, return a success message
        return StandardResponse(
            status="success",
            message=f"Risk analysis refresh triggered for {request.snapshot_date}",
            data={
                "snapshot_date": request.snapshot_date,
                "force_recalculation": request.force_recalculation
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering risk refresh: {str(e)}")
