"""
Trade Stream Processor

Processes incoming trade disclosure events in real-time:
1. Enriches trade with current price data
2. Dispatches to Oracle Cloud workers for analysis
3. Publishes analysis results to event stream
4. Triggers alerts for suspicious trades

Usage:
    from streaming import TradeStreamProcessor
    from services.event_stream import EventStream

    stream = EventStream()
    processor = TradeStreamProcessor(stream)

    # Processor automatically subscribes to 'trades' channel
    stream.listen()  # Start processing
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .base_processor import BaseStreamProcessor
from services.event_stream import (
    publish_analysis_event,
    publish_alert_event,
    publish_dashboard_event
)

logger = logging.getLogger(__name__)


class TradeStreamProcessor(BaseStreamProcessor):
    """Process trade disclosure events in real-time"""

    def __init__(
        self,
        event_stream,
        orchestrator=None,
        price_service=None,
        alert_threshold: float = 0.7
    ):
        """
        Initialize trade processor

        Args:
            event_stream: EventStream instance
            orchestrator: JobOrchestrator for distributed analysis (optional)
            price_service: Price service for current prices (optional)
            alert_threshold: Suspicion score threshold for alerts (0-1)
        """
        super().__init__(event_stream, name="TradeStreamProcessor")

        self.orchestrator = orchestrator
        self.price_service = price_service
        self.alert_threshold = alert_threshold

        # Subscribe to trades channel
        self.event_stream.subscribe('trades', self.handle_event)

        logger.info(
            f"Trade processor initialized (alert_threshold={alert_threshold})"
        )

    async def process_event(self, event: Dict) -> Dict[str, Any]:
        """
        Process trade disclosure event

        Args:
            event: Trade event from scraper
                {
                    'event_type': 'trade_disclosure',
                    'timestamp': '2024-12-08T10:30:15Z',
                    'data': {
                        'politician': 'Nancy Pelosi',
                        'ticker': 'NVDA',
                        'transaction_type': 'purchase',
                        'amount': '$250,000-$500,000',
                        'trade_date': '2024-12-01',
                        'disclosure_date': '2024-12-08'
                    }
                }

        Returns:
            Processing result with analysis
        """
        event_id = event.get('event_id', 'unknown')
        trade_data = event.get('data', {})

        logger.info(
            f"Processing trade: {trade_data.get('politician')} - "
            f"{trade_data.get('ticker')} ({trade_data.get('transaction_type')})"
        )

        # Step 1: Enrich with current price
        trade_data = await self._enrich_with_price(trade_data)

        # Step 2: Run analysis
        analysis = await self._analyze_trade(trade_data)

        # Step 3: Publish analysis results
        publish_analysis_event(
            self.event_stream,
            event_id,
            analysis
        )

        # Step 4: Check for alerts
        if self._should_alert(analysis):
            await self._trigger_alert(event_id, trade_data, analysis)

        # Step 5: Update dashboard
        self._update_dashboard(trade_data, analysis)

        return {
            'status': 'success',
            'event_id': event_id,
            'analysis': analysis
        }

    async def _enrich_with_price(self, trade: Dict) -> Dict:
        """Enrich trade with current price data"""
        ticker = trade.get('ticker')

        if not ticker:
            return trade

        try:
            if self.price_service:
                # Get current price from price service
                price_data = await self.price_service.get_current_price(ticker)
                trade['current_price'] = price_data.get('price')
                trade['current_volume'] = price_data.get('volume')
            else:
                # Fallback: get from cache or API
                from analysis.stock_analysis import get_current_price
                price = get_current_price(ticker)
                trade['current_price'] = price

            logger.debug(f"Enriched {ticker} with price: ${trade.get('current_price')}")

        except Exception as e:
            logger.warning(f"Failed to get current price for {ticker}: {e}")

        return trade

    async def _analyze_trade(self, trade: Dict) -> Dict:
        """
        Run full analysis on trade

        Returns analysis results with:
        - Sentiment analysis
        - Market impact
        - Front-running detection
        - Volume anomalies
        - Compliance checks
        """
        ticker = trade.get('ticker')

        # If orchestrator available, use distributed processing
        if self.orchestrator:
            try:
                logger.debug("Dispatching trade to Oracle Cloud workers...")

                # Analyze using distributed workers
                result = await self.orchestrator.analyze_single_trade(
                    trade,
                    analysis_types=['sentiment', 'market_impact', 'volume', 'compliance']
                )

                return result

            except Exception as e:
                logger.error(f"Orchestrator analysis failed: {e}")
                # Fall through to local analysis

        # Local analysis (fallback)
        return await self._analyze_local(trade)

    async def _analyze_local(self, trade: Dict) -> Dict:
        """Run analysis locally (fallback if orchestrator unavailable)"""
        results = {}

        try:
            # Sentiment analysis
            from analysis.sentiment import analyze_disclosure_sentiment

            if trade.get('disclosure_text'):
                sentiment = analyze_disclosure_sentiment(trade['disclosure_text'])
                results['sentiment'] = sentiment

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")

        try:
            # Market impact analysis
            from analysis.market_impact import (
                analyze_disclosure_impact,
                detect_front_running
            )

            ticker = trade.get('ticker')
            if ticker:
                # Price impact
                impact = analyze_disclosure_impact(
                    ticker,
                    trade.get('disclosure_date'),
                    trade.get('price_data', [])
                )
                results['market_impact'] = impact

                # Front-running detection
                front_running = detect_front_running(
                    ticker,
                    trade.get('trade_date'),
                    trade.get('disclosure_date'),
                    trade.get('transaction_type'),
                    trade.get('price_data', [])
                )
                results['front_running'] = front_running

        except Exception as e:
            logger.error(f"Market impact analysis failed: {e}")

        # Calculate overall suspicion score
        results['suspicion_score'] = self._calculate_suspicion_score(results)

        return results

    def _calculate_suspicion_score(self, analysis: Dict) -> float:
        """
        Calculate overall suspicion score (0-1)

        Combines signals from:
        - Sentiment (insider signal)
        - Front-running detection
        - Market impact
        - Compliance violations
        """
        score = 0.0
        factors = 0

        # Sentiment insider signal
        if 'sentiment' in analysis:
            insider_signal = analysis['sentiment'].get('insider_signal_score', 0)
            score += insider_signal * 0.3
            factors += 0.3

        # Front-running
        if 'front_running' in analysis:
            if analysis['front_running'].get('front_running_detected'):
                suspicion = analysis['front_running'].get('suspicion_score', 0)
                score += suspicion * 0.4
                factors += 0.4

        # Market impact
        if 'market_impact' in analysis:
            impact_score = analysis['market_impact'].get('impact_score', 0)
            score += impact_score * 0.2
            factors += 0.2

        # Compliance violations
        if 'compliance' in analysis:
            if analysis['compliance'].get('violations', []):
                score += 0.1
                factors += 0.1

        # Normalize
        if factors > 0:
            return score / factors
        else:
            return 0.0

    def _should_alert(self, analysis: Dict) -> bool:
        """Determine if trade should trigger an alert"""
        suspicion_score = analysis.get('suspicion_score', 0)
        return suspicion_score >= self.alert_threshold

    async def _trigger_alert(self, event_id: str, trade: Dict, analysis: Dict):
        """Trigger critical alert for suspicious trade"""
        severity = 'CRITICAL' if analysis['suspicion_score'] >= 0.9 else 'HIGH'

        # Determine alert type
        alert_types = []
        if analysis.get('front_running', {}).get('front_running_detected'):
            alert_types.append('front_running')
        if analysis.get('sentiment', {}).get('insider_signal_score', 0) > 0.7:
            alert_types.append('insider_information')
        if analysis.get('compliance', {}).get('violations'):
            alert_types.append('compliance_violation')

        alert_type = ', '.join(alert_types) if alert_types else 'suspicious_trade'

        # Publish alert
        publish_alert_event(
            self.event_stream,
            severity=severity,
            alert_type=alert_type,
            data={
                'event_id': event_id,
                'politician': trade.get('politician'),
                'ticker': trade.get('ticker'),
                'transaction_type': trade.get('transaction_type'),
                'amount': trade.get('amount'),
                'suspicion_score': analysis['suspicion_score'],
                'red_flags': self._get_red_flags(analysis)
            }
        )

        logger.warning(
            f"ALERT: Suspicious trade detected - "
            f"{trade.get('politician')} - {trade.get('ticker')} "
            f"(score: {analysis['suspicion_score']:.2f})"
        )

    def _get_red_flags(self, analysis: Dict) -> list:
        """Extract red flags from analysis"""
        flags = []

        if 'sentiment' in analysis:
            flags.extend(analysis['sentiment'].get('red_flags', []))

        if 'front_running' in analysis:
            if analysis['front_running'].get('front_running_detected'):
                flags.append({
                    'type': 'front_running',
                    'description': 'Price moved before disclosure',
                    'severity': 'HIGH'
                })

        if 'compliance' in analysis:
            for violation in analysis['compliance'].get('violations', []):
                flags.append({
                    'type': 'compliance',
                    'description': violation.get('description'),
                    'severity': violation.get('severity', 'MEDIUM')
                })

        return flags

    def _update_dashboard(self, trade: Dict, analysis: Dict):
        """Send update to live dashboard"""
        publish_dashboard_event(
            self.event_stream,
            {
                'update_type': 'new_trade',
                'trade': {
                    'politician': trade.get('politician'),
                    'ticker': trade.get('ticker'),
                    'transaction_type': trade.get('transaction_type'),
                    'amount': trade.get('amount'),
                    'trade_date': trade.get('trade_date'),
                    'current_price': trade.get('current_price')
                },
                'analysis': {
                    'suspicion_score': analysis.get('suspicion_score'),
                    'sentiment': analysis.get('sentiment', {}).get('sentiment'),
                    'front_running_detected': analysis.get('front_running', {}).get(
                        'front_running_detected',
                        False
                    )
                }
            }
        )

    def on_error(self, event: Dict, error: Exception):
        """Handle processing error"""
        trade_data = event.get('data', {})
        event_id = event.get('event_id', 'unknown')

        # Log error details
        logger.error(
            f"Trade processing error: {error}\n"
            f"Trade: {trade_data.get('politician')} - {trade_data.get('ticker')}\n"
            f"Event ID: {event_id}"
        )

        # Publish error event for monitoring
        try:
            from services.event_stream import publish_error_event

            publish_error_event(
                self.event_stream,
                event_id=event_id,
                processor='TradeStreamProcessor',
                error_type=type(error).__name__,
                error_message=str(error),
                event_data={
                    'politician': trade_data.get('politician'),
                    'ticker': trade_data.get('ticker'),
                    'transaction_type': trade_data.get('transaction_type')
                }
            )
        except Exception as publish_error:
            logger.error(f"Failed to publish error event: {publish_error}")

        # Store failed event for retry
        try:
            self._store_failed_event(event, error)
        except Exception as store_error:
            logger.error(f"Failed to store failed event: {store_error}")

    def _store_failed_event(self, event: Dict, error: Exception):
        """Store failed event for later retry"""
        import json

        failed_event = {
            'event': event,
            'error': {
                'type': type(error).__name__,
                'message': str(error),
                'timestamp': datetime.utcnow().isoformat()
            },
            'retry_count': event.get('retry_count', 0) + 1,
            'processor': 'TradeStreamProcessor'
        }

        # Store in Redis for retry
        if self.event_stream.redis:
            try:
                redis_key = f"failed_events:trade:{event.get('event_id', 'unknown')}"

                # Store with TTL of 7 days
                self.event_stream.redis.setex(
                    redis_key,
                    86400 * 7,
                    json.dumps(failed_event)
                )

                # Add to failed events list for batch retry
                self.event_stream.redis.lpush('failed_events:list', redis_key)
                self.event_stream.redis.ltrim('failed_events:list', 0, 999)  # Keep last 1000

                logger.info(f"Stored failed event for retry: {event.get('event_id')}")

            except Exception as e:
                logger.error(f"Failed to store in Redis: {e}")
        else:
            # Fallback: log to file
            from pathlib import Path

            failed_dir = Path("data/failed_events")
            failed_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            event_id = event.get('event_id', 'unknown')
            filepath = failed_dir / f"trade_{event_id}_{timestamp}.json"

            with open(filepath, 'w') as f:
                json.dump(failed_event, f, indent=2)

            logger.info(f"Stored failed event to file: {filepath}")


# Convenience function
def start_trade_processor(
    event_stream,
    orchestrator=None,
    price_service=None,
    alert_threshold: float = 0.7
) -> TradeStreamProcessor:
    """
    Start trade stream processor

    Args:
        event_stream: EventStream instance
        orchestrator: Optional JobOrchestrator for distributed processing
        price_service: Optional price service
        alert_threshold: Suspicion score threshold for alerts

    Returns:
        Running TradeStreamProcessor
    """
    processor = TradeStreamProcessor(
        event_stream=event_stream,
        orchestrator=orchestrator,
        price_service=price_service,
        alert_threshold=alert_threshold
    )

    logger.info("Trade stream processor started")
    return processor
