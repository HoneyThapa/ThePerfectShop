"""
Monitoring configuration for ExpiryShield Backend.

This module contains configuration settings for monitoring, alerting,
and observability features.
"""

import os
from typing import Dict, Any, List
from app.alerting import AlertSeverity


class MonitoringConfig:
    """Configuration class for monitoring settings."""
    
    # Metrics collection settings
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    METRICS_PORT = int(os.getenv('METRICS_PORT', '9090'))
    METRICS_PATH = '/metrics'
    
    # Performance monitoring thresholds
    PERFORMANCE_THRESHOLDS = {
        'response_time_ms': {
            'warning': 1000,   # 1 second
            'critical': 2000   # 2 seconds
        },
        'memory_usage_mb': {
            'warning': 512,    # 512 MB
            'critical': 1024   # 1 GB
        },
        'cpu_usage_percent': {
            'warning': 70,     # 70%
            'critical': 85     # 85%
        },
        'error_rate_percent': {
            'warning': 2,      # 2%
            'critical': 5      # 5%
        },
        'db_query_time_ms': {
            'warning': 500,    # 500ms
            'critical': 1000   # 1 second
        }
    }
    
    # Alert configuration
    ALERT_CONFIG = {
        'email': {
            'enabled': os.getenv('ALERT_EMAIL_ENABLED', 'false').lower() == 'true',
            'smtp_server': os.getenv('SMTP_SERVER', 'localhost'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'smtp_username': os.getenv('SMTP_USERNAME'),
            'smtp_password': os.getenv('SMTP_PASSWORD'),
            'from_email': os.getenv('ALERT_FROM_EMAIL', 'alerts@expiryshield.com'),
            'to_emails': [email.strip() for email in os.getenv('ALERT_TO_EMAILS', '').split(',') if email.strip()]
        },
        'webhook': {
            'enabled': os.getenv('ALERT_WEBHOOK_ENABLED', 'false').lower() == 'true',
            'url': os.getenv('ALERT_WEBHOOK_URL'),
            'timeout': int(os.getenv('ALERT_WEBHOOK_TIMEOUT', '10'))
        },
        'slack': {
            'enabled': os.getenv('ALERT_SLACK_ENABLED', 'false').lower() == 'true',
            'webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
            'channel': os.getenv('SLACK_CHANNEL', '#alerts')
        }
    }
    
    # Alert rules configuration
    ALERT_RULES = [
        {
            'name': 'high_error_rate',
            'description': 'High error rate detected',
            'severity': AlertSeverity.HIGH,
            'condition': 'error_rate_percent > 5',
            'cooldown_minutes': 15,
            'enabled': True
        },
        {
            'name': 'high_response_time',
            'description': 'High response time detected',
            'severity': AlertSeverity.MEDIUM,
            'condition': 'avg_response_time_ms > 2000',
            'cooldown_minutes': 10,
            'enabled': True
        },
        {
            'name': 'database_connection_issues',
            'description': 'Database connection issues detected',
            'severity': AlertSeverity.CRITICAL,
            'condition': 'database_status != "healthy"',
            'cooldown_minutes': 5,
            'enabled': True
        },
        {
            'name': 'high_memory_usage',
            'description': 'High memory usage detected',
            'severity': AlertSeverity.MEDIUM,
            'condition': 'memory_usage_mb > 1024',
            'cooldown_minutes': 20,
            'enabled': True
        },
        {
            'name': 'job_failures',
            'description': 'Multiple job failures detected',
            'severity': AlertSeverity.HIGH,
            'condition': 'job_failure_rate_percent > 10',
            'cooldown_minutes': 30,
            'enabled': True
        },
        {
            'name': 'disk_space_low',
            'description': 'Low disk space detected',
            'severity': AlertSeverity.HIGH,
            'condition': 'disk_free_percent < 10',
            'cooldown_minutes': 60,
            'enabled': True
        },
        {
            'name': 'high_upload_failure_rate',
            'description': 'High upload failure rate detected',
            'severity': AlertSeverity.MEDIUM,
            'condition': 'upload_failure_rate_percent > 5',
            'cooldown_minutes': 15,
            'enabled': True
        }
    ]
    
    # Logging configuration for monitoring
    LOGGING_CONFIG = {
        'level': os.getenv('LOG_LEVEL', 'INFO'),
        'format': os.getenv('LOG_FORMAT', 'json'),
        'file_path': os.getenv('LOG_FILE_PATH', 'logs/expiryshield.log'),
        'max_size_mb': int(os.getenv('LOG_MAX_SIZE_MB', '10')),
        'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5')),
        'structured_logging': True,
        'include_request_id': True
    }
    
    # Health check configuration
    HEALTH_CHECK_CONFIG = {
        'timeout_seconds': int(os.getenv('HEALTH_CHECK_TIMEOUT', '10')),
        'interval_seconds': int(os.getenv('HEALTH_CHECK_INTERVAL', '30')),
        'failure_threshold': int(os.getenv('HEALTH_CHECK_FAILURE_THRESHOLD', '3')),
        'success_threshold': int(os.getenv('HEALTH_CHECK_SUCCESS_THRESHOLD', '1'))
    }
    
    # Prometheus configuration
    PROMETHEUS_CONFIG = {
        'enabled': ENABLE_METRICS,
        'port': METRICS_PORT,
        'path': METRICS_PATH,
        'job_name': 'expiryshield-backend',
        'scrape_interval': '30s',
        'scrape_timeout': '10s',
        'metrics_retention': '7d'
    }
    
    # Grafana dashboard configuration
    GRAFANA_CONFIG = {
        'enabled': os.getenv('GRAFANA_ENABLED', 'false').lower() == 'true',
        'port': int(os.getenv('GRAFANA_PORT', '3000')),
        'admin_password': os.getenv('GRAFANA_PASSWORD', 'admin'),
        'dashboards': [
            'expiryshield-overview',
            'expiryshield-performance',
            'expiryshield-business-metrics',
            'expiryshield-alerts'
        ]
    }
    
    # Business metrics configuration
    BUSINESS_METRICS_CONFIG = {
        'update_interval_minutes': int(os.getenv('BUSINESS_METRICS_UPDATE_INTERVAL', '5')),
        'retention_days': int(os.getenv('BUSINESS_METRICS_RETENTION_DAYS', '90')),
        'aggregation_levels': ['hourly', 'daily', 'weekly', 'monthly'],
        'key_metrics': [
            'total_risk_value',
            'total_savings',
            'actions_generated',
            'actions_completed',
            'inventory_turnover',
            'write_off_reduction'
        ]
    }
    
    # Security monitoring configuration
    SECURITY_MONITORING_CONFIG = {
        'enabled': os.getenv('SECURITY_MONITORING_ENABLED', 'true').lower() == 'true',
        'suspicious_activity_threshold': int(os.getenv('SUSPICIOUS_ACTIVITY_THRESHOLD', '10')),
        'rate_limit_monitoring': True,
        'failed_auth_monitoring': True,
        'sql_injection_detection': True,
        'xss_detection': True,
        'log_security_events': True
    }
    
    # Performance monitoring configuration
    PERFORMANCE_MONITORING_CONFIG = {
        'enabled': True,
        'collection_interval_seconds': int(os.getenv('PERFORMANCE_COLLECTION_INTERVAL', '30')),
        'history_retention_hours': int(os.getenv('PERFORMANCE_HISTORY_RETENTION_HOURS', '24')),
        'alert_on_degradation': True,
        'track_slow_queries': True,
        'track_memory_leaks': True,
        'track_cpu_spikes': True
    }
    
    @classmethod
    def get_alert_rule_by_name(cls, name: str) -> Dict[str, Any]:
        """Get alert rule configuration by name."""
        for rule in cls.ALERT_RULES:
            if rule['name'] == name:
                return rule
        return None
    
    @classmethod
    def is_alert_enabled(cls, name: str) -> bool:
        """Check if an alert rule is enabled."""
        rule = cls.get_alert_rule_by_name(name)
        return rule and rule.get('enabled', False)
    
    @classmethod
    def get_threshold(cls, metric_name: str, level: str = 'warning') -> float:
        """Get threshold value for a metric."""
        thresholds = cls.PERFORMANCE_THRESHOLDS.get(metric_name, {})
        return thresholds.get(level, 0)
    
    @classmethod
    def get_monitoring_summary(cls) -> Dict[str, Any]:
        """Get summary of monitoring configuration."""
        return {
            'metrics_enabled': cls.ENABLE_METRICS,
            'alerts_enabled': any(rule['enabled'] for rule in cls.ALERT_RULES),
            'email_alerts_enabled': cls.ALERT_CONFIG['email']['enabled'],
            'webhook_alerts_enabled': cls.ALERT_CONFIG['webhook']['enabled'],
            'slack_alerts_enabled': cls.ALERT_CONFIG['slack']['enabled'],
            'security_monitoring_enabled': cls.SECURITY_MONITORING_CONFIG['enabled'],
            'performance_monitoring_enabled': cls.PERFORMANCE_MONITORING_CONFIG['enabled'],
            'total_alert_rules': len(cls.ALERT_RULES),
            'enabled_alert_rules': len([r for r in cls.ALERT_RULES if r['enabled']]),
            'prometheus_enabled': cls.PROMETHEUS_CONFIG['enabled'],
            'grafana_enabled': cls.GRAFANA_CONFIG['enabled']
        }


# Export configuration instance
monitoring_config = MonitoringConfig()

# Export commonly used configurations
__all__ = [
    'MonitoringConfig',
    'monitoring_config'
]