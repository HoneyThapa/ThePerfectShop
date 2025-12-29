"""
Manual test script to verify upload functionality
"""
import pandas as pd
import requests
import json
from io import BytesIO

# Create test data
def create_test_sales_data():
    data = {
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'Store ID': ['S001', 'S002', 'S001'],
        'SKU Code': ['SKU001', 'SKU002', 'SKU001'],
        'Units Sold': [10, 15, 8],
        'Selling Price': [25.99, 30.50, 25.99]
    }
    return pd.DataFrame(data)

def create_test_inventory_data():
    data = {
        'Snapshot': ['2024-01-01', '2024-01-01', '2024-01-01'],
        'Store': ['S001', 'S002', 'S001'],
        'SKU': ['SKU001', 'SKU002', 'SKU003'],
        'Batch ID': ['B001', 'B002', 'B003'],
        'Expiry': ['2024-06-01', '2024-07-15', '2024-05-30'],
        'Qty': [100, 150, 75]
    }
    return pd.DataFrame(data)

def create_messy_data_with_issues():
    """Create data with validation issues for testing"""
    data = {
        'Date': ['2024-01-01', '2024-01-02', None],  # Missing date
        'Store ID': ['S001', 'S002', 'S001'],
        'SKU Code': ['SKU001', 'SKU002', 'SKU001'],
        'Units Sold': [10, -5, 8],  # Negative value
        'Selling Price': [25.99, 30.50, 25.99]
    }
    df = pd.DataFrame(data)
    # Add duplicate row
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    return df

if __name__ == "__main__":
    print("Testing upload functionality...")
    
    # Test 1: Valid sales data
    print("\n1. Testing valid sales data...")
    sales_df = create_test_sales_data()
    print("Sample data:")
    print(sales_df.head())
    
    # Test 2: Valid inventory data  
    print("\n2. Testing valid inventory data...")
    inventory_df = create_test_inventory_data()
    print("Sample data:")
    print(inventory_df.head())
    
    # Test 3: Data with validation issues
    print("\n3. Testing data with validation issues...")
    messy_df = create_messy_data_with_issues()
    print("Sample messy data:")
    print(messy_df.head())
    
    print("\nManual test data created successfully!")
    print("To test the API, start the FastAPI server and use these DataFrames")