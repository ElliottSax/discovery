#!/usr/bin/env python3
"""
Database initialization script
Creates all tables and optionally seeds with test data
"""

import sys
import os
from pathlib import Path
import argparse
import logging
from datetime import datetime, timedelta
import random

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.database import Base, engine, check_connection, db_session
from api.db_models import (
    Politician, Trade, Stock, Pattern, Alert,
    AnalysisRun, User, Subscription, PriceHistory
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✓ All tables created successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to create tables: {e}")
        return False


def drop_tables():
    """Drop all database tables (use with caution!)"""
    logger.warning("Dropping all database tables...")
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("✓ All tables dropped successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to drop tables: {e}")
        return False


def seed_test_data():
    """Insert test data for development"""
    logger.info("Seeding test data...")

    try:
        with db_session() as session:
            # Create test politicians
            politicians = [
                Politician(
                    name="John Doe",
                    chamber="senate",
                    state="CA",
                    party="democrat"
                ),
                Politician(
                    name="Jane Smith",
                    chamber="house",
                    state="TX",
                    party="republican",
                    district="12"
                ),
                Politician(
                    name="Bob Johnson",
                    chamber="senate",
                    state="NY",
                    party="democrat"
                ),
            ]
            session.add_all(politicians)
            session.flush()  # Get IDs
            logger.info(f"✓ Created {len(politicians)} test politicians")

            # Create test stocks
            stocks = [
                Stock(
                    ticker="AAPL",
                    name="Apple Inc.",
                    sector="Technology",
                    industry="Consumer Electronics",
                    exchange="NASDAQ",
                    current_price=175.50,
                    market_cap=2800000000000,
                    pe_ratio=28.5
                ),
                Stock(
                    ticker="MSFT",
                    name="Microsoft Corporation",
                    sector="Technology",
                    industry="Software",
                    exchange="NASDAQ",
                    current_price=380.25,
                    market_cap=2850000000000,
                    pe_ratio=35.2
                ),
                Stock(
                    ticker="JPM",
                    name="JPMorgan Chase & Co.",
                    sector="Financial Services",
                    industry="Banking",
                    exchange="NYSE",
                    current_price=155.80,
                    market_cap=450000000000,
                    pe_ratio=11.5
                ),
            ]
            session.add_all(stocks)
            logger.info(f"✓ Created {len(stocks)} test stocks")

            # Create test trades
            trades = []
            base_date = datetime.now() - timedelta(days=90)

            for i in range(20):
                politician = random.choice(politicians)
                stock = random.choice(stocks)
                trade_date = base_date + timedelta(days=random.randint(0, 90))

                trades.append(Trade(
                    politician_id=politician.id,
                    disclosure_date=trade_date + timedelta(days=random.randint(1, 45)),
                    transaction_date=trade_date,
                    ticker=stock.ticker,
                    asset_name=stock.name,
                    transaction_type=random.choice(["purchase", "sale"]),
                    amount_range="$15,001 - $50,000",
                    amount_min=15001,
                    amount_max=50000,
                    price_at_transaction=stock.current_price * random.uniform(0.9, 1.1),
                    current_price=stock.current_price,
                    sector=stock.sector,
                    industry=stock.industry,
                ))

            session.add_all(trades)
            logger.info(f"✓ Created {len(trades)} test trades")

            # Create test pattern
            pattern = Pattern(
                pattern_name="Tech Sector Cluster",
                pattern_type="sector_rotation",
                description="Multiple politicians purchasing tech stocks",
                politicians_involved=["John Doe", "Bob Johnson"],
                stocks_involved=["AAPL", "MSFT"],
                confidence=0.85,
                significance="high",
                start_date=base_date,
                end_date=datetime.now(),
                detection_method="fourier",
                analysis_data={"cycle_period": 30, "strength": 0.75}
            )
            session.add(pattern)
            logger.info("✓ Created test pattern")

            # Create test alert
            alert = Alert(
                alert_type="unusual_activity",
                title="Unusual Trading Cluster Detected",
                message="Multiple senators purchased technology stocks within 48 hours",
                severity="warning",
                status="active",
                metadata={
                    "politicians": ["John Doe", "Bob Johnson"],
                    "stocks": ["AAPL", "MSFT"],
                    "time_window": "48h"
                }
            )
            session.add(alert)
            logger.info("✓ Created test alert")

            # Create test user
            user = User(
                username="demo",
                email="demo@example.com",
                hashed_password="$2b$12$demo_hashed_password",  # In production, use proper hashing
                full_name="Demo User",
                is_active=True,
                is_admin=False,
                api_key="demo_api_key_12345",
                rate_limit_tier="standard"
            )
            session.add(user)
            session.flush()
            logger.info("✓ Created test user")

            # Create test subscription
            subscription = Subscription(
                user_id=user.id,
                email="demo@example.com",
                alert_types=["unusual_activity", "pattern_detected"],
                frequency="daily",
                active=True
            )
            session.add(subscription)
            logger.info("✓ Created test subscription")

            # Create test analysis run
            analysis_run = AnalysisRun(
                analysis_type="fourier_cyclical",
                status="completed",
                started_at=datetime.now() - timedelta(hours=1),
                completed_at=datetime.now(),
                duration_seconds=3600,
                records_processed=100,
                patterns_detected=5,
                errors=0,
                results={"dominant_cycles": [{"period": 30, "strength": 0.8}]},
                config={"min_period": 5, "max_period": 365}
            )
            session.add(analysis_run)
            logger.info("✓ Created test analysis run")

        logger.info("✓ All test data seeded successfully")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to seed test data: {e}")
        return False


def verify_schema():
    """Verify database schema"""
    logger.info("Verifying database schema...")

    try:
        with db_session() as session:
            # Check each table
            tables = [
                ("politicians", Politician),
                ("trades", Trade),
                ("stocks", Stock),
                ("patterns", Pattern),
                ("alerts", Alert),
                ("analysis_runs", AnalysisRun),
                ("users", User),
                ("subscriptions", Subscription),
                ("price_history", PriceHistory),
            ]

            for table_name, model in tables:
                count = session.query(model).count()
                logger.info(f"  ✓ {table_name}: {count} records")

        logger.info("✓ Schema verification complete")
        return True

    except Exception as e:
        logger.error(f"✗ Schema verification failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Initialize database for politician trading analysis"
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop existing tables before creating (WARNING: destroys data)"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed database with test data"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify database schema"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Database Initialization Script")
    logger.info("=" * 60)

    # Check database connection
    logger.info("Checking database connection...")
    if not check_connection():
        logger.error("✗ Cannot connect to database. Check your configuration.")
        logger.error("  DATABASE_URL or DB_* environment variables")
        return 1

    logger.info("✓ Database connection successful")

    # Drop tables if requested
    if args.drop:
        if not drop_tables():
            return 1

    # Create tables
    if not create_tables():
        return 1

    # Seed test data if requested
    if args.seed:
        if not seed_test_data():
            return 1

    # Verify schema
    if args.verify or args.seed:
        if not verify_schema():
            return 1

    logger.info("=" * 60)
    logger.info("✓ Database initialization complete!")
    logger.info("=" * 60)

    if args.seed:
        logger.info("\nTest credentials:")
        logger.info("  Username: demo")
        logger.info("  Password: demo123")
        logger.info("  API Key: demo_api_key_12345")

    return 0


if __name__ == "__main__":
    sys.exit(main())
