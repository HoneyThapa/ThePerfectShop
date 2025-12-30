#!/usr/bin/env python3
"""
Complete database setup script for ThePerfectShop AI Operations Copilot.
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

from app.db.models import Base, SalesDaily, InventoryBatch, Purchase, FeatureStoreSKU, BatchRisk
from app.db.session import DATABASE_URL, engine
from app.services.features import build_features
from app.services.scoring import compute_batch_risk

def create_all_tables():
    """Create all database tables"""
    print("🗄️ Creating all database tables...")
    
    with engine.connect() as conn:
        # Create core tables
        Base.metadata.create_all(engine)
        
        # Create AI Operations Copilot tables
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR DEFAULT 'default',
                optimize_for VARCHAR DEFAULT 'balanced',
                service_level_priority VARCHAR DEFAULT 'medium',
                multi_location_aggressiveness VARCHAR DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS recommendation_feedback (
                id SERIAL PRIMARY KEY,
                recommendation_id VARCHAR,
                user_id VARCHAR DEFAULT 'default',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action VARCHAR,
                context_hash VARCHAR,
                action_type VARCHAR,
                action_parameters JSONB,
                risk_score NUMERIC
            );
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS news_events (
                id SERIAL PRIMARY KEY,
                event_date DATE,
                event_type VARCHAR,
                description VARCHAR,
                impact_stores JSONB,
                impact_skus JSONB,
                score_modifier NUMERIC DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Ensure risk_score column exists
        try:
            conn.execute(text("""
                ALTER TABLE batch_risk 
                ADD COLUMN IF NOT EXISTS risk_score NUMERIC;
            """))
        except Exception as e:
            print(f"Note: risk_score column handling: {e}")
        
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

def create_sample_user_preferences():
    """Create sample user preferences"""
    print("⚙️ Creating sample user preferences...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        from app.db.models import UserPreferences
        
        # Create default user preferences
        prefs = UserPreferences(
            user_id="default",
            optimize_for="balanced",
            service_level_priority="medium",
            multi_location_aggressiveness="medium"
        )
        db.merge(prefs)
        
        db.commit()
        print("✅ Created default user preferences")
        
    finally:
        db.close()

def create_sample_news_events():
    """Create sample news events"""
    print("📰 Creating sample news events...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        from app.db.models import NewsEvents
        
        # Create some sample news events
        events = [
            {
                "event_date": date.today() - timedelta(days=2),
                "event_type": "demand_spike",
                "description": "Holiday season demand increase for dairy products",
                "impact_stores": ["S001", "S002"],
                "impact_skus": ["SKU101", "SKU102"],
                "score_modifier": -0.1  # Reduce risk due to higher demand
            },
            {
                "event_date": date.today() - timedelta(days=5),
                "event_type": "supplier_delay",
                "description": "Bakery supplier delivery delayed by 2 days",
                "impact_stores": ["S001"],
                "impact_skus": ["SKU103"],
                "score_modifier": 0.15  # Increase risk due to supply issues
            },
            {
                "event_date": date.today() - timedelta(days=1),
                "event_type": "weather",
                "description": "Hot weather increasing beverage demand",
                "impact_stores": ["S003"],
                "impact_skus": ["SKU106", "SKU107"],
                "score_modifier": -0.05  # Slightly reduce risk
            }
        ]
        
        for event_data in events:
            event = NewsEvents(**event_data)
            db.add(event)
        
        db.commit()
        print(f"✅ Created {len(events)} sample news events")
        
    finally:
        db.close()

def build_features_and_risk():
    """Build features and compute risk scores"""
    print("🧮 Building features and computing risk scores...")
    
    snapshot_date = date.today()
    
    # Build features
    print("  - Building sales velocity features...")
    build_features(snapshot_date)
    
    # Compute risk scores
    print("  - Computing batch risk scores...")
    compute_batch_risk(snapshot_date)
    
    print("✅ Features and risk scores computed!")

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
    print("🚀 Setting up ThePerfectShop AI Operations Copilot Database")
    print("=" * 60)
    
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
            print("1. Start the backend: uvicorn app.main:app --reload --port 8000")
            print("2. Start the frontend: streamlit run ../frontend/streamlit_app.py")
            print("3. Test AI features: python test_ai_endpoints.py")
        else:
            print("\n❌ Database setup failed. Please check the errors above.")
            
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()