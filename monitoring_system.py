#!/usr/bin/env python3
"""
Production Monitoring and Alerting System
Real-time monitoring with alerts for critical issues
"""

import os
import sys
import time
import json
import smtplib
import logging
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Alert:
    """Alert notification"""
    level: str  # INFO, WARNING, CRITICAL
    category: str  # CPU, MEMORY, ERROR, SECURITY, etc.
    message: str
    timestamp: datetime
    details: Dict = field(default_factory=dict)
    
@dataclass
class HealthCheck:
    """Health check result"""
    service: str
    status: str  # HEALTHY, DEGRADED, DOWN
    response_time: float
    details: Dict
    timestamp: datetime

class MonitoringSystem:
    """Comprehensive monitoring and alerting system"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.alerts: deque = deque(maxlen=1000)  # Keep last 1000 alerts
        self.metrics_history: deque = deque(maxlen=10000)  # Keep last 10000 metrics
        self.health_checks: Dict[str, HealthCheck] = {}
        self.monitoring_active = False
        self.alert_handlers: List[Callable] = []
        
        # Alert thresholds
        self.thresholds = {
            'cpu_critical': 90,
            'cpu_warning': 75,
            'memory_critical': 90,
            'memory_warning': 80,
            'disk_critical': 95,
            'disk_warning': 85,
            'error_rate_critical': 5,  # 5% error rate
            'error_rate_warning': 2,
            'response_time_critical': 5000,  # 5 seconds
            'response_time_warning': 2000,  # 2 seconds
        }
        
        # Update thresholds from config
        self.thresholds.update(self.config.get('thresholds', {}))
        
    def start(self):
        """Start monitoring system"""
        self.monitoring_active = True
        
        # Start monitoring threads
        threads = [
            threading.Thread(target=self._monitor_system_resources, daemon=True),
            threading.Thread(target=self._monitor_application_health, daemon=True),
            threading.Thread(target=self._monitor_security, daemon=True),
            threading.Thread(target=self._process_alerts, daemon=True),
        ]
        
        for thread in threads:
            thread.start()
            
        logger.info("Monitoring system started")
        
    def stop(self):
        """Stop monitoring system"""
        self.monitoring_active = False
        logger.info("Monitoring system stopped")
        
    def _monitor_system_resources(self):
        """Monitor system resource usage"""
        while self.monitoring_active:
            try:
                # CPU monitoring
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > self.thresholds['cpu_critical']:
                    self._create_alert(
                        level='CRITICAL',
                        category='CPU',
                        message=f'Critical CPU usage: {cpu_percent}%',
                        details={'cpu_percent': cpu_percent}
                    )
                elif cpu_percent > self.thresholds['cpu_warning']:
                    self._create_alert(
                        level='WARNING',
                        category='CPU',
                        message=f'High CPU usage: {cpu_percent}%',
                        details={'cpu_percent': cpu_percent}
                    )
                    
                # Memory monitoring
                memory = psutil.virtual_memory()
                if memory.percent > self.thresholds['memory_critical']:
                    self._create_alert(
                        level='CRITICAL',
                        category='MEMORY',
                        message=f'Critical memory usage: {memory.percent}%',
                        details={'memory_percent': memory.percent, 'available_mb': memory.available / 1024 / 1024}
                    )
                elif memory.percent > self.thresholds['memory_warning']:
                    self._create_alert(
                        level='WARNING',
                        category='MEMORY',
                        message=f'High memory usage: {memory.percent}%',
                        details={'memory_percent': memory.percent}
                    )
                    
                # Disk monitoring
                disk = psutil.disk_usage('/')
                if disk.percent > self.thresholds['disk_critical']:
                    self._create_alert(
                        level='CRITICAL',
                        category='DISK',
                        message=f'Critical disk usage: {disk.percent}%',
                        details={'disk_percent': disk.percent, 'free_gb': disk.free / 1024 / 1024 / 1024}
                    )
                elif disk.percent > self.thresholds['disk_warning']:
                    self._create_alert(
                        level='WARNING',
                        category='DISK',
                        message=f'High disk usage: {disk.percent}%',
                        details={'disk_percent': disk.percent}
                    )
                    
                # Store metrics
                self.metrics_history.append({
                    'timestamp': datetime.now(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent,
                    'network_connections': len(psutil.net_connections()),
                    'process_count': len(psutil.pids()),
                })
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                time.sleep(30)
                
    def _monitor_application_health(self):
        """Monitor application health"""
        while self.monitoring_active:
            try:
                # Check database connectivity
                db_health = self._check_database_health()
                self.health_checks['database'] = db_health
                
                if db_health.status == 'DOWN':
                    self._create_alert(
                        level='CRITICAL',
                        category='DATABASE',
                        message='Database connection lost',
                        details=db_health.details
                    )
                elif db_health.status == 'DEGRADED':
                    self._create_alert(
                        level='WARNING',
                        category='DATABASE',
                        message='Database performance degraded',
                        details=db_health.details
                    )
                    
                # Check cache health
                cache_health = self._check_cache_health()
                self.health_checks['cache'] = cache_health
                
                # Check MLflow health
                mlflow_health = self._check_mlflow_health()
                self.health_checks['mlflow'] = mlflow_health
                
                # Check API health
                api_health = self._check_api_health()
                self.health_checks['api'] = api_health
                
                if api_health.response_time > self.thresholds['response_time_critical']:
                    self._create_alert(
                        level='CRITICAL',
                        category='PERFORMANCE',
                        message=f'Critical response time: {api_health.response_time}ms',
                        details=api_health.details
                    )
                elif api_health.response_time > self.thresholds['response_time_warning']:
                    self._create_alert(
                        level='WARNING',
                        category='PERFORMANCE',
                        message=f'Slow response time: {api_health.response_time}ms',
                        details=api_health.details
                    )
                    
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(60)
                
    def _monitor_security(self):
        """Monitor security events"""
        while self.monitoring_active:
            try:
                # Check for suspicious patterns
                suspicious_patterns = self._check_suspicious_activity()
                
                if suspicious_patterns:
                    for pattern in suspicious_patterns:
                        self._create_alert(
                            level='WARNING',
                            category='SECURITY',
                            message=f'Suspicious activity detected: {pattern["type"]}',
                            details=pattern
                        )
                        
                # Check for authentication failures
                auth_failures = self._check_auth_failures()
                if auth_failures > 5:
                    self._create_alert(
                        level='CRITICAL',
                        category='SECURITY',
                        message=f'Multiple authentication failures: {auth_failures}',
                        details={'failure_count': auth_failures}
                    )
                    
                # Check for data exposure risks
                exposure_risks = self._check_data_exposure()
                if exposure_risks:
                    self._create_alert(
                        level='CRITICAL',
                        category='SECURITY',
                        message='Potential data exposure detected',
                        details={'risks': exposure_risks}
                    )
                    
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Security monitoring error: {e}")
                time.sleep(120)
                
    def _check_database_health(self) -> HealthCheck:
        """Check database health"""
        start_time = time.time()
        
        try:
            # Simulate database check (in production, would actually connect)
            time.sleep(0.1)  # Simulate query time
            
            return HealthCheck(
                service='database',
                status='HEALTHY',
                response_time=(time.time() - start_time) * 1000,
                details={'connections': 5, 'queries_per_second': 100},
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthCheck(
                service='database',
                status='DOWN',
                response_time=-1,
                details={'error': str(e)},
                timestamp=datetime.now()
            )
            
    def _check_cache_health(self) -> HealthCheck:
        """Check cache system health"""
        try:
            # Check cache directory size
            cache_dir = Path('./cache')
            if cache_dir.exists():
                size_mb = sum(f.stat().st_size for f in cache_dir.rglob('*')) / 1024 / 1024
                
                status = 'HEALTHY'
                if size_mb > 400:
                    status = 'DEGRADED'
                    
                return HealthCheck(
                    service='cache',
                    status=status,
                    response_time=0,
                    details={'size_mb': size_mb, 'files': len(list(cache_dir.rglob('*')))},
                    timestamp=datetime.now()
                )
            else:
                return HealthCheck(
                    service='cache',
                    status='HEALTHY',
                    response_time=0,
                    details={'size_mb': 0},
                    timestamp=datetime.now()
                )
        except Exception as e:
            return HealthCheck(
                service='cache',
                status='DOWN',
                response_time=-1,
                details={'error': str(e)},
                timestamp=datetime.now()
            )
            
    def _check_mlflow_health(self) -> HealthCheck:
        """Check MLflow health"""
        try:
            # In production, would check actual MLflow server
            return HealthCheck(
                service='mlflow',
                status='HEALTHY',
                response_time=50,
                details={'experiments': 10, 'runs': 100},
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthCheck(
                service='mlflow',
                status='DOWN',
                response_time=-1,
                details={'error': str(e)},
                timestamp=datetime.now()
            )
            
    def _check_api_health(self) -> HealthCheck:
        """Check API health"""
        start_time = time.time()
        
        try:
            # Simulate API check
            time.sleep(0.05)
            
            return HealthCheck(
                service='api',
                status='HEALTHY',
                response_time=(time.time() - start_time) * 1000,
                details={'endpoints_tested': 5, 'all_responsive': True},
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthCheck(
                service='api',
                status='DOWN',
                response_time=-1,
                details={'error': str(e)},
                timestamp=datetime.now()
            )
            
    def _check_suspicious_activity(self) -> List[Dict]:
        """Check for suspicious activity patterns"""
        suspicious = []
        
        # Check recent alerts for patterns
        recent_alerts = [a for a in self.alerts if 
                        (datetime.now() - a.timestamp).seconds < 300]  # Last 5 minutes
        
        # Too many errors
        error_alerts = [a for a in recent_alerts if 'ERROR' in a.category]
        if len(error_alerts) > 10:
            suspicious.append({
                'type': 'excessive_errors',
                'count': len(error_alerts)
            })
            
        return suspicious
        
    def _check_auth_failures(self) -> int:
        """Check authentication failure count"""
        # In production, would check actual auth logs
        return 0
        
    def _check_data_exposure(self) -> List[str]:
        """Check for data exposure risks"""
        risks = []
        
        # Check if sensitive data in logs
        log_files = Path('.').glob('*.log')
        for log_file in log_files:
            try:
                content = log_file.read_text()
                if 'password' in content.lower() or 'api_key' in content.lower():
                    risks.append(f"Sensitive data in {log_file}")
            except:
                pass
                
        return risks
        
    def _create_alert(self, level: str, category: str, message: str, details: Dict = None):
        """Create and queue an alert"""
        alert = Alert(
            level=level,
            category=category,
            message=message,
            timestamp=datetime.now(),
            details=details or {}
        )
        
        self.alerts.append(alert)
        
        # Log alert
        if level == 'CRITICAL':
            logger.critical(f"[{category}] {message}")
        elif level == 'WARNING':
            logger.warning(f"[{category}] {message}")
        else:
            logger.info(f"[{category}] {message}")
            
    def _process_alerts(self):
        """Process and send alerts"""
        while self.monitoring_active:
            try:
                # Check for critical alerts to send
                recent_critical = [
                    a for a in self.alerts 
                    if a.level == 'CRITICAL' and 
                    (datetime.now() - a.timestamp).seconds < 60
                ]
                
                if recent_critical:
                    # Send alert notifications
                    for handler in self.alert_handlers:
                        handler(recent_critical)
                        
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
                time.sleep(30)
                
    def add_alert_handler(self, handler: Callable):
        """Add custom alert handler"""
        self.alert_handlers.append(handler)
        
    def get_system_status(self) -> Dict:
        """Get current system status"""
        # Get latest metrics
        latest_metrics = self.metrics_history[-1] if self.metrics_history else {}
        
        # Calculate alert counts
        recent_alerts = [a for a in self.alerts if 
                        (datetime.now() - a.timestamp).seconds < 3600]  # Last hour
        
        alert_summary = {
            'critical': len([a for a in recent_alerts if a.level == 'CRITICAL']),
            'warning': len([a for a in recent_alerts if a.level == 'WARNING']),
            'info': len([a for a in recent_alerts if a.level == 'INFO'])
        }
        
        # Overall health
        if alert_summary['critical'] > 0:
            overall_health = 'CRITICAL'
        elif alert_summary['warning'] > 5:
            overall_health = 'DEGRADED'
        else:
            overall_health = 'HEALTHY'
            
        return {
            'overall_health': overall_health,
            'timestamp': datetime.now().isoformat(),
            'metrics': latest_metrics,
            'alert_summary': alert_summary,
            'health_checks': {
                name: {
                    'status': check.status,
                    'response_time': check.response_time
                }
                for name, check in self.health_checks.items()
            }
        }
        
    def generate_dashboard(self) -> str:
        """Generate monitoring dashboard"""
        status = self.get_system_status()
        
        dashboard = f"""
================================================================================
SYSTEM MONITORING DASHBOARD
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

OVERALL HEALTH: {status['overall_health']}

SYSTEM METRICS:
  CPU Usage: {status['metrics'].get('cpu_percent', 'N/A')}%
  Memory Usage: {status['metrics'].get('memory_percent', 'N/A')}%
  Disk Usage: {status['metrics'].get('disk_percent', 'N/A')}%
  Active Connections: {status['metrics'].get('network_connections', 'N/A')}
  Process Count: {status['metrics'].get('process_count', 'N/A')}

ALERTS (Last Hour):
  🔴 Critical: {status['alert_summary']['critical']}
  🟡 Warning: {status['alert_summary']['warning']}
  🔵 Info: {status['alert_summary']['info']}

SERVICE HEALTH:
"""
        
        for service, health in status['health_checks'].items():
            icon = "✅" if health['status'] == 'HEALTHY' else "⚠️" if health['status'] == 'DEGRADED' else "❌"
            dashboard += f"  {icon} {service}: {health['status']}"
            if health['response_time'] > 0:
                dashboard += f" ({health['response_time']:.0f}ms)"
            dashboard += "\n"
            
        dashboard += """
================================================================================
        """
        
        return dashboard

# Alert handler examples
def email_alert_handler(alerts: List[Alert]):
    """Send email alerts"""
    # In production, would send actual emails
    logger.info(f"Would send email for {len(alerts)} critical alerts")
    
def slack_alert_handler(alerts: List[Alert]):
    """Send Slack alerts"""
    # In production, would send to Slack
    logger.info(f"Would send Slack notification for {len(alerts)} critical alerts")
    
def pagerduty_alert_handler(alerts: List[Alert]):
    """Send PagerDuty alerts"""
    # In production, would trigger PagerDuty
    logger.info(f"Would trigger PagerDuty for {len(alerts)} critical alerts")

if __name__ == "__main__":
    print("Starting monitoring system...")
    
    # Create monitoring system
    monitor = MonitoringSystem({
        'thresholds': {
            'cpu_warning': 70,
            'memory_warning': 75
        }
    })
    
    # Add alert handlers
    monitor.add_alert_handler(email_alert_handler)
    monitor.add_alert_handler(slack_alert_handler)
    
    # Start monitoring
    monitor.start()
    
    try:
        # Run for demonstration
        for i in range(6):
            time.sleep(10)
            
            # Print dashboard
            print(monitor.generate_dashboard())
            
            # Simulate some issues for testing
            if i == 2:
                monitor._create_alert(
                    'WARNING',
                    'TEST',
                    'This is a test warning',
                    {'test': True}
                )
            if i == 4:
                monitor._create_alert(
                    'CRITICAL',
                    'TEST',
                    'This is a test critical alert',
                    {'test': True}
                )
                
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
    finally:
        monitor.stop()
        
        # Final status
        print("\nFinal System Status:")
        print(json.dumps(monitor.get_system_status(), indent=2, default=str))