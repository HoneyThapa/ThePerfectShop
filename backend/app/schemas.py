"""
Pydantic schemas for API request/response validation and serialization.

This module defines all the data models used for API validation,
ensuring type safety and proper serialization across the application.
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum


# Enums for validation
class ActionType(str, Enum):
    TRANSFER = "TRANSFER"
    MARKDOWN = "MARKDOWN"
    LIQUIDATE = "LIQUIDATE"


class ActionStatus(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    DONE = "DONE"
    REJECTED = "REJECTED"


class FileType(str, Enum):
    CSV = "csv"
    EXCEL = "xlsx"


class UploadStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Upload Schemas
class UploadResponse(BaseModel):
    """Response for file upload operations."""
    status: str = Field(..., description="Upload status", example="success")
    message: str = Field(..., description="Human-readable status message", example="Sales data loaded successfully")
    upload_id: Optional[int] = Field(None, description="Unique upload identifier", example=123)
    errors: Optional[List[str]] = Field(None, description="List of validation errors", example=["Missing required column: sku_id"])
    warnings: Optional[List[str]] = Field(None, description="List of data quality warnings", example=["10 records have missing selling_price"])
    records_processed: Optional[int] = Field(None, description="Number of records successfully processed", example=950)
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Sales data loaded successfully",
                "upload_id": 123,
                "errors": None,
                "warnings": ["5 records have missing selling_price values"],
                "records_processed": 995
            }
        }


class UploadStatusResponse(BaseModel):
    """Response for upload status check."""
    upload_id: int
    status: UploadStatus
    file_name: str
    file_type: str
    uploaded_at: datetime
    error_report: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class DataHealthReport(BaseModel):
    """Data health metrics for uploaded files."""
    total_records: int
    valid_records: int
    invalid_records: int
    missing_values: Dict[str, int]
    data_quality_score: float
    column_mapping: Dict[str, str]
    date_range: Optional[Dict[str, date]] = None


# Risk Analysis Schemas
class BatchRiskResponse(BaseModel):
    """Response model for batch risk data."""
    snapshot_date: date = Field(..., description="Date of risk analysis", example="2024-01-15")
    store_id: str = Field(..., description="Store identifier", example="STORE001")
    sku_id: str = Field(..., description="SKU identifier", example="SKU123")
    batch_id: str = Field(..., description="Batch identifier", example="BATCH001")
    days_to_expiry: int = Field(..., description="Days until batch expires", example=30)
    expected_sales_to_expiry: float = Field(..., description="Predicted units to sell before expiry", example=45.5)
    at_risk_units: int = Field(..., description="Units likely to expire unsold", example=25)
    at_risk_value: float = Field(..., description="Financial value at risk", example=625.00)
    risk_score: float = Field(..., description="Risk score (0-100, higher = more risk)", example=85.2)
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "snapshot_date": "2024-01-15",
                "store_id": "STORE001",
                "sku_id": "SKU123",
                "batch_id": "BATCH001",
                "days_to_expiry": 30,
                "expected_sales_to_expiry": 45.5,
                "at_risk_units": 25,
                "at_risk_value": 625.00,
                "risk_score": 85.2
            }
        }


class RiskSummaryResponse(BaseModel):
    """Summary of risk analysis by store/category."""
    store_id: Optional[str] = None
    category: Optional[str] = None
    total_batches: int
    high_risk_batches: int
    medium_risk_batches: int
    low_risk_batches: int
    total_at_risk_value: float
    avg_risk_score: float


class RiskRefreshRequest(BaseModel):
    """Request to refresh risk calculations."""
    snapshot_date: date
    force_recalculation: bool = False


# Action Schemas
class ActionGenerateRequest(BaseModel):
    """Request to generate action recommendations."""
    snapshot_date: date
    min_risk_score: float = Field(default=50.0, ge=0, le=100)
    include_transfers: bool = True
    include_markdowns: bool = True
    include_liquidations: bool = True
    max_recommendations: int = Field(default=1000, gt=0, le=10000)


class ActionResponse(BaseModel):
    """Response model for action data."""
    action_id: int = Field(..., description="Unique action identifier", example=1001)
    action_type: ActionType = Field(..., description="Type of recommended action", example="TRANSFER")
    from_store: str = Field(..., description="Source store for the action", example="STORE001")
    to_store: Optional[str] = Field(None, description="Destination store (for transfers)", example="STORE005")
    sku_id: str = Field(..., description="SKU identifier", example="SKU123")
    batch_id: str = Field(..., description="Batch identifier", example="BATCH001")
    qty: int = Field(..., gt=0, description="Quantity to act upon", example=25)
    discount_pct: Optional[float] = Field(None, ge=0, le=100, description="Discount percentage (for markdowns)", example=15.0)
    expected_savings: float = Field(..., ge=0, description="Expected financial savings", example=312.50)
    status: ActionStatus = Field(..., description="Current action status", example="PROPOSED")
    created_at: datetime = Field(..., description="Action creation timestamp", example="2024-01-15T10:30:00Z")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "action_id": 1001,
                "action_type": "TRANSFER",
                "from_store": "STORE001",
                "to_store": "STORE005",
                "sku_id": "SKU123",
                "batch_id": "BATCH001",
                "qty": 25,
                "discount_pct": None,
                "expected_savings": 312.50,
                "status": "PROPOSED",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class ActionApprovalRequest(BaseModel):
    """Request to approve or reject an action."""
    approved: bool
    notes: Optional[str] = Field(None, max_length=1000)


class ActionCompletionRequest(BaseModel):
    """Request to mark an action as completed."""
    recovered_value: float = Field(ge=0)
    cleared_units: int = Field(ge=0)
    notes: Optional[str] = Field(None, max_length=1000)


class ActionOutcomeResponse(BaseModel):
    """Response model for action outcome data."""
    action_id: int
    recovered_value: float
    cleared_units: int
    notes: Optional[str] = None
    measured_at: datetime
    
    class Config:
        from_attributes = True


class ActionDetailResponse(BaseModel):
    """Detailed response for a specific action."""
    action_id: int
    action_type: ActionType
    from_store: str
    to_store: Optional[str] = None
    sku_id: str
    batch_id: str
    qty: int
    discount_pct: Optional[float] = None
    expected_savings: float
    status: ActionStatus
    created_at: datetime
    outcome: Optional[ActionOutcomeResponse] = None
    
    class Config:
        from_attributes = True


# KPI Schemas
class DashboardMetrics(BaseModel):
    """Main dashboard KPI metrics."""
    as_of_date: date = Field(..., description="Date for metrics calculation", example="2024-01-15")
    total_at_risk_value: float = Field(..., description="Total inventory value at risk of expiry", example=125000.00)
    recovered_value: float = Field(..., description="Actual savings from completed actions", example=45000.00)
    write_off_reduction: float = Field(..., description="Percentage reduction in write-offs", example=15.5)
    inventory_turnover_improvement: float = Field(..., description="Percentage improvement in turnover", example=8.2)
    cash_freed: float = Field(..., description="Working capital released through optimization", example=38000.00)
    actions_completed: int = Field(..., description="Number of completed actions", example=156)
    actions_pending: int = Field(..., description="Number of pending actions", example=23)
    roi_percentage: float = Field(..., description="Return on investment percentage", example=285.7)
    
    class Config:
        schema_extra = {
            "example": {
                "as_of_date": "2024-01-15",
                "total_at_risk_value": 125000.00,
                "recovered_value": 45000.00,
                "write_off_reduction": 15.5,
                "inventory_turnover_improvement": 8.2,
                "cash_freed": 38000.00,
                "actions_completed": 156,
                "actions_pending": 23,
                "roi_percentage": 285.7
            }
        }


class SavingsPeriod(BaseModel):
    """Savings data for a specific time period."""
    period_start: date
    period_end: date
    total_savings: float
    transfer_savings: float
    markdown_savings: float
    liquidation_savings: float
    prevented_writeoffs: float
    actions_count: int


class SavingsTrackingResponse(BaseModel):
    """Response for savings tracking over time."""
    period_type: str
    start_date: date
    end_date: date
    summary: Dict[str, float]
    periods: List[SavingsPeriod]


class InventoryHealthMetrics(BaseModel):
    """Inventory health metrics."""
    as_of_date: date
    total_inventory_value: float
    at_risk_inventory_value: float
    at_risk_percentage: float
    risk_distribution: Dict[str, int]
    avg_days_to_expiry: float
    inventory_turnover_rate: float


class AuditTrailEntry(BaseModel):
    """Single audit trail entry."""
    timestamp: datetime
    event_type: str
    user_id: Optional[str] = None
    details: Dict[str, Any]
    financial_impact: Optional[float] = None


class AuditTrailResponse(BaseModel):
    """Response for action audit trail."""
    action_id: int
    audit_trail: List[AuditTrailEntry]


class FinancialImpactSummary(BaseModel):
    """Financial impact summary."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_recovered_value: float
    total_expected_savings: float
    variance: float
    variance_percentage: float
    actions_analyzed: int
    avg_recovery_rate: float


class ActionOutcomeDetailResponse(BaseModel):
    """Detailed outcome data for a specific action."""
    action_id: int
    action_type: ActionType
    expected_savings: float
    actual_recovered_value: float
    cleared_units: int
    completion_date: datetime
    variance: float
    variance_percentage: float
    notes: Optional[str] = None


# Master Data Schemas
class StoreMasterResponse(BaseModel):
    """Response model for store master data."""
    store_id: str
    city: str
    zone: str
    
    class Config:
        from_attributes = True


class SKUMasterResponse(BaseModel):
    """Response model for SKU master data."""
    sku_id: str
    category: str
    mrp: float
    
    class Config:
        from_attributes = True


# Common Response Schemas
class StandardResponse(BaseModel):
    """Standard API response wrapper."""
    status: str = "success"
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    status: str = "error"
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    status: str = "validation_error"
    message: str
    field_errors: List[Dict[str, str]]


# Validators
class BaseModelWithValidation(BaseModel):
    """Base model with common validation methods."""
    
    @validator('*', pre=True)
    def empty_str_to_none(cls, v):
        """Convert empty strings to None."""
        if v == '':
            return None
        return v


# Request/Response wrappers for consistent API format
def create_success_response(message: str, data: Any = None) -> StandardResponse:
    """Create a standardized success response."""
    return StandardResponse(status="success", message=message, data=data)


def create_error_response(message: str, error_code: str = None, details: Dict[str, Any] = None) -> ErrorResponse:
    """Create a standardized error response."""
    return ErrorResponse(
        status="error", 
        message=message, 
        error_code=error_code, 
        details=details
    )