#!/usr/bin/env python3
"""
Test AI endpoints directly
"""

import requests
import json
from datetime import date

API_BASE = "http://localhost:8000"

def test_ai_insights():
    """Test AI insights endpoint"""
    print("🔍 Testing AI insights endpoint...")
    
    # Sample data
    payload = {
        "inventory_data": [
            {
                "store_id": "STORE001",
                "sku_id": "SKU001", 
                "batch_id": "BATCH001",
                "product_name": "Fresh Apples",
                "category": "Fruits",
                "on_hand_qty": 50,
                "expiry_date": "2024-02-15",
                "cost_per_unit": 2.50,
                "selling_price": 4.00
            }
        ],
        "snapshot_date": date.today().isoformat(),
        "store_id": None,
        "sku_id": None,
        "top_n": 20
    }
    
    try:
        response = requests.post(f"{API_BASE}/ai/insights", json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AI Insights successful!")
            print(f"Executive Summary: {result.get('executive_summary', 'N/A')[:100]}...")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_ai_chat():
    """Test AI chat endpoint"""
    print("\n🔍 Testing AI chat endpoint...")
    
    payload = {
        "message": "What are the main risks in my inventory?",
        "store_id": None,
        "sku_id": None,
        "snapshot_date": date.today().isoformat()
    }
    
    try:
        response = requests.post(f"{API_BASE}/ai/chat", json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AI Chat successful!")
            print(f"Response: {result.get('response', 'N/A')[:100]}...")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_server_health():
    """Test if server is running"""
    print("🔍 Testing server health...")
    
    try:
        response = requests.get(f"{API_BASE}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Make sure the backend server is running on port 8000")
        return False

if __name__ == "__main__":
    print("🚀 Testing AI Endpoints")
    print("=" * 40)
    
    # Test server health first
    if not test_server_health():
        print("\n❌ Server is not accessible. Start the backend first.")
        exit(1)
    
    # Test AI endpoints
    insights_ok = test_ai_insights()
    chat_ok = test_ai_chat()
    
    print("\n📊 Results:")
    print(f"  Server Health: ✅")
    print(f"  AI Insights: {'✅' if insights_ok else '❌'}")
    print(f"  AI Chat: {'✅' if chat_ok else '❌'}")
    
    if insights_ok and chat_ok:
        print("\n🎉 All AI endpoints are working!")
    else:
        print("\n⚠️ Some AI endpoints have issues. Check the logs above.")