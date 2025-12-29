from fastapi import APIRouter, UploadFile
import pandas as pd
from app.services.ingestion import (
    normalize_columns,
    load_sales,
    load_inventory,
    load_purchases,
)
from app.services.validation import validate_dataframe

router = APIRouter()


@router.post("/upload")
def upload_file(file: UploadFile):
    df = (
        pd.read_excel(file.file)
        if file.filename.endswith("xlsx")
        else pd.read_csv(file.file)
    )

    df = normalize_columns(df)

    if "units_sold" in df.columns:
        errors = validate_dataframe(df, ["date", "store_id", "sku_id", "units_sold"])
        if errors:
            return {"status": "error", "errors": errors}
        load_sales(df)
        return {"status": "sales loaded"}

    if "expiry_date" in df.columns:
        errors = validate_dataframe(
            df,
            ["snapshot_date", "store_id", "sku_id", "batch_id", "expiry_date"],
        )
        if errors:
            return {"status": "error", "errors": errors}
        load_inventory(df)
        return {"status": "inventory loaded"}

    if "unit_cost" in df.columns:
        load_purchases(df)
        return {"status": "purchases loaded"}

    return {"status": "unknown file format"}
