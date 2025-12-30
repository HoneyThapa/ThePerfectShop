#!/usr/bin/env python3
"""
Test specific API endpoints to verify functionality
"""

import requests
import json
import time
import threading
import uvicorn
from app.main import app

def start_test_server():
    uvicorn.run(app, host='127.0.0.1', port=8002, log_level='error')

def test_endpoints():
    base_url = "http://127.0.0.1:8002"
    
    print("🔍 Testing Specific API Endpoints")
    print("=" * 50)
    
    # Start server
    server_thread = threading.Thread(target=start_test_server, daemon=True)
    server_thread.start()
    time.sleep(3)
    
    # Get OpenAPI spec to see all available endpoints
    try:
        response = requests.get(f"{base_url}/openapi.json")
        spec = response.json()
        paths = spec.get('paths', {})
        
        print(f"📋 Available API Endpoints:")
        for path, methods in paths.items():
            method_list = list(methods.keys())
            print(f"   {path}: {', '.join(method_list).upper()}")
        
        print(f"\n📊 Total endpoints: {len(paths)}")
        
        # Test some key endpoints that don't require database
        print(f"\n🧪 Testing Key Endpoints:")
        
        # Test actions endpoint (should fail gracefully without DB)
        try:
            response = requests.get(f"{base_url}/actions/")
            print(f"   GET /actions/: {response.status_code} - {response.text[:100]}...")
        except Exception as e:
            print(f"   GET /actions/: Error - {e}")
        
        # Test KPIs endpoint (should fail gracefully without DB)
        try:
            response = requests.get(f"{base_url}/kpis/dashboard")
            print(f"   GET /kpis/dashboard: {response.status_code} - {response.text[:100]}...")
        except Exception as e:
            print(f"   GET /kpis/dashboard: Error - {e}")
        
        # Test upload endpoint structure
        try:
            response = requests.get(f"{base_url}/upload/")
            print(f"   GET /upload/: {response.status_code} - {response.text[:100]}...")
        except Exception as e:
            print(f"   GET /upload/: Error - {e}")
            
    except Exception as e:
        print(f"❌ Failed to get API spec: {e}")

if __name__ == "__main__":
    test_endpoints()