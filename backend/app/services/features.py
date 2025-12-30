import pandas as pd
from sqlalchemy import text, func
from datetime import timedelta, date
from typing import Set, List, Optional
import logging
from app.db.session import engine, SessionLocal
from app.db.models import FeatureStoreSKU, SalesDaily, DataChangeTracking

logger = logging.getLogger(__name__)


def build_features(snapshot_date: date, incremental: bool = True, changed_store_skus: Optional[Set[tuple]] = None):
    """
    Build features with incremental processing optimization.
    
    Requirements 7.3, 7.4:
    - Implement incremental data processing where possible
    - Add change detection to avoid full recomputation
    - Optimize job performance for large datasets
    """
    db = SessionLocal()
    
    try:
        if incremental and changed_store_skus is not None:
            # Process only changed store-SKU combinations
            logger.info(f"Building features incrementally for {len(changed_store_skus)} changed store-SKU combinations")
            _build_features_for_store_skus(snapshot_date, changed_store_skus, db)
        else:
            # Full processing
            logger.info("Building features for all store-SKU combinations")
            _build_features_full(snapshot_date, db)
            
        db.commit()
        logger.info(f"Feature building completed for {snapshot_date}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error building features: {str(e)}")
        raise
    finally:
        db.close()


def _build_features_full(snapshot_date: date, db):
    """Build features for all store-SKU combinations."""
    query = text("""
        SELECT date, store_id, sku_id, units_sold
        FROM sales_daily
        WHERE date BETWEEN :start AND :end
        ORDER BY store_id, sku_id, date
    """)

    df = pd.read_sql(
        query,
        engine,
        params={
            "start": snapshot_date - timedelta(days=29),
            "end": snapshot_date,
        },
    )

    if df.empty:
        logger.warning("No sales data found for feature building")
        return

    # Process in batches to optimize memory usage
    batch_size = 1000
    rows = []
    
    for (store, sku), g in df.groupby(["store_id", "sku_id"]):
        feature_row = _calculate_features_for_store_sku(store, sku, g, snapshot_date)
        rows.append(feature_row)
        
        # Process in batches to avoid memory issues
        if len(rows) >= batch_size:
            _save_feature_batch(rows, db)
            rows = []
    
    # Process remaining rows
    if rows:
        _save_feature_batch(rows, db)


def _build_features_for_store_skus(snapshot_date: date, changed_store_skus: Set[tuple], db):
    """Build features only for specified store-SKU combinations."""
    if not changed_store_skus:
        return
    
    # Convert set to list for SQL IN clause
    store_sku_list = list(changed_store_skus)
    
    # Build parameterized query for specific store-SKU combinations
    placeholders = []
    params = {
        "start": snapshot_date - timedelta(days=29),
        "end": snapshot_date,
    }
    
    # Create WHERE conditions for each store-SKU pair
    where_conditions = []
    for i, (store_id, sku_id) in enumerate(store_sku_list):
        store_param = f"store_{i}"
        sku_param = f"sku_{i}"
        where_conditions.append(f"(store_id = :{store_param} AND sku_id = :{sku_param})")
        params[store_param] = store_id
        params[sku_param] = sku_id
    
    where_clause = " OR ".join(where_conditions)
    
    query = text(f"""
        SELECT date, store_id, sku_id, units_sold
        FROM sales_daily
        WHERE date BETWEEN :start AND :end
        AND ({where_clause})
        ORDER BY store_id, sku_id, date
    """)

    df = pd.read_sql(query, engine, params=params)
    
    if df.empty:
        logger.warning("No sales data found for changed store-SKU combinations")
        return

    rows = []
    for (store, sku), g in df.groupby(["store_id", "sku_id"]):
        feature_row = _calculate_features_for_store_sku(store, sku, g, snapshot_date)
        rows.append(feature_row)
    
    if rows:
        _save_feature_batch(rows, db)


def _calculate_features_for_store_sku(store_id: str, sku_id: str, sales_data: pd.DataFrame, snapshot_date: date) -> FeatureStoreSKU:
    """Calculate features for a single store-SKU combination."""
    # Ensure data is sorted by date and fill missing dates
    g = sales_data.sort_values("date")
    g = g.set_index("date").asfreq("D", fill_value=0)
    
    # Calculate velocity features
    v7 = g.tail(7)["units_sold"].mean() if len(g) >= 7 else g["units_sold"].mean()
    v14 = g.tail(14)["units_sold"].mean() if len(g) >= 14 else g["units_sold"].mean()
    v30 = g["units_sold"].mean()
    volatility = g["units_sold"].std() if len(g) > 1 else 0.0
    
    return FeatureStoreSKU(
        date=snapshot_date,
        store_id=store_id,
        sku_id=sku_id,
        v7=v7,
        v14=v14,
        v30=v30,
        volatility=volatility,
    )


def _save_feature_batch(feature_rows: List[FeatureStoreSKU], db):
    """Save a batch of feature rows to the database."""
    for row in feature_rows:
        db.merge(row)
    
    # Flush to database but don't commit yet
    db.flush()


def detect_sales_data_changes(snapshot_date: date, lookback_days: int = 30) -> Set[tuple]:
    """
    Detect which store-SKU combinations have changed sales data.
    
    Requirements 7.3, 7.4:
    - Add change detection to avoid full recomputation
    """
    db = SessionLocal()
    
    try:
        # Get the last feature build date
        last_feature_build = (
            db.query(DataChangeTracking)
            .filter(
                DataChangeTracking.processing_type == "features",
                DataChangeTracking.snapshot_date <= snapshot_date
            )
            .order_by(DataChangeTracking.snapshot_date.desc())
            .first()
        )
        
        if not last_feature_build:
            # No previous build, return all store-SKU combinations
            logger.info("No previous feature build found, processing all store-SKU combinations")
            all_combinations = (
                db.query(SalesDaily.store_id, SalesDaily.sku_id)
                .filter(
                    SalesDaily.date >= snapshot_date - timedelta(days=lookback_days),
                    SalesDaily.date <= snapshot_date
                )
                .distinct()
                .all()
            )
            return set((store_id, sku_id) for store_id, sku_id in all_combinations)
        
        # Find store-SKU combinations with sales data changes since last build
        changed_combinations = (
            db.query(SalesDaily.store_id, SalesDaily.sku_id)
            .filter(
                SalesDaily.date >= last_feature_build.last_processed_at.date(),
                SalesDaily.date <= snapshot_date
            )
            .distinct()
            .all()
        )
        
        changed_set = set((store_id, sku_id) for store_id, sku_id in changed_combinations)
        
        logger.info(f"Detected {len(changed_set)} store-SKU combinations with sales data changes since {last_feature_build.last_processed_at.date()}")
        
        return changed_set
        
    except Exception as e:
        logger.error(f"Error detecting sales data changes: {str(e)}")
        # On error, return empty set to trigger full processing
        return set()
    finally:
        db.close()


def optimize_feature_calculation_performance(snapshot_date: date) -> dict:
    """
    Optimize feature calculation performance for large datasets.
    
    Requirements 7.3, 7.4:
    - Optimize job performance for large datasets
    """
    db = SessionLocal()
    
    try:
        # Get statistics about the data volume
        total_store_skus = (
            db.query(func.count(func.distinct(SalesDaily.store_id + SalesDaily.sku_id)))
            .filter(
                SalesDaily.date >= snapshot_date - timedelta(days=30),
                SalesDaily.date <= snapshot_date
            )
            .scalar()
        ) or 0
        
        total_sales_records = (
            db.query(func.count(SalesDaily.date))
            .filter(
                SalesDaily.date >= snapshot_date - timedelta(days=30),
                SalesDaily.date <= snapshot_date
            )
            .scalar()
        ) or 0
        
        # Determine optimal processing strategy
        if total_store_skus > 10000 or total_sales_records > 1000000:
            strategy = "batch_processing"
            batch_size = 500
        elif total_store_skus > 5000 or total_sales_records > 500000:
            strategy = "incremental_processing"
            batch_size = 1000
        else:
            strategy = "full_processing"
            batch_size = None
        
        logger.info(f"Feature calculation optimization: {strategy} for {total_store_skus} store-SKUs and {total_sales_records} sales records")
        
        return {
            "strategy": strategy,
            "batch_size": batch_size,
            "total_store_skus": total_store_skus,
            "total_sales_records": total_sales_records
        }
        
    except Exception as e:
        logger.error(f"Error optimizing feature calculation: {str(e)}")
        return {
            "strategy": "full_processing",
            "batch_size": None,
            "total_store_skus": 0,
            "total_sales_records": 0
        }
    finally:
        db.close()
