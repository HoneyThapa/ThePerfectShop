from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import logging
from typing import Dict, Any
from datetime import datetime
from app.services.ingestion import (
    normalize_columns,
    load_sales,
    load_inventory,
    load_purchases,
)
from app.services.validation import validate_dataframe, ValidationReport
from app.db.session import SessionLocal
from app.db.models import RawUpload

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


def generate_data_health_report(df: pd.DataFrame, file_type: str, validation_report: ValidationReport) -> Dict[str, Any]:
    """Generate comprehensive data health report"""
    health_report = {
        "file_type": file_type,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "data_quality": {
            "completeness": {},
            "validity": {},
            "consistency": {}
        },
        "issues_summary": {
            "critical_errors": len(validation_report.errors),
            "warnings": len(validation_report.warnings),
            "data_quality_score": 0
        }
    }
    
    # Completeness analysis
    for col in df.columns:
        missing_count = df[col].isna().sum()
        completeness_pct = ((len(df) - missing_count) / len(df)) * 100
        health_report["data_quality"]["completeness"][col] = {
            "missing_count": int(missing_count),
            "completeness_percentage": round(completeness_pct, 2)
        }
    
    # Validity analysis for specific columns
    if "expiry_date" in df.columns:
        try:
            parsed_dates = pd.to_datetime(df["expiry_date"], errors='coerce')
            valid_dates = parsed_dates.notna().sum()
            health_report["data_quality"]["validity"]["expiry_date"] = {
                "valid_dates": int(valid_dates),
                "invalid_dates": int(len(df) - valid_dates),
                "validity_percentage": round((valid_dates / len(df)) * 100, 2)
            }
        except Exception:
            health_report["data_quality"]["validity"]["expiry_date"] = {
                "error": "Could not parse dates"
            }
    
    # Check for negative stock levels
    quantity_columns = ["on_hand_qty", "units_sold", "received_qty"]
    for col in quantity_columns:
        if col in df.columns:
            negative_count = (df[col] < 0).sum()
            health_report["data_quality"]["validity"][col] = {
                "negative_values": int(negative_count),
                "validity_percentage": round(((len(df) - negative_count) / len(df)) * 100, 2)
            }
    
    # Consistency analysis
    duplicate_count = df.duplicated().sum()
    health_report["data_quality"]["consistency"]["duplicates"] = {
        "duplicate_rows": int(duplicate_count),
        "uniqueness_percentage": round(((len(df) - duplicate_count) / len(df)) * 100, 2)
    }
    
    # Calculate overall data quality score
    scores = []
    
    # Completeness score (average completeness across all columns)
    completeness_scores = [item["completeness_percentage"] for item in health_report["data_quality"]["completeness"].values()]
    if completeness_scores:
        scores.append(sum(completeness_scores) / len(completeness_scores))
    
    # Validity score
    validity_scores = []
    for col_data in health_report["data_quality"]["validity"].values():
        if isinstance(col_data, dict) and "validity_percentage" in col_data:
            validity_scores.append(col_data["validity_percentage"])
    if validity_scores:
        scores.append(sum(validity_scores) / len(validity_scores))
    
    # Consistency score
    if "uniqueness_percentage" in health_report["data_quality"]["consistency"]["duplicates"]:
        scores.append(health_report["data_quality"]["consistency"]["duplicates"]["uniqueness_percentage"])
    
    # Overall score
    if scores:
        health_report["issues_summary"]["data_quality_score"] = round(sum(scores) / len(scores), 2)
    
    return health_report


def store_upload_record(file_name: str, file_type: str, status: str, validation_report: ValidationReport = None) -> int:
    """Store upload record in database"""
    db = SessionLocal()
    try:
        upload_record = RawUpload(
            file_name=file_name,
            file_type=file_type.upper(),
            status=status.upper(),
            error_report=validation_report.to_dict() if validation_report else None
        )
        db.add(upload_record)
        db.commit()
        db.refresh(upload_record)
        return upload_record.id
    finally:
        db.close()


def handle_upload_error(error: Exception, file_name: str) -> JSONResponse:
    """Centralized error handling for upload operations"""
    logger.error(f"Upload error for file {file_name}: {str(error)}")
    
    # Store failed upload record
    try:
        store_upload_record(file_name, "UNKNOWN", "FAILED")
    except Exception as db_error:
        logger.error(f"Failed to store upload record: {str(db_error)}")
    
    if isinstance(error, pd.errors.EmptyDataError):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_type": "empty_file",
                "message": "The uploaded file is empty or contains no data"
            }
        )
    elif isinstance(error, pd.errors.ParserError):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_type": "parse_error",
                "message": f"Failed to parse file: {str(error)}"
            }
        )
    elif isinstance(error, UnicodeDecodeError):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_type": "encoding_error",
                "message": "File encoding is not supported. Please use UTF-8 encoding."
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_type": "internal_error",
                "message": "An unexpected error occurred while processing the file"
            }
        )


@router.post("/upload")
def upload_file(file: UploadFile) -> Dict[str, Any]:
    """Enhanced upload endpoint with comprehensive error handling and data health reporting"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Validate file extension
    allowed_extensions = ['.csv', '.xlsx', '.xls']
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Load the file
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file.file)
        else:
            df = pd.read_csv(file.file)
        
        # Check if dataframe is empty
        if df.empty:
            store_upload_record(file.filename, "UNKNOWN", "FAILED")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error_type": "empty_data",
                    "message": "The uploaded file contains no data rows"
                }
            )
        
        # Normalize column names
        df = normalize_columns(df)
        
        # Determine file type and validate
        if "units_sold" in df.columns:
            # Sales data
            file_type = "sales"
            required_columns = ["date", "store_id", "sku_id", "units_sold"]
            validation_report = validate_dataframe(df, required_columns)
            
            if not validation_report.is_valid:
                upload_id = store_upload_record(file.filename, file_type, "VALIDATION_FAILED", validation_report)
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "validation_failed",
                        "file_type": file_type,
                        "upload_id": upload_id,
                        "validation_report": validation_report.to_dict(),
                        "data_health_report": generate_data_health_report(df, file_type, validation_report)
                    }
                )
            
            load_sales(df)
            upload_id = store_upload_record(file.filename, file_type, "COMPLETED", validation_report)
            
            response = {
                "status": "success",
                "file_type": file_type,
                "upload_id": upload_id,
                "message": "Sales data loaded successfully",
                "rows_processed": len(df),
                "data_health_report": generate_data_health_report(df, file_type, validation_report)
            }
            
            if validation_report.warnings:
                response["warnings"] = validation_report.to_dict()["warnings"]
            
            return response
            
        elif "expiry_date" in df.columns:
            # Inventory data
            file_type = "inventory"
            required_columns = ["snapshot_date", "store_id", "sku_id", "batch_id", "expiry_date", "on_hand_qty"]
            validation_report = validate_dataframe(df, required_columns)
            
            if not validation_report.is_valid:
                upload_id = store_upload_record(file.filename, file_type, "VALIDATION_FAILED", validation_report)
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "validation_failed",
                        "file_type": file_type,
                        "upload_id": upload_id,
                        "validation_report": validation_report.to_dict(),
                        "data_health_report": generate_data_health_report(df, file_type, validation_report)
                    }
                )
            
            load_inventory(df)
            upload_id = store_upload_record(file.filename, file_type, "COMPLETED", validation_report)
            
            response = {
                "status": "success",
                "file_type": file_type,
                "upload_id": upload_id,
                "message": "Inventory data loaded successfully",
                "rows_processed": len(df),
                "data_health_report": generate_data_health_report(df, file_type, validation_report)
            }
            
            if validation_report.warnings:
                response["warnings"] = validation_report.to_dict()["warnings"]
            
            return response
            
        elif "unit_cost" in df.columns:
            # Purchase data
            file_type = "purchases"
            required_columns = ["received_date", "store_id", "sku_id", "batch_id", "received_qty", "unit_cost"]
            validation_report = validate_dataframe(df, required_columns)
            
            if not validation_report.is_valid:
                upload_id = store_upload_record(file.filename, file_type, "VALIDATION_FAILED", validation_report)
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "validation_failed",
                        "file_type": file_type,
                        "upload_id": upload_id,
                        "validation_report": validation_report.to_dict(),
                        "data_health_report": generate_data_health_report(df, file_type, validation_report)
                    }
                )
            
            load_purchases(df)
            upload_id = store_upload_record(file.filename, file_type, "COMPLETED", validation_report)
            
            response = {
                "status": "success",
                "file_type": file_type,
                "upload_id": upload_id,
                "message": "Purchase data loaded successfully",
                "rows_processed": len(df),
                "data_health_report": generate_data_health_report(df, file_type, validation_report)
            }
            
            if validation_report.warnings:
                response["warnings"] = validation_report.to_dict()["warnings"]
            
            return response
        else:
            store_upload_record(file.filename, "UNKNOWN", "FAILED")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error_type": "unknown_format",
                    "message": "Unable to determine file type. Expected columns not found.",
                    "available_columns": list(df.columns),
                    "expected_columns": {
                        "sales": ["date", "store_id", "sku_id", "units_sold"],
                        "inventory": ["snapshot_date", "store_id", "sku_id", "batch_id", "expiry_date", "on_hand_qty"],
                        "purchases": ["received_date", "store_id", "sku_id", "batch_id", "received_qty", "unit_cost"]
                    }
                }
            )
            
    except Exception as e:
        return handle_upload_error(e, file.filename)


@router.get("/upload/{upload_id}/health")
def get_data_health_report(upload_id: int):
    """Get data health report for a specific upload"""
    db = SessionLocal()
    try:
        upload_record = db.query(RawUpload).filter(RawUpload.id == upload_id).first()
        if not upload_record:
            raise HTTPException(status_code=404, detail="Upload record not found")
        
        return {
            "upload_id": upload_id,
            "file_name": upload_record.file_name,
            "file_type": upload_record.file_type,
            "status": upload_record.status,
            "uploaded_at": upload_record.uploaded_at,
            "validation_report": upload_record.error_report
        }
    finally:
        db.close()


@router.get("/uploads")
def list_uploads():
    """List all upload records"""
    db = SessionLocal()
    try:
        uploads = db.query(RawUpload).order_by(RawUpload.uploaded_at.desc()).limit(50).all()
        return {
            "uploads": [
                {
                    "upload_id": upload.id,
                    "file_name": upload.file_name,
                    "file_type": upload.file_type,
                    "status": upload.status,
                    "uploaded_at": upload.uploaded_at
                }
                for upload in uploads
            ]
        }
    finally:
        db.close()
