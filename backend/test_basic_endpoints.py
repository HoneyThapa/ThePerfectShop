#!/usr/bin/env python3
"""
Basic test script for core endpoints without requiring Groq API.
Tests the database functionality and basic API responses.
"""

import requests
import json
from datetime import date

API_BASE = "http://localhost:8000"

def test_risk_endpoint():
    """Test the basic risk endpoint"""
    print("⚠️ Testing risk endpoint...")
    try:
        response = requests.get(f"{API_BASE}/risk", params={"snapshot_date": date.today().isoformat()}, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Risk items found: {len(data)}")
            if data:
                print(f"Sample risk item: {data[0]}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Risk test failed: {e}")
        return False

def test_preferences():
    """Test preferences endpoints"""
    print("\n⚙️ Testing preferences...")
    try:
        # Get preferences
        response = requests.get(f"{API_BASE}/preferences/", timeout=10)
        print(f"Get Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Current Preferences: {response.json()}")
        
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

def test_news_events():
    """Test news events endpoints"""
    print("\n📰 Testing news events...")
    try:
        # Get news events
        response = requests.get(f"{API_BASE}/news/", timeout=10)
        print(f"Get Status: {response.status_code}")
        
        if response.status_code == 200:
            events = response.json()
            print(f"News events found: {len(events)}")
            if events:
                print(f"Sample event: {events[0]}")
        
        # Create a news event
        payload = {
            "event_date": date.today().isoformat(),
            "event_type": "test_event",
            "description": "Test event for API validation",
            "impact_stores": ["S001"],
            "impact_skus": ["SKU101"],
            "score_modifier": 0.1
        }
        response = requests.post(f"{API_BASE}/news/", json=payload, timeout=10)
        print(f"Create Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Created Event: {response.json()}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ News events test failed: {e}")
        return False

def main():
    """Run basic tests"""
    print("🚀 Testing Basic API Endpoints (No AI Required)")
    print("=" * 50)
    
    tests = [
        ("Risk Endpoint", test_risk_endpoint),
        ("Preferences", test_preferences),
        ("Feedback", test_feedback),
        ("News Events", test_news_events)
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
        print("🎉 All basic tests passed! Core functionality is working.")
        print("\nNote: AI features require Groq API connection.")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()