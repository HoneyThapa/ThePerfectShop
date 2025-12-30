#!/usr/bin/env python3
"""
Test insights without Groq client
"""

def test_context_and_actions():
    """Test just context building and action generation"""
    print("🔍 Testing context and actions without Groq...")
    
    try:
        from app.services.context_builder import ContextBuilder
        from app.services.action_engine import generate_actions_for_risks
        from datetime import date
        
        # Build context
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
        
        print(f"✅ Context built: {len(context['risk_items'])} risk items")
        
        # Generate actions
        actions = generate_actions_for_risks(
            context["risk_items"], 
            context["user_preferences"]
        )
        
        print(f"✅ Actions generated: {len(actions)} actions")
        
        # Create response without Groq
        response = {
            "executive_summary": "Test analysis without AI",
            "prioritized_actions": actions[:10],
            "key_metrics": context["key_metrics"],
            "confidence_scores": {
                "data_quality": 0.8,
                "recommendation_confidence": 0.7
            },
            "assumptions": ["Test mode - no AI analysis"],
            "context_summary": {
                "total_risk_items": len(context["risk_items"]),
                "snapshot_date": context["snapshot_date"],
                "filters_applied": context["filters"]
            }
        }
        
        print("✅ Response created successfully!")
        print(f"Executive summary: {response['executive_summary']}")
        print(f"Actions: {len(response['prioritized_actions'])}")
        
        context_builder.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Without Groq")
    print("=" * 30)
    
    success = test_context_and_actions()
    
    if success:
        print("\n✅ All components work without Groq!")
    else:
        print("\n❌ Issue found in components!")