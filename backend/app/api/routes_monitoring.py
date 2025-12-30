"""
Monitoring and observability API routes for ExpiryShield Backend.

This module provides endpoints for monitoring system health, performance metrics,
alerts, and operational dashboards.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from app.monitoring import metrics
from app.performance import performance_monitor, get_performance_report
from app.alerting import alert_manager, AlertSeverity, AlertStatus
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health/detailed")
async def get_detailed_health():
    """
    Get detailed health check with comprehensive system status.
    
    Returns detailed information about all system components including
    database, Redis, scheduled jobs, and performance metrics.
    """
    from app.db.session import get_db
    import os
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "uptime_seconds": metrics.APP_UPTIME._value._value if hasattr(metrics.APP_UPTIME, '_value') else 0,
        "checks": {}
    }
    
    # Database health check
    try:
        db = next(get_db())
        result = db.execute("SELECT 1, NOW()").fetchone()
        db.close()
        
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": 0,  # Could add timing
            "server_time": result[1].isoformat() if result else None
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Redis health check
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            info = r.info()
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "memory_usage_mb": round(info.get('used_memory', 0) / 1024 / 1024, 2),
                "connected_clients": info.get('connected_clients', 0)
            }
        except Exception as e:
            health_status["checks"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
    
    # Disk space check
    upload_dir = os.getenv("UPLOAD_DIR", "uploads")
    try:
        import shutil
        if os.path.exists(upload_dir):
            total, used, free = shutil.disk_usage(upload_dir)
            free_percent = (free / total) * 100
            health_status["checks"]["disk_space"] = {
                "status": "healthy" if free_percent > 10 else "warning",
                "free_percent": round(free_percent, 2),
                "free_gb": round(free / (1024**3), 2),
                "total_gb": round(total / (1024**3), 2)
            }
    except Exception as e:
        health_status["checks"]["disk_space"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # Scheduler health check
    if os.getenv("ENABLE_SCHEDULED_JOBS", "true").lower() == "true":
        try:
            from app.jobs.scheduler import scheduler
            health_status["checks"]["scheduler"] = {
                "status": "healthy" if scheduler.running else "stopped",
                "job_count": len(scheduler.get_jobs()),
                "next_run_time": None  # Could add next job run time
            }
        except Exception as e:
            health_status["checks"]["scheduler"] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Performance metrics summary
    perf_report = get_performance_report()
    health_status["performance"] = perf_report["summary"]
    
    # Alert summary
    alert_summary = alert_manager.get_alert_summary()
    health_status["alerts"] = alert_summary
    
    if alert_summary["by_severity"]["critical"] > 0:
        health_status["status"] = "unhealthy"
    elif alert_summary["by_severity"]["high"] > 0 or alert_summary["total_active"] > 5:
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/metrics/summary")
async def get_metrics_summary():
    """
    Get summary of key performance metrics.
    
    Returns aggregated metrics for monitoring dashboards including
    request rates, response times, error rates, and system resources.
    """
    summary = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "http_metrics": {
            "total_requests": metrics.HTTP_REQUESTS_TOTAL._value._value if hasattr(metrics.HTTP_REQUESTS_TOTAL, '_value') else 0,
            "avg_response_time_ms": performance_monitor.get_average_metric("response_time_ms", minutes=5),
            "error_rate_5min": performance_monitor.get_average_metric("error_rate_percent", minutes=5)
        },
        "database_metrics": {
            "active_connections": metrics.DB_CONNECTIONS_ACTIVE._value._value if hasattr(metrics.DB_CONNECTIONS_ACTIVE, '_value') else 0,
            "total_queries": metrics.DB_QUERIES_TOTAL._value._value if hasattr(metrics.DB_QUERIES_TOTAL, '_value') else 0,
            "avg_query_time_ms": performance_monitor.get_average_metric("db_query_time_ms", minutes=5)
        },
        "business_metrics": {
            "risk_batches": metrics.RISK_BATCHES_TOTAL._value._value if hasattr(metrics.RISK_BATCHES_TOTAL, '_value') else 0,
            "risk_value": metrics.RISK_VALUE_TOTAL._value._value if hasattr(metrics.RISK_VALUE_TOTAL, '_value') else 0,
            "total_savings": metrics.SAVINGS_TOTAL._value._value if hasattr(metrics.SAVINGS_TOTAL, '_value') else 0
        },
        "system_metrics": {
            "cpu_usage_percent": metrics.SYSTEM_CPU_USAGE._value._value if hasattr(metrics.SYSTEM_CPU_USAGE, '_value') else 0,
            "memory_usage_mb": round((metrics.SYSTEM_MEMORY_USAGE._value._value or 0) / 1024 / 1024, 2),
            "process_memory_mb": round((metrics.PROCESS_MEMORY_USAGE._value._value or 0) / 1024 / 1024, 2)
        }
    }
    
    return summary


@router.get("/alerts")
async def get_alerts(
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    status: Optional[AlertStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of alerts to return")
):
    """
    Get active alerts with optional filtering.
    
    Returns list of alerts filtered by severity and status with pagination support.
    """
    alerts = alert_manager.get_active_alerts(severity=severity)
    
    if status:
        alerts = [alert for alert in alerts if alert.status == status]
    
    # Limit results
    alerts = alerts[:limit]
    
    # Convert to dict for JSON serialization
    alert_data = []
    for alert in alerts:
        alert_dict = {
            "id": alert.id,
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "created_at": alert.created_at.isoformat(),
            "updated_at": alert.updated_at.isoformat(),
            "source": alert.source,
            "tags": alert.tags,
            "metadata": alert.metadata,
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
        }
        alert_data.append(alert_dict)
    
    return {
        "alerts": alert_data,
        "total": len(alert_data),
        "summary": alert_manager.get_alert_summary()
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Acknowledge an alert.
    
    Marks an alert as acknowledged by the current user.
    """
    success = alert_manager.acknowledge_alert(alert_id, current_user.get("username", "unknown"))
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert acknowledged successfully", "alert_id": alert_id}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Resolve an alert.
    
    Marks an alert as resolved and removes it from active alerts.
    """
    success = alert_manager.resolve_alert(alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert resolved successfully", "alert_id": alert_id}


@router.get("/performance")
async def get_performance_metrics():
    """
    Get detailed performance metrics and analysis.
    
    Returns comprehensive performance data including response times,
    resource usage, and performance trends.
    """
    return get_performance_report()


@router.get("/dashboard")
async def get_monitoring_dashboard():
    """
    Get comprehensive monitoring dashboard data.
    
    Returns all data needed for a monitoring dashboard including health status,
    metrics, alerts, and performance information.
    """
    dashboard_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "health": await get_detailed_health(),
        "metrics": await get_metrics_summary(),
        "alerts": await get_alerts(limit=10),
        "performance": get_performance_report(),
        "system_info": {
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "uptime_seconds": metrics.APP_UPTIME._value._value if hasattr(metrics.APP_UPTIME, '_value') else 0
        }
    }
    
    return dashboard_data


@router.get("/logs/recent")
async def get_recent_logs(
    level: str = Query("INFO", description="Log level filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of log entries"),
    minutes: int = Query(60, ge=1, le=1440, description="Time window in minutes")
):
    """
    Get recent log entries.
    
    Returns recent log entries filtered by level and time window.
    Note: This is a simplified implementation. In production, you'd integrate
    with your log aggregation system (ELK, Fluentd, etc.).
    """
    # This is a placeholder implementation
    # In production, you'd query your log aggregation system
    
    logs = [
        {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "INFO",
            "message": "Application started successfully",
            "source": "main",
            "request_id": None
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z",
            "level": "WARNING",
            "message": "High response time detected",
            "source": "middleware",
            "request_id": "req-123"
        }
    ]
    
    return {
        "logs": logs,
        "total": len(logs),
        "filters": {
            "level": level,
            "limit": limit,
            "minutes": minutes
        }
    }


@router.get("/jobs/status")
async def get_job_status():
    """
    Get status of scheduled jobs.
    
    Returns information about all scheduled jobs including their status,
    last run time, and next scheduled execution.
    """
    try:
        from app.jobs.scheduler import scheduler
        
        jobs = []
        for job in scheduler.get_jobs():
            job_info = {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "func": f"{job.func.__module__}.{job.func.__name__}" if hasattr(job.func, '__name__') else str(job.func)
            }
            jobs.append(job_info)
        
        return {
            "scheduler_running": scheduler.running,
            "job_count": len(jobs),
            "jobs": jobs
        }
        
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving job status")


@router.post("/test-alert")
async def create_test_alert(
    severity: AlertSeverity = AlertSeverity.LOW,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a test alert for testing monitoring systems.
    
    Creates a test alert with specified severity for testing purposes.
    """
    alert = alert_manager.create_alert(
        title="Test Alert",
        description=f"This is a test alert created by {current_user.get('username', 'unknown')}",
        severity=severity,
        source="manual_test",
        tags={"created_by": current_user.get("username", "unknown")},
        metadata={"test": True, "created_at": datetime.utcnow().isoformat()}
    )
    
    return {
        "message": "Test alert created successfully",
        "alert_id": alert.id,
        "alert": {
            "id": alert.id,
            "title": alert.title,
            "severity": alert.severity.value,
            "created_at": alert.created_at.isoformat()
        }
    }


# Add import for os
import os