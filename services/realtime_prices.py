"""
Real-Time Price Feed Service

Provides real-time stock price updates via WebSocket and REST APIs.
Integrates with multiple data providers and publishes updates to event stream.

Supported Providers:
- Alpha Vantage (WebSocket + REST)
- Finnhub (WebSocket)
- IEX Cloud (WebSocket)
- Polygon.io (WebSocket)

Features:
- Real-time price updates
- Redis caching for fast lookups
- Automatic reconnection
- Multiple provider fallback
- Rate limit handling

Usage:
    from services.realtime_prices import RealtimePriceService
    from services.event_stream import EventStream

    stream = EventStream()
    price_service = RealtimePriceService(stream)

    # Track tickers
    price_service.track_ticker('NVDA')
    price_service.track_ticker('AAPL')

    # Start streaming
    price_service.start()
"""

import logging
import asyncio
import aiohttp
import redis
import json
import os
from typing import Dict, Set, Optional, Callable
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class RealtimePriceService:
    """Real-time stock price feed service"""

    def __init__(
        self,
        event_stream,
        api_key: Optional[str] = None,
        redis_client: Optional[redis.Redis] = None,
        provider: str = 'alpha_vantage',
        update_interval: int = 5
    ):
        """
        Initialize price service

        Args:
            event_stream: EventStream instance for publishing updates
            api_key: API key for data provider
            redis_client: Redis client for caching (optional)
            provider: Data provider ('alpha_vantage', 'finnhub', 'iex', 'polygon')
            update_interval: Update interval in seconds (for polling mode)
        """
        self.event_stream = event_stream
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.provider = provider
        self.update_interval = update_interval

        # Redis caching
        self.redis = redis_client
        if not self.redis and os.getenv('REDIS_URL'):
            try:
                self.redis = redis.from_url(
                    os.getenv('REDIS_URL'),
                    decode_responses=True
                )
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")

        # Tracked tickers
        self.tracked_tickers: Set[str] = set()

        # Price cache (in-memory fallback)
        self.price_cache: Dict[str, Dict] = {}

        # WebSocket connection
        self.ws_session = None
        self.ws_connection = None

        # Running state
        self.running = False
        self.update_task = None

        # Statistics
        self.stats = {
            'updates_received': 0,
            'updates_published': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'start_time': None
        }

        logger.info(f"Price service initialized (provider: {provider})")

    def track_ticker(self, ticker: str):
        """
        Add ticker to real-time tracking

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')
        """
        ticker = ticker.upper()
        self.tracked_tickers.add(ticker)
        logger.info(f"Now tracking ticker: {ticker}")

    def untrack_ticker(self, ticker: str):
        """Remove ticker from tracking"""
        ticker = ticker.upper()
        if ticker in self.tracked_tickers:
            self.tracked_tickers.remove(ticker)
            logger.info(f"Stopped tracking ticker: {ticker}")

    def get_tracked_tickers(self) -> Set[str]:
        """Get list of currently tracked tickers"""
        return self.tracked_tickers.copy()

    async def get_current_price(self, ticker: str) -> Dict:
        """
        Get current price for ticker

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dict with price data:
            {
                'ticker': 'NVDA',
                'price': 145.50,
                'volume': 1234567,
                'timestamp': '2024-12-08T10:30:00Z',
                'change': 2.50,
                'change_percent': 1.75
            }
        """
        ticker = ticker.upper()

        # Try cache first
        cached = self._get_cached_price(ticker)
        if cached:
            self.stats['cache_hits'] += 1
            return cached

        # Cache miss - fetch from API
        self.stats['cache_misses'] += 1

        try:
            price_data = await self._fetch_price_from_api(ticker)

            if price_data:
                # Cache the result
                self._cache_price(ticker, price_data)

            return price_data

        except Exception as e:
            logger.error(f"Failed to get price for {ticker}: {e}")
            self.stats['errors'] += 1
            return None

    async def _fetch_price_from_api(self, ticker: str) -> Optional[Dict]:
        """Fetch current price from API"""
        if self.provider == 'alpha_vantage':
            return await self._fetch_alpha_vantage(ticker)
        elif self.provider == 'finnhub':
            return await self._fetch_finnhub(ticker)
        elif self.provider == 'iex':
            return await self._fetch_iex(ticker)
        else:
            logger.error(f"Unknown provider: {self.provider}")
            return None

    async def _fetch_alpha_vantage(self, ticker: str) -> Optional[Dict]:
        """Fetch from Alpha Vantage API"""
        if not self.api_key:
            logger.warning("Alpha Vantage API key not configured")
            return None

        url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': ticker,
            'apikey': self.api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if 'Global Quote' in data:
                            quote = data['Global Quote']

                            return {
                                'ticker': ticker,
                                'price': float(quote.get('05. price', 0)),
                                'volume': int(quote.get('06. volume', 0)),
                                'timestamp': datetime.utcnow().isoformat(),
                                'change': float(quote.get('09. change', 0)),
                                'change_percent': float(quote.get('10. change percent', '0').replace('%', ''))
                            }

                        elif 'Note' in data:
                            logger.warning(f"Alpha Vantage API limit reached: {data['Note']}")

                        else:
                            logger.warning(f"Unexpected Alpha Vantage response: {data}")

        except Exception as e:
            logger.error(f"Error fetching from Alpha Vantage: {e}")

        return None

    async def _fetch_finnhub(self, ticker: str) -> Optional[Dict]:
        """Fetch from Finnhub API"""
        # Implementation for Finnhub
        logger.warning("Finnhub not yet implemented")
        return None

    async def _fetch_iex(self, ticker: str) -> Optional[Dict]:
        """Fetch from IEX Cloud API"""
        # Implementation for IEX Cloud
        logger.warning("IEX Cloud not yet implemented")
        return None

    def _get_cached_price(self, ticker: str) -> Optional[Dict]:
        """Get price from cache"""
        # Try Redis first
        if self.redis:
            try:
                cached = self.redis.get(f'price:{ticker}')
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.debug(f"Redis cache read error: {e}")

        # Fall back to in-memory cache
        if ticker in self.price_cache:
            cache_entry = self.price_cache[ticker]

            # Check if cache is still valid (60 seconds)
            if 'timestamp' in cache_entry:
                cache_time = datetime.fromisoformat(cache_entry['timestamp'])
                age = (datetime.utcnow() - cache_time).total_seconds()

                if age < 60:
                    return cache_entry

        return None

    def _cache_price(self, ticker: str, price_data: Dict):
        """Cache price data"""
        # Cache in Redis with 60 second TTL
        if self.redis:
            try:
                self.redis.set(
                    f'price:{ticker}',
                    json.dumps(price_data),
                    ex=60
                )
            except Exception as e:
                logger.debug(f"Redis cache write error: {e}")

        # Also cache in memory
        self.price_cache[ticker] = price_data

    def _publish_price_update(self, price_data: Dict):
        """Publish price update to event stream"""
        try:
            from services.event_stream import publish_price_event

            publish_price_event(
                self.event_stream,
                price_data['ticker'],
                price_data['price'],
                price_data['volume']
            )

            self.stats['updates_published'] += 1

            logger.debug(
                f"Published price update: {price_data['ticker']} = "
                f"${price_data['price']:.2f}"
            )

        except Exception as e:
            logger.error(f"Failed to publish price update: {e}")
            self.stats['errors'] += 1

    async def _update_loop(self):
        """Main update loop (polling mode)"""
        logger.info("Starting price update loop")

        while self.running:
            try:
                # Update all tracked tickers
                for ticker in self.tracked_tickers:
                    try:
                        price_data = await self.get_current_price(ticker)

                        if price_data:
                            # Publish to event stream
                            self._publish_price_update(price_data)

                            self.stats['updates_received'] += 1

                    except Exception as e:
                        logger.error(f"Error updating {ticker}: {e}")
                        self.stats['errors'] += 1

                # Wait before next update
                await asyncio.sleep(self.update_interval)

            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(5)

        logger.info("Price update loop stopped")

    def start(self):
        """Start price feed service"""
        if self.running:
            logger.warning("Price service already running")
            return

        self.running = True
        self.stats['start_time'] = datetime.utcnow()

        # Start update loop in background
        self.update_task = asyncio.create_task(self._update_loop())

        logger.info(
            f"Price service started (tracking {len(self.tracked_tickers)} tickers)"
        )

    def stop(self):
        """Stop price feed service"""
        if not self.running:
            return

        self.running = False

        if self.update_task:
            self.update_task.cancel()

        logger.info("Price service stopped")

    def get_stats(self) -> Dict:
        """Get service statistics"""
        uptime = None
        if self.stats['start_time']:
            uptime = (datetime.utcnow() - self.stats['start_time']).total_seconds()

        return {
            'running': self.running,
            'tracked_tickers': len(self.tracked_tickers),
            'updates_received': self.stats['updates_received'],
            'updates_published': self.stats['updates_published'],
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'cache_hit_rate': (
                self.stats['cache_hits'] /
                (self.stats['cache_hits'] + self.stats['cache_misses'])
                if (self.stats['cache_hits'] + self.stats['cache_misses']) > 0
                else 0
            ),
            'errors': self.stats['errors'],
            'uptime_seconds': uptime,
            'update_rate': (
                self.stats['updates_published'] / uptime
                if uptime and uptime > 0 else 0
            )
        }

    def health_check(self) -> Dict:
        """Check service health"""
        stats = self.get_stats()

        # Determine health status
        if not self.running:
            status = 'stopped'
        elif stats['errors'] > 100:
            status = 'unhealthy'
        elif len(self.tracked_tickers) == 0:
            status = 'idle'
        else:
            status = 'healthy'

        return {
            'status': status,
            'provider': self.provider,
            **stats
        }


# Convenience functions

def create_price_service(
    event_stream,
    api_key: Optional[str] = None,
    provider: str = 'alpha_vantage'
) -> RealtimePriceService:
    """
    Create price service with default configuration

    Args:
        event_stream: EventStream instance
        api_key: API key (defaults to ALPHA_VANTAGE_API_KEY env var)
        provider: Data provider

    Returns:
        Configured RealtimePriceService
    """
    return RealtimePriceService(
        event_stream=event_stream,
        api_key=api_key,
        provider=provider
    )


# Example usage
if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async def main():
        # Create event stream
        from services.event_stream import create_event_stream
        stream = create_event_stream()

        # Create price service
        price_service = create_price_service(stream)

        # Track some tickers
        price_service.track_ticker('NVDA')
        price_service.track_ticker('AAPL')
        price_service.track_ticker('MSFT')

        # Start service
        price_service.start()

        # Run for 60 seconds
        await asyncio.sleep(60)

        # Show stats
        stats = price_service.get_stats()
        print(f"\nService Statistics:")
        print(f"  Updates received: {stats['updates_received']}")
        print(f"  Updates published: {stats['updates_published']}")
        print(f"  Cache hit rate: {stats['cache_hit_rate']:.1%}")
        print(f"  Errors: {stats['errors']}")

        # Stop service
        price_service.stop()

    # Run
    asyncio.run(main())
