#!/usr/bin/env python3
"""
Train ML Models and Run Stock Predictions
Comprehensive script for model training, prediction, and backtesting
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict
from dotenv import load_dotenv

# Import our modules
from services.prediction_service import PredictionService
from analysis.backtesting.backtest_engine import BacktestEngine
from analysis.backtesting.prediction_strategy import (
    MLPredictionStrategy,
    AdaptivePredictionStrategy,
    ConsensusBoostStrategy
)
from ml_models.stock_predictor import MultiHorizonPredictor
from ml_models.model_explainer import ModelExplainer, create_explainer_for_predictor
import numpy as np

# Load environment
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PredictionPipeline:
    """End-to-end prediction pipeline"""

    def __init__(self):
        self.db_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'quant_db'),
            'user': os.getenv('DB_USER', 'quant_user'),
            'password': os.getenv('DB_PASSWORD', '')
        }

        self.prediction_service = PredictionService(model_dir='data/models')
        self.multi_horizon_predictor = MultiHorizonPredictor(model_dir='data/models')
        self.use_mock_data = False

    def load_trades_from_db(self) -> List[Dict]:
        """Load trades from PostgreSQL"""

        logger.info("Loading trades from database...")

        try:
            conn = psycopg2.connect(**self.db_params)

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
                        t.disclosure_date,
                        p.chamber,
                        p.state,
                        p.party
                    FROM trades t
                    LEFT JOIN politicians p ON t.politician_id = p.id
                    WHERE t.ticker IS NOT NULL
                    ORDER BY t.transaction_date DESC
                """)

                rows = cur.fetchall()
                trades = [dict(row) for row in rows]

            conn.close()

            logger.info(f"Loaded {len(trades)} trades from database")
            return trades

        except Exception as e:
            logger.error(f"Error loading trades from DB: {e}")
            return []

    def generate_mock_trades(self, count: int = 500) -> List[Dict]:
        """Generate mock trading data for testing/training"""
        logger.info(f"Generating {count} mock trades...")

        tickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN', 'META', 'NFLX',
                   'AMD', 'CRM', 'ORCL', 'INTC', 'CSCO', 'ADBE', 'QCOM']

        politicians = [
            {'name': 'Nancy Pelosi', 'party': 'D', 'chamber': 'House', 'state': 'CA'},
            {'name': 'Mitch McConnell', 'party': 'R', 'chamber': 'Senate', 'state': 'KY'},
            {'name': 'AOC', 'party': 'D', 'chamber': 'House', 'state': 'NY'},
            {'name': 'Ted Cruz', 'party': 'R', 'chamber': 'Senate', 'state': 'TX'},
            {'name': 'Elizabeth Warren', 'party': 'D', 'chamber': 'Senate', 'state': 'MA'},
            {'name': 'Josh Hawley', 'party': 'R', 'chamber': 'Senate', 'state': 'MO'},
            {'name': 'Ro Khanna', 'party': 'D', 'chamber': 'House', 'state': 'CA'},
            {'name': 'Dan Crenshaw', 'party': 'R', 'chamber': 'House', 'state': 'TX'}
        ]

        trades = []
        base_date = datetime.now() - timedelta(days=730)  # 2 years of history

        for i in range(count):
            trade_date = base_date + timedelta(days=i % 720)
            disclosure_date = trade_date + timedelta(days=15 + (i % 30))

            pol = politicians[i % len(politicians)]
            ticker = tickers[i % len(tickers)]

            # Bias towards purchases
            is_purchase = (i % 4) != 0

            trade = {
                'id': i + 1,
                'politician_name': pol['name'],
                'ticker': ticker,
                'transaction_date': trade_date,
                'transaction_type': 'purchase' if is_purchase else 'sale',
                'amount_min': 15000 + (i * 500),
                'amount_max': 50000 + (i * 1000),
                'disclosure_date': disclosure_date,
                'chamber': pol['chamber'],
                'state': pol['state'],
                'party': pol['party']
            }

            trades.append(trade)

        logger.info(f"Generated {len(trades)} mock trades")
        self.use_mock_data = True
        return trades

    def generate_synthetic_prices(
        self,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """Generate synthetic price data (fallback when yfinance fails)"""
        logger.info(f"Generating synthetic prices for {len(tickers)} tickers...")

        price_data = {}
        dates = pd.date_range(start_date, end_date, freq='D')

        for ticker in tickers:
            # Start price varies by ticker
            base_price = 100 + (hash(ticker) % 400)

            # Random walk with drift
            np.random.seed(hash(ticker) % 10000)
            returns = np.random.normal(0.0005, 0.02, len(dates))  # ~12% annual return, 30% volatility
            prices = base_price * np.exp(np.cumsum(returns))

            # Create DataFrame
            df = pd.DataFrame({
                'open': prices * (1 + np.random.normal(0, 0.01, len(prices))),
                'high': prices * (1 + abs(np.random.normal(0, 0.015, len(prices)))),
                'low': prices * (1 - abs(np.random.normal(0, 0.015, len(prices)))),
                'close': prices,
                'volume': np.random.randint(1000000, 10000000, len(prices)),
                'adj close': prices
            }, index=dates)

            price_data[ticker] = df

        logger.info(f"Generated synthetic data for {len(price_data)} tickers")
        return price_data

    def download_price_data(
        self,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """Download price data from Yahoo Finance"""

        logger.info(f"Downloading price data for {len(tickers)} tickers...")

        price_data = {}

        for ticker in tickers:
            try:
                logger.debug(f"Downloading {ticker}...")

                df = yf.download(
                    ticker,
                    start=start_date - timedelta(days=90),
                    end=end_date + timedelta(days=60),
                    progress=False
                )

                if df.empty:
                    logger.warning(f"No data for {ticker}")
                    continue

                df.columns = [c.lower() for c in df.columns]
                price_data[ticker] = df

            except Exception as e:
                logger.error(f"Error downloading {ticker}: {e}")

        logger.info(f"Downloaded data for {len(price_data)} tickers")

        return price_data

    def train_models(
        self,
        trades: List[Dict],
        price_data: Dict[str, pd.DataFrame]
    ) -> Dict:
        """Train ML prediction models"""

        logger.info("\n" + "="*80)
        logger.info("TRAINING ML MODELS")
        logger.info("="*80)

        # Training period: 2 years ago to 6 months ago
        end_date = datetime.now() - timedelta(days=180)
        start_date = end_date - timedelta(days=730)

        logger.info(f"Training period: {start_date.date()} to {end_date.date()}")

        results = self.prediction_service.train_models(
            trades,
            price_data,
            start_date,
            end_date,
            save_models=True
        )

        return results

    def make_predictions(
        self,
        trades: List[Dict],
        price_data: Dict[str, pd.DataFrame],
        top_n: int = 20
    ) -> List[Dict]:
        """Make predictions for current date"""

        logger.info("\n" + "="*80)
        logger.info("GENERATING PREDICTIONS")
        logger.info("="*80)

        predictions = self.prediction_service.predict_from_politician_activity(
            trades=trades,
            price_data=price_data,
            lookback_days=30,
            min_trade_count=2,
            min_confidence=0.3,
            top_n=top_n
        )

        # Display top predictions
        logger.info(f"\nTop {min(10, len(predictions))} Predictions:")
        logger.info("-" * 80)

        for i, pred in enumerate(predictions[:10], 1):
            logger.info(
                f"{i}. {pred['ticker']:<6} "
                f"{pred['prediction']:<5} "
                f"Confidence: {pred['confidence']:.2%}  "
                f"Prob(UP): {pred['probability_up']:.2%}  "
                f"Trades: {pred.get('recent_trade_count', 0)}"
            )

        return predictions

    def run_backtest(
        self,
        trades: List[Dict],
        price_data: Dict[str, pd.DataFrame],
        strategy_name: str = 'ml_prediction'
    ) -> Dict:
        """Run backtest with ML prediction strategy"""

        logger.info("\n" + "="*80)
        logger.info(f"BACKTESTING: {strategy_name.upper()}")
        logger.info("="*80)

        # Backtest period: 6 months ago to now
        start_date = datetime.now() - timedelta(days=180)
        end_date = datetime.now()

        logger.info(f"Backtest period: {start_date.date()} to {end_date.date()}")

        # Initialize strategy
        if strategy_name == 'ml_prediction':
            strategy = MLPredictionStrategy(
                hold_days=30,
                confidence_threshold=0.5,
                max_positions=10
            )
        elif strategy_name == 'adaptive':
            strategy = AdaptivePredictionStrategy(
                hold_days=30,
                confidence_threshold=0.5,
                max_positions=10
            )
        elif strategy_name == 'consensus_boost':
            strategy = ConsensusBoostStrategy(
                hold_days=30,
                confidence_threshold=0.5,
                max_positions=10
            )
        else:
            logger.error(f"Unknown strategy: {strategy_name}")
            return {}

        # Initialize backtest engine
        engine = BacktestEngine(
            initial_capital=100000,
            commission_per_trade=10,
            slippage_pct=0.001,
            position_size_pct=0.1,
            max_positions=10
        )

        # Run backtest
        result = engine.run_backtest(
            strategy_func=lambda td, pd, cd: strategy.generate_signals(td, pd, cd),
            trades_data=trades,
            price_data=price_data,
            start_date=start_date,
            end_date=end_date,
            strategy_name=strategy_name
        )

        # Display results
        logger.info("\nBacktest Results:")
        logger.info("-" * 80)
        logger.info(f"Initial Capital:    ${result.initial_capital:,.2f}")
        logger.info(f"Final Capital:      ${result.final_capital:,.2f}")
        logger.info(f"Total Return:       {result.total_return*100:.2f}%")
        logger.info(f"Annual Return:      {result.annual_return*100:.2f}%")
        logger.info(f"Sharpe Ratio:       {result.sharpe_ratio:.2f}")
        logger.info(f"Max Drawdown:       {result.max_drawdown*100:.2f}%")
        logger.info(f"Win Rate:           {result.win_rate*100:.2f}%")
        logger.info(f"Total Trades:       {result.total_trades}")
        logger.info(f"Profit Factor:      {result.profit_factor:.2f}")

        return {
            'strategy': strategy_name,
            'total_return': result.total_return,
            'annual_return': result.annual_return,
            'sharpe_ratio': result.sharpe_ratio,
            'max_drawdown': result.max_drawdown,
            'win_rate': result.win_rate,
            'total_trades': result.total_trades,
            'profit_factor': result.profit_factor
        }

    def save_predictions(self, predictions: List[Dict], filename: str = None):
        """Save predictions to file"""

        output_dir = Path('data/predictions')
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'predictions_{timestamp}.json'

        filepath = output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(predictions, f, indent=2)

        logger.info(f"Saved predictions to {filepath}")

        # Also save as latest
        latest_path = output_dir / 'predictions_latest.json'
        with open(latest_path, 'w') as f:
            json.dump(predictions, f, indent=2)


def main():
    """Main execution"""

    print("\n" + "="*80)
    print("STOCK PREDICTION & BACKTESTING PIPELINE")
    print("="*80 + "\n")

    pipeline = PredictionPipeline()

    # 1. Load data
    logger.info("Step 1: Loading data...")
    trades = pipeline.load_trades_from_db()

    if not trades:
        logger.warning("No trades in database - using mock data")
        trades = pipeline.generate_mock_trades(count=500)

    # Get unique tickers
    tickers = list(set(t.get('ticker', '').upper() for t in trades if t.get('ticker')))
    logger.info(f"Found {len(tickers)} unique tickers")

    # Download price data
    start_date = datetime.now() - timedelta(days=900)  # ~2.5 years
    end_date = datetime.now()

    if pipeline.use_mock_data:
        # Use synthetic prices for mock data
        logger.info("Using synthetic price data...")
        price_data = pipeline.generate_synthetic_prices(tickers, start_date, end_date)
    else:
        price_data = pipeline.download_price_data(tickers, start_date, end_date)

    if not price_data:
        logger.error("No price data available - exiting")
        return

    # 2. Train models
    logger.info("\nStep 2: Training ML models...")
    training_results = pipeline.train_models(trades, price_data)

    print("\nTraining Results:")
    print(json.dumps(training_results, indent=2))

    # 3. Make predictions for current date
    logger.info("\nStep 3: Generating predictions...")
    predictions = pipeline.make_predictions(trades, price_data, top_n=20)

    # Save predictions
    pipeline.save_predictions(predictions)

    # 4. Run backtests
    logger.info("\nStep 4: Running backtests...")

    backtest_results = {}

    # Test different strategies
    strategies = ['ml_prediction', 'adaptive', 'consensus_boost']

    for strategy_name in strategies:
        result = pipeline.run_backtest(trades, price_data, strategy_name)
        backtest_results[strategy_name] = result

    # 5. Multi-horizon predictions
    logger.info("\nStep 5: Generating multi-horizon predictions...")
    print("\n" + "="*80)
    print("MULTI-HORIZON PREDICTIONS")
    print("="*80)

    top_tickers = tickers[:5]  # Top 5 tickers
    multi_horizon_results = {}

    for ticker in top_tickers:
        logger.info(f"Predicting {ticker} across 5 horizons...")
        try:
            predictions = pipeline.multi_horizon_predictor.predict_all_horizons(
                ticker,
                trades,
                datetime.now(),
                price_data.get(ticker)
            )

            summary = pipeline.multi_horizon_predictor.get_horizon_summary(predictions)
            multi_horizon_results[ticker] = {
                'predictions': predictions,
                'summary': summary
            }

            # Display
            print(f"\n{ticker}:")
            print(f"  Consensus: {summary['consensus']}")
            print(f"  Agreement: {summary['agreement_score']:.2%}")
            print(f"  Avg Confidence: {summary['confidence_avg']:.2%}")
            print(f"  7d: {summary['short_term']}, 90d: {summary['long_term']}")

        except Exception as e:
            logger.error(f"Multi-horizon prediction failed for {ticker}: {e}")

    # Save multi-horizon predictions
    output_dir = Path('data/predictions')
    output_dir.mkdir(parents=True, exist_ok=True)

    multi_horizon_file = output_dir / 'multi_horizon_predictions.json'
    with open(multi_horizon_file, 'w') as f:
        # Convert datetime objects to strings
        saveable = {}
        for ticker, data in multi_horizon_results.items():
            saveable[ticker] = {
                'summary': data['summary'],
                'predictions': {k: v for k, v in data['predictions'].items()}
            }
        json.dump(saveable, f, indent=2, default=str)

    logger.info(f"Saved multi-horizon predictions to {multi_horizon_file}")

    # 6. Model explainability
    logger.info("\nStep 6: Generating model explanations...")
    print("\n" + "="*80)
    print("MODEL EXPLAINABILITY (SHAP)")
    print("="*80)

    try:
        # Get feature names from prediction service
        feature_extractor = pipeline.prediction_service.predictor.feature_extractor

        # Create explainer for the best model
        explainer = create_explainer_for_predictor(
            pipeline.prediction_service.predictor,
            list(feature_extractor.feature_names) if hasattr(feature_extractor, 'feature_names') else []
        )

        # Explain top 3 predictions
        for i, pred in enumerate(predictions[:3], 1):
            ticker = pred['ticker']
            print(f"\n{'='*60}")
            print(f"Explanation {i}: {ticker}")
            print('='*60)

            # Get features for this prediction
            if 'features' in pred:
                features_dict = pred['features']
                features_array = np.array([list(features_dict.values())])

                explanation = explainer.explain_prediction(features_array)

                print(f"\nPrediction: {pred['prediction']}")
                print(f"Confidence: {pred['confidence']:.2%}")
                print("\nTop Contributing Factors:")
                for factor in explanation['top_positive'][:5]:
                    print(f"  + {factor['feature']}: {factor['contribution']:+.3f}")

                print("\nTop Opposing Factors:")
                for factor in explanation['top_negative'][:3]:
                    print(f"  - {factor['feature']}: {factor['contribution']:+.3f}")

    except Exception as e:
        logger.error(f"Explainability generation failed: {e}")
        logger.debug("Stack trace:", exc_info=True)

    # 7. Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    print("\nStrategy Performance Comparison:")
    print("-" * 80)
    print(f"{'Strategy':<20} {'Return':<12} {'Sharpe':<10} {'Win Rate':<10} {'Trades':<8}")
    print("-" * 80)

    for strategy, result in backtest_results.items():
        print(
            f"{strategy:<20} "
            f"{result['total_return']*100:>10.2f}% "
            f"{result['sharpe_ratio']:>9.2f} "
            f"{result['win_rate']*100:>8.2f}% "
            f"{result['total_trades']:>7}"
        )

    print("\n" + "="*80)
    print("COMPLETE!")
    print("="*80 + "\n")

    print("Generated files:")
    print("- Single-horizon predictions: data/predictions/predictions_latest.json")
    print("- Multi-horizon predictions: data/predictions/multi_horizon_predictions.json")
    print("- Trained models: data/models/predictor_models_latest.pkl")
    print("\nNext steps:")
    print("- Run backtests: python scripts/run_backtest_analysis.py")
    print("- View predictions: cat data/predictions/predictions_latest.json")
    print()


if __name__ == "__main__":
    main()
