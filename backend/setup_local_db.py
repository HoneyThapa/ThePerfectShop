#!/usr/bin/env python3
"""
Setup local PostgreSQL database with realistic dummy data for ThePerfectShop
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pandas as pd
from datetime import datetime, date, timedelta
import random
import numpy as np
from app.db.models import Base
from app.db.session import engine, SessionLocal

def create_database():
    """Create the database if it doesn't exist"""
    print("🔧 Setting up PostgreSQL database...")
    
    try:
        # Connect to PostgreSQL server (not to specific database)
        conn = psycopg2.connect(
            host="localhost",
            user="postgres", 
            password="postgres",
            port=5432
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'ThePerfectShop'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute('CREATE DATABASE "ThePerfectShop"')
            print("✅ Database 'ThePerfectShop' created")
        else:
            print("✅ Database 'ThePerfectShop' already exists")
            
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        print("💡 Make sure PostgreSQL is installed and running:")
        print("   - macOS: brew install postgresql && brew services start postgresql")
        print("   - Ubuntu: sudo apt install postgresql && sudo systemctl start postgresql")
        print("   - Windows: Download from https://www.postgresql.org/download/")
        return False
    
    return True

def create_tables():
    """Create all database tables"""
    print("📋 Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def generate_dummy_data():
    """Generate realistic dummy data for a small grocery shop"""
    print("🏪 Generating dummy data for 'FreshMart' grocery store...")
    
    db = SessionLocal()
    
    try:
        # Store Master Data (3 stores)
        stores_data = [
            {"store_id": "FM001", "city": "Downtown", "zone": "Central"},
            {"store_id": "FM002", "city": "Suburbs", "zone": "North"},
            {"store_id": "FM003", "city": "Mall", "zone": "South"}
        ]
        
        # SKU Master Data (realistic grocery items)
        skus_data = [
            {"sku_id": "MILK001", "category": "dairy", "mrp": 4.99},
            {"sku_id": "BREAD001", "category": "bakery", "mrp": 2.49},
            {"sku_id": "EGGS001", "category": "dairy", "mrp": 3.99},
            {"sku_id": "APPLE001", "category": "produce", "mrp": 1.99},
            {"sku_id": "BANANA001", "category": "produce", "mrp": 0.99},
            {"sku_id": "YOGURT001", "category": "dairy", "mrp": 5.49},
            {"sku_id": "CHEESE001", "category": "dairy", "mrp": 6.99},
            {"sku_id": "LETTUCE001", "category": "produce", "mrp": 2.99},
            {"sku_id": "TOMATO001", "category": "produce", "mrp": 3.49},
            {"sku_id": "CHICKEN001", "category": "meat", "mrp": 8.99},
            {"sku_id": "BEEF001", "category": "meat", "mrp": 12.99},
            {"sku_id": "SALMON001", "category": "seafood", "mrp": 15.99},
            {"sku_id": "PASTA001", "category": "pantry", "mrp": 1.99},
            {"sku_id": "RICE001", "category": "pantry", "mrp": 3.99},
            {"sku_id": "CEREAL001", "category": "breakfast", "mrp": 4.99}
        ]
        
        # Insert store master data
        from app.db.models import StoreMaster, SKUMaster, SalesDaily, InventoryBatch, Purchase
        
        print("   📍 Adding stores...")
        for store_data in stores_data:
            store = StoreMaster(**store_data)
            db.merge(store)
        
        print("   🛒 Adding products...")
        for sku_data in skus_data:
            sku = SKUMaster(**sku_data)
            db.merge(sku)
        
        db.commit()
        
        # Generate historical sales data (last 60 days)
        print("   📊 Generating sales history...")
        sales_data = []
        
        for days_ago in range(60, 0, -1):
            sale_date = date.today() - timedelta(days=days_ago)
            
            for store in stores_data:
                store_id = store["store_id"]
                
                # Different stores have different performance
                store_multiplier = {"FM001": 1.2, "FM002": 0.8, "FM003": 1.0}[store_id]
                
                for sku in skus_data:
                    sku_id = sku["sku_id"]
                    category = sku["category"]
                    mrp = sku["mrp"]
                    
                    # Category-based sales patterns
                    base_sales = {
                        "dairy": random.randint(5, 25),
                        "produce": random.randint(8, 30),
                        "meat": random.randint(2, 15),
                        "seafood": random.randint(1, 8),
                        "bakery": random.randint(10, 40),
                        "pantry": random.randint(3, 12),
                        "breakfast": random.randint(2, 10)
                    }.get(category, 5)
                    
                    # Add some randomness and weekend boost
                    weekend_boost = 1.3 if sale_date.weekday() >= 5 else 1.0
                    daily_variation = random.uniform(0.7, 1.4)
                    
                    units_sold = max(0, int(base_sales * store_multiplier * weekend_boost * daily_variation))
                    
                    if units_sold > 0:
                        # Selling price with some variation
                        selling_price = mrp * random.uniform(0.95, 1.0)  # Small discounts
                        
                        sales_data.append({
                            "date": sale_date,
                            "store_id": store_id,
                            "sku_id": sku_id,
                            "units_sold": units_sold,
                            "selling_price": round(selling_price, 2)
                        })
        
        # Batch insert sales data
        for sale in sales_data:
            sales_record = SalesDaily(**sale)
            db.merge(sales_record)
        
        print(f"   ✅ Generated {len(sales_data)} sales records")
        
        # Generate current inventory with expiry dates
        print("   📦 Generating current inventory...")
        inventory_data = []
        
        snapshot_date = date.today()
        
        for store in stores_data:
            store_id = store["store_id"]
            
            for sku in skus_data:
                sku_id = sku["sku_id"]
                category = sku["category"]
                
                # Different categories have different shelf lives
                shelf_life_days = {
                    "dairy": random.randint(7, 21),
                    "produce": random.randint(3, 14),
                    "meat": random.randint(3, 10),
                    "seafood": random.randint(1, 5),
                    "bakery": random.randint(2, 7),
                    "pantry": random.randint(180, 730),
                    "breakfast": random.randint(90, 365)
                }.get(category, 30)
                
                # Generate 1-3 batches per SKU per store
                num_batches = random.randint(1, 3)
                
                for batch_num in range(num_batches):
                    batch_id = f"{sku_id}_{store_id}_B{batch_num + 1}"
                    
                    # Expiry date based on shelf life
                    days_to_expiry = random.randint(1, shelf_life_days)
                    expiry_date = snapshot_date + timedelta(days=days_to_expiry)
                    
                    # Inventory quantity
                    base_qty = {
                        "dairy": random.randint(20, 100),
                        "produce": random.randint(15, 80),
                        "meat": random.randint(10, 50),
                        "seafood": random.randint(5, 25),
                        "bakery": random.randint(25, 120),
                        "pantry": random.randint(50, 200),
                        "breakfast": random.randint(30, 100)
                    }.get(category, 50)
                    
                    on_hand_qty = max(1, int(base_qty * random.uniform(0.3, 1.2)))
                    
                    inventory_data.append({
                        "snapshot_date": snapshot_date,
                        "store_id": store_id,
                        "sku_id": sku_id,
                        "batch_id": batch_id,
                        "expiry_date": expiry_date,
                        "on_hand_qty": on_hand_qty
                    })
        
        # Insert inventory data
        for inv in inventory_data:
            inventory_record = InventoryBatch(**inv)
            db.merge(inventory_record)
        
        print(f"   ✅ Generated {len(inventory_data)} inventory batches")
        
        # Generate purchase data (cost information)
        print("   💰 Generating purchase/cost data...")
        purchase_data = []
        
        for inv in inventory_data:
            # Purchase happened some days ago
            received_date = inv["expiry_date"] - timedelta(days=random.randint(30, 90))
            
            # Unit cost (typically 60-80% of MRP)
            sku_mrp = next(s["mrp"] for s in skus_data if s["sku_id"] == inv["sku_id"])
            unit_cost = round(sku_mrp * random.uniform(0.6, 0.8), 2)
            
            purchase_data.append({
                "received_date": received_date,
                "store_id": inv["store_id"],
                "sku_id": inv["sku_id"],
                "batch_id": inv["batch_id"],
                "received_qty": inv["on_hand_qty"] + random.randint(10, 50),  # More was received
                "unit_cost": unit_cost
            })
        
        # Insert purchase data
        for purch in purchase_data:
            purchase_record = Purchase(**purch)
            db.merge(purchase_record)
        
        print(f"   ✅ Generated {len(purchase_data)} purchase records")
        
        db.commit()
        print("✅ All dummy data inserted successfully!")
        
        # Print summary
        print("\n📊 Data Summary:")
        print(f"   🏪 Stores: {len(stores_data)}")
        print(f"   🛒 Products: {len(skus_data)}")
        print(f"   📈 Sales records: {len(sales_data)} (last 60 days)")
        print(f"   📦 Inventory batches: {len(inventory_data)}")
        print(f"   💰 Purchase records: {len(purchase_data)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating dummy data: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Main setup function"""
    print("🚀 Setting up ThePerfectShop Local Database")
    print("=" * 50)
    
    # Step 1: Create database
    if not create_database():
        return False
    
    # Step 2: Create tables
    if not create_tables():
        return False
    
    # Step 3: Generate dummy data
    if not generate_dummy_data():
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n🔗 Next steps:")
    print("   1. Start the API: python -m uvicorn app.main:app --reload")
    print("   2. Open docs: http://localhost:8000/docs")
    print("   3. Test endpoints with realistic data!")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)