# KPIs Service - simplified for MVP
from datetime import date, datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.db.models import BatchRisk, Action, ActionOutcome
from app.schemas import (
    DashboardMetrics, SavingsPeriod, InventoryHealthMetrics,
    AuditTrailEntry, FinancialImpactSummary, ActionOutcomeDetailResponse
)

@dataclass
class DashboardMetricsData:
    total_at_risk_value: float
    recovered_value: float
    write_off_reduction: float
    inventory_turnover_improvement: float
    cash_freed: float
    actions_completed: int
    actions_pending: int
    roi_percentage: float

@dataclass
class InventoryHealthData:
    total_inventory_value: float
    at_risk_inventory_value: float
    at_risk_percentage: float
    high_risk_batches: int
    medium_risk_batches: int
    low_risk_batches: int
    avg_days_to_expiry: float
    inventory_turnover_rate: float

class KPIService:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_dashboard_metrics(self, as_of_date: Optional[date] = None) -> DashboardMetricsData:
        """Calculate main dashboard KPI metrics"""
        if not as_of_date:
            as_of_date = date.today()
        
        # Get total at-risk value
        total_at_risk_value = (
            self.db.query(func.sum(BatchRisk.at_risk_value))
            .filter(BatchRisk.snapshot_date == as_of_date)
            .scalar()
        ) or 0.0
        total_at_risk_value = float(total_at_risk_value)
        
        # Get recovered value from completed actions
        recovered_value = (
            self.db.query(func.sum(ActionOutcome.recovered_value))
            .join(Action)
            .filter(Action.status == 'DONE')
            .scalar()
        ) or 0.0
        recovered_value = float(recovered_value)
        
        # Count actions
        actions_completed = (
            self.db.query(func.count(Action.action_id))
            .filter(Action.status == 'DONE')
            .scalar()
        ) or 0
        
        actions_pending = (
            self.db.query(func.count(Action.action_id))
            .filter(Action.status.in_(['PROPOSED', 'APPROVED']))
            .scalar()
        ) or 0
        
        # Simplified calculations for MVP
        write_off_reduction = 15.5  # Placeholder
        inventory_turnover_improvement = 8.2  # Placeholder
        cash_freed = float(recovered_value * 0.8)  # Estimate
        roi_percentage = float((recovered_value / max(total_at_risk_value, 1)) * 100)
        
        return DashboardMetricsData(
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
        period_type: str
    ) -> List[SavingsPeriod]:
        """Calculate savings over time periods"""
        periods = []
        
        # Generate date ranges based on period type
        current_date = start_date
        while current_date <= end_date:
            if period_type == 'daily':
                period_end = current_date
                next_date = current_date + timedelta(days=1)
            elif period_type == 'weekly':
                period_end = current_date + timedelta(days=6)
                next_date = current_date + timedelta(days=7)
            else:  # monthly
                if current_date.month == 12:
                    period_end = date(current_date.year + 1, 1, 1) - timedelta(days=1)
                    next_date = date(current_date.year + 1, 1, 1)
                else:
                    period_end = date(current_date.year, current_date.month + 1, 1) - timedelta(days=1)
                    next_date = date(current_date.year, current_date.month + 1, 1)
            
            # Get savings for this period
            period_savings = (
                self.db.query(func.sum(ActionOutcome.recovered_value))
                .join(Action)
                .filter(
                    and_(
                        ActionOutcome.measured_at >= current_date,
                        ActionOutcome.measured_at <= period_end,
                        Action.status == 'DONE'
                    )
                )
                .scalar()
            ) or 0.0
            
            # Get action count for this period
            actions_count = (
                self.db.query(func.count(Action.action_id))
                .join(ActionOutcome)
                .filter(
                    and_(
                        ActionOutcome.measured_at >= current_date,
                        ActionOutcome.measured_at <= period_end,
                        Action.status == 'DONE'
                    )
                )
                .scalar()
            ) or 0
            
            periods.append(SavingsPeriod(
                period_start=current_date,
                period_end=min(period_end, end_date),
                total_savings=float(period_savings),
                actions_count=actions_count,
                transfer_savings=float(period_savings * 0.4),  # Simplified breakdown
                markdown_savings=float(period_savings * 0.5),
                liquidation_savings=float(period_savings * 0.1)
            ))
            
            current_date = next_date
            if current_date > end_date:
                break
        
        return periods
    
    def calculate_inventory_health_metrics(self, as_of_date: Optional[date] = None) -> InventoryHealthData:
        """Calculate inventory health metrics"""
        if not as_of_date:
            as_of_date = date.today()
        
        # Get total inventory value (simplified - using at-risk value as proxy)
        total_inventory_value = (
            self.db.query(func.sum(BatchRisk.at_risk_value))
            .filter(BatchRisk.snapshot_date == as_of_date)
            .scalar()
        ) or 0.0
        
        at_risk_inventory_value = total_inventory_value  # Simplified
        at_risk_percentage = 100.0 if total_inventory_value > 0 else 0.0
        
        # Risk distribution
        high_risk_batches = (
            self.db.query(func.count(BatchRisk.batch_id))
            .filter(
                BatchRisk.snapshot_date == as_of_date,
                BatchRisk.risk_score >= 70
            )
            .scalar()
        ) or 0
        
        medium_risk_batches = (
            self.db.query(func.count(BatchRisk.batch_id))
            .filter(
                BatchRisk.snapshot_date == as_of_date,
                BatchRisk.risk_score >= 30,
                BatchRisk.risk_score < 70
            )
            .scalar()
        ) or 0
        
        low_risk_batches = (
            self.db.query(func.count(BatchRisk.batch_id))
            .filter(
                BatchRisk.snapshot_date == as_of_date,
                BatchRisk.risk_score < 30
            )
            .scalar()
        ) or 0
        
        # Average days to expiry
        avg_days_to_expiry = (
            self.db.query(func.avg(BatchRisk.days_to_expiry))
            .filter(BatchRisk.snapshot_date == as_of_date)
            .scalar()
        ) or 0.0
        
        return InventoryHealthData(
            total_inventory_value=float(total_inventory_value),
            at_risk_inventory_value=float(at_risk_inventory_value),
            at_risk_percentage=at_risk_percentage,
            high_risk_batches=high_risk_batches,
            medium_risk_batches=medium_risk_batches,
            low_risk_batches=low_risk_batches,
            avg_days_to_expiry=float(avg_days_to_expiry),
            inventory_turnover_rate=5.2  # Placeholder
        )

class AuditTrailService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_action_audit_trail(self, action_id: int) -> List[AuditTrailEntry]:
        """Get audit trail for an action - simplified for MVP"""
        action = self.db.query(Action).filter(Action.action_id == action_id).first()
        if not action:
            return []
        
        # Simplified audit trail
        trail = [
            AuditTrailEntry(
                timestamp=action.created_at,
                action="created",
                user_id="system",
                details={"action_type": action.action_type, "expected_savings": float(action.expected_savings)}
            )
        ]
        
        if action.status != 'PROPOSED':
            trail.append(AuditTrailEntry(
                timestamp=action.created_at + timedelta(hours=1),  # Placeholder
                action="status_changed",
                user_id="manager",
                details={"new_status": action.status}
            ))
        
        return trail
    
    def record_action_outcome(
        self, 
        action_id: int, 
        recovered_value: float, 
        cleared_units: int, 
        notes: str,
        user_id: Optional[str] = None
    ) -> ActionOutcome:
        """Record outcome for an action"""
        # Check if action exists and is approved
        action = self.db.query(Action).filter(Action.action_id == action_id).first()
        if not action:
            raise ValueError(f"Action {action_id} not found")
        
        if action.status != 'APPROVED':
            raise ValueError(f"Action {action_id} must be approved before recording outcome")
        
        # Create outcome record
        outcome = ActionOutcome(
            action_id=action_id,
            recovered_value=recovered_value,
            cleared_units=cleared_units,
            notes=notes
        )
        
        self.db.add(outcome)
        
        # Update action status
        action.status = 'DONE'
        
        self.db.commit()
        return outcome
    
    def get_financial_impact_summary(
        self, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> FinancialImpactSummary:
        """Get financial impact summary"""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        # Get total recovered value in period
        total_recovered = (
            self.db.query(func.sum(ActionOutcome.recovered_value))
            .join(Action)
            .filter(
                ActionOutcome.measured_at >= start_date,
                ActionOutcome.measured_at <= end_date
            )
            .scalar()
        ) or 0.0
        
        # Get total at-risk value (simplified)
        total_at_risk = (
            self.db.query(func.sum(Action.expected_savings))
            .filter(
                Action.created_at >= start_date,
                Action.created_at <= end_date
            )
            .scalar()
        ) or 0.0
        
        roi_percentage = (total_recovered / max(total_at_risk, 1)) * 100
        
        return FinancialImpactSummary(
            total_at_risk_value=float(total_at_risk),
            total_recovered_value=float(total_recovered),
            total_writeoff_prevented=float(total_recovered * 0.8),  # Estimate
            roi_percentage=roi_percentage,
            period_start=start_date,
            period_end=end_date
        )
    
    def get_action_outcome_data(self, action_id: int) -> Optional[ActionOutcomeDetailResponse]:
        """Get detailed outcome data for an action"""
        action = self.db.query(Action).filter(Action.action_id == action_id).first()
        if not action:
            return None
        
        outcome = self.db.query(ActionOutcome).filter(ActionOutcome.action_id == action_id).first()
        
        outcome_variance = None
        if outcome:
            outcome_variance = float(outcome.recovered_value) - float(action.expected_savings)
        
        return ActionOutcomeDetailResponse(
            action_id=action_id,
            action_type=action.action_type,
            expected_savings=float(action.expected_savings),
            actual_recovered_value=float(outcome.recovered_value) if outcome else None,
            actual_cleared_units=outcome.cleared_units if outcome else None,
            outcome_variance=outcome_variance,
            measured_at=outcome.measured_at if outcome else None
        )