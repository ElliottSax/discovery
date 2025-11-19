#!/usr/bin/env python3
"""
Quick Cyclical Analysis - Simplified Version

Runs cyclical analysis without requiring full backend environment.
Uses direct database connection and simplified models.
"""

import psycopg2
import numpy as np
from datetime import datetime, timedelta
import json

# Database connection
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'quant_db',
    'user': 'postgres',
    'password': 'postgres'
}


def simple_fft_analysis(trade_dates):
    """Simplified Fourier analysis to detect dominant cycles"""
    # Create daily time series
    if not trade_dates:
        return None

    min_date = min(trade_dates)
    max_date = max(trade_dates)

    date_range = []
    current = min_date
    while current <= max_date:
        date_range.append(current)
        current += timedelta(days=1)

    # Count trades per day
    trade_counts = []
    for date in date_range:
        count = sum(1 for d in trade_dates if d == date)
        trade_counts.append(count)

    # Simple FFT
    from scipy import fft, signal

    # Detrend
    detrended = signal.detrend(trade_counts)

    # FFT
    N = len(detrended)
    yf = fft.fft(detrended)
    xf = fft.fftfreq(N, 1)[:N//2]

    # Power spectrum
    power = 2.0/N * np.abs(yf[0:N//2])

    # Find peaks
    peaks, _ = signal.find_peaks(power, height=0.05)

    cycles = []
    for peak in peaks[:5]:  # Top 5
        if xf[peak] > 0:
            period = 1 / xf[peak]
            if 5 < period < 200:  # Reasonable range
                cycles.append({
                    'period_days': round(period, 1),
                    'strength': round(float(power[peak]), 3)
                })

    cycles.sort(key=lambda x: x['strength'], reverse=True)
    return cycles


def analyze_politician(conn, politician_name):
    """Analyze one politician's trading patterns"""

    print(f"\n{'='*80}")
    print(f"Analyzing: {politician_name}")
    print('='*80)

    cursor = conn.cursor()

    # Load trades
    cursor.execute("""
        SELECT
            transaction_date,
            ticker,
            transaction_type,
            (amount_min + amount_max) / 2 AS amount
        FROM trades t
        JOIN politicians p ON t.politician_id = p.id
        WHERE p.name = %s
        ORDER BY transaction_date
    """, (politician_name,))

    trades = cursor.fetchall()

    if not trades:
        print(f"No trades found for {politician_name}")
        return None

    print(f"\nTrade Summary:")
    print(f"  Total trades: {len(trades)}")
    print(f"  Date range: {trades[0][0]} to {trades[-1][0]}")
    print(f"  Duration: {(trades[-1][0] - trades[0][0]).days} days")

    # Get ticker distribution
    tickers = {}
    for trade in trades:
        ticker = trade[1]
        tickers[ticker] = tickers.get(ticker, 0) + 1

    top_tickers = sorted(tickers.items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"  Top tickers: {', '.join([f'{t[0]}({t[1]})' for t in top_tickers])}")

    # Fourier Analysis
    print(f"\n{'-'*80}")
    print("FOURIER CYCLE DETECTION")
    print('-'*80)

    try:
        trade_dates = [trade[0] for trade in trades]
        cycles = simple_fft_analysis(trade_dates)

        if cycles:
            print(f"\nDetected {len(cycles)} dominant cycles:")
            for i, cycle in enumerate(cycles, 1):
                period = cycle['period_days']
                strength = cycle['strength']

                # Categorize
                if 5 <= period <= 9:
                    category = "Weekly"
                elif 18 <= period <= 31:
                    category = "Monthly"
                elif 55 <= period <= 70:
                    category = "Quarterly"
                else:
                    category = "Other"

                print(f"  {i}. {category:12} - {period:6.1f} days (strength: {strength:.3f})")
        else:
            print("  No significant cycles detected")

    except Exception as e:
        print(f"  Error in Fourier analysis: {e}")

    # Trade Pattern Analysis
    print(f"\n{'-'*80}")
    print("TRADE PATTERN ANALYSIS")
    print('-'*80)

    # Calculate trade bursts
    trade_dates_list = [trade[0] for trade in trades]
    bursts = []
    current_burst = [trade_dates_list[0]]

    for i in range(1, len(trade_dates_list)):
        if (trade_dates_list[i] - trade_dates_list[i-1]).days <= 7:
            current_burst.append(trade_dates_list[i])
        else:
            if len(current_burst) >= 3:
                bursts.append(current_burst)
            current_burst = [trade_dates_list[i]]

    if len(current_burst) >= 3:
        bursts.append(current_burst)

    print(f"\nTrading Bursts Detected:")
    print(f"  Total bursts: {len(bursts)} (3+ trades within 7 days)")
    if bursts:
        avg_burst_size = sum(len(b) for b in bursts) / len(bursts)
        print(f"  Average burst size: {avg_burst_size:.1f} trades")
        print(f"  Largest burst: {max(len(b) for b in bursts)} trades")

    # Buy/Sell ratio
    buys = sum(1 for t in trades if t[2] == 'buy')
    sells = len(trades) - buys
    print(f"\nTrade Type Distribution:")
    print(f"  Buys: {buys} ({buys/len(trades)*100:.1f}%)")
    print(f"  Sells: {sells} ({sells/len(trades)*100:.1f}%)")

    cursor.close()

    return {
        'name': politician_name,
        'total_trades': len(trades),
        'cycles': cycles,
        'bursts': len(bursts),
        'buy_ratio': buys / len(trades)
    }


def main():
    """Run analysis on all politicians"""

    print("="*80)
    print("POLITICIAN TRADING PATTERN ANALYSIS")
    print("Cyclical Detection Models: Fourier + Pattern Analysis")
    print("="*80)

    try:
        # Connect to database
        conn = psycopg2.connect(**DB_PARAMS)
        print("\n✓ Connected to database")

        # Get politicians
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM politicians ORDER BY name")
        politicians = [row[0] for row in cursor.fetchall()]
        cursor.close()

        print(f"✓ Found {len(politicians)} politicians\n")

        results = []

        # Analyze each
        for politician in politicians:
            try:
                result = analyze_politician(conn, politician)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"\n✗ Error analyzing {politician}: {e}")
                import traceback
                traceback.print_exc()

        # Summary
        print(f"\n{'='*80}")
        print("ANALYSIS SUMMARY")
        print('='*80)

        for result in results:
            print(f"\n{result['name']}:")
            if result['cycles']:
                top_cycle = result['cycles'][0]
                print(f"  • Dominant cycle: {top_cycle['period_days']:.0f} days (strength: {top_cycle['strength']:.3f})")
            print(f"  • Trading bursts: {result['bursts']}")
            print(f"  • Buy preference: {result['buy_ratio']*100:.0f}%")

        print(f"\n{'='*80}")
        print("✓ ANALYSIS COMPLETE")
        print('='*80)

        conn.close()

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
