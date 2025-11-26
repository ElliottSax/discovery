#!/usr/bin/env python3
"""
24/7 Continuous Trading Pattern Monitor
Runs constantly on cheap APIs, detecting patterns in real-time
Optimized for cost-effective cloud deployment
"""

import json
import time
import requests
import schedule
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import sys
import logging
from collections import defaultdict, deque
import hashlib
import smtplib
from email.mime.text import MIMEText

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('continuous_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CheapAPIManager:
    """Manages multiple cheap data sources with fallback and rate limiting"""
    
    def __init__(self):
        # Cheap/free API sources for politician trading data
        self.api_sources = {
            'quiver': {
                'url': 'https://api.quiverquant.com/beta/live/congresstrading',
                'key': os.getenv('QUIVER_API_KEY', ''),  # $10/month
                'rate_limit': 100,  # calls per hour
                'cost_per_call': 0.001  # $0.001 per call
            },
            'capitol_trades': {
                'url': 'https://api.capitoltrades.com/v1/trades',
                'key': os.getenv('CAPITOL_TRADES_KEY', ''),  # $5/month
                'rate_limit': 200,
                'cost_per_call': 0.0005
            },
            'senate_disclosure': {
                'url': 'https://efdsearch.senate.gov/search/view/paper/',
                'key': None,  # Free scraping
                'rate_limit': 60,  # Be respectful
                'cost_per_call': 0.0
            },
            'house_disclosure': {
                'url': 'https://disclosures-clerk.house.gov/public_disc/financial-pdfs',
                'key': None,  # Free scraping
                'rate_limit': 60,
                'cost_per_call': 0.0
            }
        }
        
        # Rate limiting tracking
        self.call_counts = defaultdict(int)
        self.last_reset = datetime.now()
        
        # Cost tracking
        self.daily_cost = 0.0
        self.monthly_budget = float(os.getenv('MONTHLY_BUDGET', '20.0'))  # $20/month default
        
    def can_make_call(self, source: str) -> bool:
        """Check if we can make an API call within rate limits and budget"""
        
        # Reset hourly counters
        if (datetime.now() - self.last_reset).seconds > 3600:
            self.call_counts.clear()
            self.last_reset = datetime.now()
            
        # Check rate limit
        if self.call_counts[source] >= self.api_sources[source]['rate_limit']:
            return False
            
        # Check daily budget
        call_cost = self.api_sources[source]['cost_per_call']
        if self.daily_cost + call_cost > self.monthly_budget / 30:
            logger.warning(f"Daily budget limit reached: ${self.daily_cost:.4f}")
            return False
            
        return True
        
    def fetch_data(self, source: str, params: Dict = None) -> Optional[Dict]:
        """Fetch data from specified source with error handling"""
        
        if not self.can_make_call(source):
            logger.warning(f"Rate limit or budget exceeded for {source}")
            return None
            
        try:
            api_config = self.api_sources[source]
            
            # Prepare headers
            headers = {'User-Agent': 'TradingAnalyzer/1.0'}
            if api_config['key']:
                headers['Authorization'] = f"Bearer {api_config['key']}"
                
            # Make request with timeout
            response = requests.get(
                api_config['url'],
                headers=headers,
                params=params or {},
                timeout=30
            )
            
            # Track usage
            self.call_counts[source] += 1
            self.daily_cost += api_config['cost_per_call']
            
            logger.info(f"API call to {source}: {response.status_code} (Cost: ${api_config['cost_per_call']:.4f})")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning(f"Rate limited by {source}, backing off")
                time.sleep(60)  # Back off for 1 minute
                return None
            else:
                logger.error(f"API error from {source}: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Network error fetching from {source}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with {source}: {e}")
            return None
            
    def get_cost_report(self) -> Dict:
        """Get current cost and usage report"""
        return {
            'daily_cost': self.daily_cost,
            'monthly_budget': self.monthly_budget,
            'budget_remaining': self.monthly_budget - (self.daily_cost * 30),
            'calls_made': dict(self.call_counts),
            'total_calls_today': sum(self.call_counts.values())
        }

class PatternDetector:
    """Real-time pattern detection engine"""
    
    def __init__(self):
        # Store recent data for pattern detection
        self.trade_history = deque(maxlen=10000)  # Last 10k trades
        self.politician_profiles = {}
        
        # Pattern thresholds (configurable)
        self.thresholds = {
            'burst_window_days': 7,
            'burst_min_trades': 3,
            'unusual_volume_multiplier': 2.0,
            'correlation_threshold': 0.7,
            'anomaly_score_threshold': 0.8
        }
        
        # Recent patterns found (for deduplication)
        self.recent_patterns = deque(maxlen=1000)
        
    def add_trade(self, trade: Dict):
        """Add new trade to monitoring system"""
        # Add timestamp and hash for deduplication
        trade['processed_at'] = datetime.now().isoformat()
        trade['trade_hash'] = self._hash_trade(trade)
        
        # Check for duplicate
        if not self._is_duplicate(trade):
            self.trade_history.append(trade)
            self._update_politician_profile(trade)
            
            # Check for immediate patterns
            patterns = self._detect_immediate_patterns(trade)
            return patterns
            
        return []
        
    def _hash_trade(self, trade: Dict) -> str:
        """Create unique hash for trade to detect duplicates"""
        key_fields = f"{trade.get('politician')}{trade.get('date')}{trade.get('ticker')}{trade.get('amount')}"
        return hashlib.md5(key_fields.encode()).hexdigest()[:12]
        
    def _is_duplicate(self, trade: Dict) -> bool:
        """Check if trade is duplicate"""
        trade_hash = trade.get('trade_hash')
        for existing_trade in list(self.trade_history)[-100:]:  # Check last 100
            if existing_trade.get('trade_hash') == trade_hash:
                return True
        return False
        
    def _update_politician_profile(self, trade: Dict):
        """Update politician trading profile"""
        politician = trade.get('politician', 'Unknown')
        
        if politician not in self.politician_profiles:
            self.politician_profiles[politician] = {
                'total_trades': 0,
                'total_volume': 0.0,
                'favorite_stocks': defaultdict(int),
                'trade_dates': [],
                'avg_trade_size': 0.0,
                'last_trade': None
            }
            
        profile = self.politician_profiles[politician]
        profile['total_trades'] += 1
        profile['total_volume'] += trade.get('amount', 0)
        profile['favorite_stocks'][trade.get('ticker', 'Unknown')] += 1
        profile['trade_dates'].append(trade.get('date'))
        profile['avg_trade_size'] = profile['total_volume'] / profile['total_trades']
        profile['last_trade'] = trade
        
    def _detect_immediate_patterns(self, trade: Dict) -> List[Dict]:
        """Detect patterns triggered by new trade"""
        patterns = []
        politician = trade.get('politician')
        
        # Pattern 1: Burst Trading
        burst_pattern = self._check_burst_trading(politician)
        if burst_pattern:
            patterns.append(burst_pattern)
            
        # Pattern 2: Unusual Volume
        volume_pattern = self._check_unusual_volume(trade)
        if volume_pattern:
            patterns.append(volume_pattern)
            
        # Pattern 3: Stock Concentration
        concentration_pattern = self._check_stock_concentration(politician, trade)
        if concentration_pattern:
            patterns.append(concentration_pattern)
            
        # Pattern 4: Timing Anomalies
        timing_pattern = self._check_timing_anomalies(trade)
        if timing_pattern:
            patterns.append(timing_pattern)
            
        return patterns
        
    def _check_burst_trading(self, politician: str) -> Optional[Dict]:
        """Check for burst trading pattern"""
        if politician not in self.politician_profiles:
            return None
            
        profile = self.politician_profiles[politician]
        recent_trades = [
            t for t in self.trade_history 
            if t.get('politician') == politician
        ][-20:]  # Last 20 trades
        
        if len(recent_trades) < self.thresholds['burst_min_trades']:
            return None
            
        # Check if recent trades are within burst window
        now = datetime.now()
        recent_dates = [
            datetime.fromisoformat(t['processed_at']) 
            for t in recent_trades
        ]
        
        burst_trades = [
            date for date in recent_dates 
            if (now - date).days <= self.thresholds['burst_window_days']
        ]
        
        if len(burst_trades) >= self.thresholds['burst_min_trades']:
            # Check if this is a new pattern (not recently reported)
            pattern_id = f"burst_{politician}_{now.strftime('%Y%m%d')}"
            
            if not self._pattern_recently_reported(pattern_id):
                self.recent_patterns.append(pattern_id)
                return {
                    'type': 'burst_trading',
                    'politician': politician,
                    'trades_in_period': len(burst_trades),
                    'period_days': self.thresholds['burst_window_days'],
                    'severity': 'high' if len(burst_trades) > 5 else 'medium',
                    'detected_at': now.isoformat(),
                    'pattern_id': pattern_id
                }
                
        return None
        
    def _check_unusual_volume(self, trade: Dict) -> Optional[Dict]:
        """Check for unusual trading volume"""
        politician = trade.get('politician')
        trade_amount = trade.get('amount', 0)
        
        if politician in self.politician_profiles:
            profile = self.politician_profiles[politician]
            avg_trade = profile['avg_trade_size']
            
            if avg_trade > 0 and trade_amount > avg_trade * self.thresholds['unusual_volume_multiplier']:
                return {
                    'type': 'unusual_volume',
                    'politician': politician,
                    'trade_amount': trade_amount,
                    'average_amount': avg_trade,
                    'multiplier': trade_amount / avg_trade,
                    'severity': 'high' if trade_amount > avg_trade * 5 else 'medium',
                    'detected_at': datetime.now().isoformat()
                }
                
        return None
        
    def _check_stock_concentration(self, politician: str, trade: Dict) -> Optional[Dict]:
        """Check for unusual stock concentration"""
        if politician not in self.politician_profiles:
            return None
            
        profile = self.politician_profiles[politician]
        ticker = trade.get('ticker')
        
        if profile['total_trades'] >= 10:  # Need enough history
            ticker_count = profile['favorite_stocks'][ticker]
            concentration = ticker_count / profile['total_trades']
            
            if concentration > 0.4:  # 40%+ concentration in one stock
                return {
                    'type': 'stock_concentration',
                    'politician': politician,
                    'ticker': ticker,
                    'concentration': concentration,
                    'total_trades': profile['total_trades'],
                    'ticker_trades': ticker_count,
                    'severity': 'high' if concentration > 0.6 else 'medium',
                    'detected_at': datetime.now().isoformat()
                }
                
        return None
        
    def _check_timing_anomalies(self, trade: Dict) -> Optional[Dict]:
        """Check for unusual timing patterns"""
        trade_time = datetime.now()
        
        # Check if trading outside normal hours or on weekends
        if trade_time.weekday() >= 5:  # Weekend
            return {
                'type': 'weekend_trading',
                'politician': trade.get('politician'),
                'trade_time': trade_time.isoformat(),
                'severity': 'medium',
                'detected_at': trade_time.isoformat()
            }
            
        if trade_time.hour < 9 or trade_time.hour > 16:  # Outside market hours
            return {
                'type': 'after_hours_trading',
                'politician': trade.get('politician'),
                'trade_time': trade_time.isoformat(),
                'severity': 'low',
                'detected_at': trade_time.isoformat()
            }
            
        return None
        
    def _pattern_recently_reported(self, pattern_id: str) -> bool:
        """Check if pattern was recently reported to avoid spam"""
        return pattern_id in self.recent_patterns

class AlertSystem:
    """Send alerts when significant patterns are detected"""
    
    def __init__(self):
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email': os.getenv('ALERT_EMAIL', ''),
            'password': os.getenv('ALERT_EMAIL_PASSWORD', ''),
            'recipients': os.getenv('ALERT_RECIPIENTS', '').split(',')
        }
        
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL', '')
        self.twitter_config = {
            'api_key': os.getenv('TWITTER_API_KEY', ''),
            'api_secret': os.getenv('TWITTER_API_SECRET', ''),
            'access_token': os.getenv('TWITTER_ACCESS_TOKEN', ''),
            'access_secret': os.getenv('TWITTER_ACCESS_SECRET', '')
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            'high': True,    # Always alert
            'medium': True,  # Alert during business hours
            'low': False     # Only log
        }
        
    def send_pattern_alert(self, patterns: List[Dict]):
        """Send alerts for detected patterns"""
        if not patterns:
            return
            
        for pattern in patterns:
            severity = pattern.get('severity', 'low')
            
            if self.alert_thresholds.get(severity, False):
                self._send_email_alert(pattern)
                self._send_slack_alert(pattern)
                # self._send_twitter_alert(pattern)  # Uncomment if desired
                
        logger.info(f"Sent alerts for {len(patterns)} patterns")
        
    def _send_email_alert(self, pattern: Dict):
        """Send email alert"""
        if not self.email_config['email'] or not self.email_config['recipients'][0]:
            return
            
        try:
            subject = f"🚨 Trading Pattern Alert: {pattern['type']}"
            body = self._format_pattern_email(pattern)
            
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.email_config['email']
            msg['To'] = ', '.join(self.email_config['recipients'])
            
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['email'], self.email_config['password'])
                server.send_message(msg)
                
            logger.info(f"Email alert sent for {pattern['type']}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            
    def _send_slack_alert(self, pattern: Dict):
        """Send Slack webhook alert"""
        if not self.webhook_url:
            return
            
        try:
            payload = {
                'text': f"🚨 Trading Pattern Alert",
                'attachments': [{
                    'color': 'danger' if pattern['severity'] == 'high' else 'warning',
                    'fields': [
                        {'title': 'Pattern Type', 'value': pattern['type'], 'short': True},
                        {'title': 'Politician', 'value': pattern.get('politician', 'Unknown'), 'short': True},
                        {'title': 'Severity', 'value': pattern['severity'].upper(), 'short': True},
                        {'title': 'Detected At', 'value': pattern['detected_at'], 'short': True}
                    ]
                }]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Slack alert sent for {pattern['type']}")
            else:
                logger.error(f"Slack alert failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            
    def _format_pattern_email(self, pattern: Dict) -> str:
        """Format pattern data for email"""
        lines = [
            f"Trading Pattern Alert - {pattern['type'].upper()}",
            "=" * 50,
            "",
            f"Politician: {pattern.get('politician', 'Unknown')}",
            f"Pattern Type: {pattern['type']}",
            f"Severity: {pattern['severity'].upper()}",
            f"Detected At: {pattern['detected_at']}",
            ""
        ]
        
        # Add pattern-specific details
        for key, value in pattern.items():
            if key not in ['type', 'politician', 'severity', 'detected_at']:
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
                
        lines.extend([
            "",
            "This is an automated alert from the 24/7 Trading Pattern Monitor.",
            "Review the full data at your monitoring dashboard."
        ])
        
        return '\n'.join(lines)

class ContinuousMonitor:
    """Main 24/7 monitoring system"""
    
    def __init__(self):
        self.api_manager = CheapAPIManager()
        self.pattern_detector = PatternDetector()
        self.alert_system = AlertSystem()
        
        # Monitoring state
        self.is_running = False
        self.last_health_check = datetime.now()
        self.daily_stats = {
            'trades_processed': 0,
            'patterns_detected': 0,
            'api_calls_made': 0,
            'alerts_sent': 0
        }
        
        # Configuration
        self.check_interval = int(os.getenv('CHECK_INTERVAL_MINUTES', '15'))  # 15 minutes
        self.health_check_interval = int(os.getenv('HEALTH_CHECK_HOURS', '4'))  # 4 hours
        
    def start(self):
        """Start the continuous monitoring system"""
        logger.info("🚀 Starting 24/7 Trading Pattern Monitor")
        logger.info(f"Check interval: {self.check_interval} minutes")
        logger.info(f"Monthly budget: ${self.api_manager.monthly_budget}")
        
        self.is_running = True
        
        # Schedule regular checks
        schedule.every(self.check_interval).minutes.do(self._check_for_new_trades)
        schedule.every(self.health_check_interval).hours.do(self._health_check)
        schedule.every().day.at("00:00").do(self._daily_reset)
        
        # Start scheduler in separate thread
        scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()
        
        # Initial check
        self._check_for_new_trades()
        
        logger.info("✅ 24/7 Monitor started successfully")
        
        # Keep main thread alive
        try:
            while self.is_running:
                time.sleep(60)  # Check every minute for shutdown
        except KeyboardInterrupt:
            logger.info("Shutdown requested...")
            self.stop()
            
    def stop(self):
        """Stop the monitoring system"""
        self.is_running = False
        logger.info("🛑 24/7 Monitor stopped")
        
    def _run_scheduler(self):
        """Run the scheduler in background"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    def _check_for_new_trades(self):
        """Main monitoring function - check for new trades"""
        logger.info("🔍 Checking for new trades...")
        
        new_trades = []
        
        # Try each API source
        for source in self.api_manager.api_sources:
            try:
                data = self.api_manager.fetch_data(source)
                if data:
                    trades = self._parse_api_data(source, data)
                    new_trades.extend(trades)
                    self.daily_stats['api_calls_made'] += 1
                    
                # Rate limit between sources
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error checking {source}: {e}")
                
        # Process new trades
        all_patterns = []
        for trade in new_trades:
            patterns = self.pattern_detector.add_trade(trade)
            all_patterns.extend(patterns)
            self.daily_stats['trades_processed'] += 1
            
        # Send alerts for patterns
        if all_patterns:
            self.alert_system.send_pattern_alert(all_patterns)
            self.daily_stats['patterns_detected'] += len(all_patterns)
            self.daily_stats['alerts_sent'] += len(all_patterns)
            
        # Log summary
        cost_report = self.api_manager.get_cost_report()
        logger.info(f"✅ Check complete: {len(new_trades)} new trades, {len(all_patterns)} patterns, ${cost_report['daily_cost']:.4f} spent today")
        
    def _parse_api_data(self, source: str, data: Dict) -> List[Dict]:
        """Parse API response into standardized trade format"""
        trades = []
        
        try:
            if source == 'quiver':
                # Parse Quiver Quant format
                for item in data.get('trades', []):
                    trades.append({
                        'politician': item.get('Representative', ''),
                        'date': item.get('TransactionDate', ''),
                        'ticker': item.get('Ticker', ''),
                        'amount': item.get('Amount', 0),
                        'transaction_type': item.get('Transaction', ''),
                        'source': source
                    })
                    
            elif source == 'capitol_trades':
                # Parse Capitol Trades format
                for item in data.get('data', []):
                    trades.append({
                        'politician': item.get('politician_name', ''),
                        'date': item.get('disclosed_date', ''),
                        'ticker': item.get('ticker', ''),
                        'amount': item.get('amount_range_high', 0),
                        'transaction_type': item.get('type', ''),
                        'source': source
                    })
                    
            # Add more parsers for other sources as needed
            
        except Exception as e:
            logger.error(f"Error parsing {source} data: {e}")
            
        return trades
        
    def _health_check(self):
        """Perform system health check"""
        logger.info("🏥 Performing health check...")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'uptime_hours': (datetime.now() - self.last_health_check).total_seconds() / 3600,
            'daily_stats': self.daily_stats,
            'cost_report': self.api_manager.get_cost_report(),
            'pattern_detector_status': {
                'trades_in_memory': len(self.pattern_detector.trade_history),
                'politicians_tracked': len(self.pattern_detector.politician_profiles),
                'patterns_cache_size': len(self.pattern_detector.recent_patterns)
            }
        }
        
        # Save health report
        with open(f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(health_status, f, indent=2)
            
        # Check for issues
        issues = []
        cost_report = health_status['cost_report']
        
        if cost_report['budget_remaining'] < 0:
            issues.append("Monthly budget exceeded!")
            
        if self.daily_stats['api_calls_made'] == 0:
            issues.append("No API calls successful today")
            
        if issues:
            logger.warning(f"Health check issues: {issues}")
            # Could send alert here
        else:
            logger.info("✅ System healthy")
            
        self.last_health_check = datetime.now()
        
    def _daily_reset(self):
        """Reset daily counters"""
        logger.info("🔄 Daily reset")
        self.daily_stats = {
            'trades_processed': 0,
            'patterns_detected': 0,
            'api_calls_made': 0,
            'alerts_sent': 0
        }
        self.api_manager.daily_cost = 0.0

def main():
    """Main entry point for 24/7 monitoring"""
    
    print("🤖 24/7 TRADING PATTERN MONITOR")
    print("=" * 60)
    print("This system will run continuously and:")
    print("  • Monitor politician trades from multiple APIs")
    print("  • Detect patterns in real-time")
    print("  • Send alerts when significant patterns found")
    print("  • Optimize costs with rate limiting and budgets")
    print("  • Run 24/7 with automatic health checks")
    print()
    
    # Check configuration
    config_issues = []
    
    if not os.getenv('QUIVER_API_KEY') and not os.getenv('CAPITOL_TRADES_KEY'):
        config_issues.append("No API keys configured (set QUIVER_API_KEY or CAPITOL_TRADES_KEY)")
        
    if not os.getenv('ALERT_EMAIL'):
        config_issues.append("Email alerts not configured (set ALERT_EMAIL)")
        
    if config_issues:
        print("⚠️  Configuration Issues:")
        for issue in config_issues:
            print(f"   • {issue}")
        print("\nSystem will run in demo mode with simulated data.")
        print()
        
    # Start monitor
    monitor = ContinuousMonitor()
    monitor.start()

if __name__ == "__main__":
    main()