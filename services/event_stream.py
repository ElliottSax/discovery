"""
Event Streaming Service - Redis Pub/Sub

Provides pub/sub event streaming for real-time trade analysis and notifications.
Uses Redis as the message broker for low-latency event distribution.

Key Features:
- Publish events to named channels
- Subscribe to channels with custom handlers
- JSON message serialization
- Error handling and retry logic
- Health monitoring

Usage:
    stream = EventStream()

    # Publish event
    stream.publish('trades', {'trade_id': 123, 'ticker': 'NVDA'})

    # Subscribe to channel
    def handle_trade(event):
        print(f"New trade: {event}")

    stream.subscribe('trades', handle_trade)
    stream.listen()  # Blocking
"""

import redis
import json
import logging
import threading
from typing import Dict, Callable, Optional, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)


# Channel definitions
CHANNELS = {
    'trades': 'ultrathink:trades',              # New trade disclosures
    'prices': 'ultrathink:prices',              # Real-time price updates
    'news': 'ultrathink:news',                  # News feed events
    'analysis': 'ultrathink:analysis',          # Analysis results
    'alerts': 'ultrathink:alerts',              # Critical alerts
    'dashboard': 'ultrathink:dashboard',        # Dashboard updates
}


class EventStream:
    """Redis-based event streaming service"""

    def __init__(
        self,
        redis_url: str = 'redis://localhost:6379',
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize event stream

        Args:
            redis_url: Redis connection URL
            max_retries: Maximum retry attempts for failed operations
            retry_delay: Delay between retries (seconds)
        """
        self.redis_url = redis_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Redis clients
        self.redis = None
        self.pubsub = None

        # Subscription handlers
        self.handlers: Dict[str, Callable] = {}

        # Statistics
        self.stats = {
            'published': 0,
            'received': 0,
            'errors': 0,
            'start_time': datetime.utcnow()
        }

        # Connect to Redis
        self._connect()

    def _connect(self):
        """Connect to Redis with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.redis = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )

                # Test connection
                self.redis.ping()

                # Create pub/sub client
                self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)

                logger.info(f"Connected to Redis at {self.redis_url}")
                return

            except redis.RedisError as e:
                logger.warning(
                    f"Redis connection attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise ConnectionError(f"Failed to connect to Redis: {e}")

    def publish(
        self,
        channel: str,
        event: Dict[str, Any],
        event_type: Optional[str] = None
    ) -> bool:
        """
        Publish event to channel

        Args:
            channel: Channel name (use CHANNELS constants)
            event: Event data dictionary
            event_type: Optional event type for metadata

        Returns:
            True if published successfully

        Example:
            stream.publish('trades', {
                'politician': 'Nancy Pelosi',
                'ticker': 'NVDA',
                'amount': '$250,000-$500,000'
            }, event_type='trade_disclosure')
        """
        try:
            # Get full channel name
            channel_name = CHANNELS.get(channel, channel)

            # Add metadata
            message = {
                'event_type': event_type or 'unknown',
                'timestamp': datetime.utcnow().isoformat(),
                'data': event
            }

            # Serialize to JSON
            message_str = json.dumps(message)

            # Publish
            num_subscribers = self.redis.publish(channel_name, message_str)

            # Update stats
            self.stats['published'] += 1

            logger.debug(
                f"Published event to {channel} (type: {event_type}, "
                f"subscribers: {num_subscribers})"
            )

            return True

        except redis.RedisError as e:
            self.stats['errors'] += 1
            logger.error(f"Failed to publish event to {channel}: {e}")
            return False

        except json.JSONEncodeError as e:
            self.stats['errors'] += 1
            logger.error(f"Failed to serialize event: {e}")
            return False

    def subscribe(
        self,
        channel: str,
        handler: Callable[[Dict], None]
    ):
        """
        Subscribe to channel with handler function

        Args:
            channel: Channel name (use CHANNELS constants)
            handler: Function to call when event is received
                     Must accept Dict parameter with event data

        Example:
            def handle_trade(event):
                print(f"Trade: {event['data']['ticker']}")

            stream.subscribe('trades', handle_trade)
        """
        try:
            # Get full channel name
            channel_name = CHANNELS.get(channel, channel)

            # Store handler
            self.handlers[channel_name] = handler

            # Subscribe to channel
            self.pubsub.subscribe(channel_name)

            logger.info(f"Subscribed to channel: {channel}")

        except redis.RedisError as e:
            self.stats['errors'] += 1
            logger.error(f"Failed to subscribe to {channel}: {e}")
            raise

    def unsubscribe(self, channel: str):
        """Unsubscribe from channel"""
        try:
            channel_name = CHANNELS.get(channel, channel)

            # Remove handler
            if channel_name in self.handlers:
                del self.handlers[channel_name]

            # Unsubscribe
            self.pubsub.unsubscribe(channel_name)

            logger.info(f"Unsubscribed from channel: {channel}")

        except redis.RedisError as e:
            logger.error(f"Failed to unsubscribe from {channel}: {e}")

    def listen(self, timeout: Optional[float] = None):
        """
        Start listening for events (blocking)

        Args:
            timeout: Optional timeout in seconds (None = infinite)

        Note:
            This is a blocking call. Events are dispatched to registered handlers.
            Use listen_async() for non-blocking operation.
        """
        try:
            logger.info("Starting event listener...")

            # Track start time for timeout
            start_time = time.time()

            for message in self.pubsub.listen():
                # Check timeout
                if timeout:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        logger.info(f"Event listener timeout after {elapsed:.1f}s")
                        break

                # Process message
                if message['type'] == 'message':
                    self._handle_message(message)

        except KeyboardInterrupt:
            logger.info("Event listener stopped by user")

        except redis.RedisError as e:
            self.stats['errors'] += 1
            logger.error(f"Redis error in listener: {e}")
            raise

    def listen_async(self):
        """
        Start listening in background thread

        Returns:
            Thread object (already started)

        Example:
            listener_thread = stream.listen_async()
            # Do other work...
            listener_thread.join()  # Wait for completion
        """
        thread = threading.Thread(target=self.listen, daemon=True)
        thread.start()
        logger.info("Started async event listener")
        return thread

    def _handle_message(self, message: Dict):
        """Handle incoming message"""
        try:
            # Parse JSON
            data = json.loads(message['data'])

            # Get handler for this channel
            channel = message['channel']
            handler = self.handlers.get(channel)

            if not handler:
                logger.warning(f"No handler registered for channel: {channel}")
                return

            # Call handler
            handler(data)

            # Update stats
            self.stats['received'] += 1

        except json.JSONDecodeError as e:
            self.stats['errors'] += 1
            logger.error(f"Failed to parse message: {e}")

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error in event handler: {e}", exc_info=True)

    def get_stats(self) -> Dict:
        """Get streaming statistics"""
        uptime = (datetime.utcnow() - self.stats['start_time']).total_seconds()

        return {
            'published': self.stats['published'],
            'received': self.stats['received'],
            'errors': self.stats['errors'],
            'uptime_seconds': uptime,
            'publish_rate': self.stats['published'] / uptime if uptime > 0 else 0,
            'receive_rate': self.stats['received'] / uptime if uptime > 0 else 0,
        }

    def health_check(self) -> Dict:
        """Check health of event stream"""
        try:
            # Test Redis connection
            self.redis.ping()

            # Get Redis info
            info = self.redis.info()

            return {
                'status': 'healthy',
                'redis_version': info.get('redis_version', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'unknown'),
                'uptime_days': info.get('uptime_in_days', 0),
                **self.get_stats()
            }

        except redis.RedisError as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def close(self):
        """Close connections"""
        try:
            if self.pubsub:
                self.pubsub.close()
            if self.redis:
                self.redis.close()
            logger.info("Event stream closed")

        except redis.RedisError as e:
            logger.error(f"Error closing connections: {e}")


# Convenience functions

def create_event_stream(redis_url: Optional[str] = None) -> EventStream:
    """Create event stream with environment-based config"""
    import os

    if not redis_url:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

    return EventStream(redis_url=redis_url)


def publish_trade_event(stream: EventStream, trade: Dict):
    """Publish trade disclosure event"""
    stream.publish(
        'trades',
        trade,
        event_type='trade_disclosure'
    )


def publish_price_event(stream: EventStream, ticker: str, price: float, volume: int):
    """Publish price update event"""
    stream.publish(
        'prices',
        {
            'ticker': ticker,
            'price': price,
            'volume': volume
        },
        event_type='price_update'
    )


def publish_analysis_event(stream: EventStream, trade_id: str, analysis: Dict):
    """Publish analysis result event"""
    stream.publish(
        'analysis',
        {
            'trade_id': trade_id,
            'analysis': analysis
        },
        event_type='analysis_complete'
    )


def publish_alert_event(
    stream: EventStream,
    severity: str,
    alert_type: str,
    data: Dict
):
    """Publish critical alert event"""
    stream.publish(
        'alerts',
        {
            'severity': severity,
            'alert_type': alert_type,
            **data
        },
        event_type='critical_alert'
    )


def publish_dashboard_event(stream: EventStream, update: Dict):
    """Publish dashboard update event"""
    stream.publish(
        'dashboard',
        update,
        event_type='dashboard_update'
    )


def publish_error_event(
    stream: EventStream,
    event_id: str,
    processor: str,
    error_type: str,
    error_message: str,
    event_data: Optional[Dict] = None
):
    """
    Publish error event for monitoring

    Args:
        stream: EventStream instance
        event_id: ID of the event that failed
        processor: Name of processor that encountered error
        error_type: Type/class of error
        error_message: Error message
        event_data: Optional event data that caused error
    """
    stream.publish(
        'alerts',
        {
            'event_id': event_id,
            'processor': processor,
            'error_type': error_type,
            'error_message': error_message,
            'event_data': event_data or {},
            'severity': 'MEDIUM'
        },
        event_type='processing_error'
    )


# Example usage
if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create event stream
    stream = create_event_stream()

    # Example: Subscribe to trades
    def handle_trade(event):
        print(f"\nReceived trade event:")
        print(f"  Type: {event['event_type']}")
        print(f"  Time: {event['timestamp']}")
        print(f"  Data: {event['data']}")

    stream.subscribe('trades', handle_trade)

    # Example: Publish test event
    publish_trade_event(stream, {
        'politician': 'Nancy Pelosi',
        'ticker': 'NVDA',
        'transaction_type': 'purchase',
        'amount': '$250,000-$500,000'
    })

    # Listen for events (blocking)
    try:
        stream.listen()
    except KeyboardInterrupt:
        print("\nStopping...")
        stream.close()
