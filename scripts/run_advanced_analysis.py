#!/usr/bin/env python3
"""
Advanced Analysis - HMM, DTW, and Correlation
Runs comprehensive pattern detection on politician trading data
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import json

# Load environment
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor

# Analysis modules
from analysis.cyclical.hmm import RegimeDetector
from analysis.cyclical.dtw import DynamicTimeWarpingMatcher
from analysis.correlation import CorrelationAnalyzer

# Database connection
DB_PARAMS = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'quant_db'),
    'user': os.getenv('DB_USER', 'quant_user'),
    'password': os.getenv('DB_PASSWORD', '')
}


def fetch_politician_trades(conn, politician_name: str) -> pd.DataFrame:
    """Fetch trades for a politician as DataFrame"""
    query = """
        SELECT
            t.transaction_date,
            t.ticker,
            t.transaction_type,
            t.amount_min,
            t.amount_max,
            (t.amount_min + t.amount_max) / 2 as amount_estimate
        FROM trades t
        JOIN politicians p ON t.politician_id = p.id
        WHERE p.name = %s
        ORDER BY t.transaction_date
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (politician_name,))
        rows = cur.fetchall()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    return df


def create_daily_series(trades_df: pd.DataFrame) -> pd.Series:
    """Convert trades to daily frequency time series"""
    if trades_df.empty:
        return pd.Series(dtype=float)

    # Create daily range
    start_date = trades_df['transaction_date'].min()
    end_date = trades_df['transaction_date'].max()
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    # Count trades per day
    daily_counts = trades_df.groupby(trades_df['transaction_date'].dt.date).size()
    daily_counts.index = pd.to_datetime(daily_counts.index)

    # Reindex to fill missing days with 0
    series = daily_counts.reindex(date_range, fill_value=0)

    return series


def run_hmm_analysis(politician_name: str, trades_df: pd.DataFrame) -> Dict:
    """Run Hidden Markov Model regime detection"""
    print(f"\n{'='*80}")
    print(f"HMM REGIME DETECTION - {politician_name}")
    print(f"{'='*80}\n")

    if trades_df.empty or len(trades_df) < 30:
        print("⚠ Not enough data for HMM analysis (need 30+ trades)")
        return None

    # Create daily series and calculate returns
    daily_series = create_daily_series(trades_df)

    # Use trade frequency as proxy for "returns"
    # More sophisticated: use actual stock returns if available
    trade_frequency = daily_series.values.reshape(-1, 1).astype(float)

    # Add some noise to avoid constant values
    trade_frequency = trade_frequency + np.random.normal(0, 0.1, trade_frequency.shape)

    try:
        # Initialize HMM with 3 states
        hmm_detector = RegimeDetector(n_states=3)

        # Fit and predict
        results = hmm_detector.fit_and_predict(trade_frequency.flatten())

        print(f"Current Regime: {results['current_regime']['name']}")
        print(f"Description: {results['current_regime']['description']}")
        print(f"Confidence: {results['current_regime']['confidence']:.2%}\n")

        print("Regime Characteristics:")
        for regime_name, stats in results['regime_characteristics'].items():
            print(f"\n  {regime_name}:")
            print(f"    Mean activity: {stats['mean']:.2f}")
            print(f"    Volatility: {stats['std']:.2f}")
            print(f"    Frequency: {stats['frequency']:.1%}")

        print("\nTransition Probabilities:")
        trans_matrix = results['transition_matrix']
        regime_names = list(results['regime_characteristics'].keys())

        for i, from_regime in enumerate(regime_names):
            print(f"\n  From {from_regime}:")
            for j, to_regime in enumerate(regime_names):
                print(f"    → {to_regime}: {trans_matrix[i][j]:.2%}")

        # Calculate expected duration in each regime
        print("\nExpected Duration in Each Regime:")
        for i, regime in enumerate(regime_names):
            stay_prob = trans_matrix[i][i]
            if stay_prob < 1.0:
                expected_days = 1 / (1 - stay_prob)
                print(f"  {regime}: {expected_days:.1f} days")

        return results

    except Exception as e:
        print(f"✗ HMM analysis failed: {e}")
        return None


def run_dtw_analysis(politician_name: str, trades_df: pd.DataFrame) -> Dict:
    """Run Dynamic Time Warping pattern matching"""
    print(f"\n{'='*80}")
    print(f"DTW PATTERN MATCHING - {politician_name}")
    print(f"{'='*80}\n")

    if trades_df.empty or len(trades_df) < 60:
        print("⚠ Not enough data for DTW analysis (need 60+ trades)")
        return None

    # Create daily series
    daily_series = create_daily_series(trades_df)

    if len(daily_series) < 60:
        print("⚠ Not enough days for DTW analysis")
        return None

    try:
        # Use last 30 days as current pattern
        current_pattern = daily_series.values[-30:]

        # Use earlier data as historical
        historical_data = daily_series.values[:-30]

        if len(historical_data) < 30:
            print("⚠ Not enough historical data")
            return None

        # Initialize DTW matcher
        dtw_matcher = DynamicTimeWarpingMatcher(window_size=30)

        # Find similar patterns
        matches = dtw_matcher.find_similar_patterns(
            current_pattern=current_pattern,
            historical_data=historical_data,
            top_k=5
        )

        print(f"Found {len(matches)} similar historical patterns:\n")

        for i, match in enumerate(matches, 1):
            print(f"{i}. Match from {match['days_ago']} days ago")
            print(f"   Similarity: {match['similarity_score']:.2%}")
            print(f"   DTW Distance: {match['dtw_distance']:.2f}")

            if 'predicted_outcome' in match:
                print(f"   Predicted outcome: {match['predicted_outcome']}")
            print()

        # Aggregate predictions
        if matches:
            avg_similarity = np.mean([m['similarity_score'] for m in matches])
            print(f"Average similarity to historical patterns: {avg_similarity:.2%}")

            if avg_similarity > 0.7:
                print("✓ Strong historical precedent found")
            elif avg_similarity > 0.5:
                print("⚠ Moderate historical similarity")
            else:
                print("✗ Weak historical similarity - novel pattern")

        return {
            'matches': matches,
            'avg_similarity': avg_similarity if matches else 0,
            'pattern_novelty': 1 - (avg_similarity if matches else 0)
        }

    except Exception as e:
        print(f"✗ DTW analysis failed: {e}")
        return None


def run_correlation_analysis(conn) -> Dict:
    """Run correlation analysis across all politicians"""
    print(f"\n{'='*80}")
    print(f"CROSS-POLITICIAN CORRELATION ANALYSIS")
    print(f"{'='*80}\n")

    # Fetch all politicians with trades
    query = """
        SELECT DISTINCT p.name, COUNT(t.id) as trade_count
        FROM politicians p
        JOIN trades t ON p.id = t.politician_id
        GROUP BY p.name
        HAVING COUNT(t.id) >= 30
        ORDER BY trade_count DESC
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        politicians = [row['name'] for row in cur.fetchall()]

    if len(politicians) < 2:
        print("⚠ Need at least 2 politicians for correlation analysis")
        return None

    print(f"Analyzing correlations between {len(politicians)} politicians\n")

    # Create time series for each politician
    politician_series = {}

    for pol_name in politicians:
        trades_df = fetch_politician_trades(conn, pol_name)
        series = create_daily_series(trades_df)
        politician_series[pol_name] = series

    # Convert to DataFrame with aligned dates
    # Find common date range
    all_dates = set()
    for series in politician_series.values():
        all_dates.update(series.index)

    date_range = pd.DatetimeIndex(sorted(all_dates))

    # Create aligned DataFrame
    aligned_df = pd.DataFrame(index=date_range)
    for pol_name, series in politician_series.items():
        aligned_df[pol_name] = series.reindex(date_range, fill_value=0)

    # Calculate correlation matrix
    corr_matrix = aligned_df.corr()

    print("Correlation Matrix:")
    print("=" * 80)
    print(corr_matrix.round(3))
    print()

    # Find highly correlated pairs
    high_corr_pairs = []

    for i, pol1 in enumerate(politicians):
        for j, pol2 in enumerate(politicians):
            if i < j:  # Avoid duplicates
                corr = corr_matrix.loc[pol1, pol2]
                if abs(corr) > 0.3:  # Threshold for "high" correlation
                    high_corr_pairs.append({
                        'politician_1': pol1,
                        'politician_2': pol2,
                        'correlation': corr
                    })

    # Sort by absolute correlation
    high_corr_pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)

    if high_corr_pairs:
        print("\nHighly Correlated Trading Pairs (|r| > 0.3):")
        print("=" * 80)
        for pair in high_corr_pairs:
            direction = "positively" if pair['correlation'] > 0 else "negatively"
            print(f"  {pair['politician_1']} ↔ {pair['politician_2']}")
            print(f"    Correlation: {pair['correlation']:.3f} ({direction} correlated)")
            print()
    else:
        print("\n✗ No highly correlated pairs found (threshold: 0.3)")

    # Detect potential clusters
    try:
        analyzer = CorrelationAnalyzer()

        # Convert to dict of series for analyzer
        series_dict = {name: series for name, series in politician_series.items()}

        # Analyze cycle correlation
        cycle_corr = analyzer.analyze_cycle_correlation(series_dict)

        print("\nCycle Correlation Analysis:")
        print("=" * 80)

        if 'cycle_correlations' in cycle_corr:
            for pair_key, corr_data in list(cycle_corr['cycle_correlations'].items())[:5]:
                print(f"  {pair_key}: r={corr_data['correlation']:.3f}, lag={corr_data.get('optimal_lag', 0)} days")

    except Exception as e:
        print(f"\n⚠ Advanced correlation analysis failed: {e}")

    return {
        'correlation_matrix': corr_matrix.to_dict(),
        'high_corr_pairs': high_corr_pairs,
        'num_politicians': len(politicians),
        'date_range': f"{date_range[0].date()} to {date_range[-1].date()}"
    }


def main():
    """Run comprehensive advanced analysis"""
    print("=" * 80)
    print("ADVANCED POLITICIAN TRADING ANALYSIS")
    print("HMM Regime Detection | DTW Pattern Matching | Correlation Analysis")
    print("=" * 80)

    # Connect to database
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        print("✓ Connected to database\n")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return 1

    try:
        # Get active politicians
        query = """
            SELECT DISTINCT p.name, COUNT(t.id) as trade_count
            FROM politicians p
            JOIN trades t ON p.id = t.politician_id
            GROUP BY p.name
            HAVING COUNT(t.id) >= 30
            ORDER BY trade_count DESC
            LIMIT 3
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            politicians = cur.fetchall()

        results = {
            'timestamp': datetime.now().isoformat(),
            'politicians_analyzed': [],
            'correlation_analysis': None
        }

        # Run HMM and DTW for each politician
        for pol in politicians:
            pol_name = pol['name']
            trades_df = fetch_politician_trades(conn, pol_name)

            pol_results = {
                'name': pol_name,
                'trade_count': pol['trade_count'],
                'hmm': None,
                'dtw': None
            }

            # HMM analysis
            hmm_results = run_hmm_analysis(pol_name, trades_df)
            if hmm_results:
                pol_results['hmm'] = {
                    'current_regime': hmm_results['current_regime']['name'],
                    'confidence': hmm_results['current_regime']['confidence'],
                    'regimes': list(hmm_results['regime_characteristics'].keys())
                }

            # DTW analysis
            dtw_results = run_dtw_analysis(pol_name, trades_df)
            if dtw_results:
                pol_results['dtw'] = {
                    'avg_similarity': dtw_results['avg_similarity'],
                    'pattern_novelty': dtw_results['pattern_novelty'],
                    'top_matches': len(dtw_results['matches'])
                }

            results['politicians_analyzed'].append(pol_results)

        # Cross-politician correlation
        corr_results = run_correlation_analysis(conn)
        if corr_results:
            results['correlation_analysis'] = corr_results

        # Save results
        output_file = Path(__file__).parent.parent / 'advanced_analysis_results.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n{'='*80}")
        print(f"✓ ANALYSIS COMPLETE")
        print(f"{'='*80}")
        print(f"\nResults saved to: {output_file}")

    finally:
        conn.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
