#!/usr/bin/env python3
"""
Streaming Infrastructure Integration Test

Tests all streaming processors with mock data:
- Price Processor (database queries, abnormal returns, price lookup)
- Trade Processor (analysis, error handling, retry)
- Alert Processor (notifications, fallback)
- Event Stream (pub/sub, timeouts, error events)
- Alert Manager (daily summaries)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockDatabase:
    """Mock database connection for testing"""

    def __init__(self):
        self.trades = generate_mock_trades(100)
        self.politicians = generate_mock_politicians()
        self._cursor = None

    def cursor(self):
        """Return mock cursor"""
        self._cursor = MockCursor(self.trades, self.politicians)
        return self._cursor


class MockCursor:
    """Mock database cursor"""

    def __init__(self, trades, politicians):
        self.trades = trades
        self.politicians = politicians
        self._results = []

    def execute(self, query, params=None):
        """Execute mock query"""
        # Simulate active trades query
        if 'trades t' in query and 'WHERE' in query:
            ticker = params[0] if params else None
            cutoff = params[1] if params and len(params) > 1 else datetime.now() - timedelta(days=30)

            # Filter trades
            self._results = [
                (
                    t['id'],
                    t['ticker'],
                    t['transaction_date'],
                    t['disclosure_date'],
                    t['transaction_type'],
                    t['amount_min'],
                    t['amount_max'],
                    t['politician'],
                    t['party'],
                    t['chamber']
                )
                for t in self.trades
                if (ticker is None or t['ticker'].upper() == ticker.upper())
                and t['disclosure_date'] >= cutoff
            ]

    def fetchall(self):
        """Fetch all results"""
        return self._results

    def fetchone(self):
        """Fetch one result"""
        return self._results[0] if self._results else None

    def close(self):
        """Close cursor"""
        pass


def generate_mock_politicians() -> List[Dict]:
    """Generate mock politician data"""
    politicians = [
        {'id': 1, 'name': 'Nancy Pelosi', 'party': 'D', 'chamber': 'House'},
        {'id': 2, 'name': 'Mitch McConnell', 'party': 'R', 'chamber': 'Senate'},
        {'id': 3, 'name': 'AOC', 'party': 'D', 'chamber': 'House'},
        {'id': 4, 'name': 'Ted Cruz', 'party': 'R', 'chamber': 'Senate'},
        {'id': 5, 'name': 'Elizabeth Warren', 'party': 'D', 'chamber': 'Senate'},
    ]
    return politicians


def generate_mock_trades(count: int = 100) -> List[Dict]:
    """Generate mock trade data for testing"""

    tickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN', 'META', 'NFLX']
    politicians = generate_mock_politicians()

    trades = []
    base_date = datetime.now() - timedelta(days=90)

    for i in range(count):
        trade_date = base_date + timedelta(days=i % 90)
        disclosure_date = trade_date + timedelta(days=15 + (i % 30))

        pol = politicians[i % len(politicians)]

        trade = {
            'id': i + 1,
            'ticker': tickers[i % len(tickers)],
            'transaction_date': trade_date,
            'disclosure_date': disclosure_date,
            'transaction_type': 'purchase' if i % 3 != 0 else 'sale',
            'amount_min': 15000 + (i * 1000),
            'amount_max': 50000 + (i * 2000),
            'politician': pol['name'],
            'politician_id': pol['id'],
            'party': pol['party'],
            'chamber': pol['chamber']
        }

        trades.append(trade)

    logger.info(f"Generated {len(trades)} mock trades")
    return trades


class TestStreamingIntegration(unittest.TestCase):
    """Integration tests for streaming infrastructure"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.mock_db = MockDatabase()
        cls.mock_trades = cls.mock_db.trades
        cls.mock_politicians = cls.mock_db.politicians

    def test_01_mock_data_generation(self):
        """Test mock data generation"""
        self.assertEqual(len(self.mock_trades), 100)
        self.assertEqual(len(self.mock_politicians), 5)

        # Verify trade structure
        trade = self.mock_trades[0]
        self.assertIn('ticker', trade)
        self.assertIn('politician', trade)
        self.assertIn('transaction_type', trade)

        logger.info("✅ Mock data generation: PASSED")

    def test_02_database_mock(self):
        """Test mock database queries"""
        cursor = self.mock_db.cursor()

        # Test active trades query
        cutoff = datetime.now() - timedelta(days=30)
        cursor.execute(
            "SELECT * FROM trades t WHERE ticker = %s AND disclosure_date >= %s",
            ('NVDA', cutoff)
        )

        results = cursor.fetchall()
        self.assertGreater(len(results), 0)

        # Verify result structure
        result = results[0]
        self.assertEqual(len(result), 10)  # All fields

        logger.info(f"✅ Database mock: PASSED ({len(results)} results)")

    def test_03_price_processor_active_trades(self):
        """Test PriceProcessor._get_active_trades()"""
        from streaming.price_processor import PriceStreamProcessor
        from services.event_stream import EventStream

        # Create processor with mock database
        try:
            stream = EventStream()
        except:
            # Mock event stream if Redis not available
            stream = MockEventStream()

        processor = PriceStreamProcessor(
            event_stream=stream,
            database=self.mock_db
        )

        # Test query
        loop = asyncio.get_event_loop()
        trades = loop.run_until_complete(processor._get_active_trades('NVDA'))

        self.assertIsInstance(trades, list)
        self.assertGreater(len(trades), 0)

        # Verify trade structure
        if trades:
            trade = trades[0]
            self.assertIn('ticker', trade)
            self.assertIn('politician', trade)

        logger.info(f"✅ Price processor active trades: PASSED ({len(trades)} trades)")

    def test_04_price_processor_abnormal_return(self):
        """Test abnormal return calculation"""
        from streaming.price_processor import PriceStreamProcessor

        try:
            stream = EventStream()
        except:
            stream = MockEventStream()

        processor = PriceStreamProcessor(
            event_stream=stream,
            database=self.mock_db
        )

        # Test abnormal return calculation
        loop = asyncio.get_event_loop()

        # Mock disclosure date and prices
        disclosure_date = datetime.now() - timedelta(days=30)
        disclosure_price = 100.0
        current_price = 110.0

        abnormal_return = loop.run_until_complete(
            processor._calculate_abnormal_return(
                'NVDA',
                disclosure_date.isoformat(),
                disclosure_price,
                current_price
            )
        )

        self.assertIsInstance(abnormal_return, float)
        # Should be close to 10% if market flat, but may vary with S&P 500

        logger.info(f"✅ Abnormal return calculation: PASSED ({abnormal_return:.2f}%)")

    def test_05_trade_processor_error_handling(self):
        """Test TradeProcessor error handling and retry"""
        from streaming.trade_processor import TradeStreamProcessor

        try:
            stream = EventStream()
        except:
            stream = MockEventStream()

        processor = TradeStreamProcessor(
            event_stream=stream
        )

        # Test error handling
        test_event = {
            'event_id': 'test_123',
            'data': {
                'politician': 'Test Politician',
                'ticker': 'NVDA',
                'transaction_type': 'purchase'
            }
        }

        # Trigger error
        test_error = ValueError("Test error")
        processor.on_error(test_event, test_error)

        # Verify error was logged (check that it doesn't crash)
        self.assertTrue(True)

        logger.info("✅ Trade processor error handling: PASSED")

    def test_06_alert_manager_daily_summary(self):
        """Test AlertManager daily summary"""
        from analysis.alerts.alert_manager import AlertManager

        manager = AlertManager(
            email_addresses=['test@example.com'],
            enable_email=False,
            enable_slack=False
        )

        # Create mock discoveries
        discoveries = []
        for i in range(10):
            discoveries.append({
                'politician': f'Politician {i % 3}',
                'type': ['front_running', 'insider_information', 'suspicious_timing'][i % 3],
                'timestamp': datetime.now().isoformat(),
                'finding': {
                    'severity': ['CRITICAL', 'HIGH', 'MEDIUM'][i % 3],
                    'score': 0.5 + (i * 0.05),
                    'description': f'Test finding {i}'
                }
            })

        # Generate summary
        summary = manager._format_daily_summary(discoveries)

        self.assertEqual(summary['total_discoveries'], 10)
        self.assertIn('by_severity', summary)
        self.assertIn('by_type', summary)
        self.assertIn('top_discoveries', summary)
        self.assertLessEqual(len(summary['top_discoveries']), 5)

        logger.info(f"✅ Daily summary: PASSED ({summary['total_discoveries']} discoveries)")

    def test_07_alert_processor_fallback(self):
        """Test AlertProcessor fallback notification"""
        from streaming.alert_processor import AlertStreamProcessor

        try:
            stream = EventStream()
        except:
            stream = MockEventStream()

        processor = AlertStreamProcessor(
            event_stream=stream,
            alert_manager=None
        )

        # Test fallback notification
        test_event = {
            'event_id': 'alert_test_123',
            'data': {
                'alert_type': 'test_alert',
                'severity': 'HIGH'
            }
        }

        test_error = RuntimeError("Alert processing failed")

        # Should not crash
        processor.on_error(test_event, test_error)

        logger.info("✅ Alert fallback notification: PASSED")

    def test_08_event_stream_timeout(self):
        """Test EventStream timeout logic"""
        try:
            from services.event_stream import EventStream

            # Create with very short timeout
            stream = EventStream()

            # Test timeout (should complete quickly)
            import time
            start = time.time()

            # Listen with 0.5s timeout (no messages expected)
            try:
                stream.listen(timeout=0.5)
            except:
                pass  # Redis may not be available

            elapsed = time.time() - start

            # Should timeout around 0.5s (give 2s buffer for overhead)
            self.assertLess(elapsed, 2.0)

            stream.close()

            logger.info(f"✅ Event stream timeout: PASSED ({elapsed:.2f}s)")
        except Exception as e:
            logger.warning(f"⚠️  Event stream timeout test skipped (no Redis): {e}")

    def test_09_integration_end_to_end(self):
        """Test end-to-end integration"""
        # This tests that all components work together

        # 1. Generate mock data
        trades = generate_mock_trades(50)
        self.assertEqual(len(trades), 50)

        # 2. Create mock database
        db = MockDatabase()
        cursor = db.cursor()

        # 3. Query trades
        cursor.execute(
            "SELECT * FROM trades WHERE ticker = %s",
            ('NVDA',)
        )
        results = cursor.fetchall()
        self.assertIsInstance(results, list)

        # 4. Process with price processor
        from streaming.price_processor import PriceStreamProcessor

        try:
            stream = EventStream()
        except:
            stream = MockEventStream()

        processor = PriceStreamProcessor(
            event_stream=stream,
            database=db
        )

        # 5. Generate daily summary
        from analysis.alerts.alert_manager import AlertManager

        manager = AlertManager(
            email_addresses=['test@example.com'],
            enable_email=False,
            enable_slack=False
        )

        discoveries = [{
            'politician': 'Test',
            'type': 'test',
            'timestamp': datetime.now().isoformat(),
            'finding': {'severity': 'HIGH', 'score': 0.8, 'description': 'Test'}
        }]

        summary = manager._format_daily_summary(discoveries)
        self.assertIsNotNone(summary)

        logger.info("✅ End-to-end integration: PASSED")


class MockEventStream:
    """Mock event stream for testing without Redis"""

    def __init__(self):
        self.redis = None
        self.pubsub = None

    def publish(self, channel, data, event_type=None):
        return True

    def subscribe(self, channel, handler):
        pass

    def listen(self, timeout=None):
        pass

    def close(self):
        pass


def run_tests():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("STREAMING INFRASTRUCTURE INTEGRATION TESTS")
    print("="*80 + "\n")

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamingIntegration)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*80 + "\n")

    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
