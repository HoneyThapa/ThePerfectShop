#!/usr/bin/env python3
"""
Complete database setup script for ThePerfectShop AI Operations Copilot using SQLite.
This script creates all tables and populates them with sample data for testing.
"""

import os
import sys
import pandas as pd
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Use SQLite for easy testing
DATABASE_URL = "sqlite:///./theperfectshop.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

from app.db.models import Base, SalesDaily, InventoryBatch, Purchase, FeatureStoreSKU, BatchRisk

def create_all_tables():
    """Create all database tables"""
    print("🗄️ Creating all database tables...")
    
    # Create core tables
    Base.metadata.create_all(engine)
    
    with engine.connect() as conn:
        # Create AI Operations Copilot tables
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                optimize_for TEXT DEFAULT 'balanced',
                service_level_priority TEXT DEFAULT 'medium',
                multi_location_aggressiveness TEXT DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS recommendation_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_id TEXT,
                user_id TEXT DEFAULT 'default',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action TEXT,
                context_hash TEXT,
                action_type TEXT,
                action_parameters TEXT,
                risk_score REAL
            );
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS news_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_date DATE,
                event_type TEXT,
                description TEXT,
                impact_stores TEXT,
                impact_skus TEXT,
                score_modifier REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        conn.commit()
    
    print("✅ All tables created successfully!")

def load_sample_inventory_data():
    """Load sample inventory data from CSV"""
    print("📦 Loading sample inventory data...")
    
    # Read the sample CSV
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'sample_inventory.csv')
    df = pd.read_csv(csv_path)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Convert to inventory batches
        snapshot_date = date.today()
        
        for _, row in df.iterrows():
            # Create inventory batch
            inventory = InventoryBatch(
                snapshot_date=snapshot_date,
                store_id=row['store_id'],
                sku_id=row['sku_id'],
                batch_id=row['batch_id'],
                expiry_date=pd.to_datetime(row['expiry_date']).date(),
                on_hand_qty=int(row['on_hand_qty'])
            )
            db.merge(inventory)
            
            # Create purchase record
            purchase = Purchase(
                received_date=snapshot_date - timedelta(days=30),  # 30 days ago
                store_id=row['store_id'],
                sku_id=row['sku_id'],
                batch_id=row['batch_id'],
                received_qty=int(row['on_hand_qty']) + 50,  # Assume some was sold
                unit_cost=float(row['unit_cost'])
            )
            db.add(purchase)
        
        db.commit()
        print(f"✅ Loaded {len(df)} inventory batches")
        
    finally:
        db.close()

def generate_sample_sales_data():
    """Generate sample sales data for the last 30 days"""
    print("📊 Generating sample sales data...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get all inventory items
        inventory_items = db.query(InventoryBatch).all()
        
        # Generate sales for last 30 days
        for days_back in range(30):
            sales_date = date.today() - timedelta(days=days_back)
            
            for item in inventory_items:
                # Simulate daily sales based on some logic
                base_sales = max(1, int(item.on_hand_qty / 20))  # Rough daily sales
                
                # Add some randomness (simulate with deterministic pattern)
                day_factor = (days_back % 7) / 7  # Weekly pattern
                sales = max(0, int(base_sales * (1 + day_factor)))
                
                if sales > 0:
                    sale = SalesDaily(
                        date=sales_date,
                        store_id=item.store_id,
                        sku_id=item.sku_id,
                        units_sold=sales,
                        selling_price=50.0  # Default selling price
                    )
                    db.merge(sale)
        
        db.commit()
        print("✅ Generated 30 days of sample sales data")
        
    finally:
        db.close()

def build_features_and_risk():
    """Build features and compute risk scores"""
    print("🧮 Building features and computing risk scores...")
    
    snapshot_date = date.today()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Build features manually (simplified version)
        print("  - Building sales velocity features...")
        
        # Get sales data for last 30 days
        sales_data = db.query(SalesDaily).filter(
            SalesDaily.date >= snapshot_date - timedelta(days=30)
        ).all()
        
        # Group by store and SKU
        sales_by_store_sku = {}
        for sale in sales_data:
            key = (sale.store_id, sale.sku_id)
            if key not in sales_by_store_sku:
                sales_by_store_sku[key] = []
            sales_by_store_sku[key].append(sale.units_sold)
        
        # Calculate features
        for (store_id, sku_id), sales_list in sales_by_store_sku.items():
            v7 = sum(sales_list[-7:]) / 7 if len(sales_list) >= 7 else sum(sales_list) / len(sales_list)
            v14 = sum(sales_list[-14:]) / 14 if len(sales_list) >= 14 else sum(sales_list) / len(sales_list)
            v30 = sum(sales_list) / len(sales_list)
            volatility = pd.Series(sales_list).std() if len(sales_list) > 1 else 0
            
            feature = FeatureStoreSKU(
                date=snapshot_date,
                store_id=store_id,
                sku_id=sku_id,
                v7=v7,
                v14=v14,
                v30=v30,
                volatility=volatility
            )
            db.merge(feature)
        
        db.commit()
        
        # Compute risk scores
        print("  - Computing batch risk scores...")
        
        # Get features
        features = {
            (f.store_id, f.sku_id): float(f.v14 or 0)
            for f in db.query(FeatureStoreSKU).filter_by(date=snapshot_date)
        }
        
        # Get costs
        costs = {}
        for p in db.query(Purchase):
            costs[(p.store_id, p.sku_id)] = float(p.unit_cost)
        
        # Calculate risk for each inventory batch
        for inv in db.query(InventoryBatch).filter_by(snapshot_date=snapshot_date):
            v14 = features.get((inv.store_id, inv.sku_id), 0)
            days = (inv.expiry_date - snapshot_date).days
            expected = max(0, v14 * days)
            at_risk = max(0, inv.on_hand_qty - expected)
            
            risk_score = (
                0.7 * (at_risk / inv.on_hand_qty if inv.on_hand_qty else 0)
                + 0.3 * (1 / (days + 1))
            ) * 100
            
            cost = costs.get((inv.store_id, inv.sku_id), 10.0)
            
            db.merge(
                BatchRisk(
                    snapshot_date=snapshot_date,
                    store_id=inv.store_id,
                    sku_id=inv.sku_id,
                    batch_id=inv.batch_id,
                    days_to_expiry=days,
                    expected_sales_to_expiry=expected,
                    at_risk_units=int(at_risk),
                    at_risk_value=at_risk * cost,
                    risk_score=min(100, round(risk_score, 1)),
                )
            )
        
        db.commit()
        print("✅ Features and risk scores computed!")
        
    finally:
        db.close()

def create_sample_user_preferences():
    """Create sample user preferences"""
    print("⚙️ Creating sample user preferences...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT OR REPLACE INTO user_preferences 
                (user_id, optimize_for, service_level_priority, multi_location_aggressiveness)
                VALUES ('default', 'balanced', 'medium', 'medium')
            """))
            conn.commit()
        
        print("✅ Created default user preferences")
        
    finally:
        db.close()

def create_sample_news_events():
    """Create sample news events"""
    print("📰 Creating sample news events...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        with engine.connect() as conn:
            # Create some sample news events
            events = [
                {
                    "event_date": (date.today() - timedelta(days=2)).isoformat(),
                    "event_type": "demand_spike",
                    "description": "Holiday season demand increase for dairy products",
                    "impact_stores": '["S001", "S002"]',
                    "impact_skus": '["SKU101", "SKU102"]',
                    "score_modifier": -0.1
                },
                {
                    "event_date": (date.today() - timedelta(days=5)).isoformat(),
                    "event_type": "supplier_delay",
                    "description": "Bakery supplier delivery delayed by 2 days",
                    "impact_stores": '["S001"]',
                    "impact_skus": '["SKU103"]',
                    "score_modifier": 0.15
                },
                {
                    "event_date": (date.today() - timedelta(days=1)).isoformat(),
                    "event_type": "weather",
                    "description": "Hot weather increasing beverage demand",
                    "impact_stores": '["S003"]',
                    "impact_skus": '["SKU106", "SKU107"]',
                    "score_modifier": -0.05
                }
            ]
            
            for event in events:
                conn.execute(text("""
                    INSERT INTO news_events 
                    (event_date, event_type, description, impact_stores, impact_skus, score_modifier)
                    VALUES (:event_date, :event_type, :description, :impact_stores, :impact_skus, :score_modifier)
                """), event)
            
            conn.commit()
        
        print(f"✅ Created {len(events)} sample news events")
        
    finally:
        db.close()

def verify_setup():
    """Verify the database setup"""
    print("🔍 Verifying database setup...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check data counts
        inventory_count = db.query(InventoryBatch).count()
        sales_count = db.query(SalesDaily).count()
        features_count = db.query(FeatureStoreSKU).count()
        risk_count = db.query(BatchRisk).count()
        
        print(f"  📦 Inventory batches: {inventory_count}")
        print(f"  📊 Sales records: {sales_count}")
        print(f"  🧮 Feature records: {features_count}")
        print(f"  ⚠️ Risk records: {risk_count}")
        
        if all([inventory_count > 0, sales_count > 0, features_count > 0, risk_count > 0]):
            print("✅ Database setup verification passed!")
            return True
        else:
            print("❌ Database setup verification failed!")
            return False
            
    finally:
        db.close()

def main():
    """Main setup function"""
    print("🚀 Setting up ThePerfectShop AI Operations Copilot Database (SQLite)")
    print("=" * 70)
    
    try:
        # Step 1: Create all tables
        create_all_tables()
        
        # Step 2: Load sample data
        load_sample_inventory_data()
        generate_sample_sales_data()
        create_sample_user_preferences()
        create_sample_news_events()
        
        # Step 3: Build features and compute risks
        build_features_and_risk()
        
        # Step 4: Verify setup
        if verify_setup():
            print("\n🎉 Database setup completed successfully!")
            print("\nNext steps:")
            print("1. Start the backend: python -m uvicorn app.main:app --reload --port 8000")
            print("2. Start the frontend: streamlit run ../frontend/streamlit_app.py")
            print("3. Test AI features: python test_ai_endpoints.py")
            print(f"\nDatabase file created: {os.path.abspath('theperfectshop.db')}")
        else:
            print("\n❌ Database setup failed. Please check the errors above.")
            
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()