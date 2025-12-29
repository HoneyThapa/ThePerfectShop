import pandas as pd
from app.db.session import SessionLocal
from app.db.models import SalesDaily, InventoryBatch, Purchase

COLUMN_ALIASES = {
    "sku_id": ["sku", "sku code", "item_id"],
    "store_id": ["store", "store_id", "location"],
    "date": ["date", "txn_date"],
    "snapshot_date": ["snapshot", "as_of_date"],
    "expiry_date": ["expiry", "exp_dt", "best before"],
    "on_hand_qty": ["qty", "on hand", "stock"],
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.lower().strip() for c in df.columns]
    rename_map = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for col in df.columns:
            if col in aliases:
                rename_map[col] = canonical
    return df.rename(columns=rename_map)


def load_sales(df: pd.DataFrame):
    db = SessionLocal()
    for _, r in df.iterrows():
        db.merge(
            SalesDaily(
                date=r["date"],
                store_id=r["store_id"],
                sku_id=r["sku_id"],
                units_sold=int(r["units_sold"]),
                selling_price=r.get("selling_price"),
            )
        )
    db.commit()


def load_inventory(df: pd.DataFrame):
    db = SessionLocal()
    for _, r in df.iterrows():
        db.merge(
            InventoryBatch(
                snapshot_date=r["snapshot_date"],
                store_id=r["store_id"],
                sku_id=r["sku_id"],
                batch_id=r["batch_id"],
                expiry_date=r["expiry_date"],
                on_hand_qty=int(r["on_hand_qty"]),
            )
        )
    db.commit()


def load_purchases(df: pd.DataFrame):
    db = SessionLocal()
    for _, r in df.iterrows():
        db.add(
            Purchase(
                received_date=r["received_date"],
                store_id=r["store_id"],
                sku_id=r["sku_id"],
                batch_id=r["batch_id"],
                received_qty=int(r["received_qty"]),
                unit_cost=float(r["unit_cost"]),
            )
        )
    db.commit()
