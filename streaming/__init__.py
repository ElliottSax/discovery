"""
Streaming Module - Real-Time Event Processing

Provides stream processors for handling real-time events:
- Trade disclosures
- Price updates
- Analysis results
- Critical alerts

Usage:
    from streaming import TradeStreamProcessor, AlertStreamProcessor
    from services.event_stream import EventStream

    stream = EventStream()

    trade_processor = TradeStreamProcessor(stream)
    alert_processor = AlertStreamProcessor(stream)

    stream.listen()  # Start processing events
"""

from .base_processor import BaseStreamProcessor
from .trade_processor import TradeStreamProcessor
from .alert_processor import AlertStreamProcessor
from .price_processor import PriceStreamProcessor

__all__ = [
    'BaseStreamProcessor',
    'TradeStreamProcessor',
    'AlertStreamProcessor',
    'PriceStreamProcessor',
]
