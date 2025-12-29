from sqlalchemy import (
    Column, Integer, String, Date, Numeric,
    TIMESTAMP, JSON, PrimaryKeyConstraint, ForeignKey, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

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
    store_id = Column(String, ForeignKey("store_master.store_id"))
    sku_id = Column(String, ForeignKey("sku_master.sku_id"))
    units_sold = Column(Integer)
    selling_price = Column(Numeric)
    __table_args__ = (PrimaryKeyConstraint("date", "store_id", "sku_id"),)
    
    # Relationships
    store = relationship("StoreMaster", back_populates="sales")
    sku = relationship("SKUMaster", back_populates="sales")


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"
    snapshot_date = Column(Date)
    store_id = Column(String, ForeignKey("store_master.store_id"))
    sku_id = Column(String, ForeignKey("sku_master.sku_id"))
    batch_id = Column(String)
    expiry_date = Column(Date)
    on_hand_qty = Column(Integer)
    __table_args__ = (
        PrimaryKeyConstraint("snapshot_date", "store_id", "sku_id", "batch_id"),
    )
    
    # Relationships
    store = relationship("StoreMaster", back_populates="inventory_batches")
    sku = relationship("SKUMaster", back_populates="inventory_batches")


class Purchase(Base):
    __tablename__ = "purchases"
    received_date = Column(Date)
    store_id = Column(String, ForeignKey("store_master.store_id"))
    sku_id = Column(String, ForeignKey("sku_master.sku_id"))
    batch_id = Column(String)
    received_qty = Column(Integer)
    unit_cost = Column(Numeric)
    __table_args__ = (
        PrimaryKeyConstraint("received_date", "store_id", "sku_id", "batch_id"),
    )
    
    # Relationships
    store = relationship("StoreMaster", back_populates="purchases")
    sku = relationship("SKUMaster", back_populates="purchases")


class FeatureStoreSKU(Base):
    __tablename__ = "features_store_sku"
    date = Column(Date)
    store_id = Column(String, ForeignKey("store_master.store_id"))
    sku_id = Column(String, ForeignKey("sku_master.sku_id"))
    v7 = Column(Numeric)
    v14 = Column(Numeric)
    v30 = Column(Numeric)
    volatility = Column(Numeric)
    __table_args__ = (PrimaryKeyConstraint("date", "store_id", "sku_id"),)
    
    # Relationships
    store = relationship("StoreMaster", back_populates="features")
    sku = relationship("SKUMaster", back_populates="features")


class BatchRisk(Base):
    __tablename__ = "batch_risk"
    snapshot_date = Column(Date)
    store_id = Column(String, ForeignKey("store_master.store_id"))
    sku_id = Column(String, ForeignKey("sku_master.sku_id"))
    batch_id = Column(String)
    days_to_expiry = Column(Integer)
    expected_sales_to_expiry = Column(Numeric)
    at_risk_units = Column(Integer)
    at_risk_value = Column(Numeric)
    risk_score = Column(Numeric)
    __table_args__ = (
        PrimaryKeyConstraint("snapshot_date", "store_id", "sku_id", "batch_id"),
    )
    
    # Relationships
    store = relationship("StoreMaster", back_populates="batch_risks")
    sku = relationship("SKUMaster", back_populates="batch_risks")


class StoreMaster(Base):
    __tablename__ = "store_master"
    store_id = Column(String(50), primary_key=True)
    city = Column(String(100))
    zone = Column(String(50))
    
    # Relationships
    sales = relationship("SalesDaily", back_populates="store")
    inventory_batches = relationship("InventoryBatch", back_populates="store")
    purchases = relationship("Purchase", back_populates="store")
    features = relationship("FeatureStoreSKU", back_populates="store")
    batch_risks = relationship("BatchRisk", back_populates="store")
    actions_from = relationship("Action", foreign_keys="Action.from_store", back_populates="from_store_ref")
    actions_to = relationship("Action", foreign_keys="Action.to_store", back_populates="to_store_ref")


class SKUMaster(Base):
    __tablename__ = "sku_master"
    sku_id = Column(String(100), primary_key=True)
    category = Column(String(100))
    mrp = Column(Numeric(10, 2))
    
    # Relationships
    sales = relationship("SalesDaily", back_populates="sku")
    inventory_batches = relationship("InventoryBatch", back_populates="sku")
    purchases = relationship("Purchase", back_populates="sku")
    features = relationship("FeatureStoreSKU", back_populates="sku")
    batch_risks = relationship("BatchRisk", back_populates="sku")
    actions = relationship("Action", back_populates="sku")


class Action(Base):
    __tablename__ = "actions"
    action_id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    action_type = Column(String(20))  # TRANSFER, MARKDOWN, LIQUIDATE
    from_store = Column(String(50), ForeignKey("store_master.store_id"))
    to_store = Column(String(50), ForeignKey("store_master.store_id"), nullable=True)
    sku_id = Column(String(100), ForeignKey("sku_master.sku_id"))
    batch_id = Column(String(100))
    qty = Column(Integer)
    discount_pct = Column(Numeric(5, 2), nullable=True)
    expected_savings = Column(Numeric(12, 2))
    status = Column(String(20))  # PROPOSED, APPROVED, DONE, REJECTED
    
    # Relationships
    from_store_ref = relationship("StoreMaster", foreign_keys=[from_store], back_populates="actions_from")
    to_store_ref = relationship("StoreMaster", foreign_keys=[to_store], back_populates="actions_to")
    sku = relationship("SKUMaster", back_populates="actions")
    outcomes = relationship("ActionOutcome", back_populates="action")


class ActionOutcome(Base):
    __tablename__ = "action_outcomes"
    action_id = Column(Integer, ForeignKey("actions.action_id"), primary_key=True)
    measured_at = Column(TIMESTAMP, server_default=func.now())
    recovered_value = Column(Numeric(12, 2))
    cleared_units = Column(Integer)
    notes = Column(String)
    
    # Relationships
    action = relationship("Action", back_populates="outcomes")
