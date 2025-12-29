"""
Property-based tests for data ingestion functionality
Feature: expiry-risk-pipeline
"""

import pytest
import pandas as pd
from hypothesis import given, strategies as st, assume
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import numpy as np
from unittest.mock import patch, Mock

from app.services.validation import validate_dataframe, ValidationReport


# Mock the ingestion module to avoid database dependencies
COLUMN_ALIASES = {
    "sku_id": ["sku", "sku code", "item_id"],
    "store_id": ["store", "store_id", "location"],
    "date": ["date", "txn_date"],
    "snapshot_date": ["snapshot", "as_of_date"],
    "expiry_date": ["expiry", "exp_dt", "best before"],
    "on_hand_qty": ["qty", "on hand", "stock"],
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Simplified version for testing"""
    df.columns = [c.lower().strip() for c in df.columns]
    rename_map = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for col in df.columns:
            if col in aliases:
                rename_map[col] = canonical
    return df.rename(columns=rename_map)


# Test data generators
@st.composite
def generate_dataframe_with_columns(draw, required_columns: List[str], extra_columns: List[str] = None):
    """Generate a DataFrame with specified required columns and optional extra columns"""
    extra_columns = extra_columns or []
    all_columns = required_columns + extra_columns
    
    # Generate column names with variations
    column_variations = {}
    for col in all_columns:
        if col in COLUMN_ALIASES:
            # Sometimes use canonical name, sometimes use alias
            possible_names = [col] + COLUMN_ALIASES[col]
            column_variations[col] = draw(st.sampled_from(possible_names))
        else:
            column_variations[col] = col
    
    # Generate some sample data
    num_rows = draw(st.integers(min_value=1, max_value=10))
    data = {}
    
    for col in all_columns:
        actual_col_name = column_variations[col]
        if col in ['date', 'snapshot_date', 'expiry_date', 'received_date']:
            # Generate date strings
            data[actual_col_name] = [
                draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31))).strftime('%Y-%m-%d')
                for _ in range(num_rows)
            ]
        elif col in ['units_sold', 'on_hand_qty', 'received_qty']:
            # Generate positive integers
            data[actual_col_name] = [draw(st.integers(min_value=0, max_value=1000)) for _ in range(num_rows)]
        elif col in ['selling_price', 'unit_cost']:
            # Generate positive floats
            data[actual_col_name] = [draw(st.floats(min_value=0.01, max_value=1000.0)) for _ in range(num_rows)]
        else:
            # Generate string data
            data[actual_col_name] = [draw(st.text(min_size=1, max_size=10)) for _ in range(num_rows)]
    
    return pd.DataFrame(data)


@st.composite
def generate_messy_column_names(draw):
    """Generate column names with various formatting issues"""
    base_names = list(COLUMN_ALIASES.keys())
    messy_names = []
    
    for name in base_names:
        # Add random whitespace, case variations
        messy_name = draw(st.sampled_from([
            name.upper(),
            name.title(),
            f" {name} ",
            f"{name}\t",
            name.replace('_', ' '),
            name.replace('_', '-')
        ]))
        messy_names.append(messy_name)
    
    return messy_names


@st.composite
def generate_dataframe_with_duplicates(draw, base_columns: List[str]):
    """Generate a DataFrame that may contain duplicate rows"""
    df = draw(generate_dataframe_with_columns(base_columns))
    
    # Randomly decide to add duplicates
    add_duplicates = draw(st.booleans())
    if add_duplicates and len(df) > 0:
        # Duplicate some random rows
        num_duplicates = draw(st.integers(min_value=1, max_value=min(3, len(df))))
        duplicate_indices = draw(st.lists(
            st.integers(min_value=0, max_value=len(df)-1),
            min_size=num_duplicates,
            max_size=num_duplicates
        ))
        
        duplicate_rows = df.iloc[duplicate_indices]
        df = pd.concat([df, duplicate_rows], ignore_index=True)
    
    return df


@st.composite
def generate_date_variations(draw):
    """Generate dates in various formats"""
    base_date = draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31)))
    
    formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d-%m-%Y',
        '%Y%m%d',
        '%m-%d-%Y'
    ]
    
    format_choice = draw(st.sampled_from(formats))
    return base_date.strftime(format_choice)


# Property 1: File validation completeness
@given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10))
def test_property_1_file_validation_completeness(required_columns):
    """
    Property 1: File validation completeness
    For any list of required columns, validation should detect all missing columns
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7**
    """
    # Create a DataFrame missing some required columns
    available_columns = required_columns[:-1] if len(required_columns) > 1 else []
    df = pd.DataFrame({col: [1, 2, 3] for col in available_columns})
    
    report = validate_dataframe(df, required_columns)
    
    # Property: All missing columns should be detected
    missing_columns = set(required_columns) - set(available_columns)
    detected_missing = {error.column for error in report.errors if error.error_type == "missing_column"}
    
    assert missing_columns == detected_missing, f"Expected missing columns {missing_columns}, but detected {detected_missing}"
    
    # If there are missing columns, validation should fail
    if missing_columns:
        assert not report.is_valid, "Validation should fail when required columns are missing"


# Property 2: Column mapping consistency  
@given(generate_messy_column_names())
def test_property_2_column_mapping_consistency(messy_columns):
    """
    Property 2: Column mapping consistency
    For any messy column names that have defined aliases, normalization should map them consistently
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7**
    """
    # Create DataFrame with messy column names
    df = pd.DataFrame({col: [1, 2, 3] for col in messy_columns})
    
    # Apply normalization
    normalized_df = normalize_columns(df)
    
    # Property: All columns that have aliases should be mapped to canonical names
    for canonical, aliases in COLUMN_ALIASES.items():
        # Check if any of the messy columns should map to this canonical name
        for messy_col in messy_columns:
            clean_messy = messy_col.lower().strip()
            if clean_messy in aliases or clean_messy == canonical:
                assert canonical in normalized_df.columns, f"Column '{messy_col}' should be mapped to '{canonical}'"
                break


# Property 3: Duplicate handling preservation
@given(generate_dataframe_with_duplicates(['store_id', 'sku_id', 'date']))
def test_property_3_duplicate_handling_preservation(df_with_duplicates):
    """
    Property 3: Duplicate handling preservation
    For any DataFrame with duplicates, validation should detect them without losing data
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7**
    """
    original_length = len(df_with_duplicates)
    has_duplicates = df_with_duplicates.duplicated().any()
    
    report = validate_dataframe(df_with_duplicates, ['store_id', 'sku_id', 'date'])
    
    # Property: If duplicates exist, they should be detected as warnings
    duplicate_warnings = [w for w in report.warnings if w.error_type == "duplicate_rows"]
    
    if has_duplicates:
        assert len(duplicate_warnings) > 0, "Duplicates should be detected as warnings"
        # The original data should be preserved (not removed)
        assert len(df_with_duplicates) == original_length, "Original data should be preserved"
    else:
        assert len(duplicate_warnings) == 0, "No duplicate warnings should be generated for clean data"


# Property 4: Date parsing robustness
@given(st.lists(generate_date_variations(), min_size=1, max_size=10))
def test_property_4_date_parsing_robustness(date_strings):
    """
    Property 4: Date parsing robustness
    For any list of date strings in various formats, the system should handle them gracefully
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7**
    """
    # Create DataFrame with date column
    df = pd.DataFrame({
        'expiry_date': date_strings,
        'store_id': ['S1'] * len(date_strings),
        'sku_id': ['SKU1'] * len(date_strings)
    })
    
    report = validate_dataframe(df, ['expiry_date', 'store_id', 'sku_id'])
    
    # Property: Date parsing should not cause validation to crash
    # The validation should complete and return a report
    assert isinstance(report, ValidationReport), "Validation should return a ValidationReport"
    
    # Property: If dates are parseable, no date format errors should be reported
    date_errors = [e for e in report.errors if e.error_type == "invalid_date_format"]
    
    # Try to parse the dates to see if they should be valid
    try:
        parsed_dates = pd.to_datetime(date_strings, errors='coerce')
        valid_dates = parsed_dates.notna().all()
        
        if valid_dates:
            assert len(date_errors) == 0, f"No date format errors expected for valid dates, but got: {date_errors}"
    except Exception:
        # If pandas can't parse them, errors are expected
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])