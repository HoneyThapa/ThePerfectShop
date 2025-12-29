import pandas as pd
from app.db.session import SessionLocal
from app.db.models import SalesDaily, InventoryBatch, Purchase
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

COLUMN_ALIASES = {
    "sku_id": ["sku", "sku code", "item_id", "item id", "product_id"],
    "store_id": ["store", "store_id", "location", "store code", "shop_id"],
    "date": ["date", "txn_date", "transaction_date", "sale_date"],
    "snapshot_date": ["snapshot", "as_of_date", "snapshot_date", "as of date"],
    "expiry_date": ["expiry", "exp_dt", "best before", "expiry_date", "expiration_date"],
    "on_hand_qty": ["qty", "on hand", "stock", "quantity", "on_hand_qty", "inventory"],
    "units_sold": ["units_sold", "sold", "quantity_sold", "units sold"],
    "batch_id": ["batch_id", "batch", "lot", "lot_id", "batch code"],
    "received_date": ["received_date", "received", "receipt_date", "delivery_date"],
    "received_qty": ["received_qty", "received", "quantity_received", "delivered_qty"],
    "unit_cost": ["unit_cost", "cost", "price", "unit_price", "cost_per_unit"],
    "selling_price": ["selling_price", "price", "sale_price", "retail_price"]
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names with intelligent mapping"""
    # Clean column names: lowercase, strip whitespace, replace common separators
    df.columns = [c.lower().strip().replace(' ', '_').replace('-', '_') for c in df.columns]
    
    rename_map = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for col in df.columns:
            # Direct match or fuzzy match
            if col in aliases or col.replace('_', ' ') in aliases:
                rename_map[col] = canonical
                break
    
    logger.info(f"Column mapping applied: {rename_map}")
    return df.rename(columns=rename_map)


def safe_date_parse(date_value):
    """Safely parse date values with multiple format support"""
    if pd.isna(date_value):
        return None
    
    if isinstance(date_value, (datetime, pd.Timestamp)):
        return date_value.date()
    
    # Try multiple date formats
    date_formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%Y%m%d',
        '%m-%d-%Y',
        '%d-%m-%Y',
        '%Y/%m/%d'
    ]
    
    date_str = str(date_value).strip()
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # If all formats fail, try pandas parsing
    try:
        return pd.to_datetime(date_str, errors='coerce').date()
    except Exception:
        logger.warning(f"Could not parse date: {date_value}")
        return None


def safe_numeric_convert(value, target_type=int):
    """Safely convert numeric values"""
    if pd.isna(value):
        return None
    
    try:
        if target_type == int:
            return int(float(value))
        else:
            return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert to {target_type.__name__}: {value}")
        return None


def load_sales(df: pd.DataFrame):
    """Load sales data with robust error handling"""
    db = SessionLocal()
    try:
        success_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                sales_record = SalesDaily(
                    date=safe_date_parse(row["date"]),
                    store_id=str(row["store_id"]).strip(),
                    sku_id=str(row["sku_id"]).strip(),
                    units_sold=safe_numeric_convert(row["units_sold"], int),
                    selling_price=safe_numeric_convert(row.get("selling_price"), float) if "selling_price" in row else None,
                )
                
                # Skip rows with critical missing data
                if not all([sales_record.date, sales_record.store_id, sales_record.sku_id, sales_record.units_sold]):
                    logger.warning(f"Skipping row {idx + 2} due to missing critical data")
                    error_count += 1
                    continue
                
                db.merge(sales_record)
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error processing sales row {idx + 2}: {str(e)}")
                error_count += 1
                continue
        
        db.commit()
        logger.info(f"Sales data loaded: {success_count} successful, {error_count} errors")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to load sales data: {str(e)}")
        raise
    finally:
        db.close()


def load_inventory(df: pd.DataFrame):
    """Load inventory data with robust error handling"""
    db = SessionLocal()
    try:
        success_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                inventory_record = InventoryBatch(
                    snapshot_date=safe_date_parse(row["snapshot_date"]),
                    store_id=str(row["store_id"]).strip(),
                    sku_id=str(row["sku_id"]).strip(),
                    batch_id=str(row["batch_id"]).strip(),
                    expiry_date=safe_date_parse(row["expiry_date"]),
                    on_hand_qty=safe_numeric_convert(row["on_hand_qty"], int),
                )
                
                # Skip rows with critical missing data
                if not all([inventory_record.snapshot_date, inventory_record.store_id, 
                           inventory_record.sku_id, inventory_record.batch_id, 
                           inventory_record.expiry_date, inventory_record.on_hand_qty is not None]):
                    logger.warning(f"Skipping row {idx + 2} due to missing critical data")
                    error_count += 1
                    continue
                
                db.merge(inventory_record)
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error processing inventory row {idx + 2}: {str(e)}")
                error_count += 1
                continue
        
        db.commit()
        logger.info(f"Inventory data loaded: {success_count} successful, {error_count} errors")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to load inventory data: {str(e)}")
        raise
    finally:
        db.close()


def load_purchases(df: pd.DataFrame):
    """Load purchase data with robust error handling"""
    db = SessionLocal()
    try:
        success_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                purchase_record = Purchase(
                    received_date=safe_date_parse(row["received_date"]),
                    store_id=str(row["store_id"]).strip(),
                    sku_id=str(row["sku_id"]).strip(),
                    batch_id=str(row["batch_id"]).strip(),
                    received_qty=safe_numeric_convert(row["received_qty"], int),
                    unit_cost=safe_numeric_convert(row["unit_cost"], float),
                )
                
                # Skip rows with critical missing data
                if not all([purchase_record.received_date, purchase_record.store_id,
                           purchase_record.sku_id, purchase_record.batch_id,
                           purchase_record.received_qty is not None, purchase_record.unit_cost is not None]):
                    logger.warning(f"Skipping row {idx + 2} due to missing critical data")
                    error_count += 1
                    continue
                
                db.add(purchase_record)
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error processing purchase row {idx + 2}: {str(e)}")
                error_count += 1
                continue
        
        db.commit()
        logger.info(f"Purchase data loaded: {success_count} successful, {error_count} errors")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to load purchase data: {str(e)}")
        raise
    finally:
        db.close()
