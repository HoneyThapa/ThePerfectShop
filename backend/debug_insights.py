#!/usr/bin/env python3
"""
Debug the insights endpoint step by step
"""

import requests
import json
import traceback
from datetime import date

API_BASE = "http://localhost:8000"

def debug_insights():
    """Debug the insights endpoint step by step"""
    print("🔍 Debugging AI insights endpoint...")
    
    # Simple test data
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
        print("📤 Sending request...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(f"{API_BASE}/ai/insights", json=payload, timeout=30)
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Error Response:")
            try:
                error_detail = response.json()
                print(json.dumps(error_detail, indent=2))
            except:
                print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        traceback.print_exc()
        return False

def test_context_builder():
    """Test the context builder directly"""
    print("\n🔍 Testing context builder directly...")
    
    try:
        from app.services.context_builder import ContextBuilder
        
        context_builder = ContextBuilder()
        
        inventory_data = [
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
        ]
        
        context = context_builder.build_context_from_data(
            inventory_data=inventory_data,
            snapshot_date=date.today(),
            top_n=20
        )
        
        print("✅ Context builder working!")
        print(f"Risk items: {len(context.get('risk_items', []))}")
        print(f"Key metrics: {context.get('key_metrics', {})}")
        
        context_builder.close()
        return True
        
    except Exception as e:
        print(f"❌ Context builder error: {e}")
        traceback.print_exc()
        return False

def test_action_engine():
    """Test the action engine directly"""
    print("\n🔍 Testing action engine directly...")
    
    try:
        from app.services.action_engine import generate_actions_for_risks
        
        risk_items = [
            {
                "store_id": "STORE001",
                "sku_id": "SKU001",
                "batch_id": "BATCH001",
                "product_name": "Fresh Apples",
                "category": "Fruits",
                "on_hand_qty": 50,
                "at_risk_units": 50,
                "at_risk_value": 125.0,
                "expiry_date": "2024-02-15",
                "cost_per_unit": 2.50,
                "selling_price": 4.00,
                "days_to_expiry": 45,
                "risk_score": 75.0,
                "total_value": 125.0
            }
        ]
        
        user_preferences = {
            "optimize_for": "cost",
            "service_level_priority": "medium",
            "multi_location_aggressiveness": "medium"
        }
        
        actions = generate_actions_for_risks(risk_items, user_preferences)
        
        print("✅ Action engine working!")
        print(f"Generated {len(actions)} actions")
        
        return True
        
    except Exception as e:
        print(f"❌ Action engine error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Debugging AI Insights Endpoint")
    print("=" * 50)
    
    # Test individual components
    context_ok = test_context_builder()
    action_ok = test_action_engine()
    
    print("\n" + "=" * 50)
    
    # Test full endpoint
    endpoint_ok = debug_insights()
    
    print(f"\n📊 Results:")
    print(f"  Context Builder: {'✅' if context_ok else '❌'}")
    print(f"  Action Engine: {'✅' if action_ok else '❌'}")
    print(f"  Full Endpoint: {'✅' if endpoint_ok else '❌'}")