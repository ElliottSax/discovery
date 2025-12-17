#!/usr/bin/env python3
"""
Alert Manager

Coordinates all alert channels (email, Slack, SMS) and determines
when to send alerts based on severity and configuration.
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from .email_notifier import EmailNotifier
from .slack_notifier import SlackNotifier

logger = logging.getLogger(__name__)


class AlertManager:
    """Manage and coordinate all alert channels"""

    # Minimum severity levels that trigger alerts
    ALERT_SEVERITIES = {'CRITICAL', 'HIGH'}

    # Rate limiting: max alerts per politician per hour
    MAX_ALERTS_PER_HOUR = 5

    def __init__(
        self,
        email_addresses: List[str] = None,
        slack_webhook: str = None,
        enable_email: bool = True,
        enable_slack: bool = True
    ):
        """
        Initialize alert manager

        Args:
            email_addresses: List of email addresses for alerts
            slack_webhook: Slack webhook URL
            enable_email: Whether to enable email alerts
            enable_slack: Whether to enable Slack alerts
        """
        # Get configuration from environment if not provided
        if email_addresses is None:
            email_env = os.getenv('ALERT_EMAILS', '')
            email_addresses = [e.strip() for e in email_env.split(',') if e.strip()]

        self.email_addresses = email_addresses
        self.enable_email = enable_email and bool(email_addresses)
        self.enable_slack = enable_slack

        # Initialize notifiers
        self.email_notifier = EmailNotifier() if self.enable_email else None
        self.slack_notifier = SlackNotifier(slack_webhook) if self.enable_slack else None

        # Rate limiting state
        self.alert_history = defaultdict(list)  # politician -> list of alert timestamps

        logger.info(
            f"AlertManager initialized: "
            f"email={'✅' if self.enable_email else '❌'}, "
            f"slack={'✅' if self.enable_slack else '❌'}"
        )

    def should_send_alert(self, discovery: Dict) -> bool:
        """
        Determine if alert should be sent based on severity and rate limits

        Args:
            discovery: Discovery dict

        Returns:
            True if alert should be sent
        """
        finding = discovery.get('finding', {})
        severity = finding.get('severity', 'MEDIUM')

        # Check severity threshold
        if severity not in self.ALERT_SEVERITIES:
            logger.debug(f"Severity {severity} below alert threshold")
            return False

        # Check rate limiting
        politician = discovery.get('politician', 'Unknown')
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)

        # Clean old alerts
        self.alert_history[politician] = [
            ts for ts in self.alert_history[politician]
            if ts > one_hour_ago
        ]

        # Check if we've hit the rate limit
        if len(self.alert_history[politician]) >= self.MAX_ALERTS_PER_HOUR:
            logger.warning(
                f"Rate limit reached for {politician}: "
                f"{len(self.alert_history[politician])} alerts in last hour"
            )
            return False

        return True

    def send_alert(self, discovery: Dict, force: bool = False) -> Dict[str, bool]:
        """
        Send alert through all enabled channels

        Args:
            discovery: Discovery dict
            force: If True, bypass severity and rate limit checks

        Returns:
            Dict mapping channel name to success status
        """
        results = {}

        # Check if we should send
        if not force and not self.should_send_alert(discovery):
            logger.info("Alert suppressed (severity/rate limit)")
            return {'suppressed': True}

        # Record alert for rate limiting
        politician = discovery.get('politician', 'Unknown')
        self.alert_history[politician].append(datetime.now())

        # Send via email
        if self.enable_email:
            try:
                results['email'] = self.email_notifier.send_discovery_alert(
                    discovery,
                    self.email_addresses
                )
            except Exception as e:
                logger.error(f"Email alert failed: {e}")
                results['email'] = False

        # Send via Slack
        if self.enable_slack:
            try:
                results['slack'] = self.slack_notifier.send_discovery_alert(discovery)
            except Exception as e:
                logger.error(f"Slack alert failed: {e}")
                results['slack'] = False

        # Log summary
        successful = [ch for ch, success in results.items() if success]
        if successful:
            logger.info(f"✅ Alert sent via: {', '.join(successful)}")
        else:
            logger.warning("⚠️ No alerts sent successfully")

        return results

    def send_compliance_alert(self, violation: Dict, force: bool = False) -> Dict[str, bool]:
        """
        Send compliance violation alert

        Args:
            violation: Violation dict
            force: If True, bypass checks

        Returns:
            Dict mapping channel name to success status
        """
        results = {}

        severity = violation.get('severity', 'MEDIUM')

        if not force and severity not in self.ALERT_SEVERITIES:
            logger.info(f"Compliance alert suppressed (severity: {severity})")
            return {'suppressed': True}

        # Send via email
        if self.enable_email:
            try:
                results['email'] = self.email_notifier.send_compliance_alert(
                    violation,
                    self.email_addresses
                )
            except Exception as e:
                logger.error(f"Email alert failed: {e}")
                results['email'] = False

        # Send via Slack (convert to discovery format)
        if self.enable_slack:
            try:
                # Convert violation to discovery format for Slack
                discovery = {
                    'type': violation.get('type', 'compliance_violation'),
                    'politician': violation.get('politician', 'Unknown'),
                    'timestamp': datetime.now().isoformat(),
                    'finding': {
                        'severity': severity,
                        'description': violation.get('description', ''),
                        'score': violation.get('score', 0)
                    }
                }
                results['slack'] = self.slack_notifier.send_discovery_alert(discovery)
            except Exception as e:
                logger.error(f"Slack alert failed: {e}")
                results['slack'] = False

        return results

    def send_daily_summary(self, discoveries: List[Dict]) -> Dict[str, bool]:
        """
        Send daily summary of discoveries

        Args:
            discoveries: List of discoveries from the day

        Returns:
            Dict mapping channel name to success status
        """
        if not discoveries:
            logger.info("No discoveries to summarize")
            return {}

        logger.info(f"Generating daily summary for {len(discoveries)} discoveries")

        # Format summary
        summary = self._format_daily_summary(discoveries)

        # Send via configured channels
        results = {}

        # Email summary
        if self.enable_email and self.email_notifier:
            try:
                success = self.email_notifier.send_daily_summary(
                    self.email_addresses,
                    summary
                )
                results['email'] = success
            except Exception as e:
                logger.error(f"Email daily summary failed: {e}")
                results['email'] = False

        # Slack summary
        if self.enable_slack and self.slack_notifier:
            try:
                success = self.slack_notifier.send_daily_summary(summary)
                results['slack'] = success
            except Exception as e:
                logger.error(f"Slack daily summary failed: {e}")
                results['slack'] = False

        return results

    def _format_daily_summary(self, discoveries: List[Dict]) -> Dict:
        """
        Format daily summary data

        Returns:
            {
                'date': '2025-12-16',
                'total_discoveries': 10,
                'by_severity': {'CRITICAL': 2, 'HIGH': 5, 'MEDIUM': 3},
                'by_type': {'front_running': 3, 'insider_information': 2, ...},
                'top_discoveries': [...],
                'politicians_flagged': ['Nancy Pelosi', ...],
                'summary_text': 'Human-readable summary'
            }
        """
        from collections import Counter

        # Aggregate by severity
        severities = []
        types = []
        politicians = set()

        for disc in discoveries:
            finding = disc.get('finding', {})
            severities.append(finding.get('severity', 'MEDIUM'))
            types.append(disc.get('type', 'unknown'))

            politician = disc.get('politician', '').strip()
            if politician and politician != 'Unknown':
                politicians.add(politician)

        severity_counts = dict(Counter(severities))
        type_counts = dict(Counter(types))

        # Get top discoveries (highest severity and score)
        top_discoveries = sorted(
            discoveries,
            key=lambda d: (
                {'CRITICAL': 3, 'HIGH': 2, 'MEDIUM': 1, 'LOW': 0}.get(
                    d.get('finding', {}).get('severity', 'LOW'), 0
                ),
                d.get('finding', {}).get('score', 0)
            ),
            reverse=True
        )[:5]

        # Format top discoveries
        formatted_top = []
        for disc in top_discoveries:
            formatted_top.append({
                'politician': disc.get('politician', 'Unknown'),
                'type': disc.get('type', 'unknown'),
                'severity': disc.get('finding', {}).get('severity', 'MEDIUM'),
                'score': disc.get('finding', {}).get('score', 0),
                'description': disc.get('finding', {}).get('description', 'No description'),
                'timestamp': disc.get('timestamp', '')
            })

        # Generate summary text
        summary_text = self._generate_summary_text(
            len(discoveries),
            severity_counts,
            type_counts,
            politicians
        )

        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_discoveries': len(discoveries),
            'by_severity': severity_counts,
            'by_type': type_counts,
            'top_discoveries': formatted_top,
            'politicians_flagged': sorted(list(politicians)),
            'summary_text': summary_text
        }

    def _generate_summary_text(
        self,
        total: int,
        severities: Dict[str, int],
        types: Dict[str, int],
        politicians: set
    ) -> str:
        """Generate human-readable summary text"""
        lines = []

        lines.append(f"📊 ULTRATHINK Daily Summary")
        lines.append(f"{'='*50}")
        lines.append(f"Total Discoveries: {total}")
        lines.append("")

        # Severity breakdown
        if severities:
            lines.append("Severity Breakdown:")
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                if severity in severities:
                    emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(severity, '⚪')
                    lines.append(f"  {emoji} {severity}: {severities[severity]}")
            lines.append("")

        # Type breakdown
        if types:
            lines.append("Discovery Types:")
            sorted_types = sorted(types.items(), key=lambda x: x[1], reverse=True)
            for disc_type, count in sorted_types[:5]:
                lines.append(f"  • {disc_type.replace('_', ' ').title()}: {count}")
            lines.append("")

        # Politicians
        if politicians:
            lines.append(f"Politicians Flagged: {len(politicians)}")
            for pol in sorted(list(politicians))[:10]:
                lines.append(f"  • {pol}")
            if len(politicians) > 10:
                lines.append(f"  ... and {len(politicians) - 10} more")

        return '\n'.join(lines)


if __name__ == "__main__":
    # Test alert manager
    logging.basicConfig(level=logging.INFO)

    manager = AlertManager(
        email_addresses=['test@example.com']
    )

    # Test discovery alert
    test_discovery = {
        'type': 'committee_conflict',
        'politician': 'Sen. Test Person',
        'timestamp': datetime.now().isoformat(),
        'finding': {
            'severity': 'CRITICAL',
            'committee': 'Armed Services',
            'ticker': 'LMT',
            'sector': 'Defense',
            'description': 'Defense committee member trading defense stocks',
            'score': 0.85
        }
    }

    print("\nTesting Alert Manager...")
    print("="*60)

    results = manager.send_alert(test_discovery)

    print(f"\nResults: {results}")

    # Test rate limiting
    print("\nTesting rate limiting (sending 6 alerts)...")
    for i in range(6):
        results = manager.send_alert(test_discovery)
        print(f"  Alert {i+1}: {results}")
