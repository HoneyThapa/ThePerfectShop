"""
Test the features service functionality
"""
import pandas as pd
from datetime import date, timedelta
from app.services.features import build_features
from app.db.session import SessionLocal
from app.db.models import SalesDaily, FeatureStoreSKU
from sqlalchemy import text

def setup_test_sales_data():
    """Create test sales data for feature calculation"""
    db = SessionLocal()
    
    # Clear existing data
    db.execute(text("DELETE FROM sales_daily"))
    db.execute(text("DELETE FROM features_store_sku"))
    db.commit()
    
    # Create test sales data for the last 30 days
    base_date = date(2024, 1, 1)
    test_data = []
    
    # Store S001, SKU001 - consistent sales
    for i in range(30):
        test_data.append(SalesDaily(
            date=base_date + timedelta(days=i),
            store_id="S001",
            sku_id="SKU001",
            units_sold=10,  # Consistent 10 units per day
            selling_price=25.99
        ))
    
    # Store S001, SKU002 - variable sales
    sales_pattern = [5, 8, 12, 15, 3, 7, 20, 25, 10, 5] * 3  # Repeating pattern
    for i in range(30):
        test_data.append(SalesDaily(
            date=base_date + timedelta(days=i),
            store_id="S001",
            sku_id="SKU002",
            units_sold=sales_pattern[i],
            selling_price=30.50
        ))
    
    # Store S002, SKU001 - different velocity
    for i in range(30):
        test_data.append(SalesDaily(
            date=base_date + timedelta(days=i),
            store_id="S002",
            sku_id="SKU001",
            units_sold=5,  # Half the velocity of S001
            selling_price=25.99
        ))
    
    # Add all test data
    for record in test_data:
        db.merge(record)
    
    db.commit()
    db.close()
    
    return base_date + timedelta(days=29)  # Return the snapshot date

def test_features_functionality():
    """Test the complete features functionality"""
    
    print("=== Testing Features Service Functionality ===\n")
    
    # Setup test data
    print("1. Setting up test sales data...")
    snapshot_date = setup_test_sales_data()
    print(f"   Test data created for snapshot date: {snapshot_date}")
    
    # Test feature building
    print("\n2. Testing feature building...")
    try:
        build_features(snapshot_date)
        print("   ✅ Feature building completed without errors")
    except Exception as e:
        print(f"   ❌ Feature building failed: {str(e)}")
        return False
    
    # Verify features were created
    print("\n3. Verifying features were created...")
    db = SessionLocal()
    
    features = db.query(FeatureStoreSKU).filter(
        FeatureStoreSKU.date == snapshot_date
    ).all()
    
    print(f"   Features created: {len(features)} records")
    
    if len(features) == 0:
        print("   ❌ No features were created")
        db.close()
        return False
    
    # Test specific feature calculations
    print("\n4. Testing feature calculations...")
    
    # Find S001-SKU001 (consistent sales)
    s001_sku001 = next((f for f in features if f.store_id == "S001" and f.sku_id == "SKU001"), None)
    
    if s001_sku001:
        print(f"   S001-SKU001 features:")
        print(f"     v7: {s001_sku001.v7}")
        print(f"     v14: {s001_sku001.v14}")
        print(f"     v30: {s001_sku001.v30}")
        print(f"     volatility: {s001_sku001.volatility}")
        
        # Verify consistent sales (should be ~10 for all periods)
        v7_correct = abs(s001_sku001.v7 - 10.0) < 0.1
        v14_correct = abs(s001_sku001.v14 - 10.0) < 0.1
        v30_correct = abs(s001_sku001.v30 - 10.0) < 0.1
        volatility_low = s001_sku001.volatility < 1.0  # Should be very low for consistent sales
        
        print(f"     ✅ v7 calculation: {'PASS' if v7_correct else 'FAIL'}")
        print(f"     ✅ v14 calculation: {'PASS' if v14_correct else 'FAIL'}")
        print(f"     ✅ v30 calculation: {'PASS' if v30_correct else 'FAIL'}")
        print(f"     ✅ volatility calculation: {'PASS' if volatility_low else 'FAIL'}")
        
        consistent_sales_correct = all([v7_correct, v14_correct, v30_correct, volatility_low])
    else:
        print("   ❌ S001-SKU001 features not found")
        consistent_sales_correct = False
    
    # Find S001-SKU002 (variable sales)
    s001_sku002 = next((f for f in features if f.store_id == "S001" and f.sku_id == "SKU002"), None)
    
    if s001_sku002:
        print(f"\n   S001-SKU002 features (variable sales):")
        print(f"     v7: {s001_sku002.v7}")
        print(f"     v14: {s001_sku002.v14}")
        print(f"     v30: {s001_sku002.v30}")
        print(f"     volatility: {s001_sku002.volatility}")
        
        # Variable sales should have higher volatility
        volatility_high = s001_sku002.volatility > 1.0
        print(f"     ✅ volatility for variable sales: {'PASS' if volatility_high else 'FAIL'}")
        
        variable_sales_correct = volatility_high
    else:
        print("   ❌ S001-SKU002 features not found")
        variable_sales_correct = False
    
    # Find S002-SKU001 (different velocity)
    s002_sku001 = next((f for f in features if f.store_id == "S002" and f.sku_id == "SKU001"), None)
    
    if s002_sku001:
        print(f"\n   S002-SKU001 features (different store):")
        print(f"     v7: {s002_sku001.v7}")
        print(f"     v14: {s002_sku001.v14}")
        print(f"     v30: {s002_sku001.v30}")
        print(f"     volatility: {s002_sku001.volatility}")
        
        # Should be ~5 for all periods (half of S001)
        v30_different = abs(s002_sku001.v30 - 5.0) < 0.1
        print(f"     ✅ different store velocity: {'PASS' if v30_different else 'FAIL'}")
        
        different_store_correct = v30_different
    else:
        print("   ❌ S002-SKU001 features not found")
        different_store_correct = False
    
    db.close()
    
    # Test queryability
    print("\n5. Testing queryability...")
    db = SessionLocal()
    
    # Test: "how fast does this SKU sell in this store?"
    query_result = db.query(FeatureStoreSKU).filter(
        FeatureStoreSKU.store_id == "S001",
        FeatureStoreSKU.sku_id == "SKU001",
        FeatureStoreSKU.date == snapshot_date
    ).first()
    
    if query_result:
        print(f"   Query 'S001-SKU001 velocity': {query_result.v14} units/day (14-day average)")
        print("   ✅ Queryability: PASS")
        queryable = True
    else:
        print("   ❌ Queryability: FAIL")
        queryable = False
    
    db.close()
    
    # Overall assessment
    print("\n=== Summary ===")
    all_tests_pass = all([
        len(features) > 0,
        consistent_sales_correct,
        variable_sales_correct,
        different_store_correct,
        queryable
    ])
    
    print(f"Features service functionality: {'✅ COMPLETE' if all_tests_pass else '❌ INCOMPLETE'}")
    
    return all_tests_pass

if __name__ == "__main__":
    test_features_functionality()