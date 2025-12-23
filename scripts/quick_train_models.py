#!/usr/bin/env python3
"""
Quick Model Training Script
Trains ML models for stock prediction using mock data
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_mock_trades(count: int = 500) -> List[Dict]:
    """Generate mock trading data"""
    logger.info(f"Generating {count} mock trades...")

    tickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN', 'META', 'NFLX',
               'AMD', 'CRM', 'ORCL', 'INTC', 'CSCO', 'ADBE', 'QCOM']

    politicians = [
        {'name': 'Nancy Pelosi', 'party': 'D', 'chamber': 'House', 'state': 'CA'},
        {'name': 'Mitch McConnell', 'party': 'R', 'chamber': 'Senate', 'state': 'KY'},
        {'name': 'AOC', 'party': 'D', 'chamber': 'House', 'state': 'NY'},
        {'name': 'Ted Cruz', 'party': 'R', 'chamber': 'Senate', 'state': 'TX'},
        {'name': 'Elizabeth Warren', 'party': 'D', 'chamber': 'Senate', 'state': 'MA'},
    ]

    trades = []
    base_date = datetime.now() - timedelta(days=730)

    for i in range(count):
        trade_date = base_date + timedelta(days=i % 720)

        pol = politicians[i % len(politicians)]
        ticker = tickers[i % len(tickers)]

        is_purchase = (i % 4) != 0

        trade = {
            'id': i + 1,
            'politician_name': pol['name'],
            'ticker': ticker,
            'transaction_date': trade_date,
            'transaction_type': 'purchase' if is_purchase else 'sale',
            'amount_min': 15000 + (i * 500),
            'amount_max': 50000 + (i * 1000),
            'chamber': pol['chamber'],
            'state': pol['state'],
            'party': pol['party']
        }

        trades.append(trade)

    return trades


def generate_synthetic_prices(tickers: List[str], start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
    """Generate synthetic price data"""
    logger.info(f"Generating synthetic prices for {len(tickers)} tickers...")

    price_data = {}
    dates = pd.date_range(start_date, end_date, freq='D')

    for ticker in tickers:
        base_price = 100 + (hash(ticker) % 400)

        np.random.seed(hash(ticker) % 10000)
        returns = np.random.normal(0.0005, 0.02, len(dates))
        prices = base_price * np.exp(np.cumsum(returns))

        df = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.01, len(prices))),
            'high': prices * (1 + abs(np.random.normal(0, 0.015, len(prices)))),
            'low': prices * (1 - abs(np.random.normal(0, 0.015, len(prices)))),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, len(prices)),
            'adj close': prices
        }, index=dates)

        price_data[ticker] = df

    return price_data


def main():
    print("\n" + "=" * 70)
    print("QUICK ML MODEL TRAINING")
    print("=" * 70 + "\n")

    # Generate mock data
    trades = generate_mock_trades(count=500)
    tickers = list(set(t['ticker'] for t in trades))
    logger.info(f"Generated {len(trades)} trades for {len(tickers)} tickers")

    start_date = datetime.now() - timedelta(days=900)
    end_date = datetime.now()
    price_data = generate_synthetic_prices(tickers, start_date, end_date)

    # Import and initialize prediction service
    from services.prediction_service import PredictionService

    service = PredictionService(model_dir='data/models')

    # Train models
    print("\n" + "-" * 70)
    print("TRAINING ML MODELS")
    print("-" * 70)

    training_result = service.train_models(
        trades=trades,
        price_data=price_data,
        start_date=start_date,
        end_date=end_date,
        save_models=True
    )

    print("\nTraining Results:")
    print(json.dumps(training_result, indent=2, default=str))

    # Make predictions
    print("\n" + "-" * 70)
    print("GENERATING PREDICTIONS")
    print("-" * 70)

    predictions = service.predict_from_politician_activity(
        trades=trades,
        price_data=price_data,
        lookback_days=30,
        min_confidence=0.4,
        top_n=10
    )

    print(f"\nTop {len(predictions)} Predictions:")
    print("-" * 70)
    print(f"{'Ticker':<8} {'Direction':<10} {'Confidence':<12} {'Prob UP':<10} {'Trades':<8}")
    print("-" * 70)

    for pred in predictions:
        print(
            f"{pred['ticker']:<8} "
            f"{pred['prediction']:<10} "
            f"{pred['confidence']*100:>10.1f}% "
            f"{pred['probability_up']*100:>8.1f}% "
            f"{pred['recent_trade_count']:>6}"
        )

    # Save predictions
    output_dir = Path('data/predictions')
    output_dir.mkdir(parents=True, exist_ok=True)

    pred_file = output_dir / 'predictions_latest.json'
    with open(pred_file, 'w') as f:
        json.dump(predictions, f, indent=2, default=str)

    print(f"\nSaved predictions to {pred_file}")

    # Verify models saved
    model_dir = Path('data/models')
    if (model_dir / 'predictor_models.pkl').exists():
        print(f"✓ Models saved to {model_dir / 'predictor_models.pkl'}")
    else:
        print("✗ Models not saved")

    print("\n" + "=" * 70)
    print("TRAINING COMPLETE!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
