#!/usr/bin/env python3
"""
Test the feedback endpoint
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_feedback():
    """Test the feedback endpoint"""
    print("🔍 Testing feedback endpoint...")
    
    payload = {
        "feedback_type": "will_consider",
        "context_hash": "test_hash_123",
        "action_type": "markdown",
        "action_parameters": {
            "sku_id": "SKU001",
            "discount_percentage": 30,
            "expected_savings": 500
        },
        "risk_score": 0.85,
        "user_notes": "User will consider this markdown recommendation"
    }
    
    try:
        response = requests.post(f"{API_BASE}/ai/feedback", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Feedback endpoint working!")
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Feedback Endpoint")
    print("=" * 40)
    
    success = test_feedback()
    
    if success:
        print("\n✅ Feedback system is working!")
    else:
        print("\n❌ Feedback system has issues.")