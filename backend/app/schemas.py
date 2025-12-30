# Pydantic schemas for API responses
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class StandardResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

class DashboardMetrics(BaseModel):
    as_of_date: date
    total_at_risk_value: float
    recovered_value: float
    write_off_reduction: float
    inventory_turnover_improvement: float
    cash_freed: float
    actions_completed: int
    actions_pending: int
    roi_percentage: float

class SavingsPeriod(BaseModel):
    period_start: date
    period_end: date
    total_savings: float
    actions_count: int
    transfer_savings: float
    markdown_savings: float
    liquidation_savings: float

class SavingsTrackingResponse(BaseModel):
    period_type: str
    start_date: date
    end_date: date
    summary: Dict[str, float]
    periods: List[SavingsPeriod]

class InventoryHealthMetrics(BaseModel):
    as_of_date: date
    total_inventory_value: float
    at_risk_inventory_value: float
    at_risk_percentage: float
    risk_distribution: Dict[str, int]
    avg_days_to_expiry: float
    inventory_turnover_rate: float

class AuditTrailEntry(BaseModel):
    timestamp: datetime
    action: str
    user_id: Optional[str]
    details: Dict[str, Any]

class AuditTrailResponse(BaseModel):
    action_id: int
    audit_trail: List[AuditTrailEntry]

class FinancialImpactSummary(BaseModel):
    total_at_risk_value: float
    total_recovered_value: float
    total_writeoff_prevented: float
    roi_percentage: float
    period_start: date
    period_end: date

class ActionOutcomeDetailResponse(BaseModel):
    action_id: int
    action_type: str
    expected_savings: float
    actual_recovered_value: Optional[float]
    actual_cleared_units: Optional[int]
    outcome_variance: Optional[float]
    measured_at: Optional[datetime]