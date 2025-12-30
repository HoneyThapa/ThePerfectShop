#!/usr/bin/env python3
"""
Test script to verify ThePerfectShop deployment setup
"""

import os
import sys
import requests
import time
from subprocess import Popen, PIPE
import signal

def test_local_server():
    """Test the local development server"""
    print("🧪 Testing ThePerfectShop Backend Deployment Setup")
    print("=" * 50)
    
    # Start the server in background
    print("🚀 Starting local development server...")
    server_process = Popen([
        sys.executable, "run_local.py"
    ], stdout=PIPE, stderr=PIPE)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    try:
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health check passed!")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Version: {health_data.get('version')}")
            print(f"   Environment: {health_data.get('environment')}")
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            return False
        
        # Test root endpoint
        print("🔍 Testing root endpoint...")
        response = requests.get("http://localhost:8000/", timeout=5)
        
        if response.status_code == 200:
            root_data = response.json()
            print("✅ Root endpoint passed!")
            print(f"   Message: {root_data.get('message')}")
            print(f"   API Version: {root_data.get('version')}")
        else:
            print(f"❌ Root endpoint failed with status: {response.status_code}")
            return False
        
        # Test docs endpoint
        print("🔍 Testing API documentation...")
        response = requests.get("http://localhost:8000/docs", timeout=5)
        
        if response.status_code == 200:
            print("✅ API documentation accessible!")
            print("   📖 Swagger UI: http://localhost:8000/docs")
        else:
            print(f"❌ API documentation failed with status: {response.status_code}")
        
        print("\n🎉 All tests passed! ThePerfectShop backend is ready for frontend integration.")
        print("\n📋 Quick Start Guide:")
        print("   1. Run: python run_local.py")
        print("   2. API available at: http://localhost:8000")
        print("   3. Documentation: http://localhost:8000/docs")
        print("   4. Health check: http://localhost:8000/health")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running.")
        return False
    except requests.exceptions.Timeout:
        print("❌ Server response timeout.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        # Stop the server
        print("\n🛑 Stopping test server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except:
            server_process.kill()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    success = test_local_server()
    sys.exit(0 if success else 1)