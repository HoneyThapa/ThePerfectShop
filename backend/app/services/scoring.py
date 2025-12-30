from datetime import date
from collections import defaultdict
from typing import Set, Optional, List
import logging
from sqlalchemy import func
from app.db.session import SessionLocal
from app.db.models import (
    InventoryBatch,
    FeatureStoreSKU,
    Purchase,
    BatchRisk,
    DataChangeTracking,
)

logger = logging.getLogger(__name__)


def compute_batch_risk(snapshot_date: date, incremental: bool = True, changed_batches: Optional[Set[tuple]] = None):
    """
    Compute batch risk with incremental processing optimization.
    
    Requirements 7.3, 7.4:
    - Implement incremental data processing where possible
    - Add change detection to avoid full recomputation
    - Optimize job performance for large datasets
    """
    db = SessionLocal()
    
    try:
        if incremental and changed_batches is not None:
            # Process only changed batches
            logger.info(f"Computing risk scores incrementally for {len(changed_batches)} changed batches")
            _compute_risk_for_batches(snapshot_date, changed_batches, db)
        else:
            # Full processing
            logger.info("Computing risk scores for all batches")
            _compute_risk_full(snapshot_date, db)
            
        db.commit()
        logger.info(f"Risk scoring completed for {snapshot_date}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error computing batch risk: {str(e)}")
        raise
    finally:
        db.close()


def _compute_risk_full(snapshot_date: date, db):
    """Compute risk scores for all batches."""
    # Load features and costs into memory for efficient lookup
    features = _load_features_dict(snapshot_date, db)
    costs = _load_unit_costs_dict(db)
    
    # Process inventory batches in batches to optimize memory usage
    batch_size = 1000
    offset = 0
    
    while True:
        inventory_batches = (
            db.query(InventoryBatch)
            .filter_by(snapshot_date=snapshot_date)
            .offset(offset)
            .limit(batch_size)
            .all()
        )
        
        if not inventory_batches:
            break
            
        risk_rows = []
        for inv in inventory_batches:
            risk_row = _calculate_risk_for_batch(inv, features, costs, snapshot_date)
            risk_rows.append(risk_row)
        
        # Save batch of risk scores
        _save_risk_batch(risk_rows, db)
        
        offset += batch_size
        
        if len(inventory_batches) < batch_size:
            break


def _compute_risk_for_batches(snapshot_date: date, changed_batches: Set[tuple], db):
    """Compute risk scores only for specified batches."""
    if not changed_batches:
        return
    
    # Load features and costs
    features = _load_features_dict(snapshot_date, db)
    costs = _load_unit_costs_dict(db)
    
    # Process changed batches in smaller chunks
    batch_list = list(changed_batches)
    chunk_size = 500
    
    for i in range(0, len(batch_list), chunk_size):
        chunk = batch_list[i:i + chunk_size]
        
        # Build query for this chunk of batches
        batch_conditions = []
        for store_id, sku_id, batch_id in chunk:
            batch_conditions.append(
                (InventoryBatch.store_id == store_id) &
                (InventoryBatch.sku_id == sku_id) &
                (InventoryBatch.batch_id == batch_id)
            )
        
        if not batch_conditions:
            continue
            
        # Combine conditions with OR
        combined_condition = batch_conditions[0]
        for condition in batch_conditions[1:]:
            combined_condition = combined_condition | condition
        
        inventory_batches = (
            db.query(InventoryBatch)
            .filter(
                InventoryBatch.snapshot_date == snapshot_date,
                combined_condition
            )
            .all()
        )
        
        risk_rows = []
        for inv in inventory_batches:
            risk_row = _calculate_risk_for_batch(inv, features, costs, snapshot_date)
            risk_rows.append(risk_row)
        
        if risk_rows:
            _save_risk_batch(risk_rows, db)


def _load_features_dict(snapshot_date: date, db) -> dict:
    """Load features into memory for efficient lookup."""
    features = {}
    for f in db.query(FeatureStoreSKU).filter_by(date=snapshot_date):
        features[(f.store_id, f.sku_id)] = float(f.v14 or 0)
    return features


def _load_unit_costs_dict(db) -> defaultdict:
    """Load unit costs into memory for efficient lookup."""
    costs = defaultdict(lambda: 10.0)
    for p in db.query(Purchase):
        costs[(p.store_id, p.sku_id)] = float(p.unit_cost)
    return costs


def _calculate_risk_for_batch(inv: InventoryBatch, features: dict, costs: defaultdict, snapshot_date: date) -> BatchRisk:
    """Calculate risk score for a single inventory batch."""
    v14 = features.get((inv.store_id, inv.sku_id), 0)
    days = (inv.expiry_date - snapshot_date).days
    expected = max(0, v14 * days)
    at_risk = max(0, inv.on_hand_qty - expected)

    risk_score = (
        0.7 * (at_risk / inv.on_hand_qty if inv.on_hand_qty else 0)
        + 0.3 * (1 / (days + 1))
    ) * 100

    return BatchRisk(
        snapshot_date=snapshot_date,
        store_id=inv.store_id,
        sku_id=inv.sku_id,
        batch_id=inv.batch_id,
        days_to_expiry=days,
        expected_sales_to_expiry=expected,
        at_risk_units=int(at_risk),
        at_risk_value=at_risk * costs[(inv.store_id, inv.sku_id)],
        risk_score=min(100, round(risk_score, 1)),
    )


def _save_risk_batch(risk_rows: List[BatchRisk], db):
    """Save a batch of risk scores to the database."""
    for row in risk_rows:
        db.merge(row)
    
    # Flush to database but don't commit yet
    db.flush()


def detect_inventory_changes(snapshot_date: date) -> Set[tuple]:
    """
    Detect which inventory batches have changed since last risk scoring.
    
    Requirements 7.3, 7.4:
    - Add change detection to avoid full recomputation
    """
    db = SessionLocal()
    
    try:
        # Get the last risk scoring date
        last_risk_scoring = (
            db.query(DataChangeTracking)
            .filter(
                DataChangeTracking.processing_type == "risk_scoring",
                DataChangeTracking.snapshot_date <= snapshot_date
            )
            .order_by(DataChangeTracking.snapshot_date.desc())
            .first()
        )
        
        if not last_risk_scoring:
            # No previous scoring, return all batches
            logger.info("No previous risk scoring found, processing all batches")
            all_batches = (
                db.query(
                    InventoryBatch.store_id,
                    InventoryBatch.sku_id,
                    InventoryBatch.batch_id
                )
                .filter(InventoryBatch.snapshot_date == snapshot_date)
                .distinct()
                .all()
            )
            return set((store_id, sku_id, batch_id) for store_id, sku_id, batch_id in all_batches)
        
        # Find batches that have changed since last scoring
        # This includes new batches and batches with quantity changes
        current_batches = {}
        for batch in db.query(InventoryBatch).filter_by(snapshot_date=snapshot_date):
            key = (batch.store_id, batch.sku_id, batch.batch_id)
            current_batches[key] = batch.on_hand_qty
        
        # Get previous batch data if available
        previous_batches = {}
        if last_risk_scoring.snapshot_date:
            for batch in db.query(InventoryBatch).filter_by(snapshot_date=last_risk_scoring.snapshot_date):
                key = (batch.store_id, batch.sku_id, batch.batch_id)
                previous_batches[key] = batch.on_hand_qty
        
        # Find changed batches
        changed_batches = set()
        
        # New batches or quantity changes
        for key, current_qty in current_batches.items():
            previous_qty = previous_batches.get(key)
            if previous_qty is None or previous_qty != current_qty:
                changed_batches.add(key)
        
        # Also check if features have changed (affects risk calculation)
        features_changed = _check_features_changed(snapshot_date, last_risk_scoring.last_processed_at.date(), db)
        if features_changed:
            # If features changed, we need to recalculate all batches
            logger.info("Features have changed, processing all batches")
            return set(current_batches.keys())
        
        logger.info(f"Detected {len(changed_batches)} changed inventory batches since {last_risk_scoring.snapshot_date}")
        
        return changed_batches
        
    except Exception as e:
        logger.error(f"Error detecting inventory changes: {str(e)}")
        # On error, return empty set to trigger full processing
        return set()
    finally:
        db.close()


def _check_features_changed(snapshot_date: date, last_scoring_date: date, db) -> bool:
    """Check if features have been updated since last risk scoring."""
    try:
        # Check if there are any features with updated_at > last_scoring_date
        # Since we don't have updated_at on features, check if feature build happened after last scoring
        last_feature_build = (
            db.query(DataChangeTracking)
            .filter(
                DataChangeTracking.processing_type == "features",
                DataChangeTracking.snapshot_date == snapshot_date,
                DataChangeTracking.last_processed_at > last_scoring_date
            )
            .first()
        )
        
        return last_feature_build is not None
        
    except Exception as e:
        logger.warning(f"Error checking feature changes: {str(e)}")
        return True  # Assume changed on error


def optimize_risk_calculation_performance(snapshot_date: date) -> dict:
    """
    Optimize risk calculation performance for large datasets.
    
    Requirements 7.3, 7.4:
    - Optimize job performance for large datasets
    """
    db = SessionLocal()
    
    try:
        # Get statistics about the data volume
        total_batches = (
            db.query(func.count(InventoryBatch.batch_id))
            .filter(InventoryBatch.snapshot_date == snapshot_date)
            .scalar()
        ) or 0
        
        total_features = (
            db.query(func.count(FeatureStoreSKU.sku_id))
            .filter(FeatureStoreSKU.date == snapshot_date)
            .scalar()
        ) or 0
        
        # Determine optimal processing strategy
        if total_batches > 50000:
            strategy = "chunked_processing"
            chunk_size = 500
        elif total_batches > 10000:
            strategy = "batch_processing"
            chunk_size = 1000
        else:
            strategy = "full_processing"
            chunk_size = None
        
        logger.info(f"Risk calculation optimization: {strategy} for {total_batches} batches and {total_features} features")
        
        return {
            "strategy": strategy,
            "chunk_size": chunk_size,
            "total_batches": total_batches,
            "total_features": total_features
        }
        
    except Exception as e:
        logger.error(f"Error optimizing risk calculation: {str(e)}")
        return {
            "strategy": "full_processing",
            "chunk_size": None,
            "total_batches": 0,
            "total_features": 0
        }
    finally:
        db.close()
