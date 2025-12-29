from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import logging
from typing import Dict, Any
from app.services.ingestion import (
    normalize_columns,
    load_sales,
    load_inventory,
    load_purchases,
)
from app.services.validation import validate_dataframe, ValidationReport

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


def handle_upload_error(error: Exception, file_name: str) -> JSONResponse:
    """Centralized error handling for upload operations"""
    logger.error(f"Upload error for file {file_name}: {str(error)}")
    
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
    """Enhanced upload endpoint with comprehensive error handling"""
    
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
            required_columns = ["date", "store_id", "sku_id", "units_sold"]
            validation_report = validate_dataframe(df, required_columns)
            
            if not validation_report.is_valid:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "validation_failed",
                        "file_type": "sales",
                        "validation_report": validation_report.to_dict()
                    }
                )
            
            load_sales(df)
            response = {
                "status": "success",
                "file_type": "sales",
                "message": "Sales data loaded successfully",
                "rows_processed": len(df)
            }
            
            if validation_report.warnings:
                response["warnings"] = validation_report.to_dict()["warnings"]
            
            return response
            
        elif "expiry_date" in df.columns:
            # Inventory data
            required_columns = ["snapshot_date", "store_id", "sku_id", "batch_id", "expiry_date"]
            validation_report = validate_dataframe(df, required_columns)
            
            if not validation_report.is_valid:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "validation_failed",
                        "file_type": "inventory",
                        "validation_report": validation_report.to_dict()
                    }
                )
            
            load_inventory(df)
            response = {
                "status": "success",
                "file_type": "inventory",
                "message": "Inventory data loaded successfully",
                "rows_processed": len(df)
            }
            
            if validation_report.warnings:
                response["warnings"] = validation_report.to_dict()["warnings"]
            
            return response
            
        elif "unit_cost" in df.columns:
            # Purchase data
            required_columns = ["received_date", "store_id", "sku_id", "batch_id", "received_qty", "unit_cost"]
            validation_report = validate_dataframe(df, required_columns)
            
            if not validation_report.is_valid:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "validation_failed",
                        "file_type": "purchases",
                        "validation_report": validation_report.to_dict()
                    }
                )
            
            load_purchases(df)
            response = {
                "status": "success",
                "file_type": "purchases",
                "message": "Purchase data loaded successfully",
                "rows_processed": len(df)
            }
            
            if validation_report.warnings:
                response["warnings"] = validation_report.to_dict()["warnings"]
            
            return response
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error_type": "unknown_format",
                    "message": "Unable to determine file type. Expected columns not found.",
                    "available_columns": list(df.columns),
                    "expected_columns": {
                        "sales": ["date", "store_id", "sku_id", "units_sold"],
                        "inventory": ["snapshot_date", "store_id", "sku_id", "batch_id", "expiry_date"],
                        "purchases": ["received_date", "store_id", "sku_id", "batch_id", "received_qty", "unit_cost"]
                    }
                }
            )
            
    except Exception as e:
        return handle_upload_error(e, file.filename)
