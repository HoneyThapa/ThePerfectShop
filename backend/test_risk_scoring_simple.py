"""
Simple test of risk scoring functionality without database dependencies
"""
from datetime import date
from app.services.scoring import calculate_risk_score

def test_risk_scoring_algorithm():
    """Test the core risk scoring algorithm"""
    
    print("=== Testing Risk Scoring Algorithm ===\n")
    
    # Test 1: High risk scenario
    print("1. Testing high risk scenario...")
    score_high = calculate_risk_score(
        at_risk_units=80,      # 80% at risk
        on_hand_qty=100,
        days_to_expiry=3,      # Expiring soon
        at_risk_value=800.0    # High value
    )
    print(f"   High risk score: {score_high}")
    assert score_high > 70, f"Expected high risk (>70), got {score_high}"
    print("   ✅ High risk calculation: PASS")
    
    # Test 2: Low risk scenario
    print("\n2. Testing low risk scenario...")
    score_low = calculate_risk_score(
        at_risk_units=5,       # 5% at risk
        on_hand_qty=100,
        days_to_expiry=45,     # Long time to expiry
        at_risk_value=50.0     # Low value
    )
    print(f"   Low risk score: {score_low}")
    assert score_low < 30, f"Expected low risk (<30), got {score_low}"
    print("   ✅ Low risk calculation: PASS")
    
    # Test 3: Urgency factor
    print("\n3. Testing urgency factor...")
    score_urgent = calculate_risk_score(50, 100, 2, 500)   # 2 days
    score_normal = calculate_risk_score(50, 100, 20, 500)  # 20 days
    
    print(f"   Urgent (2 days): {score_urgent}")
    print(f"   Normal (20 days): {score_normal}")
    assert score_urgent > score_normal, "Urgent items should have higher risk"
    print("   ✅ Urgency factor: PASS")
    
    # Test 4: At-risk ratio impact
    print("\n4. Testing at-risk ratio impact...")
    score_high_ratio = calculate_risk_score(90, 100, 15, 900)  # 90% at risk
    score_low_ratio = calculate_risk_score(10, 100, 15, 100)   # 10% at risk
    
    print(f"   High ratio (90%): {score_high_ratio}")
    print(f"   Low ratio (10%): {score_low_ratio}")
    assert score_high_ratio > score_low_ratio, "Higher at-risk ratio should increase risk"
    print("   ✅ At-risk ratio impact: PASS")
    
    # Test 5: Edge cases
    print("\n5. Testing edge cases...")
    
    # Zero inventory
    score_zero = calculate_risk_score(0, 0, 10, 0)
    assert score_zero == 0.0, "Zero inventory should have zero risk"
    
    # Expired items
    score_expired = calculate_risk_score(50, 100, -1, 500)
    assert score_expired >= 95.0, "Expired items should have very high risk"
    
    # No at-risk units
    score_no_risk = calculate_risk_score(0, 100, 10, 0)
    assert score_no_risk == 0.0, "No at-risk units should have zero risk"
    
    print("   ✅ Edge cases: PASS")
    
    # Test 6: Algorithm specification compliance
    print("\n6. Testing specification compliance...")
    print("   Specification: higher at_risk_units and shorter days_to_expiry → higher risk")
    
    # Create test matrix
    scenarios = [
        (90, 100, 3, 900, "High units, short expiry"),
        (10, 100, 3, 100, "Low units, short expiry"),
        (90, 100, 30, 900, "High units, long expiry"),
        (10, 100, 30, 100, "Low units, long expiry")
    ]
    
    scores = []
    for at_risk, total, days, value, desc in scenarios:
        score = calculate_risk_score(at_risk, total, days, value)
        scores.append((score, desc))
        print(f"   {desc}: {score}")
    
    # Verify ordering
    assert scores[0][0] > scores[1][0], "Higher at-risk units should increase risk"
    assert scores[0][0] > scores[2][0], "Shorter expiry should increase risk"
    assert scores[1][0] > scores[3][0], "Shorter expiry should increase risk (low units)"
    assert scores[2][0] > scores[3][0], "Higher at-risk units should increase risk (long expiry)"
    
    print("   ✅ Specification compliance: PASS")
    
    print("\n=== Summary ===")
    print("✅ Risk scoring algorithm: COMPLETE and CORRECT")
    print("   - High/low risk scenarios: Working")
    print("   - Urgency factor: Working")
    print("   - At-risk ratio impact: Working")
    print("   - Edge cases: Handled")
    print("   - Specification compliance: Verified")
    
    return True

if __name__ == "__main__":
    test_risk_scoring_algorithm()