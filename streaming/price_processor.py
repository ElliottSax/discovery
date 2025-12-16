"""
Price Stream Processor

Processes real-time price update events:
1. Receives price updates from event stream
2. Checks for active trades on that ticker
3. Calculates market impact in real-time
4. Triggers alerts for significant price movements
5. Updates dashboard with live prices

Usage:
    from streaming import PriceStreamProcessor
    from services.event_stream import EventStream

    stream = EventStream()
    processor = PriceStreamProcessor(stream)

    stream.listen()  # Start processing price updates
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_processor import BaseStreamProcessor
from services.event_stream import publish_analysis_event, publish_dashboard_event

logger = logging.getLogger(__name__)


class PriceStreamProcessor(BaseStreamProcessor):
    """Process real-time price updates"""

    def __init__(
        self,
        event_stream,
        database=None,
        impact_threshold: float = 0.03  # 3% price movement
    ):
        """
        Initialize price processor

        Args:
            event_stream: EventStream instance
            database: Database connection for querying active trades
            impact_threshold: Price movement threshold for alerts (0-1)
        """
        super().__init__(event_stream, name="PriceStreamProcessor")

        self.database = database
        self.impact_threshold = impact_threshold

        # Subscribe to prices channel
        self.event_stream.subscribe('prices', self.handle_event)

        # Track recent prices for change detection
        self.recent_prices: Dict[str, List[Dict]] = {}

        logger.info(
            f"Price processor initialized (impact_threshold={impact_threshold:.1%})"
        )

    async def process_event(self, event: Dict) -> Dict[str, Any]:
        """
        Process price update event

        Args:
            event: Price event
                {
                    'event_type': 'price_update',
                    'timestamp': '2024-12-08T10:30:15Z',
                    'data': {
                        'ticker': 'NVDA',
                        'price': 145.50,
                        'volume': 1234567
                    }
                }

        Returns:
            Processing result
        """
        price_data = event.get('data', {})
        ticker = price_data.get('ticker')
        price = price_data.get('price')

        if not ticker or not price:
            return {'status': 'skipped', 'reason': 'missing data'}

        logger.debug(f"Processing price update: {ticker} = ${price:.2f}")

        # Store recent price
        self._store_recent_price(ticker, price_data)

        # Check for active trades on this ticker
        active_trades = await self._get_active_trades(ticker)

        if not active_trades:
            logger.debug(f"No active trades for {ticker}")
            return {'status': 'success', 'active_trades': 0}

        # Analyze market impact for each active trade
        impacts = []
        for trade in active_trades:
            impact = await self._analyze_price_impact(trade, price_data)

            if impact:
                impacts.append(impact)

                # Check if significant
                if self._is_significant_impact(impact):
                    await self._trigger_impact_alert(trade, impact)

        # Update dashboard with live price
        self._update_dashboard(ticker, price_data, impacts)

        return {
            'status': 'success',
            'ticker': ticker,
            'active_trades': len(active_trades),
            'impacts_analyzed': len(impacts)
        }

    def _store_recent_price(self, ticker: str, price_data: Dict):
        """Store recent price for trend analysis"""
        if ticker not in self.recent_prices:
            self.recent_prices[ticker] = []

        # Add current price
        self.recent_prices[ticker].append({
            'price': price_data['price'],
            'volume': price_data.get('volume', 0),
            'timestamp': price_data.get('timestamp') or datetime.utcnow().isoformat()
        })

        # Keep only last 100 prices
        if len(self.recent_prices[ticker]) > 100:
            self.recent_prices[ticker] = self.recent_prices[ticker][-100:]

    async def _get_active_trades(self, ticker: str) -> List[Dict]:
        """
        Get active trades for ticker

        Active = disclosed within last 30 days
        """
        if not self.database:
            # Fallback: mock data for testing
            return []

        try:
            # Query database for recent trades on this ticker
            # TODO: Implement actual database query
            # For now, return empty list
            return []

        except Exception as e:
            logger.error(f"Failed to query active trades: {e}")
            return []

    async def _analyze_price_impact(
        self,
        trade: Dict,
        current_price_data: Dict
    ) -> Optional[Dict]:
        """
        Analyze market impact of price movement on trade

        Returns impact analysis with:
        - price_at_disclosure
        - current_price
        - price_change_pct
        - profit_loss
        - abnormal_return (vs market)
        """
        try:
            ticker = trade.get('ticker')
            disclosure_date = trade.get('disclosure_date')
            transaction_type = trade.get('transaction_type')

            if not all([ticker, disclosure_date, transaction_type]):
                return None

            # Get price at disclosure (from cache or database)
            disclosure_price = await self._get_price_at_disclosure(
                ticker,
                disclosure_date
            )

            if not disclosure_price:
                logger.debug(f"No disclosure price for {ticker} at {disclosure_date}")
                return None

            current_price = current_price_data['price']

            # Calculate price change
            price_change = current_price - disclosure_price
            price_change_pct = (price_change / disclosure_price) * 100

            # Calculate P&L based on transaction type
            if transaction_type.lower() == 'purchase':
                # Buying - profit if price goes up
                profit_direction = price_change_pct
            else:  # sale
                # Selling - profit if price goes down
                profit_direction = -price_change_pct

            # TODO: Calculate abnormal return (vs S&P 500)
            # For now, just use raw price change
            abnormal_return = price_change_pct

            return {
                'trade_id': trade.get('id'),
                'ticker': ticker,
                'disclosure_price': disclosure_price,
                'current_price': current_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'profit_direction': profit_direction,
                'abnormal_return': abnormal_return,
                'is_profitable': profit_direction > 0
            }

        except Exception as e:
            logger.error(f"Error analyzing price impact: {e}")
            return None

    async def _get_price_at_disclosure(
        self,
        ticker: str,
        disclosure_date: str
    ) -> Optional[float]:
        """Get stock price at disclosure date"""
        # Try cache first
        cache_key = f'price_at_disclosure:{ticker}:{disclosure_date}'

        if self.event_stream.redis:
            try:
                cached = self.event_stream.redis.get(cache_key)
                if cached:
                    return float(cached)
            except Exception:
                pass

        # Fetch from historical data
        # TODO: Implement historical price lookup
        # For now, use recent prices as approximation
        if ticker in self.recent_prices and self.recent_prices[ticker]:
            # Use oldest recent price as approximation
            return self.recent_prices[ticker][0]['price']

        return None

    def _is_significant_impact(self, impact: Dict) -> bool:
        """Determine if price impact is significant"""
        price_change_pct = abs(impact.get('price_change_pct', 0))
        return price_change_pct >= (self.impact_threshold * 100)

    async def _trigger_impact_alert(self, trade: Dict, impact: Dict):
        """Trigger alert for significant price impact"""
        from services.event_stream import publish_alert_event

        severity = 'HIGH' if abs(impact['price_change_pct']) > 10 else 'MEDIUM'

        publish_alert_event(
            self.event_stream,
            severity=severity,
            alert_type='significant_price_movement',
            data={
                'trade_id': trade.get('id'),
                'politician': trade.get('politician'),
                'ticker': impact['ticker'],
                'transaction_type': trade.get('transaction_type'),
                'disclosure_price': impact['disclosure_price'],
                'current_price': impact['current_price'],
                'price_change_pct': impact['price_change_pct'],
                'profit_direction': impact['profit_direction'],
                'is_profitable': impact['is_profitable']
            }
        )

        logger.info(
            f"Price impact alert: {trade.get('politician')} - {impact['ticker']} "
            f"({impact['price_change_pct']:+.2f}%)"
        )

    def _update_dashboard(
        self,
        ticker: str,
        price_data: Dict,
        impacts: List[Dict]
    ):
        """Send live price update to dashboard"""
        # Calculate aggregate stats for this ticker
        total_impacts = len(impacts)
        profitable_count = sum(1 for i in impacts if i.get('is_profitable', False))

        publish_dashboard_event(
            self.event_stream,
            {
                'update_type': 'price_update',
                'ticker': ticker,
                'price': price_data['price'],
                'volume': price_data.get('volume', 0),
                'timestamp': price_data.get('timestamp'),
                'active_trades': total_impacts,
                'profitable_trades': profitable_count
            }
        )

    def get_recent_prices(self, ticker: str, count: int = 10) -> List[Dict]:
        """Get recent prices for ticker"""
        if ticker not in self.recent_prices:
            return []

        return self.recent_prices[ticker][-count:]

    def calculate_price_trend(self, ticker: str, window: int = 10) -> Dict:
        """
        Calculate price trend for ticker

        Returns:
            {
                'trend': 'up' | 'down' | 'flat',
                'change_pct': float,
                'volatility': float
            }
        """
        recent = self.get_recent_prices(ticker, window)

        if len(recent) < 2:
            return {'trend': 'unknown', 'change_pct': 0, 'volatility': 0}

        # Calculate trend
        first_price = recent[0]['price']
        last_price = recent[-1]['price']
        change_pct = ((last_price - first_price) / first_price) * 100

        # Determine trend
        if change_pct > 1:
            trend = 'up'
        elif change_pct < -1:
            trend = 'down'
        else:
            trend = 'flat'

        # Calculate volatility (standard deviation of returns)
        returns = []
        for i in range(1, len(recent)):
            ret = (recent[i]['price'] - recent[i-1]['price']) / recent[i-1]['price']
            returns.append(ret)

        if returns:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            volatility = variance ** 0.5
        else:
            volatility = 0

        return {
            'trend': trend,
            'change_pct': change_pct,
            'volatility': volatility * 100  # Convert to percentage
        }

    def on_error(self, event: Dict, error: Exception):
        """Handle processing error"""
        logger.error(
            f"Price processing error: {error}\n"
            f"Ticker: {event.get('data', {}).get('ticker')}"
        )


# Convenience function
def start_price_processor(
    event_stream,
    database=None,
    impact_threshold: float = 0.03
) -> PriceStreamProcessor:
    """
    Start price stream processor

    Args:
        event_stream: EventStream instance
        database: Database connection
        impact_threshold: Price movement threshold for alerts

    Returns:
        Running PriceStreamProcessor
    """
    processor = PriceStreamProcessor(
        event_stream=event_stream,
        database=database,
        impact_threshold=impact_threshold
    )

    logger.info("Price stream processor started")
    return processor
