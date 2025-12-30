"""
Comprehensive input validation utilities for the ExpiryShield backend.

This module provides validation functions for preventing SQL injection,
XSS attacks, and other security vulnerabilities through input sanitization.
"""

import re
import html
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from fastapi import HTTPException, status
from app.logging_config import get_logger, log_security_event


logger = get_logger('validation')


class ValidationError(HTTPException):
    """Custom validation error."""
    
    def __init__(self, detail: str, field: str = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": detail,
                "error_code": "VALIDATION_ERROR",
                "field": field
            }
        )


class SecurityValidationError(HTTPException):
    """Security-related validation error."""
    
    def __init__(self, detail: str, attack_type: str = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": detail,
                "error_code": "SECURITY_VALIDATION_ERROR",
                "attack_type": attack_type
            }
        )


# SQL Injection Prevention
SQL_INJECTION_PATTERNS = [
    # Basic SQL injection patterns
    r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
    r"(\b(or|and)\s+\d+\s*=\s*\d+)",
    r"(\b(or|and)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
    r"(--|#|/\*|\*/)",
    r"(\bxp_cmdshell\b)",
    r"(\bsp_executesql\b)",
    r"(\bsp_configure\b)",
    r"(\bsp_addextendedproc\b)",
    r"(\bsp_oacreate\b)",
    r"(\bsp_makewebtask\b)",
    # Advanced patterns
    r"(\bunion\s+all\s+select)",
    r"(\bselect\s+.*\bfrom\s+information_schema)",
    r"(\bselect\s+.*\bfrom\s+sys\.)",
    r"(\bselect\s+.*\bfrom\s+mysql\.)",
    r"(\bselect\s+.*\bfrom\s+pg_)",
    r"(\bload_file\s*\()",
    r"(\binto\s+outfile)",
    r"(\binto\s+dumpfile)",
    # Time-based blind SQL injection
    r"(\bsleep\s*\()",
    r"(\bwaitfor\s+delay)",
    r"(\bbenchmark\s*\()",
    # Boolean-based blind SQL injection
    r"(\bsubstring\s*\()",
    r"(\bascii\s*\()",
    r"(\bord\s*\()",
    r"(\bchar\s*\()",
]

# XSS Prevention
XSS_PATTERNS = [
    # Script tags
    r"<\s*script[^>]*>.*?</\s*script\s*>",
    r"<\s*script[^>]*>",
    r"</\s*script\s*>",
    # Event handlers
    r"\bon\w+\s*=",
    r"\bjavascript\s*:",
    r"\bvbscript\s*:",
    r"\bdata\s*:",
    # HTML entities that could be XSS
    r"&\#x?[0-9a-f]+;",
    # Iframe and object tags
    r"<\s*iframe[^>]*>",
    r"<\s*object[^>]*>",
    r"<\s*embed[^>]*>",
    r"<\s*applet[^>]*>",
    # Meta refresh
    r"<\s*meta[^>]*http-equiv[^>]*refresh",
    # Link and style tags
    r"<\s*link[^>]*>",
    r"<\s*style[^>]*>",
    # Form elements
    r"<\s*form[^>]*>",
    r"<\s*input[^>]*>",
    r"<\s*textarea[^>]*>",
    r"<\s*select[^>]*>",
    # Expression() for CSS
    r"\bexpression\s*\(",
    # URL schemes
    r"\b(javascript|vbscript|data|file|ftp):",
]

# Path Traversal Prevention
PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",
    r"\.\.\\",
    r"%2e%2e%2f",
    r"%2e%2e%5c",
    r"\.\.%2f",
    r"\.\.%5c",
    r"%2e%2e/",
    r"%2e%2e\\",
    r"....//",
    r"....\\\\",
]

# Command Injection Prevention
COMMAND_INJECTION_PATTERNS = [
    r"[;&|`$(){}[\]<>]",
    r"\b(cat|ls|dir|type|more|less|head|tail|grep|find|locate)\b",
    r"\b(rm|del|rmdir|rd|copy|move|mv|cp)\b",
    r"\b(wget|curl|nc|netcat|telnet|ssh|ftp)\b",
    r"\b(ps|top|kill|killall|pkill)\b",
    r"\b(chmod|chown|chgrp|su|sudo)\b",
    r"\b(echo|printf|print)\b.*[;&|`]",
]


def sanitize_string(value: str, max_length: int = 1000, allow_html: bool = False) -> str:
    """
    Sanitize a string input to prevent various injection attacks.
    
    Args:
        value: The string to sanitize
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML tags (will be escaped if False)
    
    Returns:
        Sanitized string
    
    Raises:
        ValidationError: If validation fails
        SecurityValidationError: If security threats are detected
    """
    if not isinstance(value, str):
        raise ValidationError("Value must be a string")
    
    # Check length
    if len(value) > max_length:
        raise ValidationError(f"String too long (max {max_length} characters)")
    
    # Check for null bytes
    if '\x00' in value:
        log_security_event(
            'null_byte_injection_attempt',
            {'value': value[:100], 'length': len(value)},
            logger
        )
        raise SecurityValidationError("Null bytes not allowed", "null_byte_injection")
    
    # Check for SQL injection patterns
    value_lower = value.lower()
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value_lower, re.IGNORECASE):
            log_security_event(
                'sql_injection_attempt',
                {'value': value[:100], 'pattern': pattern},
                logger
            )
            raise SecurityValidationError("Potentially malicious SQL pattern detected", "sql_injection")
    
    # Check for XSS patterns
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
            log_security_event(
                'xss_attempt',
                {'value': value[:100], 'pattern': pattern},
                logger
            )
            raise SecurityValidationError("Potentially malicious XSS pattern detected", "xss")
    
    # Check for path traversal
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            log_security_event(
                'path_traversal_attempt',
                {'value': value[:100], 'pattern': pattern},
                logger
            )
            raise SecurityValidationError("Path traversal pattern detected", "path_traversal")
    
    # Check for command injection
    for pattern in COMMAND_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            log_security_event(
                'command_injection_attempt',
                {'value': value[:100], 'pattern': pattern},
                logger
            )
            raise SecurityValidationError("Command injection pattern detected", "command_injection")
    
    # HTML escape if not allowing HTML
    if not allow_html:
        value = html.escape(value)
    
    # Remove control characters except newlines and tabs
    value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    
    return value.strip()


def validate_identifier(value: str, field_name: str = "identifier") -> str:
    """
    Validate an identifier (like store_id, sku_id, batch_id).
    
    Args:
        value: The identifier to validate
        field_name: Name of the field for error messages
    
    Returns:
        Validated identifier
    
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field_name)
    
    # Basic sanitization
    value = sanitize_string(value, max_length=100)
    
    # Check format - alphanumeric, hyphens, underscores only
    if not re.match(r'^[a-zA-Z0-9_-]+$', value):
        raise ValidationError(
            f"{field_name} can only contain letters, numbers, hyphens, and underscores",
            field_name
        )
    
    # Check length
    if len(value) < 1 or len(value) > 100:
        raise ValidationError(f"{field_name} must be 1-100 characters long", field_name)
    
    return value


def validate_numeric(value: Union[str, int, float], field_name: str = "number", 
                    min_value: Optional[float] = None, max_value: Optional[float] = None,
                    allow_negative: bool = True) -> float:
    """
    Validate a numeric value.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        allow_negative: Whether negative values are allowed
    
    Returns:
        Validated numeric value as float
    
    Raises:
        ValidationError: If validation fails
    """
    try:
        if isinstance(value, str):
            # Sanitize string first
            value = sanitize_string(value, max_length=50)
            # Convert to float
            numeric_value = float(value)
        else:
            numeric_value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid number", field_name)
    
    # Check for infinity and NaN
    if not isinstance(numeric_value, (int, float)) or \
       numeric_value != numeric_value or \
       numeric_value == float('inf') or \
       numeric_value == float('-inf'):
        raise ValidationError(f"{field_name} must be a finite number", field_name)
    
    # Check negative values
    if not allow_negative and numeric_value < 0:
        raise ValidationError(f"{field_name} cannot be negative", field_name)
    
    # Check range
    if min_value is not None and numeric_value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}", field_name)
    
    if max_value is not None and numeric_value > max_value:
        raise ValidationError(f"{field_name} must be at most {max_value}", field_name)
    
    return numeric_value


def validate_date(value: Union[str, date], field_name: str = "date") -> date:
    """
    Validate a date value.
    
    Args:
        value: The date to validate (string in YYYY-MM-DD format or date object)
        field_name: Name of the field for error messages
    
    Returns:
        Validated date object
    
    Raises:
        ValidationError: If validation fails
    """
    if isinstance(value, date):
        return value
    
    if isinstance(value, str):
        # Sanitize string first
        value = sanitize_string(value, max_length=20)
        
        # Try to parse date
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(value, '%m/%d/%Y').date()
            except ValueError:
                try:
                    return datetime.strptime(value, '%d/%m/%Y').date()
                except ValueError:
                    raise ValidationError(
                        f"{field_name} must be in YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY format",
                        field_name
                    )
    
    raise ValidationError(f"{field_name} must be a string or date object", field_name)


def validate_email(value: str, field_name: str = "email") -> str:
    """
    Validate an email address.
    
    Args:
        value: The email to validate
        field_name: Name of the field for error messages
    
    Returns:
        Validated email address
    
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field_name)
    
    # Sanitize string first
    value = sanitize_string(value, max_length=254).lower()
    
    # Basic email regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, value):
        raise ValidationError(f"{field_name} must be a valid email address", field_name)
    
    return value


def validate_file_upload(filename: str, allowed_extensions: List[str] = None) -> str:
    """
    Validate a file upload.
    
    Args:
        filename: The filename to validate
        allowed_extensions: List of allowed file extensions
    
    Returns:
        Validated filename
    
    Raises:
        ValidationError: If validation fails
        SecurityValidationError: If security threats are detected
    """
    if not isinstance(filename, str):
        raise ValidationError("Filename must be a string")
    
    # Sanitize filename
    filename = sanitize_string(filename, max_length=255)
    
    # Check for path traversal in filename
    if '/' in filename or '\\' in filename:
        log_security_event(
            'path_traversal_in_filename',
            {'filename': filename},
            logger
        )
        raise SecurityValidationError("Filename cannot contain path separators", "path_traversal")
    
    # Check for dangerous extensions
    dangerous_extensions = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl',
        '.sh', '.bash', '.ps1', '.psm1'
    ]
    
    filename_lower = filename.lower()
    for ext in dangerous_extensions:
        if filename_lower.endswith(ext):
            log_security_event(
                'dangerous_file_extension',
                {'filename': filename, 'extension': ext},
                logger
            )
            raise SecurityValidationError(f"File extension {ext} not allowed", "dangerous_file")
    
    # Check allowed extensions
    if allowed_extensions:
        file_ext = None
        for ext in allowed_extensions:
            if filename_lower.endswith(ext.lower()):
                file_ext = ext
                break
        
        if not file_ext:
            raise ValidationError(
                f"File must have one of these extensions: {', '.join(allowed_extensions)}"
            )
    
    return filename


def validate_json_data(data: Dict[str, Any], max_depth: int = 10, max_keys: int = 1000) -> Dict[str, Any]:
    """
    Validate JSON data for security issues.
    
    Args:
        data: The JSON data to validate
        max_depth: Maximum nesting depth allowed
        max_keys: Maximum number of keys allowed
    
    Returns:
        Validated JSON data
    
    Raises:
        ValidationError: If validation fails
        SecurityValidationError: If security threats are detected
    """
    def count_keys(obj, depth=0):
        if depth > max_depth:
            raise SecurityValidationError("JSON nesting too deep", "json_bomb")
        
        key_count = 0
        if isinstance(obj, dict):
            key_count += len(obj)
            for value in obj.values():
                key_count += count_keys(value, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                key_count += count_keys(item, depth + 1)
        
        return key_count
    
    # Check for JSON bombs
    total_keys = count_keys(data)
    if total_keys > max_keys:
        log_security_event(
            'json_bomb_attempt',
            {'total_keys': total_keys, 'max_keys': max_keys},
            logger
        )
        raise SecurityValidationError("JSON data too complex", "json_bomb")
    
    # Recursively sanitize string values
    def sanitize_json_values(obj):
        if isinstance(obj, dict):
            return {key: sanitize_json_values(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_json_values(item) for item in obj]
        elif isinstance(obj, str):
            return sanitize_string(obj, max_length=10000)
        else:
            return obj
    
    return sanitize_json_values(data)


# Validation decorators for common use cases
def validate_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate common request data fields.
    
    Args:
        data: Request data dictionary
    
    Returns:
        Validated data dictionary
    """
    validated_data = {}
    
    for key, value in data.items():
        # Validate key names
        if not isinstance(key, str) or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
            raise ValidationError(f"Invalid field name: {key}")
        
        # Validate common field types
        if key.endswith('_id') or key in ['store_id', 'sku_id', 'batch_id', 'user_id']:
            validated_data[key] = validate_identifier(value, key)
        elif key.endswith('_date') or key in ['date', 'expiry_date', 'snapshot_date']:
            validated_data[key] = validate_date(value, key)
        elif key.endswith('_email') or key == 'email':
            validated_data[key] = validate_email(value, key)
        elif key in ['qty', 'units_sold', 'on_hand_qty', 'received_qty', 'cleared_units']:
            validated_data[key] = int(validate_numeric(value, key, min_value=0, allow_negative=False))
        elif key in ['price', 'cost', 'value', 'savings', 'discount_pct', 'risk_score']:
            validated_data[key] = validate_numeric(value, key, min_value=0, allow_negative=False)
        elif isinstance(value, str):
            validated_data[key] = sanitize_string(value, max_length=1000)
        else:
            validated_data[key] = value
    
    return validated_data