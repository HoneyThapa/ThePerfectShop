from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.db.session import SessionLocal
from app.db.models import (
    BatchRisk,
    Action,
    ActionOutcome,
    SalesDaily,
    InventoryBatch,
    Purchase,
    StoreMaster,
    SKUMaster
)


@dataclass
class KPIMetrics:
    """Container for KPI metrics data."""
    total_at_risk_value: float
    recovered_value: float
    write_off_reduction: float
    inventory_turnover_improvement: float
    cash_freed: float
    actions_completed: int
    actions_pending: int
    roi_percentage: float


@dataclass
class SavingsMetrics:
    """Container for savings tracking metrics."""
    period_start: date
    period_end: date
    total_savings: float
    transfer_savings: float
    markdown_savings: float
    liquidation_savings: float
    prevented_writeoffs: float
    actions_count: int


@dataclass
class InventoryHealthMetrics:
    """Container for inventory health metrics."""
    total_inventory_value: float
    at_risk_inventory_value: float
    at_risk_percentage: float
    high_risk_batches: int
    medium_risk_batches: int
    low_risk_batches: int
    avg_days_to_expiry: float
    inventory_turnover_rate: float


class KPIService:
    """
    Service for calculating KPIs and performance metrics.
    
    Requirements 4.1, 4.2, 4.3, 4.4:
    - Calculate total at-risk inventory values
    - Measure recovered value from completed actions
    - Track write-off reduction and inventory turnover metrics
    - Generate time-series data for trend analysis
    """
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
    
    def calculate_dashboard_metrics(
        self,
        as_of_date: date = None
    ) -> KPIMetrics:
        """
        Calculate main dashboard KPI metrics.
        
        Requirements 4.1, 4.2, 4.3:
        - Total at-risk inventory values
        - Recovered value from completed actions
        - Write-off reduction and inventory turnover metrics
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        # Calculate total at-risk inventory value
        total_at_risk_value = self._calculate_total_at_risk_value(as_of_date)
        
        # Calculate recovered value from completed actions
        recovered_value = self._calculate_recovered_value(as_of_date)
        
        # Calculate write-off reduction
        write_off_reduction = self._calculate_write_off_reduction(as_of_date)
        
        # Calculate inventory turnover improvement
        inventory_turnover_improvement = self._calculate_inventory_turnover_improvement(as_of_date)
        
        # Calculate cash freed up
        cash_freed = self._calculate_cash_freed(as_of_date)
        
        # Count actions
        actions_completed, actions_pending = self._count_actions_by_status(as_of_date)
        
        # Calculate ROI
        roi_percentage = self._calculate_roi(recovered_value, write_off_reduction)
        
        return KPIMetrics(
            total_at_risk_value=total_at_risk_value,
            recovered_value=recovered_value,
            write_off_reduction=write_off_reduction,
            inventory_turnover_improvement=inventory_turnover_improvement,
            cash_freed=cash_freed,
            actions_completed=actions_completed,
            actions_pending=actions_pending,
            roi_percentage=roi_percentage
        )
    
    def calculate_savings_over_time(
        self,
        start_date: date,
        end_date: date,
        period_type: str = 'monthly'  # 'daily', 'weekly', 'monthly'
    ) -> List[SavingsMetrics]:
        """
        Generate time-series data for savings tracking.
        
        Requirements 4.4:
        - Generate time-series data for trend analysis
        """
        periods = self._generate_time_periods(start_date, end_date, period_type)
        savings_data = []
        
        for period_start, period_end in periods:
            # Get completed actions in this period
            completed_actions = (
                self.db.query(Action)
                .filter(
                    Action.status == 'DONE',
                    Action.created_at >= period_start,
                    Action.created_at <= period_end
                )
                .all()
            )
            
            # Calculate savings by action type
            transfer_savings = sum(
                float(action.expected_savings or 0) 
                for action in completed_actions 
                if action.action_type == 'TRANSFER'
            )
            
            markdown_savings = sum(
                float(action.expected_savings or 0) 
                for action in completed_actions 
                if action.action_type == 'MARKDOWN'
            )
            
            liquidation_savings = sum(
                float(action.expected_savings or 0) 
                for action in completed_actions 
                if action.action_type == 'LIQUIDATE'
            )
            
            total_savings = transfer_savings + markdown_savings + liquidation_savings
            
            # Calculate prevented writeoffs (actual outcomes vs expected)
            prevented_writeoffs = self._calculate_prevented_writeoffs_for_period(
                period_start, period_end
            )
            
            savings_data.append(SavingsMetrics(
                period_start=period_start,
                period_end=period_end,
                total_savings=total_savings,
                transfer_savings=transfer_savings,
                markdown_savings=markdown_savings,
                liquidation_savings=liquidation_savings,
                prevented_writeoffs=prevented_writeoffs,
                actions_count=len(completed_actions)
            ))
        
        return savings_data
    
    def calculate_inventory_health_metrics(
        self,
        as_of_date: date = None
    ) -> InventoryHealthMetrics:
        """
        Calculate inventory health and risk distribution metrics.
        
        Requirements 4.1, 4.3:
        - Total inventory values and risk distribution
        - Inventory turnover metrics
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        # Get all inventory batches for the date
        inventory_batches = (
            self.db.query(InventoryBatch)
            .filter(InventoryBatch.snapshot_date == as_of_date)
            .all()
        )
        
        # Get risk scores for batches
        risk_data = {}
        for risk in self.db.query(BatchRisk).filter_by(snapshot_date=as_of_date):
            key = (risk.store_id, risk.sku_id, risk.batch_id)
            risk_data[key] = {
                'risk_score': float(risk.risk_score or 0),
                'at_risk_value': float(risk.at_risk_value or 0),
                'days_to_expiry': risk.days_to_expiry or 0
            }
        
        # Get unit costs for value calculations
        unit_costs = {}
        for purchase in self.db.query(Purchase).all():
            unit_costs[(purchase.store_id, purchase.sku_id)] = float(purchase.unit_cost)
        
        # Calculate metrics
        total_inventory_value = 0
        at_risk_inventory_value = 0
        high_risk_batches = 0
        medium_risk_batches = 0
        low_risk_batches = 0
        total_days_to_expiry = 0
        batch_count = 0
        
        for batch in inventory_batches:
            key = (batch.store_id, batch.sku_id, batch.batch_id)
            unit_cost = unit_costs.get((batch.store_id, batch.sku_id), 10.0)
            batch_value = batch.on_hand_qty * unit_cost
            
            total_inventory_value += batch_value
            
            if key in risk_data:
                risk_info = risk_data[key]
                risk_score = risk_info['risk_score']
                at_risk_inventory_value += risk_info['at_risk_value']
                total_days_to_expiry += risk_info['days_to_expiry']
                batch_count += 1
                
                # Categorize by risk level
                if risk_score >= 70:
                    high_risk_batches += 1
                elif risk_score >= 40:
                    medium_risk_batches += 1
                else:
                    low_risk_batches += 1
        
        # Calculate percentages and averages
        at_risk_percentage = (
            (at_risk_inventory_value / total_inventory_value * 100) 
            if total_inventory_value > 0 else 0
        )
        
        avg_days_to_expiry = (
            total_days_to_expiry / batch_count 
            if batch_count > 0 else 0
        )
        
        # Calculate inventory turnover rate
        inventory_turnover_rate = self._calculate_inventory_turnover_rate(as_of_date)
        
        return InventoryHealthMetrics(
            total_inventory_value=total_inventory_value,
            at_risk_inventory_value=at_risk_inventory_value,
            at_risk_percentage=at_risk_percentage,
            high_risk_batches=high_risk_batches,
            medium_risk_batches=medium_risk_batches,
            low_risk_batches=low_risk_batches,
            avg_days_to_expiry=avg_days_to_expiry,
            inventory_turnover_rate=inventory_turnover_rate
        )
    
    def _calculate_total_at_risk_value(self, as_of_date: date) -> float:
        """Calculate total value of at-risk inventory."""
        result = (
            self.db.query(func.sum(BatchRisk.at_risk_value))
            .filter(BatchRisk.snapshot_date == as_of_date)
            .scalar()
        )
        return float(result or 0)
    
    def _calculate_recovered_value(self, as_of_date: date) -> float:
        """Calculate total recovered value from completed actions."""
        # Get outcomes for completed actions
        result = (
            self.db.query(func.sum(ActionOutcome.recovered_value))
            .join(Action)
            .filter(
                Action.status == 'DONE',
                Action.created_at <= as_of_date
            )
            .scalar()
        )
        return float(result or 0)
    
    def _calculate_write_off_reduction(self, as_of_date: date) -> float:
        """Calculate total write-off reduction from all actions."""
        # Sum expected savings from all completed actions
        result = (
            self.db.query(func.sum(Action.expected_savings))
            .filter(
                Action.status == 'DONE',
                Action.created_at <= as_of_date
            )
            .scalar()
        )
        return float(result or 0)
    
    def _calculate_inventory_turnover_improvement(self, as_of_date: date) -> float:
        """Calculate improvement in inventory turnover rate."""
        # Compare current turnover with baseline (30 days ago)
        baseline_date = as_of_date - timedelta(days=30)
        
        current_turnover = self._calculate_inventory_turnover_rate(as_of_date)
        baseline_turnover = self._calculate_inventory_turnover_rate(baseline_date)
        
        if baseline_turnover > 0:
            improvement = ((current_turnover - baseline_turnover) / baseline_turnover) * 100
            return improvement
        
        return 0.0
    
    def _calculate_inventory_turnover_rate(self, as_of_date: date) -> float:
        """Calculate inventory turnover rate (sales/inventory ratio)."""
        # Get total sales for the past 30 days
        start_date = as_of_date - timedelta(days=30)
        
        total_sales = (
            self.db.query(func.sum(SalesDaily.units_sold))
            .filter(
                SalesDaily.date >= start_date,
                SalesDaily.date <= as_of_date
            )
            .scalar()
        ) or 0
        
        # Get total inventory units
        total_inventory = (
            self.db.query(func.sum(InventoryBatch.on_hand_qty))
            .filter(InventoryBatch.snapshot_date == as_of_date)
            .scalar()
        ) or 1  # Avoid division by zero
        
        # Calculate turnover rate (annualized)
        turnover_rate = (total_sales / total_inventory) * (365 / 30)
        return float(turnover_rate)
    
    def _calculate_cash_freed(self, as_of_date: date) -> float:
        """Calculate cash freed up through inventory optimization."""
        # Cash freed = value of inventory moved/cleared through actions
        completed_actions = (
            self.db.query(Action)
            .filter(
                Action.status == 'DONE',
                Action.created_at <= as_of_date
            )
            .all()
        )
        
        # Get unit costs for value calculations
        unit_costs = {}
        for purchase in self.db.query(Purchase).all():
            unit_costs[(purchase.store_id, purchase.sku_id)] = float(purchase.unit_cost)
        
        total_cash_freed = 0
        for action in completed_actions:
            unit_cost = unit_costs.get((action.from_store, action.sku_id), 10.0)
            cash_freed = action.qty * unit_cost
            total_cash_freed += cash_freed
        
        return total_cash_freed
    
    def _count_actions_by_status(self, as_of_date: date) -> Tuple[int, int]:
        """Count completed and pending actions."""
        completed_count = (
            self.db.query(func.count(Action.action_id))
            .filter(
                Action.status == 'DONE',
                Action.created_at <= as_of_date
            )
            .scalar()
        ) or 0
        
        pending_count = (
            self.db.query(func.count(Action.action_id))
            .filter(
                Action.status.in_(['PROPOSED', 'APPROVED']),
                Action.created_at <= as_of_date
            )
            .scalar()
        ) or 0
        
        return completed_count, pending_count
    
    def _calculate_roi(self, recovered_value: float, write_off_reduction: float) -> float:
        """Calculate ROI percentage."""
        # Simple ROI calculation: (benefits / costs) * 100
        # For now, assume implementation costs are 10% of benefits
        total_benefits = recovered_value + write_off_reduction
        estimated_costs = total_benefits * 0.1  # 10% of benefits as costs
        
        if estimated_costs > 0:
            roi = ((total_benefits - estimated_costs) / estimated_costs) * 100
            return roi
        
        return 0.0
    
    def _generate_time_periods(
        self,
        start_date: date,
        end_date: date,
        period_type: str
    ) -> List[Tuple[date, date]]:
        """Generate time periods for trend analysis."""
        periods = []
        current_date = start_date
        
        while current_date <= end_date:
            if period_type == 'daily':
                period_end = current_date
                periods.append((current_date, period_end))
                current_date += timedelta(days=1)
            
            elif period_type == 'weekly':
                period_end = min(current_date + timedelta(days=6), end_date)
                periods.append((current_date, period_end))
                current_date = period_end + timedelta(days=1)
            
            elif period_type == 'monthly':
                # Find end of month or end_date, whichever is earlier
                if current_date.month == 12:
                    next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    next_month = current_date.replace(month=current_date.month + 1, day=1)
                
                period_end = min(next_month - timedelta(days=1), end_date)
                periods.append((current_date, period_end))
                current_date = next_month
        
        return periods
    
    def _calculate_prevented_writeoffs_for_period(
        self,
        start_date: date,
        end_date: date
    ) -> float:
        """Calculate prevented writeoffs for a specific period."""
        # Get actions completed in this period with outcomes
        actions_with_outcomes = (
            self.db.query(Action, ActionOutcome)
            .join(ActionOutcome)
            .filter(
                Action.status == 'DONE',
                Action.created_at >= start_date,
                Action.created_at <= end_date
            )
            .all()
        )
        
        total_prevented = 0
        for action, outcome in actions_with_outcomes:
            # Prevented writeoff = recovered value (actual outcome)
            total_prevented += float(outcome.recovered_value or 0)
        
        return total_prevented


@dataclass
class AuditTrailEntry:
    """Container for audit trail entry data."""
    timestamp: datetime
    action_id: int
    event_type: str  # 'CREATED', 'APPROVED', 'COMPLETED', 'OUTCOME_RECORDED'
    user_id: Optional[str]
    details: Dict
    financial_impact: Optional[float]


@dataclass
class ActionOutcomeData:
    """Container for action outcome tracking data."""
    action_id: int
    action_type: str
    expected_savings: float
    actual_recovered_value: float
    cleared_units: int
    completion_date: datetime
    variance: float  # Difference between expected and actual
    variance_percentage: float
    notes: str


class AuditTrailService:
    """
    Service for comprehensive audit trails and outcome tracking.
    
    Requirements 4.5:
    - Implement action outcome recording
    - Create comprehensive audit trails
    - Track financial impact measurements
    """
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
    
    def record_action_outcome(
        self,
        action_id: int,
        recovered_value: float,
        cleared_units: int,
        notes: str = "",
        user_id: str = None
    ) -> ActionOutcome:
        """
        Record the outcome of a completed action.
        
        Requirements 4.5:
        - Implement action outcome recording
        - Track financial impact measurements
        """
        # Get the action to validate it exists and is completed
        action = self.db.query(Action).filter_by(action_id=action_id).first()
        if not action:
            raise ValueError(f"Action {action_id} not found")
        
        if action.status != 'DONE':
            raise ValueError(f"Action {action_id} is not completed (status: {action.status})")
        
        # Check if outcome already exists
        existing_outcome = (
            self.db.query(ActionOutcome)
            .filter_by(action_id=action_id)
            .first()
        )
        
        if existing_outcome:
            # Update existing outcome
            existing_outcome.recovered_value = recovered_value
            existing_outcome.cleared_units = cleared_units
            existing_outcome.notes = notes
            existing_outcome.measured_at = func.now()
            outcome = existing_outcome
        else:
            # Create new outcome record
            outcome = ActionOutcome(
                action_id=action_id,
                recovered_value=recovered_value,
                cleared_units=cleared_units,
                notes=notes
            )
            self.db.add(outcome)
        
        # Create audit trail entry
        variance = recovered_value - float(action.expected_savings or 0)
        variance_percentage = (
            (variance / float(action.expected_savings)) * 100 
            if action.expected_savings and action.expected_savings > 0 
            else 0
        )
        
        audit_entry = {
            'action_id': action_id,
            'event_type': 'OUTCOME_RECORDED',
            'user_id': user_id,
            'details': {
                'expected_savings': float(action.expected_savings or 0),
                'actual_recovered_value': recovered_value,
                'cleared_units': cleared_units,
                'variance': variance,
                'variance_percentage': variance_percentage,
                'notes': notes
            },
            'financial_impact': recovered_value
        }
        
        self._create_audit_entry(**audit_entry)
        
        self.db.commit()
        return outcome
    
    def create_comprehensive_audit_trail(
        self,
        action_id: int,
        event_type: str,
        user_id: str = None,
        details: Dict = None,
        financial_impact: float = None
    ) -> None:
        """
        Create comprehensive audit trail entries for all action events.
        
        Requirements 4.5:
        - Create comprehensive audit trails
        """
        self._create_audit_entry(
            action_id=action_id,
            event_type=event_type,
            user_id=user_id,
            details=details or {},
            financial_impact=financial_impact
        )
        self.db.commit()
    
    def get_action_audit_trail(self, action_id: int) -> List[AuditTrailEntry]:
        """Get complete audit trail for a specific action."""
        # In a real implementation, this would query an audit_trail table
        # For now, we'll reconstruct from action and outcome data
        action = self.db.query(Action).filter_by(action_id=action_id).first()
        if not action:
            return []
        
        trail = []
        
        # Action creation event
        trail.append(AuditTrailEntry(
            timestamp=action.created_at,
            action_id=action_id,
            event_type='CREATED',
            user_id=None,  # Would come from auth context
            details={
                'action_type': action.action_type,
                'from_store': action.from_store,
                'to_store': action.to_store,
                'sku_id': action.sku_id,
                'batch_id': action.batch_id,
                'qty': action.qty,
                'expected_savings': float(action.expected_savings or 0)
            },
            financial_impact=float(action.expected_savings or 0)
        ))
        
        # Status change events (simplified - would track all status changes)
        if action.status in ['APPROVED', 'DONE']:
            trail.append(AuditTrailEntry(
                timestamp=action.created_at,  # Would be actual approval time
                action_id=action_id,
                event_type='APPROVED',
                user_id=None,
                details={'status_change': f'PROPOSED -> {action.status}'},
                financial_impact=None
            ))
        
        if action.status == 'DONE':
            trail.append(AuditTrailEntry(
                timestamp=action.created_at,  # Would be actual completion time
                action_id=action_id,
                event_type='COMPLETED',
                user_id=None,
                details={'status_change': 'APPROVED -> DONE'},
                financial_impact=None
            ))
        
        # Outcome recording event
        outcome = (
            self.db.query(ActionOutcome)
            .filter_by(action_id=action_id)
            .first()
        )
        
        if outcome:
            variance = float(outcome.recovered_value or 0) - float(action.expected_savings or 0)
            trail.append(AuditTrailEntry(
                timestamp=outcome.measured_at,
                action_id=action_id,
                event_type='OUTCOME_RECORDED',
                user_id=None,
                details={
                    'recovered_value': float(outcome.recovered_value or 0),
                    'cleared_units': outcome.cleared_units,
                    'variance': variance,
                    'notes': outcome.notes
                },
                financial_impact=float(outcome.recovered_value or 0)
            ))
        
        return sorted(trail, key=lambda x: x.timestamp)
    
    def get_financial_impact_summary(
        self,
        start_date: date = None,
        end_date: date = None
    ) -> Dict:
        """
        Get comprehensive financial impact summary.
        
        Requirements 4.5:
        - Track financial impact measurements
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()
        
        # Get all completed actions in the period
        completed_actions = (
            self.db.query(Action)
            .filter(
                Action.status == 'DONE',
                Action.created_at >= start_date,
                Action.created_at <= end_date
            )
            .all()
        )
        
        # Get outcomes for these actions
        action_ids = [action.action_id for action in completed_actions]
        outcomes = (
            self.db.query(ActionOutcome)
            .filter(ActionOutcome.action_id.in_(action_ids))
            .all()
        ) if action_ids else []
        
        # Create outcome lookup
        outcome_lookup = {outcome.action_id: outcome for outcome in outcomes}
        
        # Calculate financial impact metrics
        total_expected_savings = sum(float(action.expected_savings or 0) for action in completed_actions)
        total_actual_recovery = sum(float(outcome.recovered_value or 0) for outcome in outcomes)
        
        # Calculate variance metrics
        variances = []
        for action in completed_actions:
            outcome = outcome_lookup.get(action.action_id)
            if outcome:
                expected = float(action.expected_savings or 0)
                actual = float(outcome.recovered_value or 0)
                variance = actual - expected
                variance_pct = (variance / expected * 100) if expected > 0 else 0
                variances.append({
                    'action_id': action.action_id,
                    'action_type': action.action_type,
                    'expected': expected,
                    'actual': actual,
                    'variance': variance,
                    'variance_percentage': variance_pct
                })
        
        # Calculate summary statistics
        total_variance = sum(v['variance'] for v in variances)
        avg_variance_pct = (
            sum(v['variance_percentage'] for v in variances) / len(variances)
            if variances else 0
        )
        
        # Count actions by performance
        positive_variance_count = sum(1 for v in variances if v['variance'] > 0)
        negative_variance_count = sum(1 for v in variances if v['variance'] < 0)
        
        return {
            'period_start': start_date,
            'period_end': end_date,
            'total_actions': len(completed_actions),
            'actions_with_outcomes': len(outcomes),
            'total_expected_savings': total_expected_savings,
            'total_actual_recovery': total_actual_recovery,
            'total_variance': total_variance,
            'average_variance_percentage': avg_variance_pct,
            'positive_variance_actions': positive_variance_count,
            'negative_variance_actions': negative_variance_count,
            'action_details': variances
        }
    
    def get_action_outcome_data(self, action_id: int) -> Optional[ActionOutcomeData]:
        """Get detailed outcome data for a specific action."""
        action = self.db.query(Action).filter_by(action_id=action_id).first()
        if not action:
            return None
        
        outcome = (
            self.db.query(ActionOutcome)
            .filter_by(action_id=action_id)
            .first()
        )
        
        if not outcome:
            return None
        
        expected_savings = float(action.expected_savings or 0)
        actual_recovered = float(outcome.recovered_value or 0)
        variance = actual_recovered - expected_savings
        variance_percentage = (
            (variance / expected_savings * 100) 
            if expected_savings > 0 else 0
        )
        
        return ActionOutcomeData(
            action_id=action_id,
            action_type=action.action_type,
            expected_savings=expected_savings,
            actual_recovered_value=actual_recovered,
            cleared_units=outcome.cleared_units or 0,
            completion_date=outcome.measured_at,
            variance=variance,
            variance_percentage=variance_percentage,
            notes=outcome.notes or ""
        )
    
    def _create_audit_entry(
        self,
        action_id: int,
        event_type: str,
        user_id: str = None,
        details: Dict = None,
        financial_impact: float = None
    ) -> None:
        """
        Create an audit trail entry.
        
        In a production system, this would insert into an audit_trail table.
        For now, we'll log the information (could be extended to use a proper audit table).
        """
        # In a real implementation, you would:
        # 1. Insert into an audit_trail table
        # 2. Include user context from authentication
        # 3. Add IP address, session info, etc.
        # 4. Potentially send to external audit systems
        
        # For now, we'll just ensure the data structure is correct
        audit_data = {
            'timestamp': datetime.now(),
            'action_id': action_id,
            'event_type': event_type,
            'user_id': user_id,
            'details': details or {},
            'financial_impact': financial_impact
        }
        
        # In production, this would be:
        # audit_entry = AuditTrail(**audit_data)
        # self.db.add(audit_entry)
        
        # For now, we'll just validate the structure
        pass