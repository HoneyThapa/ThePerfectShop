#!/usr/bin/env python3
"""
Test insights endpoint with minimal data
"""

import requests
import json
from datetime import date

API_BASE = "http://localhost:8000"

def test_minimal_insights():
    """Test with minimal payload"""
    print("🔍 Testing minimal insights...")
    
    # Minimal payload without inventory_data
    payload = {
        "snapshot_date": date.today().isoformat(),
        "top_n": 5
    }
    
    try:
        response = requests.post(f"{API_BASE}/ai/insights", json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Minimal test passed!")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_with_empty_inventory():
    """Test with empty inventory_data"""
    print("\n🔍 Testing with empty inventory_data...")
    
    payload = {
        "inventory_data": [],
        "snapshot_date": date.today().isoformat(),
        "top_n": 5
    }
    
    try:
        response = requests.post(f"{API_BASE}/ai/insights", json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Empty inventory test passed!")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_groq_direct():
    """Test Groq client directly"""
    print("\n🔍 Testing Groq client directly...")
    
    try:
        from app.services.groq_client import groq_client
        
        # Simple context
        context = {
            "risk_items": [],
            "key_metrics": {"total_at_risk_value": 0},
            "user_preferences": {"optimize_for": "cost"},
            "news_events": []
        }
        
        response = groq_client.get_insights(context, {})
        print("✅ Groq client working!")
        print(f"Summary: {response.get('executive_summary', 'No summary')[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Groq error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Simple Insights")
    print("=" * 40)
    
    test1 = test_minimal_insights()
    test2 = test_with_empty_inventory()
    test3 = test_groq_direct()
    
    print(f"\n📊 Results:")
    print(f"  Minimal: {'✅' if test1 else '❌'}")
    print(f"  Empty Inventory: {'✅' if test2 else '❌'}")
    print(f"  Groq Direct: {'✅' if test3 else '❌'}")