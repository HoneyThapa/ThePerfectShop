#!/usr/bin/env python3
"""
Test the local database setup and verify data
"""

from app.db.session import SessionLocal
from app.db.models import StoreMaster, SKUMaster, SalesDaily, InventoryBatch, Purchase
from sqlalchemy import func, text
from datetime import date

def test_database():
    """Test database connection and data"""
    print("🧪 Testing Database Connection and Data")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Test connection
        result = db.execute(text("SELECT 1")).fetchone()
        print("✅ Database connection: OK")
        
        # Test data counts
        stores_count = db.query(StoreMaster).count()
        skus_count = db.query(SKUMaster).count()
        sales_count = db.query(SalesDaily).count()
        inventory_count = db.query(InventoryBatch).count()
        purchases_count = db.query(Purchase).count()
        
        print(f"\n📊 Data Summary:")
        print(f"   🏪 Stores: {stores_count}")
        print(f"   🛒 Products (SKUs): {skus_count}")
        print(f"   📈 Sales records: {sales_count}")
        print(f"   📦 Inventory batches: {inventory_count}")
        print(f"   💰 Purchase records: {purchases_count}")
        
        if all([stores_count > 0, skus_count > 0, sales_count > 0, inventory_count > 0, purchases_count > 0]):
            print("\n✅ All tables have data!")
        else:
            print("\n❌ Some tables are empty. Run setup_local_db.py first.")
            return False
        
        # Test some sample queries
        print(f"\n🔍 Sample Data:")
        
        # Sample stores
        stores = db.query(StoreMaster).limit(3).all()
        for store in stores:
            print(f"   🏪 Store {store.store_id}: {store.city} ({store.zone})")
        
        # Sample products
        skus = db.query(SKUMaster).limit(5).all()
        for sku in skus:
            print(f"   🛒 {sku.sku_id}: {sku.category} - ${sku.mrp}")
        
        # Recent sales
        recent_sales = (
            db.query(SalesDaily)
            .order_by(SalesDaily.date.desc())
            .limit(3)
            .all()
        )
        for sale in recent_sales:
            print(f"   📈 {sale.date}: {sale.store_id} sold {sale.units_sold} of {sale.sku_id}")
        
        # Inventory expiring soon
        today = date.today()
        from datetime import timedelta
        week_from_now = today + timedelta(days=7)
        expiring_soon = (
            db.query(InventoryBatch)
            .filter(InventoryBatch.expiry_date <= week_from_now)
            .order_by(InventoryBatch.expiry_date)
            .limit(3)
            .all()
        )
        
        if expiring_soon:
            print(f"\n⚠️  Items expiring within 7 days:")
            for item in expiring_soon:
                days_left = (item.expiry_date - today).days
                print(f"   📦 {item.sku_id} at {item.store_id}: {item.on_hand_qty} units, expires in {days_left} days")
        
        print(f"\n🎉 Database test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_database()
    exit(0 if success else 1)