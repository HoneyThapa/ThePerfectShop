#!/usr/bin/env python3
"""
Simple script to trigger the data processing pipeline
"""

import requests
from datetime import date
import time

def trigger_pipeline():
    """Trigger the data processing pipeline via API calls"""
    base_url = "http://localhost:8000"
    
    print("🚀 Triggering Data Processing Pipeline")
    print("=" * 50)
    
    # Step 1: Generate actions (this should trigger the full pipeline)
    print("1️⃣ Generating Actions...")
    try:
        response = requests.post(f"{base_url}/actions/generate", 
                               json={
                                   "snapshot_date": date.today().isoformat(),
                                   "min_risk_score": 50.0,
                                   "include_transfers": True,
                                   "include_markdowns": True,
                                   "include_liquidations": True
                               },
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Generated {len(result.get('action_ids', []))} actions")
        else:
            print(f"❌ Action generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Action generation error: {e}")
        return False
    
    # Step 2: Check if data is now available
    print("\n2️⃣ Checking Data Availability...")
    
    endpoints_to_check = [
        ("/risk?snapshot_date=" + date.today().isoformat(), "Risk Analysis"),
        ("/actions/", "Actions List"),
        ("/kpis/dashboard", "KPI Dashboard"),
        ("/features/summary", "Features Summary")
    ]
    
    all_good = True
    for endpoint, name in endpoints_to_check:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    count = len(data)
                    print(f"✅ {name}: {count} items")
                    if count == 0:
                        all_good = False
                elif isinstance(data, dict):
                    print(f"✅ {name}: Data available")
                    # Check for meaningful values
                    if name == "KPI Dashboard":
                        at_risk = data.get('total_at_risk_value', 0)
                        if at_risk == 0:
                            print(f"   ⚠️  At-risk value is still 0")
                            all_good = False
                else:
                    print(f"✅ {name}: Response received")
            else:
                print(f"❌ {name}: Status {response.status_code}")
                all_good = False
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            all_good = False
    
    if all_good:
        print("\n🎉 Pipeline completed successfully!")
        print("✅ Your UI should now show data")
    else:
        print("\n⚠️  Some issues remain - data might still be processing")
    
    return all_good

if __name__ == "__main__":
    success = trigger_pipeline()
    if success:
        print("\n🔗 Try refreshing your UI now!")
    else:
        print("\n💡 You may need to:")
        print("   1. Ensure backend is running")
        print("   2. Check database has data")
        print("   3. Wait a moment and try again")