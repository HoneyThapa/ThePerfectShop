"""
Tests for risk scoring functionality
"""
import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.services.scoring import (
    compute_batch_risk, 
    calculate_risk_score, 
    get_unit_costs_with_fallback,
    get_risk_summary
)


class TestRiskScoring:
    """Test suite for risk scoring service"""
    
    def test_calculate_risk_score_high_risk(self):
        """Test risk score calculation for high-risk scenario"""
        
        # High risk: 80% at risk, expiring in 2 days, high value
        risk_score = calculate_risk_score(
            at_risk_units=80,
            on_hand_qty=100,
            days_to_expiry=2,
            at_risk_value=1000.0
        )
        
        # Should be high risk (>70)
        assert risk_score > 70
        assert risk_score <= 100
    
    def test_calculate_risk_score_low_risk(self):
        """Test risk score calculation for low-risk scenario"""
        
        # Low risk: 10% at risk, expiring in 45 days, low value
        risk_score = calculate_risk_score(
            at_risk_units=10,
            on_hand_qty=100,
            days_to_expiry=45,
            at_risk_value=50.0
        )
        
        # Should be low risk (<30)
        assert risk_score < 30
        assert risk_score >= 0
    
    def test_calculate_risk_score_edge_cases(self):
        """Test risk score calculation edge cases"""
        
        # Zero inventory
        risk_score = calculate_risk_score(0, 0, 10, 0)
        assert risk_score == 0.0
        
        # Already expired (negative days)
        risk_score = calculate_risk_score(50, 100, -1, 500)
        assert risk_score >= 95.0  # Should be very high risk for expired items
        
        # No at-risk units
        risk_score = calculate_risk_score(0, 100, 10, 0)
        assert risk_score == 0.0
    
    def test_calculate_risk_score_urgency_factors(self):
        """Test that urgency factor works correctly"""
        
        # Same at-risk ratio, different urgency
        score_urgent = calculate_risk_score(50, 100, 3, 500)  # 3 days
        score_normal = calculate_risk_score(50, 100, 20, 500)  # 20 days
        score_distant = calculate_risk_score(50, 100, 60, 500)  # 60 days
        
        # More urgent should have higher scores
        assert score_urgent > score_normal > score_distant
    
    @patch('app.services.scoring.SessionLocal')
    def test_get_unit_costs_with_fallback(self, mock_session):
        """Test unit cost retrieval with fallback logic"""
        
        # Mock database data
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock specific purchases
        mock_purchases = [
            Mock(store_id="S001", sku_id="SKU001", unit_cost=10.50),
            Mock(store_id="S002", sku_id="SKU001", unit_cost=11.00),
            Mock(store_id="S001", sku_id="SKU002", unit_cost=25.75)
        ]
        mock_db.query.return_value.filter.return_value = mock_purchases
        
        # Mock average costs query
        mock_avg_query = Mock()
        mock_avg_query.filter.return_value.group_by.return_value.all.return_value = [
            ("SKU001", 10.75),  # Average of 10.50 and 11.00
            ("SKU002", 25.75)
        ]
        mock_db.query.return_value = mock_avg_query
        
        specific_costs, avg_costs = get_unit_costs_with_fallback()
        
        # Verify specific costs
        assert ("S001", "SKU001") in specific_costs
        assert specific_costs[("S001", "SKU001")] == 10.50
        
        # Verify average costs
        assert "SKU001" in avg_costs
        assert avg_costs["SKU001"] == 10.75
    
    @patch('app.services.scoring.SessionLocal')
    @patch('app.services.scoring.get_unit_costs_with_fallback')
    def test_compute_batch_risk_success(self, mock_costs, mock_session):
        """Test successful batch risk computation"""
        
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock velocity features
        mock_features = [
            Mock(store_id="S001", sku_id="SKU001", v14=5.0),
            Mock(store_id="S001", sku_id="SKU002", v14=3.0)
        ]
        mock_db.query.return_value.filter_by.return_value = mock_features
        
        # Mock inventory batches
        snapshot_date = date(2024, 1, 30)
        expiry_date = date(2024, 2, 15)  # 16 days to expiry
        
        mock_inventory = [
            Mock(
                store_id="S001", 
                sku_id="SKU001", 
                batch_id="B001",
                expiry_date=expiry_date,
                on_hand_qty=100
            )
        ]
        
        # Setup query chain for inventory
        mock_inventory_query = Mock()
        mock_inventory_query.all.return_value = mock_inventory
        mock_db.query.return_value.filter_by.return_value = mock_inventory_query
        
        # Mock costs
        mock_costs.return_value = ({("S001", "SKU001"): 12.50}, {"SKU001": 12.00})
        
        result = compute_batch_risk(snapshot_date)
        
        # Verify result
        assert result["status"] == "success"
        assert result["batches_processed"] == 1
        assert result["errors"] == 0
        
        # Verify database operations
        mock_db.merge.assert_called()
        mock_db.commit.assert_called()
    
    @patch('app.services.scoring.SessionLocal')
    def test_compute_batch_risk_no_features(self, mock_session):
        """Test batch risk computation when no features exist"""
        
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock empty features
        mock_db.query.return_value.filter_by.return_value = []
        
        result = compute_batch_risk(date(2024, 1, 30))
        
        assert result["status"] == "no_features"
        assert result["batches_processed"] == 0
    
    @patch('app.services.scoring.SessionLocal')
    def test_compute_batch_risk_no_inventory(self, mock_session):
        """Test batch risk computation when no inventory exists"""
        
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock features but no inventory
        mock_features = [Mock(store_id="S001", sku_id="SKU001", v14=5.0)]
        
        # Setup different return values for different queries
        def mock_query_side_effect(model):
            mock_query = Mock()
            if hasattr(model, '__tablename__') and model.__tablename__ == 'features_store_sku':
                mock_query.filter_by.return_value = mock_features
            else:
                mock_query.filter_by.return_value.all.return_value = []
            return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        
        result = compute_batch_risk(date(2024, 1, 30))
        
        assert result["status"] == "no_inventory"
        assert result["batches_processed"] == 0
    
    @patch('app.services.scoring.SessionLocal')
    def test_get_risk_summary(self, mock_session):
        """Test risk summary calculation"""
        
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock risk data
        mock_risks = [
            Mock(risk_score=85.0, at_risk_value=1000.0, at_risk_units=50),
            Mock(risk_score=45.0, at_risk_value=500.0, at_risk_units=25),
            Mock(risk_score=15.0, at_risk_value=100.0, at_risk_units=10)
        ]
        
        mock_db.query.return_value.filter_by.return_value.all.return_value = mock_risks
        
        summary = get_risk_summary(date(2024, 1, 30))
        
        # Verify summary structure
        assert summary["status"] == "success"
        assert summary["total_batches"] == 3
        
        # Verify risk distribution
        assert summary["risk_distribution"]["high_risk"] == 1  # score >= 70
        assert summary["risk_distribution"]["medium_risk"] == 1  # 30 <= score < 70
        assert summary["risk_distribution"]["low_risk"] == 1  # score < 30
        
        # Verify financial impact
        assert summary["financial_impact"]["total_at_risk_value"] == 1600.0
        assert summary["financial_impact"]["total_at_risk_units"] == 85
    
    def test_risk_score_algorithm_specification(self):
        """Test that risk score follows the specification requirements"""
        
        # Test specification: higher at_risk_units and shorter days_to_expiry → higher risk
        
        # Scenario 1: High at-risk units, short expiry
        score1 = calculate_risk_score(90, 100, 3, 900)
        
        # Scenario 2: Low at-risk units, short expiry  
        score2 = calculate_risk_score(10, 100, 3, 100)
        
        # Scenario 3: High at-risk units, long expiry
        score3 = calculate_risk_score(90, 100, 30, 900)
        
        # Scenario 4: Low at-risk units, long expiry
        score4 = calculate_risk_score(10, 100, 30, 100)
        
        # Verify ordering: score1 > score2, score1 > score3, score2 > score4, score3 > score4
        assert score1 > score2, "Higher at-risk units should increase risk"
        assert score1 > score3, "Shorter expiry should increase risk"
        assert score2 > score4, "Shorter expiry should increase risk even with low at-risk units"
        assert score3 > score4, "Higher at-risk units should increase risk even with long expiry"
        
        # All scores should be in valid range
        for score in [score1, score2, score3, score4]:
            assert 0 <= score <= 100, f"Risk score {score} out of range"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])