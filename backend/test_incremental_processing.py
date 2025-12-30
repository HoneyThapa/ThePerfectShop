#!/usr/bin/env python3
"""
Test script for incremental processing optimizations.

This script tests the incremental processing functionality without requiring
a database connection, using mock data and in-memory operations.
"""

import sys
import os
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
import logging

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_feature_optimization_logic():
    """Test the feature calculation optimization logic."""
    print("Testing feature calculation optimization...")
    
    try:
        from app.services.features import optimize_feature_calculation_performance
        
        # Mock the database session and queries
        with patch('app.services.features.SessionLocal') as mock_session_local:
            mock_db = Mock()
            mock_session_local.return_value = mock_db
            
            # Test case 1: Small dataset
            mock_db.query.return_value.filter.return_value.scalar.return_value = 100
            result = optimize_feature_calculation_performance(date.today())
            
            assert result['strategy'] == 'full_processing'
            assert result['total_store_skus'] == 100
            print("✓ Small dataset optimization test passed")
            
            # Test case 2: Medium dataset
            mock_db.query.return_value.filter.return_value.scalar.return_value = 7000
            result = optimize_feature_calculation_performance(date.today())
            
            assert result['strategy'] == 'incremental_processing'
            assert result['batch_size'] == 1000
            print("✓ Medium dataset optimization test passed")
            
            # Test case 3: Large dataset
            mock_db.query.return_value.filter.return_value.scalar.return_value = 15000
            result = optimize_feature_calculation_performance(date.today())
            
            assert result['strategy'] == 'batch_processing'
            assert result['batch_size'] == 500
            print("✓ Large dataset optimization test passed")
            
    except Exception as e:
        print(f"✗ Feature optimization test failed: {e}")
        return False
    
    return True

def test_risk_scoring_optimization_logic():
    """Test the risk scoring optimization logic."""
    print("Testing risk scoring optimization...")
    
    try:
        from app.services.scoring import optimize_risk_calculation_performance
        
        # Mock the database session and queries
        with patch('app.services.scoring.SessionLocal') as mock_session_local:
            mock_db = Mock()
            mock_session_local.return_value = mock_db
            
            # Test case 1: Small dataset
            mock_db.query.return_value.filter.return_value.scalar.return_value = 5000
            result = optimize_risk_calculation_performance(date.today())
            
            assert result['strategy'] == 'full_processing'
            print("✓ Small risk dataset optimization test passed")
            
            # Test case 2: Medium dataset
            mock_db.query.return_value.filter.return_value.scalar.return_value = 25000
            result = optimize_risk_calculation_performance(date.today())
            
            assert result['strategy'] == 'batch_processing'
            assert result['chunk_size'] == 1000
            print("✓ Medium risk dataset optimization test passed")
            
            # Test case 3: Large dataset
            mock_db.query.return_value.filter.return_value.scalar.return_value = 75000
            result = optimize_risk_calculation_performance(date.today())
            
            assert result['strategy'] == 'chunked_processing'
            assert result['chunk_size'] == 500
            print("✓ Large risk dataset optimization test passed")
            
    except Exception as e:
        print(f"✗ Risk scoring optimization test failed: {e}")
        return False
    
    return True

def test_action_generation_optimization_logic():
    """Test the action generation optimization logic."""
    print("Testing action generation optimization...")
    
    try:
        from app.services.actions import optimize_action_generation_performance
        
        # Mock the database session and queries
        with patch('app.services.actions.SessionLocal') as mock_session_local:
            mock_db = Mock()
            mock_session_local.return_value = mock_db
            
            # Test case 1: Small dataset
            mock_db.query.return_value.filter.return_value.scalar.return_value = 2000
            result = optimize_action_generation_performance(date.today())
            
            assert result['strategy'] == 'full_processing'
            print("✓ Small action dataset optimization test passed")
            
            # Test case 2: Medium dataset
            mock_db.query.return_value.filter.return_value.scalar.return_value = 7000
            result = optimize_action_generation_performance(date.today())
            
            assert result['strategy'] == 'batch_incremental'
            assert result['chunk_size'] == 200
            print("✓ Medium action dataset optimization test passed")
            
            # Test case 3: Large dataset
            mock_db.query.return_value.filter.return_value.scalar.return_value = 15000
            result = optimize_action_generation_performance(date.today())
            
            assert result['strategy'] == 'chunked_incremental'
            assert result['chunk_size'] == 100
            print("✓ Large action dataset optimization test passed")
            
    except Exception as e:
        print(f"✗ Action generation optimization test failed: {e}")
        return False
    
    return True

def test_change_detection_logic():
    """Test the change detection logic."""
    print("Testing change detection logic...")
    
    try:
        from app.services.features import detect_sales_data_changes
        from app.services.scoring import detect_inventory_changes
        from app.services.actions import detect_risk_score_changes
        
        # Mock the database session and models
        with patch('app.services.features.SessionLocal') as mock_session_local, \
             patch('app.services.scoring.SessionLocal') as mock_session_local2, \
             patch('app.services.actions.SessionLocal') as mock_session_local3:
            
            mock_db = Mock()
            mock_session_local.return_value = mock_db
            mock_session_local2.return_value = mock_db
            mock_session_local3.return_value = mock_db
            
            # Test case 1: No previous processing (should return all data)
            mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
            mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [
                ('store1', 'sku1'), ('store2', 'sku2')
            ]
            
            result = detect_sales_data_changes(date.today())
            assert len(result) == 2
            print("✓ No previous processing test passed")
            
            # Test case 2: Previous processing exists (should detect changes)
            mock_last_processing = Mock()
            mock_last_processing.last_processed_at.date.return_value = date.today() - timedelta(days=1)
            mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_last_processing
            
            result = detect_sales_data_changes(date.today())
            assert isinstance(result, set)
            print("✓ Previous processing exists test passed")
            
    except Exception as e:
        print(f"✗ Change detection test failed: {e}")
        return False
    
    return True

def test_batch_processing_logic():
    """Test the batch processing logic for large datasets."""
    print("Testing batch processing logic...")
    
    try:
        # Test the batch processing helper functions
        from app.services.features import _calculate_features_for_store_sku
        from app.services.scoring import _calculate_risk_for_batch
        
        # Mock pandas DataFrame for feature calculation
        import pandas as pd
        
        # Create mock sales data
        mock_sales_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
            'units_sold': [10, 15, 8, 12, 20, 5, 18, 14, 9, 16] * 3
        })
        
        # Test feature calculation
        feature_result = _calculate_features_for_store_sku('store1', 'sku1', mock_sales_data, date.today())
        
        assert feature_result.store_id == 'store1'
        assert feature_result.sku_id == 'sku1'
        assert feature_result.v30 > 0
        print("✓ Feature calculation batch processing test passed")
        
        # Test risk calculation with mock inventory batch
        from app.db.models import InventoryBatch
        mock_inventory = InventoryBatch(
            snapshot_date=date.today(),
            store_id='store1',
            sku_id='sku1',
            batch_id='batch1',
            expiry_date=date.today() + timedelta(days=10),
            on_hand_qty=100
        )
        
        mock_features = {('store1', 'sku1'): 5.0}
        mock_costs = {('store1', 'sku1'): 10.0}
        
        risk_result = _calculate_risk_for_batch(mock_inventory, mock_features, mock_costs, date.today())
        
        assert risk_result.store_id == 'store1'
        assert risk_result.sku_id == 'sku1'
        assert risk_result.risk_score >= 0
        print("✓ Risk calculation batch processing test passed")
        
    except Exception as e:
        print(f"✗ Batch processing test failed: {e}")
        return False
    
    return True

def main():
    """Run all incremental processing tests."""
    print("=" * 60)
    print("INCREMENTAL PROCESSING OPTIMIZATION TESTS")
    print("=" * 60)
    
    tests = [
        test_feature_optimization_logic,
        test_risk_scoring_optimization_logic,
        test_action_generation_optimization_logic,
        test_change_detection_logic,
        test_batch_processing_logic
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"\n{test.__name__.replace('_', ' ').title()}:")
        print("-" * 40)
        
        try:
            if test():
                passed += 1
                print("✓ Test passed")
            else:
                failed += 1
                print("✗ Test failed")
        except Exception as e:
            failed += 1
            print(f"✗ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All incremental processing optimization tests passed!")
        print("\nKey optimizations implemented:")
        print("• Change detection to avoid unnecessary recomputation")
        print("• Batch processing for large datasets")
        print("• Incremental processing for modified data only")
        print("• Performance optimization strategies based on data volume")
        print("• Memory-efficient data loading and processing")
        return True
    else:
        print(f"❌ {failed} tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)