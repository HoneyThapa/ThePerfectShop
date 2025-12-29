from fastapi import APIRouter
from datetime import date
from app.db.session import SessionLocal
from app.db.models import BatchRisk

router = APIRouter()


@router.get("/risk")
def get_risk(snapshot_date: date):
    db = SessionLocal()
    rows = (
        db.query(BatchRisk)
        .filter(BatchRisk.snapshot_date == snapshot_date)
        .order_by(BatchRisk.risk_score.desc())
        .all()
    )

    return [
        {
            "store_id": r.store_id,
            "sku_id": r.sku_id,
            "batch_id": r.batch_id,
            "days_to_expiry": r.days_to_expiry,
            "at_risk_units": r.at_risk_units,
            "at_risk_value": float(r.at_risk_value),
            "risk_score": float(r.risk_score),
        }
        for r in rows
    ]
