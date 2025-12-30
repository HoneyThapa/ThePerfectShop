#!/usr/bin/env python3
"""
Test the new sample CSV data
"""

import pandas as pd
import requests
import json
from datetime import date

API_BASE = "http://localhost:8000"

def load_and_test_csv(filename):
    """Load CSV and test with AI insights"""
    print(f"🔍 Testing {filename}...")
    
    try:
        # Load CSV
        df = pd.read_csv(f"../frontend/{filename}")
        print(f"📊 Loaded {len(df)} items from {filename}")
        
        # Convert to records
        inventory_data = df.to_dict('records')
        
        # Test with AI insights
        payload = {
            "inventory_data": inventory_data,
            "snapshot_date": date.today().isoformat(),
            "top_n": 20
        }
        
        response = requests.post(f"{API_BASE}/ai/insights", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AI Insights successful!")
            print(f"📋 Executive Summary: {result.get('executive_summary', 'N/A')[:100]}...")
            print(f"🎯 Actions Generated: {len(result.get('prioritized_actions', []))}")
            
            # Print key metrics
            metrics = result.get('key_metrics', {})
            print(f"💰 Total At-Risk Value: ${metrics.get('total_at_risk_value', 0):,.2f}")
            print(f"📦 Total At-Risk Units: {metrics.get('total_at_risk_units', 0):,}")
            print(f"🔴 High Risk Batches: {metrics.get('high_risk_batches', 0)}")
            print(f"📅 Avg Days to Expiry: {metrics.get('avg_days_to_expiry', 0):.1f}")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_chat_with_data(filename):
    """Test chat with the sample data"""
    print(f"\n💬 Testing chat with {filename}...")
    
    try:
        # Load CSV
        df = pd.read_csv(f"../frontend/{filename}")
        inventory_data = df.to_dict('records')
        
        # Test chat
        payload = {
            "message": "What are the highest risk items in my inventory?",
            "inventory_data": inventory_data,
            "snapshot_date": date.today().isoformat()
        }
        
        response = requests.post(f"{API_BASE}/ai/chat", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat successful!")
            print(f"🤖 Response: {result.get('response', 'N/A')[:150]}...")
            return True
        else:
            print(f"❌ Chat Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat Exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing New Sample Data")
    print("=" * 50)
    
    # Test both CSV files
    files = ["sample_inventory.csv", "comprehensive_inventory.csv"]
    
    for filename in files:
        print(f"\n{'='*20} {filename} {'='*20}")
        insights_ok = load_and_test_csv(filename)
        chat_ok = test_chat_with_data(filename)
        
        print(f"\n📊 Results for {filename}:")
        print(f"  AI Insights: {'✅' if insights_ok else '❌'}")
        print(f"  AI Chat: {'✅' if chat_ok else '❌'}")
    
    print(f"\n🎉 Sample data testing complete!")