import pandas as pd
from sqlalchemy import text
from datetime import timedelta
import logging
from app.db.session import engine, SessionLocal
from app.db.models import FeatureStoreSKU

logger = logging.getLogger(__name__)


def build_features(snapshot_date):
    """Build velocity and volatility features for all store-SKU combinations"""
    
    logger.info(f"Building features for snapshot date: {snapshot_date}")
    
    try:
        # Query sales data for the last 30 days
        query = text("""
            SELECT date, store_id, sku_id, units_sold
            FROM sales_daily
            WHERE date BETWEEN :start AND :end
            ORDER BY date
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
            logger.warning("No sales data found for the specified date range")
            return {"status": "no_data", "features_created": 0}

        logger.info(f"Processing {len(df)} sales records")
        
        rows = []
        processed_count = 0
        error_count = 0

        # Group by store-SKU combination
        for (store, sku), group_df in df.groupby(["store_id", "sku_id"]):
            try:
                # Sort by date and create daily time series
                group_df = group_df.sort_values("date")
                group_df = group_df.set_index("date").asfreq("D", fill_value=0)
                
                # Calculate velocity metrics
                v7 = group_df.tail(7)["units_sold"].mean() if len(group_df) >= 7 else group_df["units_sold"].mean()
                v14 = group_df.tail(14)["units_sold"].mean() if len(group_df) >= 14 else group_df["units_sold"].mean()
                v30 = group_df["units_sold"].mean()
                volatility = group_df["units_sold"].std() if len(group_df) > 1 else 0.0

                # Create feature record
                feature_record = FeatureStoreSKU(
                    date=snapshot_date,
                    store_id=store,
                    sku_id=sku,
                    v7=float(v7) if pd.notna(v7) else 0.0,
                    v14=float(v14) if pd.notna(v14) else 0.0,
                    v30=float(v30) if pd.notna(v30) else 0.0,
                    volatility=float(volatility) if pd.notna(volatility) else 0.0,
                )
                
                rows.append(feature_record)
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing features for {store}-{sku}: {str(e)}")
                error_count += 1
                continue

        # Save to database
        db = SessionLocal()
        try:
            for record in rows:
                db.merge(record)
            db.commit()
            
            logger.info(f"Features built successfully: {processed_count} store-SKU combinations, {error_count} errors")
            
            return {
                "status": "success",
                "features_created": processed_count,
                "errors": error_count,
                "snapshot_date": snapshot_date.isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Database error while saving features: {str(e)}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to build features: {str(e)}")
        raise


def get_store_sku_velocity(store_id: str, sku_id: str, snapshot_date=None):
    """Get velocity metrics for a specific store-SKU combination"""
    
    db = SessionLocal()
    try:
        query = db.query(FeatureStoreSKU).filter(
            FeatureStoreSKU.store_id == store_id,
            FeatureStoreSKU.sku_id == sku_id
        )
        
        if snapshot_date:
            query = query.filter(FeatureStoreSKU.date == snapshot_date)
        else:
            # Get the most recent features
            query = query.order_by(FeatureStoreSKU.date.desc())
        
        feature = query.first()
        
        if not feature:
            return None
            
        return {
            "store_id": feature.store_id,
            "sku_id": feature.sku_id,
            "date": feature.date.isoformat(),
            "v7": float(feature.v7),
            "v14": float(feature.v14),
            "v30": float(feature.v30),
            "volatility": float(feature.volatility)
        }
        
    finally:
        db.close()


def get_all_features(snapshot_date=None, store_id=None, sku_id=None):
    """Get features with optional filtering"""
    
    db = SessionLocal()
    try:
        query = db.query(FeatureStoreSKU)
        
        if snapshot_date:
            query = query.filter(FeatureStoreSKU.date == snapshot_date)
        
        if store_id:
            query = query.filter(FeatureStoreSKU.store_id == store_id)
            
        if sku_id:
            query = query.filter(FeatureStoreSKU.sku_id == sku_id)
        
        # Order by velocity (highest first)
        query = query.order_by(FeatureStoreSKU.v14.desc())
        
        features = query.all()
        
        return [
            {
                "store_id": f.store_id,
                "sku_id": f.sku_id,
                "date": f.date.isoformat(),
                "v7": float(f.v7),
                "v14": float(f.v14),
                "v30": float(f.v30),
                "volatility": float(f.volatility)
            }
            for f in features
        ]
        
    finally:
        db.close()
