"""
Property-based tests for ExpiryShield backend KPI calculations.

Feature: expiryshield-backend
Property 4: Metrics Calculation Accuracy
"""

import pytest
import pandas as pd
from datetime import date, datetime, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.kpis import KPIService, AuditTrailService
from app.db.models import (
    Base, BatchRisk, Action, ActionOutcome, SalesDaily, InventoryBatch, 
    Purchase, StoreMaster, SKUMaster, FeatureStoreSKU
)


class TestMetricsCalculationAccuracy:
    """
    Feature: expiryshield-backend, Property 4: Metrics Calculation Accuracy
    
    For any set of inventory and action data, KPI calculations should always 
    produce accurate at-risk values, measure savings correctly, track all 
    required metrics, and maintain complete audit trails.
    
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    @st.composite
    def kpi_test_scenario(draw):
        """Generate comprehensive test scenario for KPI calculations."""
        # Generate base date
        base_date = draw(st.dates(min_value=date(2024, 1, 1), max_value=date(2024, 6, 1)))
        
        # Generate stores
        num_stores = draw(st.integers(min_value=2, max_value=4))
        store_ids = [f"ST{i:03d}" for i in range(1, num_stores + 1)]
        
        # Generate SKUs
        num_skus = draw(st.integers(min_value=2, max_value=4))
        sku_ids = [f"SKU{i:04d}" for i in range(1, num_skus + 1)]
        
        # Generate stores master data
        stores = []
        for store_id in store_ids:
            stores.append({
                'store_id': store_id,
                'city': f"City{store_id[-1]}",
                'zone': f"Zone{store_id[-1]}"
            })
        
        # Generate SKUs master data
        skus = []
        categories = ['food', 'beverage', 'personal_care', 'household']
        for sku_id in sku_ids:
            skus.append({
                'sku_id': sku_id,
                'category': draw(st.sampled_from(categories)),
                'mrp': draw(st.floats(min_value=10.0, max_value=100.0))
            })
        
        # Generate batch risk data (reduced size)
        batch_risks = []
        used_batch_keys = set()
        for i in range(draw(st.integers(min_value=2, max_value=4))):
            store_id = draw(st.sampled_from(store_ids))
            sku_id = draw(st.sampled_from(sku_ids))
            
            # Ensure unique batch ID for this store-sku combination
            batch_id = f"B{1000 + i}"  # Use sequential IDs to avoid duplicates
            
            at_risk_units = draw(st.integers(min_value=10, max_value=50))
            # Calculate at_risk_value based on a reasonable unit cost (5-15)
            unit_cost = draw(st.floats(min_value=5.0, max_value=15.0))
            at_risk_value = at_risk_units * unit_cost
            
            batch_key = (base_date, store_id, sku_id, batch_id)
            if batch_key not in used_batch_keys:
                used_batch_keys.add(batch_key)
                batch_risks.append({
                    'snapshot_date': base_date,
                    'store_id': store_id,
                    'sku_id': sku_id,
                    'batch_id': batch_id,
                    'days_to_expiry': draw(st.integers(min_value=1, max_value=60)),
                    'expected_sales_to_expiry': draw(st.floats(min_value=0.0, max_value=float(at_risk_units))),
                    'at_risk_units': at_risk_units,
                    'at_risk_value': at_risk_value,
                    'risk_score': draw(st.floats(min_value=0.0, max_value=100.0))
                })
        
        # Generate inventory batches (ensure unique keys and align with batch_risks)
        inventory_batches = []
        used_inventory_keys = set()
        for i, batch_risk in enumerate(batch_risks):
            inventory_key = (base_date, batch_risk['store_id'], batch_risk['sku_id'], batch_risk['batch_id'])
            if inventory_key not in used_inventory_keys:
                used_inventory_keys.add(inventory_key)
                # Ensure on_hand_qty is at least as much as at_risk_units to make percentage calculation reasonable
                on_hand_qty = batch_risk['at_risk_units'] + draw(st.integers(min_value=0, max_value=100))
                inventory_batches.append({
                    'snapshot_date': base_date,
                    'store_id': batch_risk['store_id'],
                    'sku_id': batch_risk['sku_id'],
                    'batch_id': batch_risk['batch_id'],
                    'expiry_date': base_date + timedelta(days=batch_risk['days_to_expiry']),
                    'on_hand_qty': on_hand_qty
                })
        
        # Generate purchase data for unit costs (ensure unique keys and consistent costs)
        purchases = []
        used_purchase_keys = set()
        for i, batch_risk in enumerate(batch_risks):
            # Use the same unit cost that was used to calculate at_risk_value
            unit_cost = batch_risk['at_risk_value'] / batch_risk['at_risk_units'] if batch_risk['at_risk_units'] > 0 else 10.0
            batch_id = f"PB{i}"  # Unique batch ID for purchases
            purchase_key = (base_date - timedelta(days=1), batch_risk['store_id'], batch_risk['sku_id'], batch_id)
            if purchase_key not in used_purchase_keys:
                used_purchase_keys.add(purchase_key)
                purchases.append({
                    'received_date': base_date - timedelta(days=draw(st.integers(min_value=1, max_value=10))),
                    'store_id': batch_risk['store_id'],
                    'sku_id': batch_risk['sku_id'],
                    'batch_id': batch_id,
                    'received_qty': draw(st.integers(min_value=50, max_value=100)),
                    'unit_cost': unit_cost
                })
        
        # Generate sales data for turnover calculations (reduced history)
        sales_data = []
        for days_back in range(7):  # Only 7 days instead of 30
            sales_date = base_date - timedelta(days=days_back)
            for store_id in store_ids:
                for sku_id in sku_ids:
                    if draw(st.booleans()):  # Not every store-sku has sales every day
                        sales_data.append({
                            'date': sales_date,
                            'store_id': store_id,
                            'sku_id': sku_id,
                            'units_sold': draw(st.integers(min_value=0, max_value=20)),
                            'selling_price': draw(st.floats(min_value=10.0, max_value=50.0))
                        })
        
        # Generate completed actions with outcomes (reduced count)
        actions = []
        action_outcomes = []
        action_types = ['TRANSFER', 'MARKDOWN', 'LIQUIDATE']
        
        for i in range(draw(st.integers(min_value=1, max_value=3))):
            action_id = i + 1
            store_id = draw(st.sampled_from(store_ids))
            sku_id = draw(st.sampled_from(sku_ids))
            expected_savings = draw(st.floats(min_value=100.0, max_value=500.0))
            
            actions.append({
                'action_id': action_id,
                'created_at': base_date - timedelta(days=draw(st.integers(min_value=1, max_value=15))),
                'action_type': draw(st.sampled_from(action_types)),
                'from_store': store_id,
                'to_store': draw(st.sampled_from(store_ids)) if draw(st.booleans()) else None,
                'sku_id': sku_id,
                'batch_id': f"B{draw(st.integers(min_value=1000, max_value=9999))}",
                'qty': draw(st.integers(min_value=10, max_value=100)),
                'discount_pct': draw(st.floats(min_value=10.0, max_value=70.0)) if draw(st.booleans()) else None,
                'expected_savings': expected_savings,
                'status': 'DONE'
            })
            
            # Generate outcome for this action
            recovered_value = expected_savings * draw(st.floats(min_value=0.5, max_value=1.5))  # 50%-150% of expected
            action_outcomes.append({
                'action_id': action_id,
                'measured_at': base_date - timedelta(days=draw(st.integers(min_value=0, max_value=10))),
                'recovered_value': recovered_value,
                'cleared_units': draw(st.integers(min_value=5, max_value=95)),
                'notes': f"Test outcome for action {action_id}"
            })
        
        return {
            'base_date': base_date,
            'stores': stores,
            'skus': skus,
            'batch_risks': batch_risks,
            'inventory_batches': inventory_batches,
            'purchases': purchases,
            'sales_data': sales_data,
            'actions': actions,
            'action_outcomes': action_outcomes
        }
    
    def setup_test_database(self, scenario):
        """Set up an in-memory SQLite database with test data."""
        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:", echo=False)
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Create session
        TestSession = sessionmaker(bind=engine)
        db = TestSession()
        
        # Insert test data
        for store_data in scenario['stores']:
            store = StoreMaster(**store_data)
            db.add(store)
        
        for sku_data in scenario['skus']:
            sku = SKUMaster(**sku_data)
            db.add(sku)
        
        for batch_risk_data in scenario['batch_risks']:
            batch_risk = BatchRisk(**batch_risk_data)
            db.add(batch_risk)
        
        for inventory_data in scenario['inventory_batches']:
            inventory = InventoryBatch(**inventory_data)
            db.add(inventory)
        
        for purchase_data in scenario['purchases']:
            purchase = Purchase(**purchase_data)
            db.add(purchase)
        
        for sales_data in scenario['sales_data']:
            sales = SalesDaily(**sales_data)
            db.add(sales)
        
        for action_data in scenario['actions']:
            action = Action(**action_data)
            db.add(action)
        
        for outcome_data in scenario['action_outcomes']:
            outcome = ActionOutcome(**outcome_data)
            db.add(outcome)
        
        db.commit()
        return db
    
    @given(kpi_test_scenario())
    @settings(max_examples=2, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large], deadline=None)
    def test_at_risk_value_calculation_accuracy(self, scenario):
        """Test that at-risk value calculations are accurate and consistent."""
        db = self.setup_test_database(scenario)
        
        try:
            kpi_service = KPIService(db)
            metrics = kpi_service.calculate_dashboard_metrics(scenario['base_date'])
            
            # Calculate expected at-risk value manually
            expected_at_risk_value = sum(batch['at_risk_value'] for batch in scenario['batch_risks'])
            
            # Property: Calculated at-risk value should match sum of individual batch values
            assert abs(metrics.total_at_risk_value - expected_at_risk_value) < 0.01, \
                f"At-risk value calculation mismatch: {metrics.total_at_risk_value} vs {expected_at_risk_value}"
            
            # Property: At-risk value should be non-negative
            assert metrics.total_at_risk_value >= 0, \
                "At-risk value should never be negative"
            
            # Property: At-risk value should be finite
            assert not (metrics.total_at_risk_value == float('inf') or 
                       metrics.total_at_risk_value != metrics.total_at_risk_value), \
                "At-risk value should be finite"
        
        finally:
            db.close()
    
    @given(kpi_test_scenario())
    @settings(max_examples=2, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
    def test_recovered_value_calculation_accuracy(self, scenario):
        """Test that recovered value calculations are accurate."""
        db = self.setup_test_database(scenario)
        
        try:
            kpi_service = KPIService(db)
            metrics = kpi_service.calculate_dashboard_metrics(scenario['base_date'])
            
            # Calculate expected recovered value manually
            expected_recovered_value = sum(outcome['recovered_value'] for outcome in scenario['action_outcomes'])
            
            # Property: Calculated recovered value should match sum of individual outcomes
            assert abs(metrics.recovered_value - expected_recovered_value) < 0.01, \
                f"Recovered value calculation mismatch: {metrics.recovered_value} vs {expected_recovered_value}"
            
            # Property: Recovered value should be non-negative
            assert metrics.recovered_value >= 0, \
                "Recovered value should never be negative"
            
            # Property: Recovered value should not exceed total expected savings
            total_expected_savings = sum(action['expected_savings'] for action in scenario['actions'])
            # Allow some variance since actual recovery can exceed expectations
            assert metrics.recovered_value <= total_expected_savings * 2, \
                "Recovered value should not be unreasonably high compared to expected savings"
        
        finally:
            db.close()
    
    @given(kpi_test_scenario())
    @settings(max_examples=2, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
    def test_action_counting_accuracy(self, scenario):
        """Test that action counting is accurate."""
        db = self.setup_test_database(scenario)
        
        try:
            kpi_service = KPIService(db)
            metrics = kpi_service.calculate_dashboard_metrics(scenario['base_date'])
            
            # Count actions manually
            completed_actions = [action for action in scenario['actions'] if action['status'] == 'DONE']
            expected_completed_count = len(completed_actions)
            
            # Property: Completed action count should be accurate
            assert metrics.actions_completed == expected_completed_count, \
                f"Completed action count mismatch: {metrics.actions_completed} vs {expected_completed_count}"
            
            # Property: Action counts should be non-negative integers
            assert isinstance(metrics.actions_completed, int) and metrics.actions_completed >= 0, \
                "Completed actions count should be non-negative integer"
            assert isinstance(metrics.actions_pending, int) and metrics.actions_pending >= 0, \
                "Pending actions count should be non-negative integer"
            
            # Property: Total actions should be sum of completed and pending
            # (Note: In this test scenario, we only have completed actions)
            assert metrics.actions_completed + metrics.actions_pending >= expected_completed_count, \
                "Total action count should be at least the number of completed actions"
        
        finally:
            db.close()
    
    @given(kpi_test_scenario())
    @settings(max_examples=2, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large], deadline=None)
    def test_inventory_health_metrics_consistency(self, scenario):
        """Test that inventory health metrics are consistent and logical."""
        db = self.setup_test_database(scenario)
        
        try:
            kpi_service = KPIService(db)
            health_metrics = kpi_service.calculate_inventory_health_metrics(scenario['base_date'])
            
            # Property: Total inventory value should be positive if there's inventory
            if scenario['inventory_batches']:
                assert health_metrics.total_inventory_value > 0, \
                    "Total inventory value should be positive when inventory exists"
            
            # Property: At-risk percentage should be between 0 and 100
            assert 0 <= health_metrics.at_risk_percentage <= 100, \
                f"At-risk percentage should be between 0 and 100, got {health_metrics.at_risk_percentage}"
            
            # Property: At-risk value should not exceed total inventory value
            assert health_metrics.at_risk_inventory_value <= health_metrics.total_inventory_value, \
                "At-risk inventory value should not exceed total inventory value"
            
            # Property: Risk distribution counts should be non-negative
            assert health_metrics.high_risk_batches >= 0, "High risk batch count should be non-negative"
            assert health_metrics.medium_risk_batches >= 0, "Medium risk batch count should be non-negative"
            assert health_metrics.low_risk_batches >= 0, "Low risk batch count should be non-negative"
            
            # Property: Average days to expiry should be reasonable
            if health_metrics.avg_days_to_expiry > 0:
                assert health_metrics.avg_days_to_expiry <= 365, \
                    "Average days to expiry should not exceed one year"
            
            # Property: Inventory turnover rate should be non-negative
            assert health_metrics.inventory_turnover_rate >= 0, \
                "Inventory turnover rate should be non-negative"
        
        finally:
            db.close()
    
    @given(kpi_test_scenario())
    @settings(max_examples=2, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
    def test_savings_time_series_consistency(self, scenario):
        """Test that savings time series data is consistent."""
        db = self.setup_test_database(scenario)
        
        try:
            kpi_service = KPIService(db)
            
            # Test different period types
            start_date = scenario['base_date'] - timedelta(days=30)
            end_date = scenario['base_date']
            
            for period_type in ['daily', 'weekly', 'monthly']:
                savings_data = kpi_service.calculate_savings_over_time(
                    start_date, end_date, period_type
                )
                
                # Property: All periods should have non-negative savings
                for period in savings_data:
                    assert period.total_savings >= 0, \
                        f"Total savings should be non-negative for {period_type} periods"
                    assert period.transfer_savings >= 0, \
                        f"Transfer savings should be non-negative for {period_type} periods"
                    assert period.markdown_savings >= 0, \
                        f"Markdown savings should be non-negative for {period_type} periods"
                    assert period.liquidation_savings >= 0, \
                        f"Liquidation savings should be non-negative for {period_type} periods"
                
                # Property: Total savings should equal sum of individual savings types
                for period in savings_data:
                    calculated_total = (period.transfer_savings + 
                                      period.markdown_savings + 
                                      period.liquidation_savings)
                    assert abs(period.total_savings - calculated_total) < 0.01, \
                        f"Total savings should equal sum of components for {period_type} periods"
                
                # Property: Period dates should be in chronological order
                for i in range(len(savings_data) - 1):
                    assert savings_data[i].period_start <= savings_data[i + 1].period_start, \
                        f"Periods should be in chronological order for {period_type}"
                
                # Property: Period end should be after or equal to period start
                for period in savings_data:
                    assert period.period_end >= period.period_start, \
                        f"Period end should be after start for {period_type} periods"
        
        finally:
            db.close()
    
    @given(kpi_test_scenario())
    @settings(max_examples=2, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
    def test_audit_trail_completeness(self, scenario):
        """Test that audit trails are complete and accurate."""
        db = self.setup_test_database(scenario)
        
        try:
            audit_service = AuditTrailService(db)
            
            # Test audit trail for each action
            for action_data in scenario['actions']:
                action_id = action_data['action_id']
                audit_trail = audit_service.get_action_audit_trail(action_id)
                
                # Property: Every action should have at least one audit entry (creation)
                assert len(audit_trail) >= 1, \
                    f"Action {action_id} should have at least one audit entry"
                
                # Property: Audit entries should be in chronological order
                for i in range(len(audit_trail) - 1):
                    assert audit_trail[i].timestamp <= audit_trail[i + 1].timestamp, \
                        f"Audit entries should be chronological for action {action_id}"
                
                # Property: All audit entries should reference the correct action
                for entry in audit_trail:
                    assert entry.action_id == action_id, \
                        f"Audit entry should reference correct action ID"
                
                # Property: Event types should be valid
                valid_event_types = {'CREATED', 'APPROVED', 'COMPLETED', 'OUTCOME_RECORDED'}
                for entry in audit_trail:
                    assert entry.event_type in valid_event_types, \
                        f"Invalid event type: {entry.event_type}"
        
        finally:
            db.close()
    
    @given(kpi_test_scenario())
    @settings(max_examples=2, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
    def test_financial_impact_accuracy(self, scenario):
        """Test that financial impact calculations are accurate."""
        db = self.setup_test_database(scenario)
        
        try:
            audit_service = AuditTrailService(db)
            
            start_date = scenario['base_date'] - timedelta(days=30)
            end_date = scenario['base_date']
            
            impact_summary = audit_service.get_financial_impact_summary(start_date, end_date)
            
            # Property: Financial impact metrics should be consistent
            assert impact_summary['total_actions'] >= 0, \
                "Total actions count should be non-negative"
            assert impact_summary['actions_with_outcomes'] >= 0, \
                "Actions with outcomes count should be non-negative"
            assert impact_summary['actions_with_outcomes'] <= impact_summary['total_actions'], \
                "Actions with outcomes should not exceed total actions"
            
            # Property: Expected and actual values should be reasonable
            assert impact_summary['total_expected_savings'] >= 0, \
                "Total expected savings should be non-negative"
            assert impact_summary['total_actual_recovery'] >= 0, \
                "Total actual recovery should be non-negative"
            
            # Property: Variance counts should sum correctly
            positive_count = impact_summary['positive_variance_actions']
            negative_count = impact_summary['negative_variance_actions']
            total_with_variance = positive_count + negative_count
            
            assert total_with_variance <= impact_summary['actions_with_outcomes'], \
                "Variance action counts should not exceed actions with outcomes"
            
            # Property: Action details should be consistent with summary
            action_details = impact_summary['action_details']
            if action_details:
                calculated_total_expected = sum(detail['expected'] for detail in action_details)
                calculated_total_actual = sum(detail['actual'] for detail in action_details)
                
                assert abs(calculated_total_expected - impact_summary['total_expected_savings']) < 0.01, \
                    "Action details should sum to summary totals for expected savings"
                assert abs(calculated_total_actual - impact_summary['total_actual_recovery']) < 0.01, \
                    "Action details should sum to summary totals for actual recovery"
        
        finally:
            db.close()
    
    @given(kpi_test_scenario())
    @settings(max_examples=2, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large], deadline=None)
    def test_outcome_recording_accuracy(self, scenario):
        """Test that outcome recording is accurate and maintains data integrity."""
        db = self.setup_test_database(scenario)
        
        try:
            audit_service = AuditTrailService(db)
            
            # Test outcome recording for each action
            for action_data in scenario['actions']:
                action_id = action_data['action_id']
                
                # Get outcome data for this action
                outcome_data = audit_service.get_action_outcome_data(action_id)
                
                if outcome_data:
                    # Property: Outcome data should be consistent with action data
                    assert outcome_data.action_id == action_id, \
                        "Outcome should reference correct action ID"
                    assert outcome_data.action_type == action_data['action_type'], \
                        "Outcome should have correct action type"
                    assert abs(outcome_data.expected_savings - action_data['expected_savings']) < 0.01, \
                        f"Outcome should preserve expected savings: {outcome_data.expected_savings} vs {action_data['expected_savings']}"
                    
                    # Property: Variance calculations should be accurate
                    expected_variance = outcome_data.actual_recovered_value - outcome_data.expected_savings
                    assert abs(outcome_data.variance - expected_variance) < 0.01, \
                        "Variance calculation should be accurate"
                    
                    # Property: Variance percentage should be calculated correctly
                    if outcome_data.expected_savings > 0:
                        expected_variance_pct = (expected_variance / outcome_data.expected_savings) * 100
                        assert abs(outcome_data.variance_percentage - expected_variance_pct) < 0.01, \
                            "Variance percentage calculation should be accurate"
                    
                    # Property: Cleared units should be non-negative
                    assert outcome_data.cleared_units >= 0, \
                        "Cleared units should be non-negative"
                    
                    # Property: Completion date should be reasonable
                    assert outcome_data.completion_date <= datetime.now(), \
                        "Completion date should not be in the future"
        
        finally:
            db.close()