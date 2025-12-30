"""
Logging configuration for the ExpiryShield backend.

This module provides centralized logging configuration with proper
formatting, filtering, and security considerations including sensitive
data masking and security event logging.
"""

import logging
import logging.config
import os
import re
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime


class SensitiveDataFilter(logging.Filter):
    """Enhanced filter to mask sensitive data in log messages."""
    
    # Patterns for sensitive data
    SENSITIVE_PATTERNS = [
        # Credit card numbers
        (re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'), '****-****-****-****'),
        # Email addresses (partial masking)
        (re.compile(r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'), r'\1***@\2'),
        # Phone numbers
        (re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'), '***-***-****'),
        # Passwords in URLs or form data
        (re.compile(r'(password[=:]\s*)([^\s&]+)', re.IGNORECASE), r'\1****'),
        # API keys and tokens
        (re.compile(r'((?:api[_-]?key|token|secret|bearer)[=:\s]+)([^\s&]+)', re.IGNORECASE), r'\1****'),
        # JWT tokens (partial masking)
        (re.compile(r'\b(eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.)([A-Za-z0-9_-]+)\b'), r'\1****'),
        # Social security numbers
        (re.compile(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'), '***-**-****'),
        # Database connection strings
        (re.compile(r'(://[^:]+:)([^@]+)(@)', re.IGNORECASE), r'\1****\3'),
        # IP addresses (partial masking)
        (re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.)\d{1,3}\b'), r'\1***'),
        # User IDs and sensitive identifiers (when in sensitive contexts)
        (re.compile(r'(user_id[=:\s]+)([^\s&,}]+)', re.IGNORECASE), r'\1****'),
        # Session IDs
        (re.compile(r'(session[_-]?id[=:\s]+)([^\s&,}]+)', re.IGNORECASE), r'\1****'),
        # Authorization headers
        (re.compile(r'(authorization[:\s]+bearer\s+)([^\s]+)', re.IGNORECASE), r'\1****'),
        # Cookie values
        (re.compile(r'(cookie[:\s]+[^;]*=)([^;]+)', re.IGNORECASE), r'\1****'),
    ]
    
    # Fields that should be completely masked
    SENSITIVE_FIELDS = {
        'password', 'passwd', 'pwd', 'secret', 'token', 'key', 'auth',
        'authorization', 'cookie', 'session', 'csrf', 'api_key',
        'access_token', 'refresh_token', 'private_key', 'cert', 'certificate'
    }
    
    def filter(self, record):
        """Filter and mask sensitive data in log records."""
        # Filter message
        if hasattr(record, 'msg') and record.msg:
            record.msg = self._mask_sensitive_data(str(record.msg))
        
        # Filter args
        if hasattr(record, 'args') and record.args:
            filtered_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    filtered_args.append(self._mask_sensitive_data(arg))
                elif isinstance(arg, dict):
                    filtered_args.append(self._mask_sensitive_dict(arg))
                else:
                    filtered_args.append(arg)
            record.args = tuple(filtered_args)
        
        # Filter extra fields
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key.lower() in self.SENSITIVE_FIELDS:
                    setattr(record, key, '****')
                elif isinstance(value, str):
                    setattr(record, key, self._mask_sensitive_data(value))
                elif isinstance(value, dict):
                    setattr(record, key, self._mask_sensitive_dict(value))
        
        return True
    
    def _mask_sensitive_data(self, text: str) -> str:
        """Apply sensitive data masking patterns to text."""
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            text = pattern.sub(replacement, text)
        return text
    
    def _mask_sensitive_dict(self, data: dict) -> dict:
        """Recursively mask sensitive data in dictionaries."""
        if not isinstance(data, dict):
            return data
        
        masked_data = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            
            if key_lower in self.SENSITIVE_FIELDS:
                masked_data[key] = '****'
            elif isinstance(value, str):
                masked_data[key] = self._mask_sensitive_data(value)
            elif isinstance(value, dict):
                masked_data[key] = self._mask_sensitive_dict(value)
            elif isinstance(value, list):
                masked_data[key] = [
                    self._mask_sensitive_dict(item) if isinstance(item, dict)
                    else self._mask_sensitive_data(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                masked_data[key] = value
        
        return masked_data


class SecurityEventFilter(logging.Filter):
    """Filter for security events to add additional context."""
    
    def filter(self, record):
        """Add security event metadata."""
        if hasattr(record, 'security_event') and record.security_event:
            # Add timestamp
            record.security_timestamp = datetime.utcnow().isoformat()
            
            # Add severity based on event type
            if hasattr(record, 'event_type'):
                event_type = record.event_type.lower()
                if any(threat in event_type for threat in ['injection', 'xss', 'traversal', 'attack']):
                    record.security_severity = 'HIGH'
                elif any(warning in event_type for warning in ['suspicious', 'unusual', 'failed']):
                    record.security_severity = 'MEDIUM'
                else:
                    record.security_severity = 'LOW'
        
        return True


class AuditTrailFormatter(logging.Formatter):
    """Custom formatter for audit trail logs."""
    
    def format(self, record):
        """Format audit trail records with structured data."""
        # Create base audit record
        audit_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add security event fields
        if hasattr(record, 'security_event') and record.security_event:
            audit_record.update({
                'event_type': 'security',
                'security_event_type': getattr(record, 'event_type', 'unknown'),
                'security_severity': getattr(record, 'security_severity', 'LOW'),
                'client_ip': getattr(record, 'client_ip', None),
                'user_agent': getattr(record, 'user_agent', None),
                'path': getattr(record, 'path', None),
                'method': getattr(record, 'method', None),
            })
        
        # Add authentication events
        if hasattr(record, 'user_id'):
            audit_record.update({
                'user_id': record.user_id,
                'username': getattr(record, 'username', None),
                'roles': getattr(record, 'roles', None),
            })
        
        # Add performance metrics
        if hasattr(record, 'performance_metric') and record.performance_metric:
            audit_record.update({
                'event_type': 'performance',
                'metric_name': getattr(record, 'metric_name', None),
                'metric_value': getattr(record, 'metric_value', None),
                'metric_unit': getattr(record, 'metric_unit', None),
            })
        
        # Add request context
        if hasattr(record, 'request_id'):
            audit_record['request_id'] = record.request_id
        
        return json.dumps(audit_record, default=str)


def get_logging_config() -> Dict[str, Any]:
    """Get enhanced logging configuration dictionary."""
    
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', 'json')  # 'json' or 'text'
    enable_audit_logging = os.getenv('ENABLE_AUDIT_LOGGING', 'true').lower() == 'true'
    
    # Base formatters
    formatters = {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        },
        'audit': {
            '()': AuditTrailFormatter,
        }
    }
    
    # Add JSON formatter if requested
    if log_format == 'json':
        formatters['json'] = {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d'
        }
    
    # Filters
    filters = {
        'sensitive_data': {
            '()': SensitiveDataFilter,
        },
        'security_event': {
            '()': SecurityEventFilter,
        }
    }
    
    # Handlers
    handlers = {
        'console': {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'json' if log_format == 'json' else 'detailed',
            'stream': 'ext://sys.stdout',
            'filters': ['sensitive_data']
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'json' if log_format == 'json' else 'detailed',
            'filename': 'logs/expiryshield.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'filters': ['sensitive_data']
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'json' if log_format == 'json' else 'detailed',
            'filename': 'logs/expiryshield_errors.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'filters': ['sensitive_data']
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'WARNING',
            'formatter': 'audit',
            'filename': 'logs/expiryshield_security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 20,  # Keep more security logs
            'filters': ['sensitive_data', 'security_event']
        }
    }
    
    # Add audit handler if enabled
    if enable_audit_logging:
        handlers['audit_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'audit',
            'filename': 'logs/expiryshield_audit.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 30,  # Keep more audit logs
            'filters': ['sensitive_data']
        }
    
    # Loggers
    loggers = {
        'app': {
            'level': log_level,
            'handlers': ['console', 'file', 'error_file'],
            'propagate': False
        },
        'app.security': {
            'level': 'WARNING',
            'handlers': ['console', 'security_file', 'error_file'],
            'propagate': False
        },
        'app.auth': {
            'level': 'INFO',
            'handlers': ['console', 'file', 'security_file'] + (['audit_file'] if enable_audit_logging else []),
            'propagate': False
        },
        'app.middleware': {
            'level': 'INFO',
            'handlers': ['console', 'file'] + (['audit_file'] if enable_audit_logging else []),
            'propagate': False
        },
        'app.validation': {
            'level': 'WARNING',
            'handlers': ['console', 'security_file', 'error_file'],
            'propagate': False
        },
        'sqlalchemy.engine': {
            'level': 'WARNING',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'uvicorn': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        },
        'uvicorn.error': {
            'level': 'INFO',
            'handlers': ['console', 'error_file'],
            'propagate': False
        },
        'uvicorn.access': {
            'level': 'INFO',
            'handlers': ['console'] + (['audit_file'] if enable_audit_logging else []),
            'propagate': False
        }
    }
    
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': filters,
        'formatters': formatters,
        'handlers': handlers,
        'loggers': loggers,
        'root': {
            'level': log_level,
            'handlers': ['console']
        }
    }


def setup_logging():
    """Set up enhanced logging configuration."""
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Get logger and log startup message
    logger = logging.getLogger('app')
    logger.info("Enhanced logging configured successfully with security features")
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance with the specified name."""
    if name:
        return logging.getLogger(f'app.{name}')
    return logging.getLogger('app')


# Enhanced security logging helpers
def log_security_event(event_type: str, details: Dict[str, Any], logger: logging.Logger = None):
    """Log security-related events with enhanced context."""
    if logger is None:
        logger = get_logger('security')
    
    # Add common security context
    security_context = {
        'event_type': event_type,
        'security_event': True,
        'timestamp': datetime.utcnow().isoformat(),
        **details
    }
    
    # Hash sensitive details for correlation without exposing data
    if 'client_ip' in details:
        security_context['client_ip_hash'] = hashlib.sha256(
            str(details['client_ip']).encode()
        ).hexdigest()[:16]
    
    logger.warning(
        f"Security event: {event_type}",
        extra=security_context
    )


def log_authentication_event(event_type: str, user_id: str = None, username: str = None, 
                           client_ip: str = None, user_agent: str = None, 
                           success: bool = True, details: Dict[str, Any] = None):
    """Log authentication-related events."""
    logger = get_logger('auth')
    
    auth_context = {
        'event_type': event_type,
        'user_id': user_id,
        'username': username,
        'client_ip': client_ip,
        'user_agent': user_agent,
        'success': success,
        'timestamp': datetime.utcnow().isoformat(),
        **(details or {})
    }
    
    level = logging.INFO if success else logging.WARNING
    logger.log(
        level,
        f"Authentication event: {event_type} - {'Success' if success else 'Failed'}",
        extra=auth_context
    )


def log_data_access_event(operation: str, table: str, user_id: str = None, 
                         record_count: int = None, filters: Dict[str, Any] = None):
    """Log data access events for audit trail."""
    logger = get_logger('audit')
    
    access_context = {
        'event_type': 'data_access',
        'operation': operation,
        'table': table,
        'user_id': user_id,
        'record_count': record_count,
        'filters': filters,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    logger.info(
        f"Data access: {operation} on {table}",
        extra=access_context
    )


def log_performance_metric(metric_name: str, value: float, unit: str = 'ms', 
                          context: Dict[str, Any] = None, logger: logging.Logger = None):
    """Log performance metrics with enhanced context."""
    if logger is None:
        logger = get_logger('performance')
    
    perf_context = {
        'metric_name': metric_name,
        'metric_value': value,
        'metric_unit': unit,
        'performance_metric': True,
        'timestamp': datetime.utcnow().isoformat(),
        **(context or {})
    }
    
    logger.info(
        f"Performance metric: {metric_name} = {value}{unit}",
        extra=perf_context
    )


def log_business_event(event_type: str, user_id: str = None, details: Dict[str, Any] = None):
    """Log business-related events for audit trail."""
    logger = get_logger('business')
    
    business_context = {
        'event_type': event_type,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat(),
        **(details or {})
    }
    
    logger.info(
        f"Business event: {event_type}",
        extra=business_context
    )


# Data protection utilities
def mask_sensitive_data(data: Any, field_name: str = None) -> Any:
    """Mask sensitive data for logging purposes."""
    if isinstance(data, str):
        # Apply sensitive data filter
        filter_instance = SensitiveDataFilter()
        return filter_instance._mask_sensitive_data(data)
    elif isinstance(data, dict):
        filter_instance = SensitiveDataFilter()
        return filter_instance._mask_sensitive_dict(data)
    else:
        return data


def create_audit_context(request_id: str = None, user_id: str = None, 
                        client_ip: str = None, operation: str = None) -> Dict[str, Any]:
    """Create standardized audit context for logging."""
    return {
        'request_id': request_id,
        'user_id': user_id,
        'client_ip': client_ip,
        'operation': operation,
        'timestamp': datetime.utcnow().isoformat(),
    }