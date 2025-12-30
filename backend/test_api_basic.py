#!/usr/bin/env python3
"""
Basic API testing script to verify the merged backend is working.
Tests endpoints that don't require database connectivity.
"""

import requests
import json
import time
import threading
import uvicorn
from app.main import app

def start_test_server():
    """Start the FastAPI server in a background thread"""
    uvicorn.run(app, host='127.0.0.1', port=8001, log_level='error')

def test_api_endpoints():
    """Test various API endpoints"""
    base_url = "http://127.0.0.1:8001"
    
    print("🧪 Testing ThePerfectShop Backend API")
    print("=" * 50)
    
    # Start server
    print("🚀 Starting test server...")
    server_thread = threading.Thread(target=start_test_server, daemon=True)
    server_thread.start()
    time.sleep(3)  # Wait for server to start
    
    tests_passed = 0
    tests_total = 0
    
    # Test cases
    test_cases = [
        {
            "name": "Root Endpoint",
            "url": f"{base_url}/",
            "expected_status": 200,
            "expected_keys": ["message", "version", "status"]
        },
        {
            "name": "Health Check",
            "url": f"{base_url}/health",
            "expected_status": 200,
            "expected_keys": ["status", "timestamp", "version"]
        },
        {
            "name": "API Documentation",
            "url": f"{base_url}/docs",
            "expected_status": 200,
            "check_content": True
        },
        {
            "name": "OpenAPI Schema",
            "url": f"{base_url}/openapi.json",
            "expected_status": 200,
            "expected_keys": ["openapi", "info", "paths"]
        }
    ]
    
    # Run tests
    for test in test_cases:
        tests_total += 1
        try:
            print(f"\n📋 Testing: {test['name']}")
            response = requests.get(test['url'], timeout=10)
            
            # Check status code
            if response.status_code == test['expected_status']:
                print(f"   ✅ Status: {response.status_code}")
            else:
                print(f"   ❌ Status: {response.status_code} (expected {test['expected_status']})")
                continue
            
            # Check JSON response keys
            if 'expected_keys' in test:
                try:
                    data = response.json()
                    missing_keys = [key for key in test['expected_keys'] if key not in data]
                    if not missing_keys:
                        print(f"   ✅ Response structure: All expected keys present")
                        print(f"   📄 Sample data: {json.dumps(data, indent=2)[:200]}...")
                    else:
                        print(f"   ❌ Missing keys: {missing_keys}")
                        continue
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response")
                    continue
            
            # Check content (for HTML endpoints)
            if test.get('check_content'):
                if len(response.text) > 1000:  # Docs page should be substantial
                    print(f"   ✅ Content: HTML documentation loaded ({len(response.text)} chars)")
                else:
                    print(f"   ❌ Content: Response too short ({len(response.text)} chars)")
                    continue
            
            tests_passed += 1
            print(f"   ✅ {test['name']}: PASSED")
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {test['name']}: FAILED - {e}")
        except Exception as e:
            print(f"   ❌ {test['name']}: ERROR - {e}")
    
    # Test API endpoint discovery
    print(f"\n📋 Testing: API Endpoint Discovery")
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=10)
        if response.status_code == 200:
            openapi_spec = response.json()
            paths = openapi_spec.get('paths', {})
            
            expected_endpoints = [
                '/upload',
                '/risk', 
                '/features',
                '/actions',
                '/kpis'
            ]
            
            found_endpoints = []
            for path in paths.keys():
                for expected in expected_endpoints:
                    if path.startswith(expected):
                        found_endpoints.append(expected)
                        break
            
            found_endpoints = list(set(found_endpoints))  # Remove duplicates
            
            print(f"   📍 Found endpoints: {found_endpoints}")
            
            if len(found_endpoints) >= 4:  # Should have most core endpoints
                print(f"   ✅ Endpoint Discovery: PASSED ({len(found_endpoints)}/5 core endpoints found)")
                tests_passed += 1
            else:
                print(f"   ❌ Endpoint Discovery: FAILED (only {len(found_endpoints)}/5 core endpoints found)")
        else:
            print(f"   ❌ Endpoint Discovery: FAILED - Could not fetch OpenAPI spec")
    except Exception as e:
        print(f"   ❌ Endpoint Discovery: ERROR - {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("🎉 All tests passed! The merged backend is working correctly.")
        return True
    else:
        print(f"⚠️  {tests_total - tests_passed} tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = test_api_endpoints()
    exit(0 if success else 1)