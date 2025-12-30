"""
Performance monitoring utilities for ExpiryShield Backend.

This module provides utilities for monitoring application performance,
database query performance, and system resource usage.
"""

import time
import functools
import asyncio
import psutil
import logging
from typing import Dict, Any, Optional, Callable, List
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime, timedelta
from dataclasses import dataclass
from app.monitoring import metrics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = None


class PerformanceMonitor:
    """Performance monitoring and alerting system."""
    
    def __init__(self):
        self.metrics_history: List[PerformanceMetric] = []
        self.alert_thresholds = {
            'response_time_ms': 2000,  # 2 seconds
            'memory_usage_mb': 1024,   # 1GB
            'cpu_usage_percent': 80,   # 80%
            'db_query_time_ms': 1000,  # 1 second
            'error_rate_percent': 5,   # 5%
        }
        self.performance_alerts: List[Dict[str, Any]] = []
    
    def record_metric(self, name: str, value: float, unit: str, tags: Dict[str, str] = None):
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.utcnow(),
            tags=tags or {}
        )
        
        self.metrics_history.append(metric)
        
        # Keep only last 1000 metrics to prevent memory issues
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        # Check for alerts
        self._check_alert_thresholds(metric)
    
    def _check_alert_thresholds(self, metric: PerformanceMetric):
        """Check if metric exceeds alert thresholds."""
        threshold = self.alert_thresholds.get(metric.name)
        if threshold and metric.value > threshold:
            alert = {
                'metric_name': metric.name,
                'value': metric.value,
                'threshold': threshold,
                'unit': metric.unit,
                'timestamp': metric.timestamp,
                'tags': metric.tags
            }
            
            self.performance_alerts.append(alert)
            logger.warning(
                f"Performance alert: {metric.name} = {metric.value}{metric.unit} "
                f"exceeds threshold {threshold}{metric.unit}",
                extra=alert
            )
            
            # Keep only last 100 alerts
            if len(self.performance_alerts) > 100:
                self.performance_alerts = self.performance_alerts[-100:]
    
    def get_recent_metrics(self, name: str, minutes: int = 5) -> List[PerformanceMetric]:
        """Get recent metrics for a specific metric name."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [
            metric for metric in self.metrics_history
            if metric.name == name and metric.timestamp > cutoff_time
        ]
    
    def get_average_metric(self, name: str, minutes: int = 5) -> Optional[float]:
        """Get average value for a metric over the specified time period."""
        recent_metrics = self.get_recent_metrics(name, minutes)
        if not recent_metrics:
            return None
        
        return sum(metric.value for metric in recent_metrics) / len(recent_metrics)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of current performance metrics."""
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {},
            'alerts': len(self.performance_alerts),
            'system': self._get_system_metrics()
        }
        
        # Calculate averages for key metrics
        for metric_name in ['response_time_ms', 'memory_usage_mb', 'cpu_usage_percent']:
            avg_value = self.get_average_metric(metric_name, minutes=5)
            if avg_value is not None:
                summary['metrics'][metric_name] = {
                    'average_5min': round(avg_value, 2),
                    'threshold': self.alert_thresholds.get(metric_name)
                }
        
        return summary
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_rss_mb': round(memory_info.rss / 1024 / 1024, 2),
                'memory_vms_mb': round(memory_info.vms / 1024 / 1024, 2),
                'open_files': len(process.open_files()),
                'connections': len(process.connections()),
                'threads': process.num_threads()
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(metric_name: str = None, tags: Dict[str, str] = None):
    """Decorator to monitor function performance."""
    def decorator(func: Callable) -> Callable:
        name = metric_name or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Record performance metric
                    performance_monitor.record_metric(
                        f"{name}_duration_ms",
                        duration_ms,
                        'ms',
                        tags
                    )
                    
                    # Record success
                    performance_monitor.record_metric(
                        f"{name}_success_count",
                        1,
                        'count',
                        tags
                    )
                    
                    return result
                    
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Record error
                    error_tags = (tags or {}).copy()
                    error_tags['error_type'] = type(e).__name__
                    
                    performance_monitor.record_metric(
                        f"{name}_error_count",
                        1,
                        'count',
                        error_tags
                    )
                    
                    performance_monitor.record_metric(
                        f"{name}_duration_ms",
                        duration_ms,
                        'ms',
                        error_tags
                    )
                    
                    raise
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Record performance metric
                    performance_monitor.record_metric(
                        f"{name}_duration_ms",
                        duration_ms,
                        'ms',
                        tags
                    )
                    
                    # Record success
                    performance_monitor.record_metric(
                        f"{name}_success_count",
                        1,
                        'count',
                        tags
                    )
                    
                    return result
                    
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Record error
                    error_tags = (tags or {}).copy()
                    error_tags['error_type'] = type(e).__name__
                    
                    performance_monitor.record_metric(
                        f"{name}_error_count",
                        1,
                        'count',
                        error_tags
                    )
                    
                    performance_monitor.record_metric(
                        f"{name}_duration_ms",
                        duration_ms,
                        'ms',
                        error_tags
                    )
                    
                    raise
            
            return sync_wrapper
    
    return decorator


@contextmanager
def monitor_database_operation(operation: str, table: str = None):
    """Context manager to monitor database operations."""
    start_time = time.time()
    tags = {'operation': operation}
    if table:
        tags['table'] = table
    
    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        
        # Record to performance monitor
        performance_monitor.record_metric(
            'db_query_time_ms',
            duration_ms,
            'ms',
            tags
        )
        
        # Record to metrics system
        metrics.record_db_query(operation, duration_ms / 1000, success=True)
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        # Record error
        error_tags = tags.copy()
        error_tags['error_type'] = type(e).__name__
        
        performance_monitor.record_metric(
            'db_query_time_ms',
            duration_ms,
            'ms',
            error_tags
        )
        
        performance_monitor.record_metric(
            'db_error_count',
            1,
            'count',
            error_tags
        )
        
        # Record to metrics system
        metrics.record_db_query(operation, duration_ms / 1000, success=False)
        
        raise


@asynccontextmanager
async def monitor_async_operation(operation_name: str, tags: Dict[str, str] = None):
    """Async context manager to monitor operations."""
    start_time = time.time()
    operation_tags = tags or {}
    
    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        
        performance_monitor.record_metric(
            f"{operation_name}_duration_ms",
            duration_ms,
            'ms',
            operation_tags
        )
        
        performance_monitor.record_metric(
            f"{operation_name}_success_count",
            1,
            'count',
            operation_tags
        )
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        error_tags = operation_tags.copy()
        error_tags['error_type'] = type(e).__name__
        
        performance_monitor.record_metric(
            f"{operation_name}_duration_ms",
            duration_ms,
            'ms',
            error_tags
        )
        
        performance_monitor.record_metric(
            f"{operation_name}_error_count",
            1,
            'count',
            error_tags
        )
        
        raise


def monitor_file_upload(file_type: str, file_size: int):
    """Monitor file upload operations."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record upload metrics
                metrics.record_upload(
                    file_type=file_type,
                    size=file_size,
                    processing_duration=duration,
                    success=True
                )
                
                performance_monitor.record_metric(
                    'upload_processing_time_ms',
                    duration * 1000,
                    'ms',
                    {'file_type': file_type}
                )
                
                performance_monitor.record_metric(
                    'upload_file_size_bytes',
                    file_size,
                    'bytes',
                    {'file_type': file_type}
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                error_type = type(e).__name__
                
                # Record upload failure
                metrics.record_upload(
                    file_type=file_type,
                    size=file_size,
                    processing_duration=duration,
                    success=False,
                    error_type=error_type
                )
                
                performance_monitor.record_metric(
                    'upload_error_count',
                    1,
                    'count',
                    {'file_type': file_type, 'error_type': error_type}
                )
                
                raise
        
        return wrapper
    return decorator


def get_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report."""
    return {
        'summary': performance_monitor.get_performance_summary(),
        'recent_alerts': performance_monitor.performance_alerts[-10:],  # Last 10 alerts
        'system_health': {
            'status': 'healthy' if len(performance_monitor.performance_alerts) == 0 else 'degraded',
            'alert_count': len(performance_monitor.performance_alerts),
            'metrics_collected': len(performance_monitor.metrics_history)
        }
    }


# Export commonly used functions
__all__ = [
    'performance_monitor',
    'monitor_performance',
    'monitor_database_operation',
    'monitor_async_operation',
    'monitor_file_upload',
    'get_performance_report',
    'PerformanceMonitor',
    'PerformanceMetric'
]