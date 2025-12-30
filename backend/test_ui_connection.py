#!/usr/bin/env python3
"""
Test UI connection to backend
"""

import requests
import time
import subprocess
import sys
import threading
from pathlib import Path

def start_backend_for_test():
    """Start backend for testing"""
    return subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "127.0.0.1", 
        "--port", "8000"
    ], cwd=Path(__file__).parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def test_ui_backend_connection():
    """Test that UI can connect to backend"""
    print("🧪 Testing UI-Backend Connection")
    print("=" * 50)
    
    # Start backend
    print("🚀 Starting backend for test...")
    backend_process = start_backend_for_test()
    
    try:
        # Wait for backend to start
        time.sleep(3)
        
        # Test all endpoints that UI uses
        base_url = "http://127.0.0.1:8000"
        
        test_endpoints = [
            ("/health", "Health Check"),
            ("/risk?snapshot_date=2025-12-30", "Risk Analysis"),
            ("/actions/", "Actions List"),
            ("/kpis/dashboard", "KPI Dashboard"),
            ("/features/summary", "Features Summary")
        ]
        
        all_passed = True
        
        for endpoint, name in test_endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    print(f"✅ {name}: OK ({response.status_code})")
                else:
                    print(f"⚠️  {name}: {response.status_code}")
                    all_passed = False
            except Exception as e:
                print(f"❌ {name}: Failed - {e}")
                all_passed = False
        
        print("\n" + "=" * 50)
        if all_passed:
            print("🎉 All UI-Backend connections working!")
            print("\n🔗 You can now run:")
            print("   python start_system.py")
            print("   OR")
            print("   streamlit run ui_connected.py")
        else:
            print("⚠️  Some connections failed. Check backend status.")
        
        return all_passed
        
    finally:
        # Cleanup
        backend_process.terminate()
        backend_process.wait()

if __name__ == "__main__":
    success = test_ui_backend_connection()
    sys.exit(0 if success else 1)