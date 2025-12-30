#!/usr/bin/env python3
"""
Diagnose UI data display issues
"""

import requests
import json
from datetime import date

def check_backend_status():
    """Check if backend is running and returning data"""
    print("🔍 Diagnosing UI Data Issues")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check if backend is running
    print("1️⃣ Testing Backend Connection...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            health_data = response.json()
            print(f"   Status: {health_data.get('status', 'unknown')}")
            
            db_status = health_data.get('checks', {}).get('database', {}).get('status')
            if db_status == 'healthy':
                print("✅ Database connection is healthy")
            else:
                print(f"❌ Database issue: {db_status}")
                return False
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running!")
        print("💡 Solution: Start the backend with:")
        print("   python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Backend connection error: {e}")
        return False
    
    # Test 2: Check specific endpoints that UI uses
    print("\n2️⃣ Testing API Endpoints...")
    
    endpoints_to_test = [
        ("/risk?snapshot_date=2025-12-30", "Risk Analysis"),
        ("/actions/", "Actions"),
        ("/kpis/dashboard", "KPI Dashboard"),
        ("/features/summary", "Features Summary")
    ]
    
    for endpoint, name in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    print(f"✅ {name}: Returns {len(data)} items")
                    if len(data) > 0:
                        print(f"   Sample: {str(data[0])[:100]}...")
                    else:
                        print("   ⚠️  Empty list returned")
                elif isinstance(data, dict):
                    print(f"✅ {name}: Returns data object")
                    print(f"   Keys: {list(data.keys())}")
                    # Show sample values
                    for key, value in list(data.items())[:3]:
                        print(f"   {key}: {value}")
                else:
                    print(f"✅ {name}: Returns {type(data)}")
            else:
                print(f"❌ {name}: Status {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
    
    # Test 3: Check data content specifically
    print("\n3️⃣ Checking Data Content...")
    
    try:
        # Check KPI data specifically
        response = requests.get(f"{base_url}/kpis/dashboard")
        if response.status_code == 200:
            kpi_data = response.json()
            print("📊 KPI Dashboard Data:")
            for key, value in kpi_data.items():
                print(f"   {key}: {value}")
            
            # Check if values are meaningful
            at_risk_value = kpi_data.get('total_at_risk_value', 0)
            if at_risk_value > 0:
                print("✅ KPI data looks good")
            else:
                print("⚠️  KPI values are zero - this might be why UI shows no data")
        
        # Check risk analysis
        response = requests.get(f"{base_url}/risk?snapshot_date=2025-12-30")
        if response.status_code == 200:
            risk_data = response.json()
            print(f"\n🚨 Risk Analysis: {len(risk_data) if isinstance(risk_data, list) else 'Not a list'} items")
            if isinstance(risk_data, list) and len(risk_data) == 0:
                print("⚠️  No risk items found - this is why risk analysis shows empty")
        
        # Check actions
        response = requests.get(f"{base_url}/actions/")
        if response.status_code == 200:
            actions_data = response.json()
            print(f"🛠️  Actions: {len(actions_data) if isinstance(actions_data, list) else 'Not a list'} items")
            if isinstance(actions_data, list) and len(actions_data) == 0:
                print("⚠️  No actions found - this is why actions list shows empty")
                
    except Exception as e:
        print(f"❌ Error checking data content: {e}")
    
    print("\n4️⃣ Recommendations:")
    print("=" * 50)
    
    # Check if this is a data generation issue
    try:
        response = requests.get(f"{base_url}/features/summary")
        if response.status_code == 200:
            features_data = response.json()
            combinations = features_data.get('total_store_sku_combinations', 0)
            
            if combinations == 0:
                print("🔧 Issue Found: No store-SKU combinations processed")
                print("💡 Solutions:")
                print("   1. The system has raw data but hasn't processed it into features")
                print("   2. Try running the feature generation manually")
                print("   3. Check if the risk scoring pipeline needs to be triggered")
                print("\n🚀 Try this:")
                print("   1. Restart the backend: python -m uvicorn app.main:app --reload")
                print("   2. Wait a few seconds for initialization")
                print("   3. Refresh your UI")
            else:
                print("✅ Feature processing looks good")
                print("💡 If UI still shows no data:")
                print("   1. Check browser console for JavaScript errors")
                print("   2. Try refreshing the page")
                print("   3. Clear browser cache")
                print("   4. Try a different browser")
    except:
        pass
    
    return True

if __name__ == "__main__":
    check_backend_status()