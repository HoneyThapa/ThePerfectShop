#!/usr/bin/env python3
"""
Test script for AI Operations Copilot endpoints.
Run this after starting the backend server to test AI functionality.
"""

import requests
import json
from datetime import date

API_BASE = "http://localhost:8000"

def test_ai_health():
    """Test AI health endpoint"""
    print("🔍 Testing AI health...")
    try:
        response = requests.get(f"{API_BASE}/ai/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_ai_insights():
    """Test AI insights endpoint"""
    print("\n🤖 Testing AI insights...")
    try:
        payload = {
            "snapshot_date": date.today().isoformat(),
            "top_n": 5
        }
        response = requests.post(f"{API_BASE}/ai/insights", json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Executive Summary: {data.get('executive_summary', 'N/A')}")
            print(f"Actions Count: {len(data.get('prioritized_actions', []))}")
            print(f"Key Metrics: {data.get('key_metrics', {})}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Insights test failed: {e}")
        return False

def test_ai_chat():
    """Test AI chat endpoint"""
    print("\n💬 Testing AI chat...")
    try:
        payload = {
            "message": "What are the top 3 risks I should focus on?",
            "snapshot_date": date.today().isoformat()
        }
        response = requests.post(f"{API_BASE}/ai/chat", json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"AI Response: {data.get('response', 'N/A')}")
            print(f"Evidence Used: {data.get('evidence_used', [])}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        return False

def test_preferences():
    """Test preferences endpoints"""
    print("\n⚙️ Testing preferences...")
    try:
        # Get preferences
        response = requests.get(f"{API_BASE}/preferences/", timeout=10)
        print(f"Get Status: {response.status_code}")
        
        # Update preferences
        payload = {
            "optimize_for": "waste_min",
            "service_level_priority": "high",
            "multi_location_aggressiveness": "low"
        }
        response = requests.post(f"{API_BASE}/preferences/", json=payload, timeout=10)
        print(f"Update Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Updated Preferences: {response.json()}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Preferences test failed: {e}")
        return False

def test_feedback():
    """Test feedback endpoint"""
    print("\n📝 Testing feedback...")
    try:
        payload = {
            "recommendation_id": "test_rec_123",
            "action": "accepted",
            "context_hash": "store1:sku1:batch1",
            "action_type": "markdown",
            "action_parameters": {"discount": 0.2},
            "risk_score": 85.5
        }
        response = requests.post(f"{API_BASE}/ai/feedback", json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Feedback Response: {response.json()}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Feedback test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing AI Operations Copilot Endpoints")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_ai_health),
        ("AI Insights", test_ai_insights),
        ("AI Chat", test_ai_chat),
        ("Preferences", test_preferences),
        ("Feedback", test_feedback)
    ]
    
    results = []
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AI Operations Copilot is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()