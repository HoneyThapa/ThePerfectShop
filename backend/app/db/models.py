from sqlalchemy import (
    Column, Integer, String, Date, Numeric,
    TIMESTAMP, JSON, PrimaryKeyConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class RawUpload(Base):
    __tablename__ = "raw_uploads"
    id = Column(Integer, primary_key=True)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())
    file_name = Column(String)
    file_type = Column(String)
    status = Column(String)
    error_report = Column(JSON)


class SalesDaily(Base):
    __tablename__ = "sales_daily"
    date = Column(Date)
    store_id = Column(String)
    sku_id = Column(String)
    units_sold = Column(Integer)
    selling_price = Column(Numeric)
    __table_args__ = (PrimaryKeyConstraint("date", "store_id", "sku_id"),)


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"
    snapshot_date = Column(Date)
    store_id = Column(String)
    sku_id = Column(String)
    batch_id = Column(String)
    expiry_date = Column(Date)
    on_hand_qty = Column(Integer)
    __table_args__ = (
        PrimaryKeyConstraint("snapshot_date", "store_id", "sku_id", "batch_id"),
    )


class Purchase(Base):
    __tablename__ = "purchases"
    received_date = Column(Date)
    store_id = Column(String)
    sku_id = Column(String)
    batch_id = Column(String)
    received_qty = Column(Integer)
    unit_cost = Column(Numeric)


class FeatureStoreSKU(Base):
    __tablename__ = "features_store_sku"
    date = Column(Date)
    store_id = Column(String)
    sku_id = Column(String)
    v7 = Column(Numeric)
    v14 = Column(Numeric)
    v30 = Column(Numeric)
    volatility = Column(Numeric)
    __table_args__ = (PrimaryKeyConstraint("date", "store_id", "sku_id"),)


class BatchRisk(Base):
    __tablename__ = "batch_risk"
    snapshot_date = Column(Date)
    store_id = Column(String)
    sku_id = Column(String)
    batch_id = Column(String)
    days_to_expiry = Column(Integer)
    expected_sales_to_expiry = Column(Numeric)
    at_risk_units = Column(Integer)
    at_risk_value = Column(Numeric)
    risk_score = Column(Numeric)
    __table_args__ = (
        PrimaryKeyConstraint("snapshot_date", "store_id", "sku_id", "batch_id"),
    )


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, default="default")  # For MVP, single user
    optimize_for = Column(String, default="balanced")  # stability, profit, waste_min
    service_level_priority = Column(String, default="medium")  # low, medium, high
    multi_location_aggressiveness = Column(String, default="medium")  # low, medium, high
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"
    id = Column(Integer, primary_key=True)
    recommendation_id = Column(String)
    user_id = Column(String, default="default")
    timestamp = Column(TIMESTAMP, server_default=func.now())
    action = Column(String)  # accepted, rejected, dismissed
    context_hash = Column(String)  # store_id:sku_id:batch_id
    action_type = Column(String)  # markdown, transfer, reorder_pause, etc.
    action_parameters = Column(JSON)
    risk_score = Column(Numeric)


class NewsEvents(Base):
    __tablename__ = "news_events"
    id = Column(Integer, primary_key=True)
    event_date = Column(Date)
    event_type = Column(String)  # demand_spike, supplier_delay, seasonal, etc.
    description = Column(String)
    impact_stores = Column(JSON)  # List of affected store_ids
    impact_skus = Column(JSON)  # List of affected sku_ids
    score_modifier = Column(Numeric, default=0.0)  # -0.2 to +0.2 adjustment
    created_at = Column(TIMESTAMP, server_default=func.now())
    risk_score = Column(Numeric)
    __table_args__ = (
        PrimaryKeyConstraint("snapshot_date", "store_id", "sku_id", "batch_id"),
    )
