"""
Middleware for the ExpiryShield backend.

This module provides middleware for request/response logging,
performance monitoring, and security features.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.logging_config import get_logger, log_performance_metric, log_security_event, log_authentication_event


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = False):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.logger = get_logger('middleware')
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log incoming request
        if self.log_requests:
            self.logger.info(
                f"Incoming request: {request.method} {request.url.path}",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'query_params': str(request.query_params),
                    'client_ip': request.client.host if request.client else None,
                    'user_agent': request.headers.get('user-agent'),
                    'content_type': request.headers.get('content-type'),
                    'request_size': request.headers.get('content-length')
                }
            )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error and re-raise
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'processing_time_ms': processing_time,
                    'error': str(e)
                }
            )
            raise
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log response
        if self.log_responses or response.status_code >= 400:
            log_level = 'error' if response.status_code >= 500 else 'warning' if response.status_code >= 400 else 'info'
            getattr(self.logger, log_level)(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'processing_time_ms': processing_time,
                    'response_size': response.headers.get('content-length')
                }
            )
        
        # Log performance metric
        log_performance_metric(
            f"request_duration_{request.method.lower()}_{request.url.path.replace('/', '_')}",
            processing_time,
            'ms'
        )
        
        return response


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security features and monitoring."""
    
    def __init__(self, app, enable_security_headers: bool = True):
        super().__init__(app)
        self.enable_security_headers = enable_security_headers
        self.logger = get_logger('security')
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check for suspicious patterns
        self._check_suspicious_requests(request)
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        if self.enable_security_headers:
            self._add_security_headers(response)
        
        return response
    
    def _check_suspicious_requests(self, request: Request):
        """Check for suspicious request patterns."""
        
        # Check for SQL injection patterns in query parameters
        query_string = str(request.query_params).lower()
        sql_injection_patterns = [
            'union select', 'drop table', 'delete from', 'insert into',
            'update set', 'exec(', 'script>', '<script', 'javascript:',
            'onload=', 'onerror=', 'eval(', 'expression(', 'alert(',
            'document.cookie', 'document.write', 'window.location',
            'iframe', 'object', 'embed', 'applet', 'meta',
            'link', 'style', 'base', 'form', 'input',
            # SQL injection patterns
            "' or '1'='1", '" or "1"="1', "' or 1=1--", '" or 1=1--',
            "' union select", '" union select', "' drop table", '" drop table',
            "' delete from", '" delete from', "' insert into", '" insert into',
            "' update ", '" update ', "' exec ", '" exec ',
            # XSS patterns
            '<script', '</script>', 'javascript:', 'vbscript:', 'onload=',
            'onerror=', 'onclick=', 'onmouseover=', 'onfocus=', 'onblur=',
            'onchange=', 'onsubmit=', 'onreset=', 'onselect=', 'onunload=',
            # Path traversal
            '../', '..\\', '..\/', '..\\\\', '%2e%2e%2f', '%2e%2e%5c',
            # Command injection
            '; cat ', '| cat ', '& cat ', '; ls ', '| ls ', '& ls ',
            '; rm ', '| rm ', '& rm ', '; wget ', '| wget ', '& wget ',
            # LDAP injection
            '*)(uid=*', '*)(cn=*', '*)(&', '*))%00'
        ]
        
        suspicious_found = []
        for pattern in sql_injection_patterns:
            if pattern in query_string:
                suspicious_found.append(pattern)
        
        if suspicious_found:
            log_security_event(
                'suspicious_query_parameter',
                {
                    'patterns': suspicious_found,
                    'query_string': str(request.query_params),
                    'client_ip': request.client.host if request.client else None,
                    'user_agent': request.headers.get('user-agent'),
                    'path': request.url.path,
                    'method': request.method
                },
                self.logger
            )
        
        # Check for suspicious headers
        suspicious_headers = {
            'x-forwarded-for': ['127.0.0.1', 'localhost', '0.0.0.0'],
            'x-real-ip': ['127.0.0.1', 'localhost', '0.0.0.0'],
            'user-agent': ['sqlmap', 'nikto', 'nmap', 'masscan', 'nessus', 'openvas']
        }
        
        for header_name, suspicious_values in suspicious_headers.items():
            header_value = request.headers.get(header_name, '').lower()
            for suspicious_value in suspicious_values:
                if suspicious_value in header_value:
                    log_security_event(
                        'suspicious_header',
                        {
                            'header': header_name,
                            'value': header_value,
                            'suspicious_pattern': suspicious_value,
                            'client_ip': request.client.host if request.client else None,
                            'path': request.url.path
                        },
                        self.logger
                    )
                    break
        
        # Check for unusually large requests
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > 100 * 1024 * 1024:  # 100MB
            log_security_event(
                'large_request',
                {
                    'content_length': content_length,
                    'client_ip': request.client.host if request.client else None,
                    'path': request.url.path,
                    'method': request.method
                },
                self.logger
            )
        
        # Check for suspicious file upload attempts
        if request.method == 'POST' and '/upload' in request.url.path:
            content_type = request.headers.get('content-type', '').lower()
            if 'multipart/form-data' not in content_type:
                log_security_event(
                    'suspicious_upload_attempt',
                    {
                        'content_type': content_type,
                        'client_ip': request.client.host if request.client else None,
                        'path': request.url.path,
                        'reason': 'invalid_content_type_for_upload'
                    },
                    self.logger
                )
        
        # Check for directory traversal in path
        path = request.url.path
        traversal_patterns = ['../', '..\\', '%2e%2e%2f', '%2e%2e%5c', '....//']
        for pattern in traversal_patterns:
            if pattern in path.lower():
                log_security_event(
                    'directory_traversal_attempt',
                    {
                        'path': path,
                        'pattern': pattern,
                        'client_ip': request.client.host if request.client else None,
                        'user_agent': request.headers.get('user-agent')
                    },
                    self.logger
                )
                break
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response."""
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Strict transport security (HTTPS only)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content security policy
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware with Redis-like functionality."""
    
    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.request_counts = {}  # In production, use Redis or similar
        self.logger = get_logger('rate_limit')
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else 'unknown'
        current_time = int(time.time())
        current_minute = current_time // 60
        current_hour = current_time // 3600
        
        # Clean old entries (simple cleanup)
        cutoff_minute = current_minute - 2
        cutoff_hour = current_hour - 2
        
        self.request_counts = {
            key: count for key, count in self.request_counts.items()
            if (key[1] == 'minute' and key[2] >= cutoff_minute) or
               (key[1] == 'hour' and key[2] >= cutoff_hour)
        }
        
        # Check minute-based rate limit
        minute_key = (client_ip, 'minute', current_minute)
        minute_count = self.request_counts.get(minute_key, 0)
        
        # Check hour-based rate limit
        hour_key = (client_ip, 'hour', current_hour)
        hour_count = self.request_counts.get(hour_key, 0)
        
        # Determine which limit is exceeded
        limit_exceeded = None
        retry_after = 60
        
        if minute_count >= self.requests_per_minute:
            limit_exceeded = 'minute'
            retry_after = 60 - (current_time % 60)
        elif hour_count >= self.requests_per_hour:
            limit_exceeded = 'hour'
            retry_after = 3600 - (current_time % 3600)
        
        if limit_exceeded:
            log_security_event(
                'rate_limit_exceeded',
                {
                    'client_ip': client_ip,
                    'limit_type': limit_exceeded,
                    'requests_count': minute_count if limit_exceeded == 'minute' else hour_count,
                    'limit': self.requests_per_minute if limit_exceeded == 'minute' else self.requests_per_hour,
                    'path': request.url.path,
                    'user_agent': request.headers.get('user-agent')
                },
                self.logger
            )
            
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": f"Rate limit exceeded: too many requests per {limit_exceeded}",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": retry_after,
                    "limit_type": limit_exceeded
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # Increment counters
        self.request_counts[minute_key] = minute_count + 1
        self.request_counts[hour_key] = hour_count + 1
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, self.requests_per_minute - minute_count - 1))
        response.headers["X-RateLimit-Reset-Minute"] = str((current_minute + 1) * 60)
        
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(max(0, self.requests_per_hour - hour_count - 1))
        response.headers["X-RateLimit-Reset-Hour"] = str((current_hour + 1) * 3600)
        
        return response