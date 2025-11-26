#!/usr/bin/env python3
"""
Analyze Politician Trading Patterns with Cyclical Models

Runs all three cyclical detection models on real politician trading data:
1. Fourier Analysis - Detect periodic trading cycles
2. HMM Regime Detection - Identify trading regimes
3. DTW Pattern Matching - Find similar historical patterns

Tracks everything to MLFlow for analysis.
"""

import sys
import os
import re
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import warnings
warnings.filterwarnings('ignore')

from analysis.cyclical.fourier import FourierCyclicalDetector
from analysis.cyclical.hmm import RegimeDetector
from analysis.cyclical.dtw import DynamicTimeWarpingMatcher
from analysis.cyclical.experiment_tracker import CyclicalExperimentTracker

# Database connection with environment variables
import os

DB_USER = os.getenv('DB_USER', 'quant_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'quant_db')

if not DB_PASSWORD:
    raise ValueError("Database password must be set via DB_PASSWORD environment variable")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine with connection pooling for better performance
# Pool size: 5 connections, overflow: 10 additional connections if needed
# Pool recycle: refresh connections every hour to prevent stale connections
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False           # Set to True for SQL query logging
)


def sanitize_name_for_mlflow(name: str) -> str:
    """
    Sanitize politician name for use in MLFlow experiment names.

    Converts to lowercase, replaces spaces and special characters with underscores.
    Handles names like "O'Brien", "Mary-Anne Smith", etc.

    Args:
        name: Original politician name

    Returns:
        Sanitized name safe for MLFlow experiments
    """
    # Convert to lowercase
    sanitized = name.lower()
    # Replace any non-alphanumeric characters (except underscores) with underscores
    sanitized = re.sub(r'[^a-z0-9_]', '_', sanitized)
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    return sanitized


def load_politician_trades(politician_name=None):
    """Load trades from database and prepare for analysis"""

    base_query = """
    SELECT
        t.transaction_date,
        t.ticker,
        t.transaction_type,
        (t.amount_min + t.amount_max) / 2 AS amount,
        p.name AS politician_name,
        p.party
    FROM trades t
    JOIN politicians p ON t.politician_id = p.id
    """

    if politician_name:
        # Use parameterized query to prevent SQL injection
        query = text(base_query + " WHERE p.name = :politician_name ORDER BY t.transaction_date")
        df = pd.read_sql(query, engine, params={"politician_name": politician_name})
    else:
        query = base_query + " ORDER BY t.transaction_date"
        df = pd.read_sql(query, engine)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    return df


def prepare_time_series(trades_df, freq='D'):
    """Convert trades to time series for analysis"""

    # Create daily trade frequency
    trade_freq = trades_df.groupby('transaction_date').size()

    # Create full date range
    date_range = pd.date_range(
        start=trades_df['transaction_date'].min(),
        end=trades_df['transaction_date'].max(),
        freq=freq
    )

    # Reindex to include all dates (fill missing with 0)
    ts = trade_freq.reindex(date_range, fill_value=0)

    return ts


def analyze_politician(politician_name):
    """Run complete cyclical analysis for one politician"""

    print("\n" + "=" * 80)
    print(f"Analyzing: {politician_name}")
    print("=" * 80)

    # Load data
    trades_df = load_politician_trades(politician_name)

    if len(trades_df) == 0:
        print(f"No trades found for {politician_name}")
        return None

    print(f"\nLoaded {len(trades_df)} trades")
    print(f"Date range: {trades_df['transaction_date'].min()} to {trades_df['transaction_date'].max()}")
    print(f"Top tickers: {trades_df['ticker'].value_counts().head(3).to_dict()}")

    # Prepare time series
    trade_frequency = prepare_time_series(trades_df)
    print(f"\nTime series length: {len(trade_frequency)} days")
    print(f"Average trades per day: {trade_frequency.mean():.2f}")

    # Initialize tracker
    tracker = CyclicalExperimentTracker(
        experiment_name=f"politician_analysis_{sanitize_name_for_mlflow(politician_name)}"
    )

    results = {}

    # 1. FOURIER ANALYSIS
    print("\n" + "-" * 80)
    print("1. Fourier Cyclical Analysis")
    print("-" * 80)

    try:
        fourier = FourierCyclicalDetector(min_strength=0.05, min_confidence=0.5)
        fourier_result = fourier.detect_cycles(trade_frequency, sampling_rate='daily')

        print(f"\nFound {fourier_result['total_cycles_found']} cycles:")
        for i, cycle in enumerate(fourier_result['dominant_cycles'][:5], 1):
            print(f"  {i}. {cycle['category'].ljust(15)} - {cycle['period_days']:6.1f} days "
                  f"(strength: {cycle['strength']:.3f}, confidence: {cycle['confidence']:.1%})")

        # Track to MLFlow
        run_id = tracker.track_fourier_detection(
            fourier, trade_frequency, fourier_result,
            tags={'politician': politician_name}
        )
        print(f"\n✓ Tracked to MLFlow: {run_id}")

        results['fourier'] = fourier_result

    except Exception as e:
        print(f"\n✗ Fourier analysis failed: {e}")

    # 2. HMM REGIME DETECTION
    print("\n" + "-" * 80)
    print("2. HMM Regime Detection")
    print("-" * 80)

    try:
        # Calculate returns (day-over-day change in trade frequency)
        returns = trade_frequency.diff().fillna(0)

        # Need at least 100 points for HMM
        if len(returns) >= 100:
            hmm = RegimeDetector(n_states=3)  # 3 states for this data size
            hmm_result = hmm.fit_and_predict(returns)

            print(f"\nCurrent Regime: {hmm_result['current_regime_name']}")
            print(f"Confidence: {hmm_result['regime_probabilities'][hmm_result['current_regime']]:.1%}")
            print(f"\nAll Regimes:")
            for state, chars in hmm_result['regime_characteristics'].items():
                print(f"  {state}. {chars['name'].ljust(20)} - "
                      f"Frequency: {chars['frequency']:.1%}, "
                      f"Avg change: {chars['avg_return']:+.3f}")

            # Track to MLFlow
            run_id = tracker.track_hmm_detection(
                hmm, hmm_result, returns,
                tags={'politician': politician_name}
            )
            print(f"\n✓ Tracked to MLFlow: {run_id}")

            results['hmm'] = hmm_result
        else:
            print(f"\nInsufficient data for HMM (need 100+ points, have {len(returns)})")

    except Exception as e:
        print(f"\n✗ HMM analysis failed: {e}")

    # 3. DTW PATTERN MATCHING
    print("\n" + "-" * 80)
    print("3. Dynamic Time Warping Pattern Matching")
    print("-" * 80)

    try:
        if len(trade_frequency) >= 90:  # Need enough for pattern matching
            # Use last 30 days as current pattern
            current_pattern = trade_frequency[-30:]

            dtw = DynamicTimeWarpingMatcher(similarity_threshold=0.6)
            matches = dtw.find_similar_patterns(
                current_pattern,
                trade_frequency,
                window_size=30,
                top_k=5
            )

            print(f"\nFound {len(matches)} similar patterns:")
            for i, match in enumerate(matches[:3], 1):
                print(f"  {i}. {str(match['match_date'])[:10]} - "
                      f"Similarity: {match['similarity_score']:.1%}, "
                      f"30d outcome: {match['outcome_30d']['total_return']:+.2f}")

            # Predict based on matches
            prediction = dtw.predict_from_matches(matches, horizon=30)
            print(f"\nPrediction (next 30 days):")
            print(f"  Expected change: {prediction['predicted_return']:+.2f} trades")
            print(f"  Confidence: {prediction['confidence']:.1%}")

            # Track to MLFlow
            run_id = tracker.track_dtw_matching(
                dtw, matches, prediction, current_pattern,
                tags={'politician': politician_name}
            )
            print(f"\n✓ Tracked to MLFlow: {run_id}")

            results['dtw'] = {'matches': matches, 'prediction': prediction}
        else:
            print(f"\nInsufficient data for DTW (need 90+ points, have {len(trade_frequency)})")

    except Exception as e:
        print(f"\n✗ DTW analysis failed: {e}")

    return results


def main():
    """Run analysis on all politicians"""

    print("=" * 80)
    print("POLITICIAN TRADING PATTERN ANALYSIS")
    print("Using Cyclical Detection Models: Fourier, HMM, DTW")
    print("=" * 80)

    try:
        # Get list of politicians
        query = "SELECT DISTINCT name FROM politicians ORDER BY name"
        politicians = pd.read_sql(query, engine)['name'].tolist()

        print(f"\nFound {len(politicians)} politicians:")
        for pol in politicians:
            print(f"  - {pol}")

        all_results = {}

        # Analyze each politician
        for politician in politicians:
            try:
                results = analyze_politician(politician)
                if results:
                    all_results[politician] = results
            except Exception as e:
                print(f"\n✗ Failed to analyze {politician}: {e}")
                import traceback
                traceback.print_exc()

        # Summary
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)

        print(f"\nAnalyzed {len(all_results)} politicians")
        print("\nKey Findings:")

        for politician, results in all_results.items():
            print(f"\n{politician}:")

            if 'fourier' in results:
                cycles = results['fourier']['dominant_cycles']
                if cycles:
                    top_cycle = cycles[0]
                    print(f"  • Dominant cycle: {top_cycle['period_days']:.0f} days ({top_cycle['category']})")

            if 'hmm' in results:
                regime = results['hmm']['current_regime_name']
                print(f"  • Current regime: {regime}")

            if 'dtw' in results and results['dtw']['matches']:
                pred = results['dtw']['prediction']
                print(f"  • 30-day prediction: {pred['predicted_return']:+.1f} trades (confidence: {pred['confidence']:.0%})")

        print(f"\n✓ All experiments tracked to MLFlow")
        print("  View at: http://localhost:5000")
        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure database connections are properly closed
        try:
            engine.dispose()
        except Exception:
            pass  # Ignore errors during cleanup


if __name__ == "__main__":
    main()
