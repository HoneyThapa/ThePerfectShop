#!/usr/bin/env python3
"""
Test insights endpoint bypassing database completely
"""

import requests
import json
from datetime import date

API_BASE = "http://localhost:8000"

def test_with_full_inventory_data():
    """Test with complete inventory data to bypass database"""
    print("🔍 Testing with full inventory data...")
    
    payload = {
        "inventory_data": [
            {
                "store_id": "STORE001",
                "sku_id": "SKU001", 
                "batch_id": "BATCH001",
                "product_name": "Fresh Apples",
                "category": "Fruits",
                "on_hand_qty": 50,
                "expiry_date": "2025-01-15",  # Future date to avoid negative days
                "cost_per_unit": 2.50,
                "selling_price": 4.00
            },
            {
                "store_id": "STORE001",
                "sku_id": "SKU002", 
                "batch_id": "BATCH002",
                "product_name": "Milk Cartons",
                "category": "Dairy",
                "on_hand_qty": 25,
                "expiry_date": "2025-01-05",
                "cost_per_unit": 1.20,
                "selling_price": 2.50
            }
        ],
        "snapshot_date": "2025-01-01",  # Use a fixed date
        "store_id": None,
        "sku_id": None,
        "top_n": 20
    }
    
    try:
        print("📤 Sending request with full data...")
        response = requests.post(f"{API_BASE}/ai/insights", json=payload, timeout=30)
        print(f"📥 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Executive Summary: {result.get('executive_summary', 'N/A')[:100]}...")
            print(f"Actions: {len(result.get('prioritized_actions', []))}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Bypass Database")
    print("=" * 30)
    
    success = test_with_full_inventory_data()
    
    if success:
        print("\n✅ Endpoint works with full data!")
    else:
        print("\n❌ Still failing with full data!")