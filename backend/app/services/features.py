import pandas as pd
from sqlalchemy import text
from datetime import timedelta
from app.db.session import engine, SessionLocal
from app.db.models import FeatureStoreSKU


def build_features(snapshot_date):
    query = text("""
        SELECT date, store_id, sku_id, units_sold
        FROM sales_daily
        WHERE date BETWEEN :start AND :end
    """)

    df = pd.read_sql(
        query,
        engine,
        params={
            "start": snapshot_date - timedelta(days=29),
            "end": snapshot_date,
        },
    )

    rows = []

    for (store, sku), g in df.groupby(["store_id", "sku_id"]):
        g = g.sort_values("date")
        g = g.set_index("date").asfreq("D", fill_value=0)

        rows.append(
            FeatureStoreSKU(
                date=snapshot_date,
                store_id=store,
                sku_id=sku,
                v7=g.tail(7)["units_sold"].mean(),
                v14=g.tail(14)["units_sold"].mean(),
                v30=g["units_sold"].mean(),
                volatility=g["units_sold"].std(),
            )
        )

    db = SessionLocal()
    for r in rows:
        db.merge(r)
    db.commit()
