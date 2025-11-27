#!/usr/bin/env python3
"""
HMM Regime Detection - Simplified
Runs Hidden Markov Model analysis without ML Flow dependencies
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
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
from hmmlearn import hmm

# Database connection
DB_PARAMS = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'quant_db'),
    'user': os.getenv('DB_USER', 'quant_user'),
    'password': os.getenv('DB_PASSWORD', '')
}


def fetch_politician_trades(conn, politician_name):
    """Fetch trades for a politician"""
    query = """
        SELECT
            t.transaction_date,
            t.transaction_type,
            (t.amount_min + t.amount_max) / 2 as amount_estimate
        FROM trades t
        JOIN politicians p ON t.politician_id = p.id
        WHERE p.name = %s
        ORDER BY t.transaction_date
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (politician_name,))
        rows = cur.fetchall()

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def create_daily_series(trades_df):
    """Convert trades to daily frequency time series"""
    if trades_df.empty:
        return pd.Series(dtype=float)

    trades_df['transaction_date'] = pd.to_datetime(trades_df['transaction_date'])
    start_date = trades_df['transaction_date'].min()
    end_date = trades_df['transaction_date'].max()
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    # Count trades per day
    daily_counts = trades_df.groupby(trades_df['transaction_date'].dt.date).size()
    daily_counts.index = pd.to_datetime(daily_counts.index)

    # Reindex to fill missing days with 0
    series = daily_counts.reindex(date_range, fill_value=0)

    return series


def run_hmm_regime_detection(politician_name, trades_df, n_states=3):
    """Run HMM regime detection"""
    print(f"\n{'='*80}")
    print(f"HMM REGIME DETECTION - {politician_name}")
    print(f"{'='*80}\n")

    if trades_df.empty or len(trades_df) < 30:
        print("⚠ Not enough data for HMM analysis (need 30+ trades)")
        return None

    # Create daily series
    daily_series = create_daily_series(trades_df)

    # Prepare data for HMM
    trade_frequency = daily_series.values.reshape(-1, 1).astype(float)

    # Add small noise to avoid constant values
    trade_frequency = trade_frequency + np.random.normal(0, 0.01, trade_frequency.shape)

    print(f"Trading days analyzed: {len(trade_frequency)}")
    print(f"Number of states: {n_states}\n")

    # Train Gaussian HMM
    model = hmm.GaussianHMM(
        n_components=n_states,
        covariance_type="full",
        n_iter=100,
        random_state=42
    )

    try:
        model.fit(trade_frequency)
        states = model.predict(trade_frequency)

        # Get statistics for each state
        regime_stats = {}
        regime_names = {}

        # Sort states by mean trading frequency
        state_means = []
        for i in range(n_states):
            state_mask = states == i
            state_data = trade_frequency[state_mask]
            state_means.append((i, state_data.mean()))

        # Sort by mean (low to high activity)
        sorted_states = sorted(state_means, key=lambda x: x[1])

        # Assign names based on activity level
        names = ['Low Activity', 'Medium Activity', 'High Activity'][:n_states]
        for idx, (state_id, _) in enumerate(sorted_states):
            regime_names[state_id] = names[idx]

        # Calculate stats for each regime
        for i in range(n_states):
            state_mask = states == i
            state_data = trade_frequency[state_mask]

            regime_stats[regime_names[i]] = {
                'mean_trades_per_day': float(state_data.mean()),
                'std': float(state_data.std()),
                'frequency': float(state_mask.sum() / len(states)),
                'total_days': int(state_mask.sum())
            }

        # Current regime
        current_state = states[-1]
        current_regime = regime_names[current_state]

        # Transition matrix
        trans_matrix = model.transmat_

        print(f"Current Regime: {current_regime}")
        print(f"Mean trades/day: {regime_stats[current_regime]['mean_trades_per_day']:.2f}\n")

        print("Regime Characteristics:")
        print("=" * 80)
        for regime_name, stats in regime_stats.items():
            print(f"\n{regime_name}:")
            print(f"  Mean trades/day: {stats['mean_trades_per_day']:.2f}")
            print(f"  Volatility: {stats['std']:.2f}")
            print(f"  Frequency: {stats['frequency']:.1%} ({stats['total_days']} days)")

        print(f"\nTransition Probabilities:")
        print("=" * 80)
        regime_list = [regime_names[i] for i in range(n_states)]

        for i, from_regime in enumerate(regime_list):
            print(f"\nFrom {from_regime}:")
            for j, to_regime in enumerate(regime_list):
                print(f"  → {to_regime}: {trans_matrix[i][j]:.2%}")

        # Expected duration
        print(f"\nExpected Duration in Each Regime:")
        print("=" * 80)
        for i, regime in enumerate(regime_list):
            stay_prob = trans_matrix[i][i]
            if stay_prob < 1.0:
                expected_days = 1 / (1 - stay_prob)
                print(f"  {regime}: {expected_days:.1f} days")
            else:
                print(f"  {regime}: Absorbing state")

        # Regime history (last 30 days)
        recent_states = states[-30:]
        recent_regimes = [regime_names[s] for s in recent_states]

        print(f"\nRecent Regime Changes (last 30 days):")
        print("=" * 80)
        changes = []
        for i in range(1, len(recent_regimes)):
            if recent_regimes[i] != recent_regimes[i-1]:
                changes.append((30-i, recent_regimes[i-1], recent_regimes[i]))

        if changes:
            for days_ago, from_reg, to_reg in changes:
                print(f"  {days_ago} days ago: {from_reg} → {to_reg}")
        else:
            print(f"  No regime changes (stable in {current_regime})")

        return {
            'current_regime': current_regime,
            'regime_stats': regime_stats,
            'transition_matrix': trans_matrix.tolist(),
            'regime_names': regime_list,
            'recent_changes': len(changes)
        }

    except Exception as e:
        print(f"✗ HMM analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run HMM analysis on top politicians"""
    print("=" * 80)
    print("HMM REGIME DETECTION ANALYSIS")
    print("Hidden Markov Models for Trading Regime Identification")
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
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            politicians = cur.fetchall()

        print(f"Analyzing {len(politicians)} politicians\n")

        results = {
            'timestamp': datetime.now().isoformat(),
            'politicians': []
        }

        # Run HMM for each politician
        for pol in politicians:
            pol_name = pol['name']
            trades_df = fetch_politician_trades(conn, pol_name)

            hmm_result = run_hmm_regime_detection(pol_name, trades_df)

            if hmm_result:
                results['politicians'].append({
                    'name': pol_name,
                    'trade_count': pol['trade_count'],
                    'hmm_analysis': hmm_result
                })

        # Save results
        output_file = Path(__file__).parent.parent / 'hmm_analysis_results.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n{'='*80}")
        print(f"✓ ANALYSIS COMPLETE")
        print(f"{'='*80}")
        print(f"\nResults saved to: {output_file}")
        print(f"Analyzed: {len(results['politicians'])} politicians")

    finally:
        conn.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
