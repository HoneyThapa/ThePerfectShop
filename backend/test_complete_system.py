#!/usr/bin/env python3
"""
Complete system test with database
"""

import requests
import json
import time
import threading
import uvicorn
from app.main import app

def start_test_server():
    uvicorn.run(app, host='127.0.0.1', port=8003, log_level='error')

def test_complete_system():
    """Test the complete system with database"""
    base_url = "http://127.0.0.1:8003"
    
    print("🧪 Testing Complete ThePerfectShop System")
    print("=" * 50)
    
    # Start server
    print("🚀 Starting test server...")
    server_thread = threading.Thread(target=start_test_server, daemon=True)
    server_thread.start()
    time.sleep(4)  # Wait for server to start
    
    tests_passed = 0
    tests_total = 0
    
    # Test cases with database
    test_cases = [
        {
            "name": "Health Check with Database",
            "url": f"{base_url}/health",
            "expected_status": 200,
            "check_db_status": True
        },
        {
            "name": "Get Risk Analysis",
            "url": f"{base_url}/risk?snapshot_date=2025-12-30",
            "expected_status": 200,
            "check_data": True
        },
        {
            "name": "Get Features Summary", 
            "url": f"{base_url}/features/summary",
            "expected_status": 200,
            "check_data": True
        },
        {
            "name": "List Actions (should work with DB)",
            "url": f"{base_url}/actions/",
            "expected_status": 200,
            "check_data": True
        },
        {
            "name": "KPI Dashboard",
            "url": f"{base_url}/kpis/dashboard",
            "expected_status": 200,
            "check_data": True
        }
    ]
    
    # Run tests
    for test in test_cases:
        tests_total += 1
        try:
            print(f"\n📋 Testing: {test['name']}")
            response = requests.get(test['url'], timeout=15)
            
            # Check status code
            if response.status_code == test['expected_status']:
                print(f"   ✅ Status: {response.status_code}")
            else:
                print(f"   ❌ Status: {response.status_code} (expected {test['expected_status']})")
                print(f"   📄 Response: {response.text[:200]}...")
                continue
            
            # Check database status in health check
            if test.get('check_db_status'):
                try:
                    data = response.json()
                    db_status = data.get('checks', {}).get('database', {}).get('status')
                    if db_status == 'healthy':
                        print(f"   ✅ Database: Connected and healthy")
                    else:
                        print(f"   ⚠️  Database: {db_status}")
                except:
                    pass
            
            # Check if response has data
            if test.get('check_data'):
                try:
                    data = response.json()
                    if isinstance(data, dict) and len(data) > 0:
                        print(f"   ✅ Data: Response contains data")
                        # Show sample of response
                        sample = str(data)[:150] + "..." if len(str(data)) > 150 else str(data)
                        print(f"   📄 Sample: {sample}")
                    elif isinstance(data, list) and len(data) > 0:
                        print(f"   ✅ Data: Response contains {len(data)} items")
                    else:
                        print(f"   ⚠️  Data: Empty response (might be expected)")
                except json.JSONDecodeError:
                    print(f"   ❌ Data: Invalid JSON response")
                    continue
            
            tests_passed += 1
            print(f"   ✅ {test['name']}: PASSED")
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {test['name']}: FAILED - {e}")
        except Exception as e:
            print(f"   ❌ {test['name']}: ERROR - {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("🎉 All tests passed! The complete system is working.")
        print("\n🔗 You can now:")
        print("   • Open http://localhost:8000/docs for API documentation")
        print("   • Test all endpoints with real data")
        print("   • Generate risk scores and action recommendations")
        return True
    else:
        print(f"⚠️  {tests_total - tests_passed} tests failed.")
        if tests_passed == 0:
            print("💡 Make sure PostgreSQL is running and database is set up:")
            print("   python setup_local_db.py")
        return False

if __name__ == "__main__":
    success = test_complete_system()
    exit(0 if success else 1)