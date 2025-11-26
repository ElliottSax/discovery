#!/usr/bin/env python3
"""
Production runner with all security features enabled
"""

import os
import sys
import time
import signal
from pathlib import Path

# Ensure all required environment variables are set
required_vars = ['DB_PASSWORD']
for var in required_vars:
    if not os.getenv(var):
        print(f"ERROR: {var} environment variable must be set")
        sys.exit(1)

# Configure secure logging
from config.logging_config import configure_production_logging
configure_production_logging()

import logging
logger = logging.getLogger(__name__)

# Import monitoring system
from monitoring_system import MonitoringSystem, email_alert_handler, slack_alert_handler

# Global monitoring system instance
monitor = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global monitor
    logger.info("Received shutdown signal, stopping services...")
    if monitor:
        monitor.stop()
    sys.exit(0)

def run_production_system():
    """Run the production monitoring and analysis system"""
    global monitor
    
    logger.info("Starting production system with security features enabled")
    logger.info("Database host: %s", os.getenv('DB_HOST', 'localhost'))
    logger.info("Cache max size: %s MB", os.getenv('CACHE_MAX_SIZE_MB', '500'))
    
    print("\n✅ Production system starting with:")
    print("  - Environment-based configuration")
    print("  - SQL injection protection")
    print("  - Sensitive data filtering in logs")
    print("  - Memory-managed caching")
    print("  - Thread-safe MLflow tracking")
    print("  - Robust error handling")
    print("  - Real-time monitoring and alerting")
    print("")
    
    # Create monitoring system with custom thresholds
    monitor = MonitoringSystem({
        'thresholds': {
            'cpu_warning': int(os.getenv('CPU_WARNING_THRESHOLD', '75')),
            'cpu_critical': int(os.getenv('CPU_CRITICAL_THRESHOLD', '90')),
            'memory_warning': int(os.getenv('MEMORY_WARNING_THRESHOLD', '80')),
            'memory_critical': int(os.getenv('MEMORY_CRITICAL_THRESHOLD', '90')),
        }
    })
    
    # Add alert handlers if configured
    if os.getenv('ENABLE_EMAIL_ALERTS', 'false').lower() == 'true':
        monitor.add_alert_handler(email_alert_handler)
        logger.info("Email alerts enabled")
    
    if os.getenv('ENABLE_SLACK_ALERTS', 'false').lower() == 'true':
        monitor.add_alert_handler(slack_alert_handler)
        logger.info("Slack alerts enabled")
    
    # Start monitoring
    monitor.start()
    logger.info("Monitoring system started successfully")
    
    # Main loop - print dashboard every 30 seconds
    dashboard_interval = int(os.getenv('DASHBOARD_INTERVAL', '30'))
    
    print(f"\nMonitoring system running. Dashboard updates every {dashboard_interval} seconds.")
    print("Press Ctrl+C to stop.\n")
    
    try:
        while True:
            # Generate and display dashboard
            dashboard = monitor.generate_dashboard()
            print(dashboard)
            
            # Check system status
            status = monitor.get_system_status()
            
            # Log critical issues
            if status['overall_health'] == 'CRITICAL':
                logger.critical("System in critical state!")
            elif status['overall_health'] == 'DEGRADED':
                logger.warning("System performance degraded")
            
            # Sleep until next update
            time.sleep(dashboard_interval)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
        raise
    finally:
        if monitor:
            monitor.stop()
            logger.info("Monitoring system stopped")

if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the production system
    run_production_system()
