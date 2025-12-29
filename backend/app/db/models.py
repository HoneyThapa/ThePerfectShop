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


class StoreMaster(Base):
    __tablename__ = "store_master"
    store_id = Column(String, primary_key=True)
    city = Column(String)
    zone = Column(String)


class SKUMaster(Base):
    __tablename__ = "sku_master"
    sku_id = Column(String, primary_key=True)
    category = Column(String)
    mrp = Column(Numeric)
