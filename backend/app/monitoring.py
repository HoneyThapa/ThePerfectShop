"""
Monitoring and metrics collection for ExpiryShield Backend.

This module provides Prometheus metrics collection, custom metrics,
and monitoring utilities for the application.
"""

import time
import functools
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging
import os
import psutil
import threading
from contextlib import contextmanager

# Prometheus client imports
try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Info, Enum,
        CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
        multiprocess, REGISTRY
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy classes if prometheus_client is not available
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def time(self): return contextmanager(lambda: (yield))()
        def labels(self, *args, **kwargs): return self
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
    
    class Enum:
        def __init__(self, *args, **kwargs): pass
        def state(self, *args, **kwargs): pass

logger = logging.getLogger(__name__)

# Application info
APP_INFO = Info('expiryshield_app_info', 'Application information')
APP_INFO.info({
    'version': '1.0.0',
    'environment': os.getenv('ENVIRONMENT', 'development'),
    'python_version': f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}"
})

# HTTP metrics
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

HTTP_REQUEST_SIZE = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    buckets=[100, 1000, 10000, 100000, 1000000, 10000000]
)

HTTP_RESPONSE_SIZE = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    buckets=[100, 1000, 10000, 100000, 1000000, 10000000]
)

# Database metrics
DB_CONNECTIONS_ACTIVE = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

DB_CONNECTIONS_TOTAL = Counter(
    'db_connections_total',
    'Total database connections created'
)

DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

DB_QUERIES_TOTAL = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'status']
)

# Job metrics
JOB_DURATION = Histogram(
    'job_duration_seconds',
    'Job execution duration in seconds',
    ['job_name'],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600]
)

JOB_SUCCESS_TOTAL = Counter(
    'job_success_total',
    'Total successful job executions',
    ['job_name']
)

JOB_FAILURES_TOTAL = Counter(
    'job_failures_total',
    'Total failed job executions',
    ['job_name', 'error_type']
)

JOB_LAST_SUCCESS = Gauge(
    'job_last_success_timestamp',
    'Timestamp of last successful job execution',
    ['job_name']
)

# Upload metrics
UPLOAD_FILES_TOTAL = Counter(
    'upload_files_total',
    'Total files uploaded',
    ['file_type', 'status']
)

UPLOAD_SIZE_BYTES = Histogram(
    'upload_size_bytes',
    'Upload file size in bytes',
    ['file_type'],
    buckets=[1000, 10000, 100000, 1000000, 10000000, 100000000]
)

UPLOAD_PROCESSING_DURATION = Histogram(
    'upload_processing_duration_seconds',
    'Upload processing duration in seconds',
    ['file_type'],
    buckets=[1, 5, 10, 30, 60, 300, 600]
)

UPLOAD_FAILURES_TOTAL = Counter(
    'upload_failures_total',
    'Total upload failures',
    ['file_type', 'error_type']
)

# Business metrics
RISK_BATCHES_TOTAL = Gauge(
    'risk_batches_total',
    'Total number of batches at risk'
)

RISK_VALUE_TOTAL = Gauge(
    'risk_value_total',
    'Total value of inventory at risk'
)

ACTIONS_GENERATED_TOTAL = Counter(
    'actions_generated_total',
    'Total actions generated',
    ['action_type']
)

ACTIONS_COMPLETED_TOTAL = Counter(
    'actions_completed_total',
    'Total actions completed',
    ['action_type', 'status']
)

SAVINGS_TOTAL = Gauge(
    'savings_total',
    'Total savings achieved'
)

# System metrics
SYSTEM_CPU_USAGE = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

SYSTEM_MEMORY_USAGE = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes'
)

SYSTEM_DISK_USAGE = Gauge(
    'system_disk_usage_bytes',
    'System disk usage in bytes',
    ['path']
)

PROCESS_MEMORY_USAGE = Gauge(
    'process_memory_usage_bytes',
    'Process memory usage in bytes'
)

PROCESS_CPU_USAGE = Gauge(
    'process_cpu_usage_percent',
    'Process CPU usage percentage'
)

# Application state
APP_HEALTH_STATUS = Enum(
    'app_health_status',
    'Application health status',
    states=['healthy', 'degraded', 'unhealthy']
)

APP_UPTIME = Gauge(
    'app_uptime_seconds',
    'Application uptime in seconds'
)

# Initialize application state
APP_HEALTH_STATUS.state('healthy')
_start_time = time.time()


class MetricsCollector:
    """Centralized metrics collection and management."""
    
    def __init__(self):
        self.enabled = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
        self._system_metrics_thread = None
        self._stop_event = threading.Event()
        
        if self.enabled and PROMETHEUS_AVAILABLE:
            self._start_system_metrics_collection()
    
    def _start_system_metrics_collection(self):
        """Start background thread for system metrics collection."""
        def collect_system_metrics():
            while not self._stop_event.wait(30):  # Collect every 30 seconds
                try:
                    # CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    SYSTEM_CPU_USAGE.set(cpu_percent)
                    
                    # Memory usage
                    memory = psutil.virtual_memory()
                    SYSTEM_MEMORY_USAGE.set(memory.used)
                    
                    # Disk usage
                    for path in ['/app', '/app/uploads', '/app/logs']:
                        if os.path.exists(path):
                            disk = psutil.disk_usage(path)
                            SYSTEM_DISK_USAGE.labels(path=path).set(disk.used)
                    
                    # Process metrics
                    process = psutil.Process()
                    PROCESS_MEMORY_USAGE.set(process.memory_info().rss)
                    PROCESS_CPU_USAGE.set(process.cpu_percent())
                    
                    # Application uptime
                    APP_UPTIME.set(time.time() - _start_time)
                    
                except Exception as e:
                    logger.error(f"Error collecting system metrics: {e}")
        
        self._system_metrics_thread = threading.Thread(
            target=collect_system_metrics,
            daemon=True
        )
        self._system_metrics_thread.start()
        logger.info("Started system metrics collection thread")
    
    def stop(self):
        """Stop metrics collection."""
        if self._system_metrics_thread:
            self._stop_event.set()
            self._system_metrics_thread.join(timeout=5)
            logger.info("Stopped system metrics collection")
    
    def record_http_request(self, method: str, endpoint: str, status: int, 
                          duration: float, request_size: int = 0, 
                          response_size: int = 0):
        """Record HTTP request metrics."""
        if not self.enabled:
            return
        
        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()
        
        HTTP_REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        if request_size > 0:
            HTTP_REQUEST_SIZE.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)
        
        if response_size > 0:
            HTTP_RESPONSE_SIZE.labels(
                method=method,
                endpoint=endpoint
            ).observe(response_size)
    
    def record_db_query(self, operation: str, duration: float, success: bool = True):
        """Record database query metrics."""
        if not self.enabled:
            return
        
        DB_QUERIES_TOTAL.labels(
            operation=operation,
            status='success' if success else 'error'
        ).inc()
        
        DB_QUERY_DURATION.labels(operation=operation).observe(duration)
    
    def record_job_execution(self, job_name: str, duration: float, 
                           success: bool = True, error_type: str = None):
        """Record job execution metrics."""
        if not self.enabled:
            return
        
        JOB_DURATION.labels(job_name=job_name).observe(duration)
        
        if success:
            JOB_SUCCESS_TOTAL.labels(job_name=job_name).inc()
            JOB_LAST_SUCCESS.labels(job_name=job_name).set(time.time())
        else:
            JOB_FAILURES_TOTAL.labels(
                job_name=job_name,
                error_type=error_type or 'unknown'
            ).inc()
    
    def record_upload(self, file_type: str, size: int, processing_duration: float,
                     success: bool = True, error_type: str = None):
        """Record file upload metrics."""
        if not self.enabled:
            return
        
        status = 'success' if success else 'error'
        UPLOAD_FILES_TOTAL.labels(file_type=file_type, status=status).inc()
        
        if success:
            UPLOAD_SIZE_BYTES.labels(file_type=file_type).observe(size)
            UPLOAD_PROCESSING_DURATION.labels(file_type=file_type).observe(processing_duration)
        else:
            UPLOAD_FAILURES_TOTAL.labels(
                file_type=file_type,
                error_type=error_type or 'unknown'
            ).inc()
    
    def update_business_metrics(self, risk_batches: int = None, risk_value: float = None,
                              savings: float = None):
        """Update business-specific metrics."""
        if not self.enabled:
            return
        
        if risk_batches is not None:
            RISK_BATCHES_TOTAL.set(risk_batches)
        
        if risk_value is not None:
            RISK_VALUE_TOTAL.set(risk_value)
        
        if savings is not None:
            SAVINGS_TOTAL.set(savings)
    
    def record_action(self, action_type: str, generated: bool = False, 
                     completed: bool = False, status: str = None):
        """Record action metrics."""
        if not self.enabled:
            return
        
        if generated:
            ACTIONS_GENERATED_TOTAL.labels(action_type=action_type).inc()
        
        if completed:
            ACTIONS_COMPLETED_TOTAL.labels(
                action_type=action_type,
                status=status or 'unknown'
            ).inc()
    
    def set_health_status(self, status: str):
        """Set application health status."""
        if not self.enabled:
            return
        
        if status in ['healthy', 'degraded', 'unhealthy']:
            APP_HEALTH_STATUS.state(status)
    
    def get_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        if not self.enabled or not PROMETHEUS_AVAILABLE:
            return "# Metrics disabled or prometheus_client not available\n"
        
        try:
            return generate_latest(REGISTRY)
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return f"# Error generating metrics: {e}\n"


# Global metrics collector instance
metrics = MetricsCollector()


def monitor_function(metric_name: str = None, labels: Dict[str, str] = None):
    """Decorator to monitor function execution time and success rate."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not metrics.enabled:
                return func(*args, **kwargs)
            
            name = metric_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record success
                if hasattr(metrics, f'{name}_duration'):
                    getattr(metrics, f'{name}_duration').observe(duration)
                
                return result
            
            except Exception as e:
                duration = time.time() - start_time
                
                # Record failure
                if hasattr(metrics, f'{name}_failures'):
                    error_type = type(e).__name__
                    getattr(metrics, f'{name}_failures').labels(
                        error_type=error_type
                    ).inc()
                
                raise
        
        return wrapper
    return decorator


@contextmanager
def monitor_database_query(operation: str):
    """Context manager to monitor database query execution."""
    start_time = time.time()
    success = True
    
    try:
        yield
    except Exception:
        success = False
        raise
    finally:
        duration = time.time() - start_time
        metrics.record_db_query(operation, duration, success)


def setup_metrics_endpoint(app):
    """Setup metrics endpoint for FastAPI application."""
    if not PROMETHEUS_AVAILABLE:
        logger.warning("Prometheus client not available, metrics endpoint disabled")
        return
    
    @app.get("/metrics")
    async def get_metrics():
        """Prometheus metrics endpoint."""
        from fastapi import Response
        
        metrics_data = metrics.get_metrics()
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    
    logger.info("Metrics endpoint configured at /metrics")


def cleanup_metrics():
    """Cleanup metrics collection on application shutdown."""
    metrics.stop()


# Export commonly used functions and classes
__all__ = [
    'metrics',
    'monitor_function',
    'monitor_database_query',
    'setup_metrics_endpoint',
    'cleanup_metrics',
    'MetricsCollector'
]