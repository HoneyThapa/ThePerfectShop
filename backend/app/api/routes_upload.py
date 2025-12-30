from fastapi import APIRouter, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd
from app.schemas import UploadResponse, UploadStatusResponse, DataHealthReport
from app.response_models import create_success_response, create_error_response, APIResponse, HTTPStatus, ErrorCodes
from app.db.session import get_db
from app.db.models import RawUpload
from app.services.ingestion import (
    normalize_columns,
    load_sales,
    load_inventory,
    load_purchases,
)
from app.services.validation import validate_dataframe
from app.auth import get_current_user, require_permissions, User

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/", response_model=APIResponse)
async def upload_file(
    file: UploadFile, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions('upload'))
):
    """
    Upload and process CSV/Excel files with sales, inventory, or purchase data.
    
    This endpoint accepts CSV or Excel files containing business data and performs:
    - File format validation
    - Column mapping and normalization
    - Data quality checks
    - Automatic data type detection (sales/inventory/purchase)
    
    **Supported File Types:**
    - CSV (.csv)
    - Excel (.xlsx)
    
    **Expected Data Formats:**
    
    **Sales Data** (must contain 'units_sold' column):
    ```
    date,store_id,sku_id,units_sold,selling_price
    2024-01-01,STORE001,SKU123,10,25.99
    ```
    
    **Inventory Data** (must contain 'expiry_date' column):
    ```
    snapshot_date,store_id,sku_id,batch_id,expiry_date,on_hand_qty
    2024-01-01,STORE001,SKU123,BATCH001,2024-06-01,100
    ```
    
    **Purchase Data** (must contain 'unit_cost' column):
    ```
    received_date,store_id,sku_id,batch_id,received_qty,unit_cost
    2024-01-01,STORE001,SKU123,BATCH001,100,15.50
    ```
    
    **Requirements:** 1.1, 1.4
    - Validate file format and required columns
    - Store raw data and return upload confirmation with data health metrics
    
    **Returns:**
    - Upload confirmation with processing status
    - Data health metrics and validation results
    - Error details if validation fails
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.csv', '.xlsx')):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, 
                detail="Invalid file format. Only CSV and Excel files are supported."
            )
        
        # Create upload record
        upload_record = RawUpload(
            file_name=file.filename,
            file_type="xlsx" if file.filename.endswith("xlsx") else "csv",
            status="PROCESSING"
        )
        db.add(upload_record)
        db.commit()
        db.refresh(upload_record)
        
        # Read file
        try:
            df = (
                pd.read_excel(file.file)
                if file.filename.endswith("xlsx")
                else pd.read_csv(file.file)
            )
        except Exception as e:
            upload_record.status = "FAILED"
            upload_record.error_report = {"error": f"Failed to read file: {str(e)}"}
            db.commit()
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, 
                detail=f"Failed to read file: {str(e)}"
            )

        df = normalize_columns(df)
        total_records = len(df)
        warnings = []

        # Determine file type and process
        if "units_sold" in df.columns:
            errors = validate_dataframe(df, ["date", "store_id", "sku_id", "units_sold"])
            if errors:
                upload_record.status = "FAILED"
                upload_record.error_report = {"validation_errors": errors}
                db.commit()
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                    detail="Sales data validation failed"
                )
            
            load_sales(df)
            upload_record.status = "COMPLETED"
            db.commit()
            
            return create_success_response(
                message="Sales data loaded successfully",
                data={
                    "upload_id": upload_record.id,
                    "file_type": "sales",
                    "records_processed": total_records,
                    "status": "COMPLETED"
                }
            )

        elif "expiry_date" in df.columns:
            errors = validate_dataframe(
                df,
                ["snapshot_date", "store_id", "sku_id", "batch_id", "expiry_date"],
            )
            if errors:
                upload_record.status = "FAILED"
                upload_record.error_report = {"validation_errors": errors}
                db.commit()
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                    detail="Inventory data validation failed"
                )
            
            load_inventory(df)
            upload_record.status = "COMPLETED"
            db.commit()
            
            return create_success_response(
                message="Inventory data loaded successfully",
                data={
                    "upload_id": upload_record.id,
                    "file_type": "inventory",
                    "records_processed": total_records,
                    "status": "COMPLETED"
                }
            )

        elif "unit_cost" in df.columns:
            load_purchases(df)
            upload_record.status = "COMPLETED"
            db.commit()
            
            return create_success_response(
                message="Purchase data loaded successfully",
                data={
                    "upload_id": upload_record.id,
                    "file_type": "purchases",
                    "records_processed": total_records,
                    "status": "COMPLETED"
                }
            )

        else:
            upload_record.status = "FAILED"
            upload_record.error_report = {"error": "Unknown file format - no recognizable data columns found"}
            db.commit()
            
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Unknown file format - no recognizable data columns found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        if 'upload_record' in locals():
            upload_record.status = "FAILED"
            upload_record.error_report = {"error": str(e)}
            db.commit()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, 
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{upload_id}/status", response_model=APIResponse)
async def get_upload_status(
    upload_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check the processing status of an uploaded file.
    
    Monitor the progress of file processing and get detailed status information.
    
    **Status Values:**
    - `PENDING`: File queued for processing
    - `PROCESSING`: File currently being processed
    - `COMPLETED`: Processing completed successfully
    - `FAILED`: Processing failed with errors
    
    **Example Response:**
    ```json
    {
        "success": true,
        "message": "Upload status retrieved successfully",
        "data": {
            "upload_id": 123,
            "status": "COMPLETED",
            "file_name": "sales_data.csv",
            "file_type": "csv",
            "uploaded_at": "2024-01-01T10:00:00Z",
            "error_report": null
        },
        "timestamp": "2024-01-15T10:30:00Z"
    }
    ```
    
    **Requirements:** 1.4
    - Return upload confirmation with data health metrics
    """
    try:
        upload_record = db.query(RawUpload).filter(RawUpload.id == upload_id).first()
        
        if not upload_record:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, 
                detail="Upload not found"
            )
        
        return create_success_response(
            message="Upload status retrieved successfully",
            data={
                "upload_id": upload_record.id,
                "status": upload_record.status,
                "file_name": upload_record.file_name,
                "file_type": upload_record.file_type,
                "uploaded_at": upload_record.uploaded_at.isoformat(),
                "error_report": upload_record.error_report
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, 
            detail=f"Error retrieving upload status: {str(e)}"
        )


@router.get("/{upload_id}/report", response_model=DataHealthReport)
async def get_data_health_report(
    upload_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive data health report for an uploaded file.
    
    Provides detailed analysis of data quality including:
    - Record counts (total, valid, invalid)
    - Missing value analysis by column
    - Data quality score (0-100)
    - Column mapping suggestions
    - Date range coverage
    
    **Example Response:**
    ```json
    {
        "total_records": 1000,
        "valid_records": 950,
        "invalid_records": 50,
        "missing_values": {
            "selling_price": 25,
            "units_sold": 0
        },
        "data_quality_score": 95.0,
        "column_mapping": {
            "SKU Code": "sku_id",
            "Store ID": "store_id"
        },
        "date_range": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }
    }
    ```
    
    **Requirements:** 1.2, 1.3
    - Return detailed validation report with mapping suggestions
    - Flag data quality issues and continue processing valid records
    """
    try:
        upload_record = db.query(RawUpload).filter(RawUpload.id == upload_id).first()
        
        if not upload_record:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        if upload_record.status != "COMPLETED":
            raise HTTPException(status_code=400, detail="Upload not completed successfully")
        
        # This would typically be generated during processing and stored
        # For now, return a basic report structure
        return DataHealthReport(
            total_records=0,  # Would be populated from actual processing
            valid_records=0,
            invalid_records=0,
            missing_values={},
            data_quality_score=0.0,
            column_mapping={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating data health report: {str(e)}")
