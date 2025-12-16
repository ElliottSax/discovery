#!/usr/bin/env python3
"""
Real-Time Streaming Example

Demonstrates the complete real-time streaming system:
- Event stream (Redis pub/sub)
- Real-time price feeds
- Trade stream processor
- Price stream processor
- Alert stream processor

This shows how all components work together for instant trade detection
and alerts.

Usage:
    # Make sure Redis is running
    redis-server

    # Set environment variables
    export REDIS_URL=redis://localhost:6379
    export ALPHA_VANTAGE_API_KEY=your_api_key_here

    # Run example
    python3 realtime_streaming_example.py
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from datetime import datetime

# Import services
from services.event_stream import create_event_stream, publish_trade_event
from services.realtime_prices import create_price_service

# Import stream processors
from streaming import (
    TradeStreamProcessor,
    PriceStreamProcessor,
    AlertStreamProcessor
)


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_1_basic_streaming():
    """Example 1: Basic event streaming"""
    print("\n" + "=" * 70)
    print("Example 1: Basic Event Streaming")
    print("=" * 70 + "\n")

    # Create event stream
    stream = create_event_stream()

    # Check health
    health = stream.health_check()
    print(f"Event Stream Health: {health['status']}")
    print(f"  Redis version: {health.get('redis_version', 'unknown')}")
    print(f"  Connected clients: {health.get('connected_clients', 0)}")
    print()

    # Define subscriber
    def handle_trade(event):
        print(f"Received trade event:")
        print(f"  Type: {event['event_type']}")
        print(f"  Politician: {event['data']['politician']}")
        print(f"  Ticker: {event['data']['ticker']}")
        print()

    # Subscribe
    stream.subscribe('trades', handle_trade)

    # Publish test event
    print("Publishing test trade event...")
    publish_trade_event(stream, {
        'politician': 'Nancy Pelosi',
        'ticker': 'NVDA',
        'transaction_type': 'purchase',
        'amount': '$250,000-$500,000',
        'trade_date': '2024-12-01',
        'disclosure_date': '2024-12-08'
    })

    # Listen for 2 seconds
    listener = stream.listen_async()
    await asyncio.sleep(2)

    # Show stats
    stats = stream.get_stats()
    print(f"Stream Statistics:")
    print(f"  Published: {stats['published']}")
    print(f"  Received: {stats['received']}")
    print(f"  Errors: {stats['errors']}")
    print()

    stream.close()


async def example_2_price_feeds():
    """Example 2: Real-time price feeds"""
    print("\n" + "=" * 70)
    print("Example 2: Real-Time Price Feeds")
    print("=" * 70 + "\n")

    # Create event stream
    stream = create_event_stream()

    # Create price service
    price_service = create_price_service(stream)

    # Track some tickers
    tickers = ['NVDA', 'AAPL', 'MSFT']
    print(f"Tracking tickers: {', '.join(tickers)}\n")

    for ticker in tickers:
        price_service.track_ticker(ticker)

    # Subscribe to price updates
    def handle_price(event):
        data = event['data']
        print(f"Price update: {data['ticker']} = ${data['price']:.2f} "
              f"(volume: {data.get('volume', 0):,})")

    stream.subscribe('prices', handle_price)

    # Start listening
    listener = stream.listen_async()

    # Start price service
    price_service.start()

    # Run for 30 seconds
    print("Collecting price updates for 30 seconds...\n")
    await asyncio.sleep(30)

    # Stop price service
    price_service.stop()

    # Show stats
    stats = price_service.get_stats()
    print(f"\nPrice Service Statistics:")
    print(f"  Updates received: {stats['updates_received']}")
    print(f"  Updates published: {stats['updates_published']}")
    print(f"  Cache hit rate: {stats['cache_hit_rate']:.1%}")
    print(f"  Update rate: {stats['update_rate']:.2f} updates/second")
    print()

    stream.close()


async def example_3_complete_system():
    """Example 3: Complete streaming system with all processors"""
    print("\n" + "=" * 70)
    print("Example 3: Complete Real-Time Streaming System")
    print("=" * 70 + "\n")

    # Create event stream
    stream = create_event_stream()

    # Create price service
    price_service = create_price_service(stream)

    # Track congressional trading activity tickers
    tracked_tickers = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'META']
    print(f"Tracking {len(tracked_tickers)} tickers for congressional trades\n")

    for ticker in tracked_tickers:
        price_service.track_ticker(ticker)

    # Initialize stream processors
    print("Initializing stream processors...")

    # Trade processor
    trade_processor = TradeStreamProcessor(
        event_stream=stream,
        alert_threshold=0.7  # Alert if suspicion score > 0.7
    )
    print("  ✓ Trade stream processor")

    # Price processor
    price_processor = PriceStreamProcessor(
        event_stream=stream,
        impact_threshold=0.03  # Alert on 3%+ price movement
    )
    print("  ✓ Price stream processor")

    # Alert processor
    alert_processor = AlertStreamProcessor(
        event_stream=stream,
        channels=['email', 'slack']
    )
    print("  ✓ Alert stream processor")
    print()

    # Start listening to events
    print("Starting event listener...")
    listener = stream.listen_async()

    # Start price service
    print("Starting real-time price feeds...")
    price_service.start()
    print()

    # Simulate some trades being detected
    print("Simulating trade disclosures...\n")

    sample_trades = [
        {
            'politician': 'Nancy Pelosi',
            'ticker': 'NVDA',
            'transaction_type': 'purchase',
            'amount': '$250,000-$500,000',
            'trade_date': '2024-12-01',
            'disclosure_date': '2024-12-08',
            'disclosure_text': 'Purchase of NVIDIA stock'
        },
        {
            'politician': 'Dan Crenshaw',
            'ticker': 'AAPL',
            'transaction_type': 'sale',
            'amount': '$100,000-$250,000',
            'trade_date': '2024-12-05',
            'disclosure_date': '2024-12-08',
            'disclosure_text': 'Sale of Apple Inc stock'
        }
    ]

    for trade in sample_trades:
        print(f"Publishing trade: {trade['politician']} - {trade['ticker']} ({trade['transaction_type']})")
        publish_trade_event(stream, trade)
        await asyncio.sleep(2)

    print()

    # Run system for 60 seconds
    print("System running... (monitoring for 60 seconds)\n")
    await asyncio.sleep(60)

    # Stop services
    print("\nStopping services...")
    price_service.stop()

    # Show statistics
    print("\n" + "=" * 70)
    print("System Statistics")
    print("=" * 70 + "\n")

    # Event stream stats
    stream_stats = stream.get_stats()
    print("Event Stream:")
    print(f"  Events published: {stream_stats['published']}")
    print(f"  Events received: {stream_stats['received']}")
    print(f"  Publish rate: {stream_stats['publish_rate']:.2f} events/second")
    print(f"  Receive rate: {stream_stats['receive_rate']:.2f} events/second")
    print()

    # Price service stats
    price_stats = price_service.get_stats()
    print("Price Service:")
    print(f"  Price updates: {price_stats['updates_received']}")
    print(f"  Cache hit rate: {price_stats['cache_hit_rate']:.1%}")
    print(f"  Update rate: {price_stats['update_rate']:.2f} updates/second")
    print()

    # Processor stats
    print("Stream Processors:")

    trade_stats = trade_processor.get_stats()
    print(f"  Trade Processor:")
    print(f"    Events processed: {trade_stats['events_processed']}")
    print(f"    Success rate: {trade_stats['success_rate']:.1%}")
    print(f"    Avg processing time: {trade_stats['avg_processing_time']:.3f}s")

    price_proc_stats = price_processor.get_stats()
    print(f"  Price Processor:")
    print(f"    Events processed: {price_proc_stats['events_processed']}")
    print(f"    Success rate: {price_proc_stats['success_rate']:.1%}")

    alert_stats = alert_processor.get_stats()
    print(f"  Alert Processor:")
    print(f"    Events processed: {alert_stats['events_processed']}")
    print(f"    Success rate: {alert_stats['success_rate']:.1%}")
    print()

    stream.close()


async def example_4_dashboard_integration():
    """Example 4: Dashboard live updates"""
    print("\n" + "=" * 70)
    print("Example 4: Dashboard Live Updates")
    print("=" * 70 + "\n")

    stream = create_event_stream()

    # Subscribe to dashboard updates
    def handle_dashboard_update(event):
        data = event['data']
        update_type = data.get('update_type')

        if update_type == 'new_trade':
            trade = data['trade']
            analysis = data['analysis']
            print(f"\n📊 Dashboard: New Trade")
            print(f"  Politician: {trade['politician']}")
            print(f"  Ticker: {trade['ticker']} (${trade.get('current_price', 0):.2f})")
            print(f"  Type: {trade['transaction_type']}")
            print(f"  Suspicion: {analysis.get('suspicion_score', 0):.2%}")

        elif update_type == 'new_alert':
            alert = data['alert']
            print(f"\n🚨 Dashboard: New Alert")
            print(f"  Severity: {alert.get('severity')}")
            print(f"  Type: {alert.get('alert_type')}")
            print(f"  Politician: {alert.get('politician')}")
            print(f"  Ticker: {alert.get('ticker')}")

        elif update_type == 'price_update':
            print(f"\n💹 Dashboard: Price Update")
            print(f"  Ticker: {data['ticker']}")
            print(f"  Price: ${data['price']:.2f}")
            print(f"  Active trades: {data.get('active_trades', 0)}")

    stream.subscribe('dashboard', handle_dashboard_update)

    # Start listener
    listener = stream.listen_async()

    # Simulate dashboard updates
    from services.event_stream import publish_dashboard_event

    print("Simulating dashboard updates...\n")

    # Price update
    publish_dashboard_event(stream, {
        'update_type': 'price_update',
        'ticker': 'NVDA',
        'price': 145.50,
        'volume': 1234567,
        'active_trades': 3,
        'profitable_trades': 2
    })

    await asyncio.sleep(2)

    # New trade
    publish_dashboard_event(stream, {
        'update_type': 'new_trade',
        'trade': {
            'politician': 'Nancy Pelosi',
            'ticker': 'NVDA',
            'transaction_type': 'purchase',
            'amount': '$250,000-$500,000',
            'trade_date': '2024-12-01',
            'current_price': 145.50
        },
        'analysis': {
            'suspicion_score': 0.85,
            'sentiment': 'positive',
            'front_running_detected': True
        }
    })

    await asyncio.sleep(2)

    # Alert
    from services.event_stream import publish_alert_event

    publish_alert_event(stream, 'HIGH', 'front_running', {
        'politician': 'Nancy Pelosi',
        'ticker': 'NVDA',
        'suspicion_score': 0.85
    })

    await asyncio.sleep(2)

    print("\n✓ Dashboard integration demonstrated\n")

    stream.close()


async def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Real-Time Streaming Examples" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")

    # Check Redis connection
    try:
        from services.event_stream import create_event_stream
        stream = create_event_stream()
        health = stream.health_check()

        if health['status'] != 'healthy':
            print("\n⚠️  WARNING: Redis connection failed!")
            print("   Make sure Redis is running: redis-server")
            print(f"   Error: {health.get('error', 'unknown')}")
            print()
            return

        stream.close()
        print("\n✓ Redis connection successful\n")

    except Exception as e:
        print(f"\n❌ Error connecting to Redis: {e}")
        print("   Make sure Redis is running and REDIS_URL is set")
        print()
        return

    # Run examples
    try:
        await example_1_basic_streaming()
        await example_2_price_feeds()
        await example_4_dashboard_integration()

        # Example 3 takes longer - ask user
        print("\n" + "=" * 70)
        print("Example 3 runs the complete system for 60 seconds")
        print("This will fetch live prices and demonstrate the full pipeline")
        print("=" * 70)

        # For automated runs, skip example 3
        # Uncomment to run:
        # await example_3_complete_system()

        print("\n" + "=" * 70)
        print("Examples completed successfully!")
        print("=" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user\n")

    except Exception as e:
        print(f"\n\nError running examples: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
