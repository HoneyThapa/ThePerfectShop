#!/usr/bin/env python3
"""
Complete demo of all AI Operations Copilot features
"""

import requests
import json
from datetime import date

API_BASE = "http://localhost:8000"

def demo_ai_insights():
    """Demo AI insights with action recommendations"""
    print("🤖 DEMO: AI Insights Generation")
    print("-" * 40)
    
    payload = {
        "snapshot_date": date.today().isoformat(),
        "top_n": 10
    }
    
    response = requests.post(f"{API_BASE}/ai/insights", json=payload, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Executive Summary:")
        print(f"   {data.get('executive_summary', 'N/A')}")
        
        print(f"\n📊 Key Metrics:")
        metrics = data.get('key_metrics', {})
        print(f"   • Total At-Risk Value: ${metrics.get('total_at_risk_value', 0):,.2f}")
        print(f"   • High Risk Batches: {metrics.get('high_risk_batches', 0)}")
        print(f"   • Average Days to Expiry: {metrics.get('avg_days_to_expiry', 0):.1f}")
        
        print(f"\n🎯 Recommended Actions ({len(data.get('prioritized_actions', []))} total):")
        for i, action in enumerate(data.get('prioritized_actions', [])[:3]):
            print(f"   {i+1}. {action.get('action_type', 'Unknown').title()} - {action.get('priority', 'medium').title()} Priority")
            print(f"      {action.get('description', 'No description')}")
            print(f"      Expected: {action.get('expected_impact', 'Unknown impact')}")
        
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

def demo_ai_chat():
    """Demo AI chat functionality"""
    print("\n💬 DEMO: AI Chat Interface")
    print("-" * 40)
    
    questions = [
        "Hello! Please introduce yourself.",
        "What are the top 3 risks I should focus on?",
        "How can I reduce waste in my inventory?"
    ]
    
    for question in questions:
        print(f"\n👤 User: {question}")
        
        payload = {
            "message": question,
            "snapshot_date": date.today().isoformat()
        }
        
        response = requests.post(f"{API_BASE}/ai/chat", json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data.get('response', 'No response')
            # Truncate long responses for demo
            if len(ai_response) > 200:
                ai_response = ai_response[:200] + "..."
            print(f"🤖 AI: {ai_response}")
        else:
            print(f"❌ Error: {response.text}")
            return False
    
    return True

def demo_preferences():
    """Demo user preferences management"""
    print("\n⚙️ DEMO: User Preferences Management")
    print("-" * 40)
    
    # Get current preferences
    response = requests.get(f"{API_BASE}/preferences/")
    if response.status_code == 200:
        prefs = response.json()
        print(f"📋 Current Preferences:")
        print(f"   • Optimize for: {prefs.get('optimize_for', 'N/A')}")
        print(f"   • Service Level: {prefs.get('service_level_priority', 'N/A')}")
        print(f"   • Multi-location: {prefs.get('multi_location_aggressiveness', 'N/A')}")
    
    # Update preferences
    new_prefs = {
        "optimize_for": "profit",
        "service_level_priority": "high",
        "multi_location_aggressiveness": "medium"
    }
    
    response = requests.post(f"{API_BASE}/preferences/", json=new_prefs)
    if response.status_code == 200:
        print(f"\n✅ Updated Preferences Successfully")
        updated = response.json()
        print(f"   • New Optimize for: {updated.get('optimize_for', 'N/A')}")
        return True
    else:
        print(f"❌ Error updating preferences: {response.text}")
        return False

def demo_feedback_learning():
    """Demo feedback learning system"""
    print("\n📝 DEMO: Feedback Learning System")
    print("-" * 40)
    
    # Simulate user feedback on recommendations
    feedback_examples = [
        {
            "recommendation_id": "demo_rec_1",
            "action": "accepted",
            "context_hash": "S001:SKU101:B001",
            "action_type": "markdown",
            "action_parameters": {"discount": 0.3},
            "risk_score": 85.5
        },
        {
            "recommendation_id": "demo_rec_2", 
            "action": "rejected",
            "context_hash": "S002:SKU102:B002",
            "action_type": "transfer",
            "action_parameters": {"to_store": "S003"},
            "risk_score": 72.1
        }
    ]
    
    for feedback in feedback_examples:
        response = requests.post(f"{API_BASE}/ai/feedback", json=feedback)
        if response.status_code == 200:
            result = response.json()
            action_status = "✅ Accepted" if feedback["action"] == "accepted" else "❌ Rejected"
            print(f"{action_status} {feedback['action_type'].title()} recommendation (ID: {result.get('feedback_id')})")
        else:
            print(f"❌ Error recording feedback: {response.text}")
            return False
    
    print("📈 Learning system updated with user preferences")
    return True

def demo_news_events():
    """Demo news events management"""
    print("\n📰 DEMO: News Events Management")
    print("-" * 40)
    
    # Get existing events
    response = requests.get(f"{API_BASE}/news/")
    if response.status_code == 200:
        events = response.json()
        print(f"📅 Current Events: {len(events)} events")
        for event in events[:2]:
            print(f"   • {event.get('event_type', 'Unknown')}: {event.get('description', 'No description')}")
    
    # Create a new event
    new_event = {
        "event_date": date.today().isoformat(),
        "event_type": "demo_event",
        "description": "Demo: Holiday season demand spike",
        "impact_stores": ["S001", "S002"],
        "impact_skus": ["SKU101", "SKU102"],
        "score_modifier": -0.1
    }
    
    response = requests.post(f"{API_BASE}/news/", json=new_event)
    if response.status_code == 200:
        created = response.json()
        print(f"✅ Created new event (ID: {created.get('id')})")
        print(f"   Impact: {created.get('score_modifier')} score adjustment")
        return True
    else:
        print(f"❌ Error creating event: {response.text}")
        return False

def main():
    """Run complete demo"""
    print("🚀 AI OPERATIONS COPILOT - COMPLETE FEATURE DEMO")
    print("=" * 60)
    print("Backend: http://localhost:8000")
    print("Frontend: http://localhost:8501")
    print("=" * 60)
    
    demos = [
        ("AI Insights Generation", demo_ai_insights),
        ("AI Chat Interface", demo_ai_chat),
        ("User Preferences", demo_preferences),
        ("Feedback Learning", demo_feedback_learning),
        ("News Events", demo_news_events)
    ]
    
    results = []
    for demo_name, demo_func in demos:
        try:
            success = demo_func()
            results.append((demo_name, success))
        except Exception as e:
            print(f"❌ {demo_name} failed: {e}")
            results.append((demo_name, False))
    
    print("\n" + "=" * 60)
    print("📊 DEMO RESULTS:")
    for demo_name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{demo_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nOverall: {passed}/{total} demos successful")
    
    if passed == total:
        print("\n🎉 ALL FEATURES WORKING PERFECTLY!")
        print("\n🌐 Ready for testing:")
        print("   • Open http://localhost:8501 in your browser")
        print("   • Upload the sample CSV file")
        print("   • Click '🤖 Get AI Insights' to see action popup")
        print("   • Click '💬 AI Chat' to chat with the assistant")
        print("   • Test all interactive features!")
    else:
        print(f"\n⚠️ {total - passed} features need attention")

if __name__ == "__main__":
    main()