from typing import Dict, List, Any
import pandas as pd


class ValidationError:
    def __init__(self, column: str, error_type: str, message: str, line_numbers: List[int] = None):
        self.column = column
        self.error_type = error_type
        self.message = message
        self.line_numbers = line_numbers or []


class ValidationReport:
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.is_valid = True
        
    def add_error(self, error: ValidationError):
        self.errors.append(error)
        self.is_valid = False
        
    def add_warning(self, warning: ValidationError):
        self.warnings.append(warning)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": [
                {
                    "column": e.column,
                    "error_type": e.error_type,
                    "message": e.message,
                    "line_numbers": e.line_numbers
                }
                for e in self.errors
            ],
            "warnings": [
                {
                    "column": w.column,
                    "error_type": w.error_type,
                    "message": w.message,
                    "line_numbers": w.line_numbers
                }
                for w in self.warnings
            ]
        }


def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> ValidationReport:
    """Enhanced validation with detailed error reporting"""
    report = ValidationReport()
    
    # Check for missing required columns
    for col in required_columns:
        if col not in df.columns:
            report.add_error(ValidationError(
                column=col,
                error_type="missing_column",
                message=f"Required column '{col}' is missing"
            ))
    
    # Check for negative quantities
    if "on_hand_qty" in df.columns:
        negative_mask = df["on_hand_qty"] < 0
        if negative_mask.any():
            negative_lines = df.index[negative_mask].tolist()
            report.add_error(ValidationError(
                column="on_hand_qty",
                error_type="negative_values",
                message=f"Found {negative_mask.sum()} negative values in on_hand_qty",
                line_numbers=[i + 2 for i in negative_lines]  # +2 for header and 0-indexing
            ))
    
    # Check for missing expiry dates
    if "expiry_date" in df.columns:
        missing_mask = df["expiry_date"].isna()
        if missing_mask.any():
            missing_lines = df.index[missing_mask].tolist()
            report.add_error(ValidationError(
                column="expiry_date",
                error_type="missing_values",
                message=f"Found {missing_mask.sum()} missing expiry dates",
                line_numbers=[i + 2 for i in missing_lines]
            ))
    
    # Check for duplicate rows
    if len(df) > 0:
        duplicate_mask = df.duplicated()
        if duplicate_mask.any():
            duplicate_lines = df.index[duplicate_mask].tolist()
            report.add_warning(ValidationError(
                column="all",
                error_type="duplicate_rows",
                message=f"Found {duplicate_mask.sum()} duplicate rows",
                line_numbers=[i + 2 for i in duplicate_lines]
            ))
    
    # Check for invalid date formats (if date columns exist)
    date_columns = ["date", "snapshot_date", "expiry_date", "received_date"]
    for col in date_columns:
        if col in df.columns:
            try:
                pd.to_datetime(df[col], errors='coerce')
            except Exception as e:
                report.add_error(ValidationError(
                    column=col,
                    error_type="invalid_date_format",
                    message=f"Invalid date format in column '{col}': {str(e)}"
                ))
    
    return report


def validate_dataframe_legacy(df, required_columns):
    """Legacy function for backward compatibility"""
    report = validate_dataframe(df, required_columns)
    
    # Convert to old format
    errors = {}
    for error in report.errors:
        if error.error_type == "missing_column":
            errors[error.column] = "missing"
        elif error.error_type == "negative_values":
            errors[error.column] = error.message
        elif error.error_type == "missing_values":
            errors[error.column] = error.message
    
    return errors
