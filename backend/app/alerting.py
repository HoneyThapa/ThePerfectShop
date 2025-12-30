"""
Alerting system for ExpiryShield Backend.

This module provides alerting capabilities for monitoring system health,
performance issues, and business-critical events.
"""

import logging
import smtplib
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText as MimeText
from email.mime.multipart import MIMEMultipart as MimeMultipart
from enum import Enum
import os
import asyncio
from app.monitoring import metrics

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class Alert:
    """Alert data structure."""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    created_at: datetime
    updated_at: datetime
    source: str
    tags: Dict[str, str]
    metadata: Dict[str, Any]
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class AlertManager:
    """Centralized alert management system."""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_rules: List[Dict[str, Any]] = []
        self.notification_channels: List[Callable] = []
        self.suppression_rules: List[Dict[str, Any]] = []
        
        # Load configuration
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'localhost'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'smtp_username': os.getenv('SMTP_USERNAME'),
            'smtp_password': os.getenv('SMTP_PASSWORD'),
            'from_email': os.getenv('ALERT_FROM_EMAIL', 'alerts@expiryshield.com'),
            'to_emails': os.getenv('ALERT_TO_EMAILS', '').split(',')
        }
        
        # Initialize default alert rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default alerting rules."""
        self.alert_rules = [
            {
                'name': 'high_error_rate',
                'condition': lambda metrics: self._check_error_rate(metrics),
                'severity': AlertSeverity.HIGH,
                'description': 'High error rate detected',
                'cooldown_minutes': 15
            },
            {
                'name': 'high_response_time',
                'condition': lambda metrics: self._check_response_time(metrics),
                'severity': AlertSeverity.MEDIUM,
                'description': 'High response time detected',
                'cooldown_minutes': 10
            },
            {
                'name': 'database_connection_issues',
                'condition': lambda metrics: self._check_database_health(metrics),
                'severity': AlertSeverity.CRITICAL,
                'description': 'Database connection issues detected',
                'cooldown_minutes': 5
            },
            {
                'name': 'high_memory_usage',
                'condition': lambda metrics: self._check_memory_usage(metrics),
                'severity': AlertSeverity.MEDIUM,
                'description': 'High memory usage detected',
                'cooldown_minutes': 20
            },
            {
                'name': 'job_failures',
                'condition': lambda metrics: self._check_job_failures(metrics),
                'severity': AlertSeverity.HIGH,
                'description': 'Multiple job failures detected',
                'cooldown_minutes': 30
            }
        ]
    
    def create_alert(
        self,
        title: str,
        description: str,
        severity: AlertSeverity,
        source: str,
        tags: Dict[str, str] = None,
        metadata: Dict[str, Any] = None
    ) -> Alert:
        """Create a new alert."""
        alert_id = f"{source}_{int(datetime.utcnow().timestamp())}"
        
        alert = Alert(
            id=alert_id,
            title=title,
            description=description,
            severity=severity,
            status=AlertStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            source=source,
            tags=tags or {},
            metadata=metadata or {}
        )
        
        # Check suppression rules
        if self._is_suppressed(alert):
            logger.info(f"Alert suppressed: {alert.title}")
            return alert
        
        # Add to active alerts
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Keep history limited
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        # Send notifications
        asyncio.create_task(self._send_notifications(alert))
        
        logger.warning(
            f"Alert created: {alert.title} ({alert.severity.value})",
            extra=asdict(alert)
        )
        
        return alert
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert."""
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()
        
        logger.info(f"Alert acknowledged: {alert.title} by {acknowledged_by}")
        return True
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()
        
        # Remove from active alerts
        del self.active_alerts[alert_id]
        
        logger.info(f"Alert resolved: {alert.title}")
        return True
    
    def get_active_alerts(self, severity: AlertSeverity = None) -> List[Alert]:
        """Get active alerts, optionally filtered by severity."""
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics."""
        active_alerts = list(self.active_alerts.values())
        
        summary = {
            'total_active': len(active_alerts),
            'by_severity': {
                'critical': len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                'high': len([a for a in active_alerts if a.severity == AlertSeverity.HIGH]),
                'medium': len([a for a in active_alerts if a.severity == AlertSeverity.MEDIUM]),
                'low': len([a for a in active_alerts if a.severity == AlertSeverity.LOW])
            },
            'by_status': {
                'active': len([a for a in active_alerts if a.status == AlertStatus.ACTIVE]),
                'acknowledged': len([a for a in active_alerts if a.status == AlertStatus.ACKNOWLEDGED])
            },
            'oldest_alert': min([a.created_at for a in active_alerts]) if active_alerts else None,
            'total_history': len(self.alert_history)
        }
        
        return summary
    
    def check_alert_rules(self, metrics_data: Dict[str, Any]):
        """Check all alert rules against current metrics."""
        for rule in self.alert_rules:
            try:
                # Check cooldown
                if self._is_in_cooldown(rule):
                    continue
                
                # Check condition
                if rule['condition'](metrics_data):
                    self.create_alert(
                        title=rule['name'].replace('_', ' ').title(),
                        description=rule['description'],
                        severity=rule['severity'],
                        source='alert_rule',
                        tags={'rule_name': rule['name']},
                        metadata={'rule': rule['name'], 'metrics': metrics_data}
                    )
                    
                    # Update last triggered time
                    rule['last_triggered'] = datetime.utcnow()
                    
            except Exception as e:
                logger.error(f"Error checking alert rule {rule['name']}: {e}")
    
    def _is_suppressed(self, alert: Alert) -> bool:
        """Check if alert should be suppressed."""
        for rule in self.suppression_rules:
            if self._matches_suppression_rule(alert, rule):
                return True
        return False
    
    def _matches_suppression_rule(self, alert: Alert, rule: Dict[str, Any]) -> bool:
        """Check if alert matches suppression rule."""
        # Simple implementation - can be extended
        if 'source' in rule and alert.source != rule['source']:
            return False
        
        if 'severity' in rule and alert.severity != rule['severity']:
            return False
        
        if 'tags' in rule:
            for key, value in rule['tags'].items():
                if alert.tags.get(key) != value:
                    return False
        
        return True
    
    def _is_in_cooldown(self, rule: Dict[str, Any]) -> bool:
        """Check if rule is in cooldown period."""
        if 'last_triggered' not in rule:
            return False
        
        cooldown_minutes = rule.get('cooldown_minutes', 10)
        cooldown_period = timedelta(minutes=cooldown_minutes)
        
        return datetime.utcnow() - rule['last_triggered'] < cooldown_period
    
    async def _send_notifications(self, alert: Alert):
        """Send alert notifications."""
        for channel in self.notification_channels:
            try:
                await channel(alert)
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
        
        # Send email notification if configured
        if self.email_config['smtp_username'] and self.email_config['to_emails']:
            try:
                await self._send_email_notification(alert)
            except Exception as e:
                logger.error(f"Error sending email notification: {e}")
    
    async def _send_email_notification(self, alert: Alert):
        """Send email notification for alert."""
        if not self.email_config['to_emails'][0]:  # Check if email list is not empty
            return
        
        subject = f"[ExpiryShield Alert] {alert.severity.value.upper()}: {alert.title}"
        
        body = f"""
Alert Details:
- Title: {alert.title}
- Description: {alert.description}
- Severity: {alert.severity.value.upper()}
- Source: {alert.source}
- Created: {alert.created_at.isoformat()}
- Tags: {json.dumps(alert.tags, indent=2)}

Metadata:
{json.dumps(alert.metadata, indent=2)}

Please investigate and acknowledge this alert in the monitoring dashboard.
        """
        
        msg = MimeMultipart()
        msg['From'] = self.email_config['from_email']
        msg['To'] = ', '.join(self.email_config['to_emails'])
        msg['Subject'] = subject
        
        msg.attach(MimeText(body, 'plain'))
        
        # Send email in background
        def send_email():
            try:
                server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
                server.starttls()
                if self.email_config['smtp_username']:
                    server.login(self.email_config['smtp_username'], self.email_config['smtp_password'])
                
                server.send_message(msg)
                server.quit()
                
                logger.info(f"Email notification sent for alert: {alert.title}")
                
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, send_email)
    
    # Alert rule condition methods
    def _check_error_rate(self, metrics_data: Dict[str, Any]) -> bool:
        """Check if error rate is too high."""
        # This would check actual metrics - simplified for example
        error_rate = metrics_data.get('error_rate_percent', 0)
        return error_rate > 5  # 5% error rate threshold
    
    def _check_response_time(self, metrics_data: Dict[str, Any]) -> bool:
        """Check if response time is too high."""
        avg_response_time = metrics_data.get('avg_response_time_ms', 0)
        return avg_response_time > 2000  # 2 second threshold
    
    def _check_database_health(self, metrics_data: Dict[str, Any]) -> bool:
        """Check database health."""
        db_status = metrics_data.get('database_status', 'healthy')
        return db_status != 'healthy'
    
    def _check_memory_usage(self, metrics_data: Dict[str, Any]) -> bool:
        """Check memory usage."""
        memory_usage_mb = metrics_data.get('memory_usage_mb', 0)
        return memory_usage_mb > 1024  # 1GB threshold
    
    def _check_job_failures(self, metrics_data: Dict[str, Any]) -> bool:
        """Check for job failures."""
        job_failure_rate = metrics_data.get('job_failure_rate_percent', 0)
        return job_failure_rate > 10  # 10% failure rate threshold


# Global alert manager instance
alert_manager = AlertManager()


def create_alert(title: str, description: str, severity: AlertSeverity, 
                source: str, tags: Dict[str, str] = None, 
                metadata: Dict[str, Any] = None) -> Alert:
    """Convenience function to create an alert."""
    return alert_manager.create_alert(title, description, severity, source, tags, metadata)


def create_business_alert(title: str, description: str, severity: AlertSeverity = AlertSeverity.MEDIUM,
                         tags: Dict[str, str] = None, metadata: Dict[str, Any] = None) -> Alert:
    """Create a business-related alert."""
    return create_alert(title, description, severity, 'business', tags, metadata)


def create_system_alert(title: str, description: str, severity: AlertSeverity = AlertSeverity.HIGH,
                       tags: Dict[str, str] = None, metadata: Dict[str, Any] = None) -> Alert:
    """Create a system-related alert."""
    return create_alert(title, description, severity, 'system', tags, metadata)


def create_security_alert(title: str, description: str, severity: AlertSeverity = AlertSeverity.CRITICAL,
                         tags: Dict[str, str] = None, metadata: Dict[str, Any] = None) -> Alert:
    """Create a security-related alert."""
    return create_alert(title, description, severity, 'security', tags, metadata)


# Export commonly used functions and classes
__all__ = [
    'AlertManager',
    'Alert',
    'AlertSeverity',
    'AlertStatus',
    'alert_manager',
    'create_alert',
    'create_business_alert',
    'create_system_alert',
    'create_security_alert'
]