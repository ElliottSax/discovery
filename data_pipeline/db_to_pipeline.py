"""
Database to Pipeline Data Generator
Generates pipeline JSON files from PostgreSQL database
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PipelineGenerator:
    """Generate pipeline data files from database"""

    def __init__(self):
        self.db_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'quant_db'),
            'user': os.getenv('DB_USER', 'quant_user'),
            'password': os.getenv('DB_PASSWORD', 'REDACTED_PASSWORD')
        }
        self.output_dir = Path("./data/pipeline")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_trades_file(self) -> str:
        """Generate trades JSON file from database"""

        logger.info("Generating trades file from database...")

        conn = psycopg2.connect(**self.db_params)
        trades = []

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        t.id,
                        p.name as politician_name,
                        t.ticker,
                        t.transaction_date,
                        t.transaction_type,
                        t.amount_min,
                        t.amount_max,
                        t.disclosure_date as filing_date,
                        p.chamber,
                        p.state,
                        p.party
                    FROM trades t
                    LEFT JOIN politicians p ON t.politician_id = p.id
                    ORDER BY t.transaction_date DESC
                """)

                rows = cur.fetchall()

                for row in rows:
                    trade = dict(row)
                    # Convert date objects to strings
                    if trade.get('transaction_date'):
                        trade['transaction_date'] = trade['transaction_date'].isoformat()
                    if trade.get('filing_date'):
                        trade['filing_date'] = trade['filing_date'].isoformat()

                    # Convert Decimal to float for JSON serialization
                    if trade.get('amount_min'):
                        trade['amount_min'] = float(trade['amount_min'])
                    if trade.get('amount_max'):
                        trade['amount_max'] = float(trade['amount_max'])

                    trades.append(trade)

            conn.close()

            # Write to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.output_dir / f"trades_{timestamp}.json"

            with open(filename, 'w') as f:
                json.dump(trades, f, indent=2)

            logger.info(f"Generated {filename} with {len(trades)} trades")
            return str(filename)

        except Exception as e:
            logger.error(f"Error generating trades file: {e}")
            if conn:
                conn.close()
            raise

    def generate_analytics_file(self) -> str:
        """Generate analytics JSON file from database"""

        logger.info("Generating analytics file from database...")

        conn = psycopg2.connect(**self.db_params)
        analytics = []

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:

                # Top traded stocks
                cur.execute("""
                    SELECT ticker, COUNT(*) as trade_count
                    FROM trades
                    WHERE ticker IS NOT NULL
                    GROUP BY ticker
                    ORDER BY trade_count DESC
                    LIMIT 20
                """)
                top_stocks = cur.fetchall()

                analytics.append({
                    'type': 'top_traded_stocks',
                    'data': [dict(row) for row in top_stocks],
                    'generated_at': datetime.now().isoformat()
                })

                # Sector distribution (would need sector data)
                cur.execute("""
                    SELECT
                        CASE
                            WHEN ticker IN ('AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA') THEN 'Technology'
                            WHEN ticker IN ('JPM', 'BAC', 'GS', 'MS') THEN 'Finance'
                            WHEN ticker IN ('JNJ', 'PFE', 'UNH', 'CVS') THEN 'Healthcare'
                            ELSE 'Other'
                        END as sector,
                        COUNT(*) as trade_count
                    FROM trades
                    WHERE ticker IS NOT NULL
                    GROUP BY sector
                    ORDER BY trade_count DESC
                """)
                sectors = cur.fetchall()

                analytics.append({
                    'type': 'sector_distribution',
                    'data': [dict(row) for row in sectors],
                    'generated_at': datetime.now().isoformat()
                })

                # Most active politicians
                cur.execute("""
                    SELECT p.name as politician_name, COUNT(*) as trade_count
                    FROM trades t
                    JOIN politicians p ON t.politician_id = p.id
                    GROUP BY p.name
                    ORDER BY trade_count DESC
                    LIMIT 20
                """)
                politicians = cur.fetchall()

                analytics.append({
                    'type': 'most_active_politicians',
                    'data': [dict(row) for row in politicians],
                    'generated_at': datetime.now().isoformat()
                })

                # Transaction type distribution
                cur.execute("""
                    SELECT transaction_type, COUNT(*) as count
                    FROM trades
                    GROUP BY transaction_type
                    ORDER BY count DESC
                """)
                transaction_types = cur.fetchall()

                analytics.append({
                    'type': 'transaction_type_distribution',
                    'data': [dict(row) for row in transaction_types],
                    'generated_at': datetime.now().isoformat()
                })

            conn.close()

            # Write to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.output_dir / f"analytics_{timestamp}.json"

            with open(filename, 'w') as f:
                json.dump(analytics, f, indent=2)

            logger.info(f"Generated {filename} with {len(analytics)} analytics")
            return str(filename)

        except Exception as e:
            logger.error(f"Error generating analytics file: {e}")
            if conn:
                conn.close()
            raise

    def cleanup_old_files(self, keep_recent: int = 5):
        """Remove old pipeline files, keeping only the most recent"""

        for pattern in ["trades_*.json", "analytics_*.json"]:
            files = sorted(self.output_dir.glob(pattern), key=lambda p: p.stat().st_mtime)

            # Remove all but the most recent N files
            for old_file in files[:-keep_recent]:
                old_file.unlink()
                logger.info(f"Removed old file: {old_file}")

    def generate_all(self) -> Dict[str, str]:
        """Generate all pipeline files"""

        files = {}

        try:
            files['trades'] = self.generate_trades_file()
            files['analytics'] = self.generate_analytics_file()
            self.cleanup_old_files()

            logger.info("Pipeline data generation complete")
            return files

        except Exception as e:
            logger.error(f"Error generating pipeline data: {e}")
            raise


# Import os for environment variables
import os

# CLI usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    generator = PipelineGenerator()
    files = generator.generate_all()

    print("\nGenerated files:")
    for file_type, filepath in files.items():
        print(f"  {file_type}: {filepath}")
