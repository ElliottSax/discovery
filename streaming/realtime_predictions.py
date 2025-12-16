"""
Real-Time Stock Prediction Streaming Service
Continuously generates predictions as new politician trades arrive
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import redis
from dotenv import load_dotenv

# Import prediction service
from services.prediction_service import PredictionService

load_dotenv()

logger = logging.getLogger(__name__)


class RealtimePredictionStream:
    """
    Real-time prediction streaming service

    Subscribes to politician trade events and generates predictions
    """

    def __init__(
        self,
        redis_url: str = None,
        prediction_interval_seconds: int = 60,
        min_confidence: float = 0.5
    ):
        """
        Initialize streaming service

        Args:
            redis_url: Redis connection URL
            prediction_interval_seconds: Seconds between prediction updates
            min_confidence: Minimum confidence threshold
        """
        if redis_url is None:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

        self.redis_url = redis_url
        self.prediction_interval = prediction_interval_seconds
        self.min_confidence = min_confidence

        # Initialize Redis
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            logger.info(f"Connected to Redis: {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

        # Initialize prediction service
        self.prediction_service = PredictionService(model_dir='data/models')

        # Cache
        self.trades_cache = []
        self.price_cache = {}
        self.latest_predictions = []

        # State
        self.running = False

    async def subscribe_to_trades(self):
        """Subscribe to politician trade events from Redis"""

        if self.redis_client is None:
            logger.error("Redis not available - cannot subscribe")
            return

        pubsub = self.redis_client.pubsub()
        pubsub.subscribe('politician_trades')

        logger.info("Subscribed to 'politician_trades' channel")

        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # Parse trade data
                        trade_data = json.loads(message['data'])

                        logger.info(f"New trade: {trade_data.get('politician_name')} "
                                   f"traded {trade_data.get('ticker')}")

                        # Add to cache
                        self.trades_cache.append(trade_data)

                        # Trigger prediction update
                        await self.update_predictions()

                    except Exception as e:
                        logger.error(f"Error processing trade: {e}")

        except KeyboardInterrupt:
            logger.info("Subscription cancelled")
            pubsub.unsubscribe()

    async def update_predictions(self):
        """Generate updated predictions based on latest trades"""

        logger.info("Updating predictions...")

        try:
            # Generate predictions from recent activity
            predictions = self.prediction_service.predict_from_politician_activity(
                trades=self.trades_cache,
                current_date=datetime.now(),
                price_data=self.price_cache,
                lookback_days=30,
                min_trade_count=2,
                min_confidence=self.min_confidence,
                top_n=20
            )

            # Store latest predictions
            self.latest_predictions = predictions

            # Publish to Redis
            if self.redis_client:
                self.redis_client.publish(
                    'stock_predictions',
                    json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'predictions': predictions,
                        'count': len(predictions)
                    })
                )

            logger.info(f"Published {len(predictions)} predictions")

            # Log top predictions
            if predictions:
                logger.info("Top 5 Predictions:")
                for i, pred in enumerate(predictions[:5], 1):
                    logger.info(
                        f"  {i}. {pred['ticker']:<6} {pred['prediction']:<5} "
                        f"Confidence: {pred['confidence']:.2%}  "
                        f"Prob(UP): {pred['probability_up']:.2%}"
                    )

        except Exception as e:
            logger.error(f"Error updating predictions: {e}")
            import traceback
            traceback.print_exc()

    async def periodic_update_loop(self):
        """Periodically update predictions"""

        logger.info(f"Starting periodic update loop (every {self.prediction_interval}s)")

        while self.running:
            try:
                await self.update_predictions()

            except Exception as e:
                logger.error(f"Error in update loop: {e}")

            # Wait for next interval
            await asyncio.sleep(self.prediction_interval)

    def load_historical_trades(self):
        """Load historical trades from database"""

        logger.info("Loading historical trades from database...")

        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            db_params = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'database': os.getenv('DB_NAME', 'quant_db'),
                'user': os.getenv('DB_USER', 'quant_user'),
                'password': os.getenv('DB_PASSWORD', '')
            }

            conn = psycopg2.connect(**db_params)

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get trades from last 90 days
                cur.execute("""
                    SELECT
                        t.id,
                        p.name as politician_name,
                        t.ticker,
                        t.transaction_date,
                        t.transaction_type,
                        t.amount_min,
                        t.amount_max,
                        t.disclosure_date,
                        p.chamber,
                        p.state,
                        p.party
                    FROM trades t
                    LEFT JOIN politicians p ON t.politician_id = p.id
                    WHERE t.ticker IS NOT NULL
                      AND t.transaction_date >= NOW() - INTERVAL '90 days'
                    ORDER BY t.transaction_date DESC
                """)

                rows = cur.fetchall()
                self.trades_cache = [dict(row) for row in rows]

            conn.close()

            logger.info(f"Loaded {len(self.trades_cache)} historical trades")

        except Exception as e:
            logger.error(f"Error loading trades: {e}")
            self.trades_cache = []

    async def start(self):
        """Start the streaming service"""

        logger.info("Starting Real-Time Prediction Stream...")

        self.running = True

        # Load historical data
        self.load_historical_trades()

        # Initial prediction update
        await self.update_predictions()

        # Start tasks
        tasks = [
            asyncio.create_task(self.periodic_update_loop()),
        ]

        # Add subscription if Redis available
        if self.redis_client:
            tasks.append(asyncio.create_task(self.subscribe_to_trades()))

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.running = False

    def get_latest_predictions(self) -> List[Dict]:
        """Get latest predictions"""
        return self.latest_predictions


# CLI Interface
async def main():
    """Main entry point"""

    import argparse

    parser = argparse.ArgumentParser(description='Real-Time Stock Prediction Stream')
    parser.add_argument('--redis-url', default=None, help='Redis URL')
    parser.add_argument('--interval', type=int, default=60, help='Update interval (seconds)')
    parser.add_argument('--confidence', type=float, default=0.5, help='Min confidence threshold')

    args = parser.parse_args()

    print("\n" + "="*80)
    print("REAL-TIME STOCK PREDICTION STREAM")
    print("="*80 + "\n")

    stream = RealtimePredictionStream(
        redis_url=args.redis_url,
        prediction_interval_seconds=args.interval,
        min_confidence=args.confidence
    )

    logger.info(f"Configuration:")
    logger.info(f"  Redis URL: {args.redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')}")
    logger.info(f"  Update Interval: {args.interval}s")
    logger.info(f"  Min Confidence: {args.confidence}")
    logger.info("")

    try:
        await stream.start()
    except KeyboardInterrupt:
        logger.info("\nShutdown complete")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    asyncio.run(main())
