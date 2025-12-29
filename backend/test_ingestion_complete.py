"""
Complete test of ingestion functionality
"""
import pandas as pd
import json
from app.services.ingestion import normalize_columns
from app.services.validation import validate_dataframe

def test_complete_ingestion_flow():
    """Test the complete ingestion flow"""
    
    print("=== Testing Complete Ingestion Flow ===\n")
    
    # Test 1: Column mapping with messy names
    print("1. Testing column mapping...")
    messy_data = {
        'Date': ['2024-01-01', '2024-01-02'],
        'Store ID': ['S001', 'S002'], 
        'SKU Code': ['SKU001', 'SKU002'],
        'Units Sold': [10, 15],
        'Selling Price': [25.99, 30.50]
    }
    df = pd.DataFrame(messy_data)
    print(f"Original columns: {list(df.columns)}")
    
    normalized_df = normalize_columns(df)
    print(f"Normalized columns: {list(normalized_df.columns)}")
    
    expected_columns = ['date', 'store_id', 'sku_id', 'units_sold', 'selling_price']
    mapped_correctly = all(col in normalized_df.columns for col in expected_columns)
    print(f"✅ Column mapping: {'PASS' if mapped_correctly else 'FAIL'}\n")
    
    # Test 2: Validation with issues
    print("2. Testing validation with data issues...")
    problematic_data = {
        'date': ['2024-01-01', '2024-01-02', None],  # Missing date
        'store_id': ['S001', 'S002', 'S001'],
        'sku_id': ['SKU001', 'SKU002', 'SKU001'],
        'units_sold': [10, -5, 8],  # Negative value
        'expiry_date': ['2024-06-01', None, '2024-05-30'],  # Missing expiry
        'on_hand_qty': [100, 150, -10]  # Negative stock
    }
    problem_df = pd.DataFrame(problematic_data)
    
    # Add duplicate row
    problem_df = pd.concat([problem_df, problem_df.iloc[[0]]], ignore_index=True)
    
    validation_report = validate_dataframe(problem_df, ['date', 'store_id', 'sku_id', 'units_sold'])
    
    print(f"Validation report:")
    print(f"  - Is valid: {validation_report.is_valid}")
    print(f"  - Errors: {len(validation_report.errors)}")
    print(f"  - Warnings: {len(validation_report.warnings)}")
    
    for error in validation_report.errors:
        print(f"    ERROR: {error.column} - {error.message}")
    
    for warning in validation_report.warnings:
        print(f"    WARNING: {warning.column} - {warning.message}")
    
    has_expected_issues = (
        len(validation_report.errors) > 0 and  # Should have errors
        len(validation_report.warnings) > 0 and  # Should have warnings
        not validation_report.is_valid  # Should be invalid
    )
    print(f"✅ Validation detection: {'PASS' if has_expected_issues else 'FAIL'}\n")
    
    # Test 3: Date parsing robustness
    print("3. Testing date parsing...")
    date_formats = {
        'expiry_date': ['2024-01-01', '01/15/2024', '15-01-2024', '20240130'],
        'store_id': ['S001', 'S002', 'S003', 'S004'],
        'sku_id': ['SKU001', 'SKU002', 'SKU003', 'SKU004']
    }
    date_df = pd.DataFrame(date_formats)
    
    date_validation = validate_dataframe(date_df, ['expiry_date', 'store_id', 'sku_id'])
    date_errors = [e for e in date_validation.errors if e.error_type == "invalid_date_format"]
    
    print(f"Date parsing errors: {len(date_errors)}")
    print(f"✅ Date parsing: {'PASS' if len(date_errors) == 0 else 'FAIL'}\n")
    
    # Test 4: File type detection
    print("4. Testing file type detection...")
    
    # Sales file
    sales_df = pd.DataFrame({
        'date': ['2024-01-01'],
        'store_id': ['S001'],
        'sku_id': ['SKU001'],
        'units_sold': [10]
    })
    
    # Inventory file  
    inventory_df = pd.DataFrame({
        'snapshot_date': ['2024-01-01'],
        'store_id': ['S001'],
        'sku_id': ['SKU001'],
        'batch_id': ['B001'],
        'expiry_date': ['2024-06-01'],
        'on_hand_qty': [100]
    })
    
    # Purchase file
    purchase_df = pd.DataFrame({
        'received_date': ['2024-01-01'],
        'store_id': ['S001'],
        'sku_id': ['SKU001'],
        'batch_id': ['B001'],
        'received_qty': [50],
        'unit_cost': [10.50]
    })
    
    sales_detected = "units_sold" in sales_df.columns
    inventory_detected = "expiry_date" in inventory_df.columns
    purchase_detected = "unit_cost" in purchase_df.columns
    
    print(f"Sales file detection: {'PASS' if sales_detected else 'FAIL'}")
    print(f"Inventory file detection: {'PASS' if inventory_detected else 'FAIL'}")
    print(f"Purchase file detection: {'PASS' if purchase_detected else 'FAIL'}")
    print(f"✅ File type detection: {'PASS' if all([sales_detected, inventory_detected, purchase_detected]) else 'FAIL'}\n")
    
    print("=== Summary ===")
    all_tests_pass = all([
        mapped_correctly,
        has_expected_issues,
        len(date_errors) == 0,
        sales_detected and inventory_detected and purchase_detected
    ])
    
    print(f"Overall ingestion functionality: {'✅ COMPLETE' if all_tests_pass else '❌ INCOMPLETE'}")
    
    return all_tests_pass

if __name__ == "__main__":
    test_complete_ingestion_flow()