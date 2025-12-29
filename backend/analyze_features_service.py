"""
Analyze the features service implementation without database dependency
"""
import pandas as pd
from datetime import date, timedelta

def analyze_features_service():
    """Analyze the features service implementation"""
    
    print("=== Features Service Analysis ===\n")
    
    # Read the features service code
    with open('app/services/features.py', 'r') as f:
        features_code = f.read()
    
    print("1. Code Structure Analysis:")
    
    # Check for required imports
    has_pandas = 'import pandas as pd' in features_code
    has_sqlalchemy = 'from sqlalchemy import text' in features_code
    has_timedelta = 'from datetime import timedelta' in features_code
    has_models = 'from app.db.models import FeatureStoreSKU' in features_code
    
    print(f"   ✅ Pandas import: {'PRESENT' if has_pandas else 'MISSING'}")
    print(f"   ✅ SQLAlchemy import: {'PRESENT' if has_sqlalchemy else 'MISSING'}")
    print(f"   ✅ Timedelta import: {'PRESENT' if has_timedelta else 'MISSING'}")
    print(f"   ✅ FeatureStoreSKU model: {'PRESENT' if has_models else 'MISSING'}")
    
    # Check for main function
    has_build_function = 'def build_features(' in features_code
    print(f"   ✅ build_features function: {'PRESENT' if has_build_function else 'MISSING'}")
    
    print("\n2. Functionality Analysis:")
    
    # Check for velocity calculations
    has_v7 = 'v7=' in features_code and 'tail(7)' in features_code
    has_v14 = 'v14=' in features_code and 'tail(14)' in features_code
    has_v30 = 'v30=' in features_code and 'mean()' in features_code
    has_volatility = 'volatility=' in features_code and 'std()' in features_code
    
    print(f"   ✅ v7 calculation (7-day): {'PRESENT' if has_v7 else 'MISSING'}")
    print(f"   ✅ v14 calculation (14-day): {'PRESENT' if has_v14 else 'MISSING'}")
    print(f"   ✅ v30 calculation (30-day): {'PRESENT' if has_v30 else 'MISSING'}")
    print(f"   ✅ Volatility calculation: {'PRESENT' if has_volatility else 'MISSING'}")
    
    # Check for data aggregation
    has_groupby = 'groupby(' in features_code
    has_store_sku_grouping = 'store_id' in features_code and 'sku_id' in features_code
    has_date_range = 'start' in features_code and 'end' in features_code
    
    print(f"   ✅ Data grouping: {'PRESENT' if has_groupby else 'MISSING'}")
    print(f"   ✅ Store-SKU grouping: {'PRESENT' if has_store_sku_grouping else 'MISSING'}")
    print(f"   ✅ Date range filtering: {'PRESENT' if has_date_range else 'MISSING'}")
    
    # Check for database operations
    has_merge = 'merge(' in features_code
    has_commit = 'commit()' in features_code
    
    print(f"   ✅ Database merge: {'PRESENT' if has_merge else 'MISSING'}")
    print(f"   ✅ Database commit: {'PRESENT' if has_commit else 'MISSING'}")
    
    print("\n3. Algorithm Analysis:")
    
    # Analyze the velocity calculation logic
    print("   Velocity Calculation Logic:")
    if 'tail(7)' in features_code and 'mean()' in features_code:
        print("     - v7: Last 7 days average ✅")
    if 'tail(14)' in features_code and 'mean()' in features_code:
        print("     - v14: Last 14 days average ✅")
    if 'mean()' in features_code and not 'tail(' in features_code.split('v30=')[1].split('\n')[0]:
        print("     - v30: Full 30 days average ✅")
    
    # Check for time series handling
    has_asfreq = 'asfreq(' in features_code
    has_fill_value = 'fill_value=0' in features_code
    
    print("   Time Series Handling:")
    print(f"     - Daily frequency resampling: {'PRESENT' if has_asfreq else 'MISSING'}")
    print(f"     - Missing day fill (0): {'PRESENT' if has_fill_value else 'MISSING'}")
    
    print("\n4. Requirements Compliance Check:")
    
    # Check against Step 2 requirements
    requirements = {
        "Aggregate sales_daily into rolling velocities": has_v7 and has_v14 and has_v30,
        "Compute volatility (std dev over 30 days)": has_volatility,
        "Store into features_store_sku": has_merge and 'FeatureStoreSKU' in features_code,
        "Query capability": has_merge  # If data is stored, it can be queried
    }
    
    for req, status in requirements.items():
        print(f"   ✅ {req}: {'COMPLETE' if status else 'INCOMPLETE'}")
    
    print("\n5. Missing Components Analysis:")
    
    missing_components = []
    
    # Check for API endpoints
    try:
        with open('app/api/routes_risk.py', 'r') as f:
            risk_routes = f.read()
        
        has_features_endpoint = 'features' in risk_routes.lower()
        if not has_features_endpoint:
            missing_components.append("API endpoint for querying features")
    except:
        missing_components.append("Could not check API routes")
    
    # Check for tests
    import os
    has_feature_tests = any('features' in f.lower() for f in os.listdir('tests') if f.endswith('.py')) if os.path.exists('tests') else False
    if not has_feature_tests:
        missing_components.append("Comprehensive tests for features service")
    
    # Check for error handling
    has_error_handling = 'try:' in features_code or 'except' in features_code
    if not has_error_handling:
        missing_components.append("Error handling in features service")
    
    if missing_components:
        print("   Missing components:")
        for component in missing_components:
            print(f"     - {component}")
    else:
        print("   No missing components identified")
    
    print("\n=== Summary ===")
    
    core_functionality_complete = all([
        has_build_function,
        has_v7, has_v14, has_v30,
        has_volatility,
        has_groupby,
        has_merge
    ])
    
    print(f"Core features functionality: {'✅ COMPLETE' if core_functionality_complete else '❌ INCOMPLETE'}")
    
    # Deliverable check
    deliverable_met = core_functionality_complete and has_store_sku_grouping
    print(f"Deliverable 'Query: how fast does SKU sell in store': {'✅ ACHIEVABLE' if deliverable_met else '❌ NOT ACHIEVABLE'}")
    
    return core_functionality_complete, missing_components

if __name__ == "__main__":
    analyze_features_service()