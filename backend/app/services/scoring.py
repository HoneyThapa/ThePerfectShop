from datetime import date
from collections import defaultdict
import logging
from typing import Dict, List, Optional
from sqlalchemy import func, text
from app.db.session import SessionLocal
from app.db.models import (
    InventoryBatch,
    FeatureStoreSKU,
    Purchase,
    BatchRisk,
)

logger = logging.getLogger(__name__)


def get_unit_costs_with_fallback() -> Dict[tuple, float]:
    """Get unit costs with fallback to average cost per SKU"""
    db = SessionLocal()
    try:
        # Get specific store-SKU unit costs
        costs = {}
        for p in db.query(Purchase).filter(Purchase.unit_cost.isnot(None)):
            key = (p.store_id, p.sku_id)
            costs[key] = float(p.unit_cost)
        
        # Calculate average costs per SKU for fallback
        avg_costs_query = db.query(
            Purchase.sku_id,
            func.avg(Purchase.unit_cost).label('avg_cost')
        ).filter(
            Purchase.unit_cost.isnot(None)
        ).group_by(Purchase.sku_id).all()
        
        avg_costs = {sku_id: float(avg_cost) for sku_id, avg_cost in avg_costs_query}
        
        logger.info(f"Loaded {len(costs)} specific costs and {len(avg_costs)} average costs")
        return costs, avg_costs
        
    finally:
        db.close()


def calculate_risk_score(at_risk_units: int, on_hand_qty: int, days_to_expiry: int, at_risk_value: float) -> float:
    """
    Calculate risk score (0-100) based on:
    - Higher at_risk_units and shorter days_to_expiry → higher risk
    - Incorporates both urgency and financial impact
    """
    if on_hand_qty <= 0 or at_risk_units <= 0:
        return 0.0
    
    # At-risk ratio (0-1): What percentage of inventory is at risk
    at_risk_ratio = min(1.0, at_risk_units / on_hand_qty)
    
    # Urgency factor (0-1): Higher for shorter days to expiry
    # Uses exponential decay: very high urgency for <7 days, moderate for 7-30 days
    if days_to_expiry <= 0:
        urgency_factor = 1.0  # Maximum urgency for expired items
    elif days_to_expiry <= 7:
        urgency_factor = 0.9 + (0.1 * (7 - days_to_expiry) / 7)  # 0.9-1.0
    elif days_to_expiry <= 30:
        urgency_factor = 0.3 + (0.6 * (30 - days_to_expiry) / 23)  # 0.3-0.9
    else:
        urgency_factor = max(0.1, 0.3 * (60 - days_to_expiry) / 30)  # 0.1-0.3
    
    # Value factor (0-1): Higher for more valuable at-risk inventory
    # Logarithmic scaling to handle wide range of values
    if at_risk_value > 0:
        # Normalize based on typical inventory values (adjust as needed)
        value_factor = min(1.0, (at_risk_value / 1000) ** 0.5)
    else:
        value_factor = 0.0
    
    # Composite score with weighted factors
    # 50% at-risk ratio, 35% urgency, 15% value
    risk_score = (
        0.50 * at_risk_ratio +
        0.35 * urgency_factor +
        0.15 * value_factor
    ) * 100
    
    # Special case: if expired and has at-risk units, ensure high score
    if days_to_expiry <= 0 and at_risk_units > 0:
        risk_score = max(risk_score, 95.0)
    
    return min(100.0, max(0.0, round(risk_score, 1)))


def compute_batch_risk(snapshot_date: date) -> Dict[str, any]:
    """
    Compute risk scores for all inventory batches on a given snapshot date
    
    Algorithm:
    1. days_to_expiry = expiry_date - snapshot_date
    2. expected_sales_to_expiry = v14 * days_to_expiry
    3. at_risk_units = max(0, on_hand_qty - expected_sales_to_expiry)
    4. at_risk_value = at_risk_units * unit_cost (with fallback to avg cost)
    5. risk_score = composite score (0-100) based on at_risk_units and days_to_expiry
    """
    
    logger.info(f"Computing batch risk for snapshot date: {snapshot_date}")
    
    db = SessionLocal()
    try:
        # Get velocity features for the snapshot date
        features_query = db.query(FeatureStoreSKU).filter_by(date=snapshot_date)
        features = {
            (f.store_id, f.sku_id): float(f.v14 or 0)
            for f in features_query
        }
        
        if not features:
            logger.warning(f"No velocity features found for {snapshot_date}")
            return {"status": "no_features", "batches_processed": 0}
        
        logger.info(f"Loaded velocity features for {len(features)} store-SKU combinations")
        
        # Get unit costs with fallback logic
        specific_costs, avg_costs = get_unit_costs_with_fallback()
        
        # Get inventory batches for the snapshot date
        inventory_query = db.query(InventoryBatch).filter_by(snapshot_date=snapshot_date)
        inventory_batches = inventory_query.all()
        
        if not inventory_batches:
            logger.warning(f"No inventory batches found for {snapshot_date}")
            return {"status": "no_inventory", "batches_processed": 0}
        
        logger.info(f"Processing {len(inventory_batches)} inventory batches")
        
        processed_count = 0
        error_count = 0
        
        # Process each inventory batch
        for inv in inventory_batches:
            try:
                # Get velocity for this store-SKU combination
                v14 = features.get((inv.store_id, inv.sku_id), 0.0)
                
                # Calculate days to expiry
                days_to_expiry = (inv.expiry_date - snapshot_date).days
                
                # Calculate expected sales to expiry
                expected_sales_to_expiry = max(0.0, v14 * days_to_expiry)
                
                # Calculate at-risk units
                at_risk_units = max(0, inv.on_hand_qty - expected_sales_to_expiry)
                
                # Get unit cost with fallback logic
                cost_key = (inv.store_id, inv.sku_id)
                if cost_key in specific_costs:
                    unit_cost = specific_costs[cost_key]
                elif inv.sku_id in avg_costs:
                    unit_cost = avg_costs[inv.sku_id]
                else:
                    unit_cost = 10.0  # Default fallback cost
                
                # Calculate at-risk value
                at_risk_value = at_risk_units * unit_cost
                
                # Calculate risk score
                risk_score = calculate_risk_score(
                    at_risk_units=int(at_risk_units),
                    on_hand_qty=inv.on_hand_qty,
                    days_to_expiry=days_to_expiry,
                    at_risk_value=at_risk_value
                )
                
                # Create or update batch risk record
                batch_risk = BatchRisk(
                    snapshot_date=snapshot_date,
                    store_id=inv.store_id,
                    sku_id=inv.sku_id,
                    batch_id=inv.batch_id,
                    days_to_expiry=days_to_expiry,
                    expected_sales_to_expiry=round(expected_sales_to_expiry, 2),
                    at_risk_units=int(at_risk_units),
                    at_risk_value=round(at_risk_value, 2),
                    risk_score=risk_score,
                )
                
                db.merge(batch_risk)
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing batch {inv.store_id}-{inv.sku_id}-{inv.batch_id}: {str(e)}")
                error_count += 1
                continue
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Batch risk computation completed: {processed_count} processed, {error_count} errors")
        
        return {
            "status": "success",
            "snapshot_date": snapshot_date.isoformat(),
            "batches_processed": processed_count,
            "errors": error_count,
            "features_loaded": len(features),
            "inventory_batches": len(inventory_batches)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to compute batch risk: {str(e)}")
        raise
    finally:
        db.close()


def get_risk_summary(snapshot_date: date) -> Dict[str, any]:
    """Get summary statistics for risk scores on a given date"""
    
    db = SessionLocal()
    try:
        # Get risk distribution
        risk_query = db.query(BatchRisk).filter_by(snapshot_date=snapshot_date)
        risks = risk_query.all()
        
        if not risks:
            return {"status": "no_data", "snapshot_date": snapshot_date.isoformat()}
        
        # Calculate summary statistics
        risk_scores = [r.risk_score for r in risks]
        at_risk_values = [r.at_risk_value for r in risks]
        at_risk_units = [r.at_risk_units for r in risks]
        
        summary = {
            "status": "success",
            "snapshot_date": snapshot_date.isoformat(),
            "total_batches": len(risks),
            "risk_distribution": {
                "high_risk": len([r for r in risk_scores if r >= 70]),
                "medium_risk": len([r for r in risk_scores if 30 <= r < 70]),
                "low_risk": len([r for r in risk_scores if r < 30])
            },
            "risk_stats": {
                "avg_risk_score": round(sum(risk_scores) / len(risk_scores), 2),
                "max_risk_score": max(risk_scores),
                "min_risk_score": min(risk_scores)
            },
            "financial_impact": {
                "total_at_risk_value": round(sum(at_risk_values), 2),
                "total_at_risk_units": sum(at_risk_units),
                "avg_at_risk_value": round(sum(at_risk_values) / len(at_risk_values), 2)
            }
        }
        
        return summary
        
    finally:
        db.close()
