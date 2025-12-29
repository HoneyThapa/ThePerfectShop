from datetime import date
from collections import defaultdict
from app.db.session import SessionLocal
from app.db.models import (
    InventoryBatch,
    FeatureStoreSKU,
    Purchase,
    BatchRisk,
)


def compute_batch_risk(snapshot_date: date):
    db = SessionLocal()

    features = {
        (f.store_id, f.sku_id): float(f.v14 or 0)
        for f in db.query(FeatureStoreSKU).filter_by(date=snapshot_date)
    }

    costs = defaultdict(lambda: 10.0)
    for p in db.query(Purchase):
        costs[(p.store_id, p.sku_id)] = float(p.unit_cost)

    for inv in db.query(InventoryBatch).filter_by(snapshot_date=snapshot_date):
        v14 = features.get((inv.store_id, inv.sku_id), 0)
        days = (inv.expiry_date - snapshot_date).days
        expected = max(0, v14 * days)
        at_risk = max(0, inv.on_hand_qty - expected)

        risk_score = (
            0.7 * (at_risk / inv.on_hand_qty if inv.on_hand_qty else 0)
            + 0.3 * (1 / (days + 1))
        ) * 100

        db.merge(
            BatchRisk(
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
        )

    db.commit()
