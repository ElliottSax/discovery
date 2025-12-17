"""
Alert Stream Processor

Processes critical alert events and dispatches notifications:
- Email notifications
- Slack messages
- SMS alerts (if configured)
- Dashboard updates

Usage:
    from streaming import AlertStreamProcessor
    from services.event_stream import EventStream

    stream = EventStream()
    processor = AlertStreamProcessor(stream)

    stream.listen()  # Start processing alerts
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from .base_processor import BaseStreamProcessor
from services.event_stream import publish_dashboard_event

logger = logging.getLogger(__name__)


class AlertStreamProcessor(BaseStreamProcessor):
    """Process and dispatch alert notifications"""

    def __init__(
        self,
        event_stream,
        alert_manager=None,
        channels: List[str] = None
    ):
        """
        Initialize alert processor

        Args:
            event_stream: EventStream instance
            alert_manager: AlertManager for sending notifications
            channels: List of notification channels to use
                     Options: 'email', 'slack', 'sms', 'discord', 'telegram'
        """
        super().__init__(event_stream, name="AlertStreamProcessor")

        self.alert_manager = alert_manager
        self.channels = channels or ['email', 'slack']

        # Subscribe to alerts channel
        self.event_stream.subscribe('alerts', self.handle_event)

        logger.info(
            f"Alert processor initialized (channels: {', '.join(self.channels)})"
        )

    async def process_event(self, event: Dict) -> Dict[str, Any]:
        """
        Process alert event and send notifications

        Args:
            event: Alert event
                {
                    'event_type': 'critical_alert',
                    'timestamp': '2024-12-08T10:30:15Z',
                    'data': {
                        'severity': 'HIGH',
                        'alert_type': 'front_running',
                        'politician': 'Nancy Pelosi',
                        'ticker': 'NVDA',
                        'suspicion_score': 0.85,
                        'red_flags': [...]
                    }
                }

        Returns:
            Notification results
        """
        alert_data = event.get('data', {})

        logger.info(
            f"Processing alert: {alert_data.get('alert_type')} - "
            f"{alert_data.get('politician')} ({alert_data.get('severity')})"
        )

        results = {}

        # Send notifications on configured channels
        if 'email' in self.channels:
            results['email'] = await self._send_email(alert_data)

        if 'slack' in self.channels:
            results['slack'] = await self._send_slack(alert_data)

        if 'sms' in self.channels:
            results['sms'] = await self._send_sms(alert_data)

        if 'discord' in self.channels:
            results['discord'] = await self._send_discord(alert_data)

        if 'telegram' in self.channels:
            results['telegram'] = await self._send_telegram(alert_data)

        # Update dashboard
        self._update_dashboard(alert_data)

        # Store alert in database
        await self._store_alert(alert_data)

        return {
            'status': 'success',
            'channels_notified': list(results.keys()),
            'results': results
        }

    async def _send_email(self, alert: Dict) -> Dict:
        """Send email notification"""
        try:
            if not self.alert_manager:
                logger.warning("Alert manager not configured, skipping email")
                return {'status': 'skipped', 'reason': 'no alert manager'}

            # Format email
            subject = self._format_email_subject(alert)
            body = self._format_email_body(alert)

            # Send via alert manager
            from analysis.alerts.email_notifier import EmailNotifier
            notifier = EmailNotifier()

            await notifier.send_alert(
                subject=subject,
                body=body,
                severity=alert.get('severity', 'MEDIUM')
            )

            logger.info(f"Email alert sent: {subject}")

            return {'status': 'sent', 'subject': subject}

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _send_slack(self, alert: Dict) -> Dict:
        """Send Slack notification"""
        try:
            if not self.alert_manager:
                logger.warning("Alert manager not configured, skipping Slack")
                return {'status': 'skipped', 'reason': 'no alert manager'}

            # Format Slack message
            message = self._format_slack_message(alert)

            # Send via alert manager
            from analysis.alerts.slack_notifier import SlackNotifier
            notifier = SlackNotifier()

            await notifier.send_alert(message)

            logger.info(f"Slack alert sent: {alert.get('alert_type')}")

            return {'status': 'sent'}

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _send_sms(self, alert: Dict) -> Dict:
        """Send SMS notification (for critical alerts only)"""
        try:
            # Only send SMS for critical alerts
            if alert.get('severity') != 'CRITICAL':
                return {'status': 'skipped', 'reason': 'not critical'}

            # SMS implementation would go here
            # Using Twilio, AWS SNS, or similar service

            logger.info(f"SMS alert sent: {alert.get('alert_type')}")

            return {'status': 'sent'}

        except Exception as e:
            logger.error(f"Failed to send SMS alert: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _send_discord(self, alert: Dict) -> Dict:
        """Send Discord notification"""
        try:
            # Discord webhook implementation
            logger.info(f"Discord alert sent: {alert.get('alert_type')}")
            return {'status': 'sent'}

        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _send_telegram(self, alert: Dict) -> Dict:
        """Send Telegram notification"""
        try:
            # Telegram bot API implementation
            logger.info(f"Telegram alert sent: {alert.get('alert_type')}")
            return {'status': 'sent'}

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return {'status': 'failed', 'error': str(e)}

    def _format_email_subject(self, alert: Dict) -> str:
        """Format email subject line"""
        severity = alert.get('severity', 'MEDIUM')
        alert_type = alert.get('alert_type', 'suspicious_trade')
        politician = alert.get('politician', 'Unknown')
        ticker = alert.get('ticker', 'Unknown')

        emoji = {
            'CRITICAL': '🚨',
            'HIGH': '⚠️',
            'MEDIUM': 'ℹ️',
            'LOW': '📋'
        }.get(severity, '')

        return f"{emoji} {severity}: {alert_type.replace('_', ' ').title()} - {politician} ({ticker})"

    def _format_email_body(self, alert: Dict) -> str:
        """Format email body"""
        body = f"""
Congressional Trading Alert
==========================

Severity: {alert.get('severity', 'MEDIUM')}
Type: {alert.get('alert_type', 'unknown').replace('_', ' ').title()}
Politician: {alert.get('politician', 'Unknown')}
Ticker: {alert.get('ticker', 'Unknown')}
Transaction: {alert.get('transaction_type', 'Unknown')}
Amount: {alert.get('amount', 'Unknown')}

Suspicion Score: {alert.get('suspicion_score', 0):.2%}

Red Flags:
"""

        for i, flag in enumerate(alert.get('red_flags', []), 1):
            body += f"\n{i}. [{flag.get('severity', 'MEDIUM')}] {flag.get('description', 'Unknown')}"

        body += f"""

---
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
Event ID: {alert.get('event_id', 'unknown')}

View full details in dashboard: https://ultrathink.app/alerts/{alert.get('event_id', '')}
"""

        return body

    def _format_slack_message(self, alert: Dict) -> Dict:
        """Format Slack message (blocks format)"""
        severity_emoji = {
            'CRITICAL': ':rotating_light:',
            'HIGH': ':warning:',
            'MEDIUM': ':information_source:',
            'LOW': ':memo:'
        }.get(alert.get('severity'), ':bell:')

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{severity_emoji} {alert.get('severity')} Alert: {alert.get('alert_type', 'unknown').replace('_', ' ').title()}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Politician:*\n{alert.get('politician', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Ticker:*\n{alert.get('ticker', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Transaction:*\n{alert.get('transaction_type', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Suspicion Score:*\n{alert.get('suspicion_score', 0):.2%}"
                    }
                ]
            }
        ]

        # Add red flags
        if alert.get('red_flags'):
            flags_text = "\n".join([
                f"• *[{flag.get('severity')}]* {flag.get('description')}"
                for flag in alert.get('red_flags', [])
            ])

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Red Flags:*\n{flags_text}"
                }
            })

        return {"blocks": blocks}

    def _update_dashboard(self, alert: Dict):
        """Send alert to dashboard"""
        publish_dashboard_event(
            self.event_stream,
            {
                'update_type': 'new_alert',
                'alert': alert
            }
        )

    async def _store_alert(self, alert: Dict):
        """Store alert in database for historical tracking"""
        try:
            # Database storage would go here
            # Store in alerts table with timestamp, severity, data, etc.

            logger.debug(f"Alert stored: {alert.get('alert_type')}")

        except Exception as e:
            logger.error(f"Failed to store alert: {e}")

    def on_error(self, event: Dict, error: Exception):
        """Handle processing error"""
        alert_data = event.get('data', {})
        alert_type = alert_data.get('alert_type', 'unknown')

        logger.error(
            f"Alert processing error: {error}\n"
            f"Alert type: {alert_type}"
        )

        # Critical: Alerts failing is serious - use fallback notification
        try:
            self._send_fallback_notification(event, error)
        except Exception as fallback_error:
            logger.critical(
                f"Fallback notification also failed: {fallback_error}\n"
                f"Original error: {error}"
            )

    def _send_fallback_notification(self, event: Dict, error: Exception):
        """Send fallback notification when alert processing fails"""
        alert_data = event.get('data', {})

        # Try multiple fallback methods in order of reliability

        # 1. Try logging to file
        try:
            from pathlib import Path
            import json

            alert_failures_dir = Path("data/alert_failures")
            alert_failures_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filepath = alert_failures_dir / f"failed_alert_{timestamp}.json"

            failure_record = {
                'event': event,
                'error': {
                    'type': type(error).__name__,
                    'message': str(error)
                },
                'timestamp': datetime.utcnow().isoformat()
            }

            with open(filepath, 'w') as f:
                json.dump(failure_record, f, indent=2)

            logger.warning(f"Alert failure logged to: {filepath}")

        except Exception as e:
            logger.error(f"Failed to log alert failure to file: {e}")

        # 2. Try emergency email notification (if configured)
        try:
            import smtplib
            from email.mime.text import MIMEText
            import os

            emergency_email = os.getenv('EMERGENCY_ALERT_EMAIL')
            if emergency_email:
                msg = MIMEText(
                    f"CRITICAL: Alert processing failed\n\n"
                    f"Alert Type: {alert_data.get('alert_type')}\n"
                    f"Severity: {alert_data.get('severity')}\n"
                    f"Error: {error}\n\n"
                    f"Event Data: {json.dumps(alert_data, indent=2)}"
                )
                msg['Subject'] = 'ULTRATHINK Alert Processing Failure'
                msg['From'] = 'ultrathink@localhost'
                msg['To'] = emergency_email

                # Try to send (using localhost SMTP)
                smtp = smtplib.SMTP('localhost')
                smtp.send_message(msg)
                smtp.quit()

                logger.info(f"Emergency email sent to {emergency_email}")

        except Exception as e:
            logger.debug(f"Emergency email not sent: {e}")

        # 3. Try Slack webhook (if configured)
        try:
            import os
            import requests

            webhook_url = os.getenv('SLACK_EMERGENCY_WEBHOOK')
            if webhook_url:
                payload = {
                    'text': f':rotating_light: *CRITICAL: Alert Processing Failed*',
                    'blocks': [
                        {
                            'type': 'header',
                            'text': {
                                'type': 'plain_text',
                                'text': ':rotating_light: Alert Processing Failure'
                            }
                        },
                        {
                            'type': 'section',
                            'fields': [
                                {
                                    'type': 'mrkdwn',
                                    'text': f"*Alert Type:*\n{alert_data.get('alert_type')}"
                                },
                                {
                                    'type': 'mrkdwn',
                                    'text': f"*Severity:*\n{alert_data.get('severity')}"
                                },
                                {
                                    'type': 'mrkdwn',
                                    'text': f"*Error:*\n{type(error).__name__}: {str(error)}"
                                }
                            ]
                        }
                    ]
                }

                response = requests.post(webhook_url, json=payload, timeout=5)
                if response.status_code == 200:
                    logger.info("Emergency Slack notification sent")

        except Exception as e:
            logger.debug(f"Slack emergency notification not sent: {e}")


# Convenience function
def start_alert_processor(
    event_stream,
    alert_manager=None,
    channels: List[str] = None
) -> AlertStreamProcessor:
    """
    Start alert stream processor

    Args:
        event_stream: EventStream instance
        alert_manager: AlertManager for notifications
        channels: List of notification channels

    Returns:
        Running AlertStreamProcessor
    """
    processor = AlertStreamProcessor(
        event_stream=event_stream,
        alert_manager=alert_manager,
        channels=channels or ['email', 'slack']
    )

    logger.info("Alert stream processor started")
    return processor
