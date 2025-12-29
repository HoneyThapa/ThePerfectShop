"""
Tests for features service functionality
"""
import pytest
import pandas as pd
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.services.features import build_features, get_store_sku_velocity, get_all_features


class TestFeaturesService:
    """Test suite for features service"""
    
    def test_build_features_with_valid_data(self):
        """Test building features with valid sales data"""
        
        # Mock data
        mock_df = pd.DataFrame({
            'date': [date(2024, 1, 1) + timedelta(days=i) for i in range(30)],
            'store_id': ['S001'] * 30,
            'sku_id': ['SKU001'] * 30,
            'units_sold': [10] * 30  # Consistent sales
        })
        
        snapshot_date = date(2024, 1, 30)
        
        with patch('app.services.features.pd.read_sql', return_value=mock_df), \
             patch('app.services.features.SessionLocal') as mock_session:
            
            mock_db = Mock()
            mock_session.return_value = mock_db
            
            result = build_features(snapshot_date)
            
            # Verify result
            assert result['status'] == 'success'
            assert result['features_created'] == 1
            assert result['errors'] == 0
            
            # Verify database operations
            mock_db.merge.assert_called()
            mock_db.commit.assert_called_once()
    
    def test_build_features_with_no_data(self):
        """Test building features when no sales data exists"""
        
        empty_df = pd.DataFrame(columns=['date', 'store_id', 'sku_id', 'units_sold'])
        snapshot_date = date(2024, 1, 30)
        
        with patch('app.services.features.pd.read_sql', return_value=empty_df):
            result = build_features(snapshot_date)
            
            assert result['status'] == 'no_data'
            assert result['features_created'] == 0
    
    def test_build_features_velocity_calculations(self):
        """Test that velocity calculations are correct"""
        
        # Create test data with known pattern
        dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(30)]
        mock_df = pd.DataFrame({
            'date': dates,
            'store_id': ['S001'] * 30,
            'sku_id': ['SKU001'] * 30,
            'units_sold': [i + 1 for i in range(30)]  # 1, 2, 3, ..., 30
        })
        
        snapshot_date = date(2024, 1, 30)
        
        with patch('app.services.features.pd.read_sql', return_value=mock_df), \
             patch('app.services.features.SessionLocal') as mock_session:
            
            mock_db = Mock()
            mock_session.return_value = mock_db
            
            # Capture the feature record that gets created
            created_features = []
            def capture_merge(feature):
                created_features.append(feature)
            mock_db.merge.side_effect = capture_merge
            
            build_features(snapshot_date)
            
            # Verify calculations
            assert len(created_features) == 1
            feature = created_features[0]
            
            # v30 should be average of 1-30 = 15.5
            assert abs(feature.v30 - 15.5) < 0.1
            
            # v14 should be average of last 14 days (17-30) = 23.5
            assert abs(feature.v14 - 23.5) < 0.1
            
            # v7 should be average of last 7 days (24-30) = 27
            assert abs(feature.v7 - 27.0) < 0.1
            
            # Volatility should be > 0 for this increasing pattern
            assert feature.volatility > 0
    
    def test_get_store_sku_velocity_found(self):
        """Test getting velocity for existing store-SKU combination"""
        
        mock_feature = Mock()
        mock_feature.store_id = "S001"
        mock_feature.sku_id = "SKU001"
        mock_feature.date = date(2024, 1, 30)
        mock_feature.v7 = 10.0
        mock_feature.v14 = 12.0
        mock_feature.v30 = 15.0
        mock_feature.volatility = 2.5
        
        with patch('app.services.features.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db
            
            # Mock the query chain properly
            mock_query = Mock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.first.return_value = mock_feature
            
            result = get_store_sku_velocity("S001", "SKU001")
            
            assert result is not None
            assert result['store_id'] == "S001"
            assert result['sku_id'] == "SKU001"
            assert result['v14'] == 12.0
    
    def test_get_store_sku_velocity_not_found(self):
        """Test getting velocity for non-existing store-SKU combination"""
        
        with patch('app.services.features.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db
            
            # Mock the query chain properly
            mock_query = Mock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.first.return_value = None
            
            result = get_store_sku_velocity("S999", "SKU999")
            
            assert result is None
    
    def test_get_all_features_with_filters(self):
        """Test getting all features with filtering"""
        
        mock_features = [
            Mock(store_id="S001", sku_id="SKU001", date=date(2024, 1, 30), 
                 v7=10.0, v14=12.0, v30=15.0, volatility=2.5),
            Mock(store_id="S002", sku_id="SKU001", date=date(2024, 1, 30),
                 v7=8.0, v14=10.0, v30=12.0, volatility=1.8)
        ]
        
        with patch('app.services.features.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db
            
            # Mock the query chain
            mock_query = Mock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.all.return_value = mock_features
            
            results = get_all_features(store_id="S001")
            
            assert len(results) == 2
            assert all('store_id' in result for result in results)
    
    def test_build_features_error_handling(self):
        """Test error handling in build_features"""
        
        snapshot_date = date(2024, 1, 30)
        
        # Test database error
        with patch('app.services.features.pd.read_sql', side_effect=Exception("Database connection failed")):
            with pytest.raises(Exception, match="Database connection failed"):
                build_features(snapshot_date)
    
    def test_velocity_calculation_edge_cases(self):
        """Test velocity calculations with edge cases"""
        
        # Test with insufficient data (less than 7 days)
        mock_df = pd.DataFrame({
            'date': [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)],
            'store_id': ['S001'] * 3,
            'sku_id': ['SKU001'] * 3,
            'units_sold': [5, 10, 15]
        })
        
        snapshot_date = date(2024, 1, 3)
        
        with patch('app.services.features.pd.read_sql', return_value=mock_df), \
             patch('app.services.features.SessionLocal') as mock_session:
            
            mock_db = Mock()
            mock_session.return_value = mock_db
            
            created_features = []
            def capture_merge(feature):
                created_features.append(feature)
            mock_db.merge.side_effect = capture_merge
            
            build_features(snapshot_date)
            
            # With insufficient data, v7 should fall back to overall mean
            feature = created_features[0]
            assert abs(feature.v7 - 10.0) < 0.1  # Mean of [5, 10, 15]
            assert abs(feature.v14 - 10.0) < 0.1  # Same fallback
            assert abs(feature.v30 - 10.0) < 0.1  # Overall mean


if __name__ == "__main__":
    pytest.main([__file__, "-v"])