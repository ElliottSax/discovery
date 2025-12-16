#!/usr/bin/env python3
"""
Test Stock Prediction System
Quick validation that all components work
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from datetime import datetime, timedelta
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_feature_engineering():
    """Test feature extraction"""
    logger.info("Testing Feature Engineering...")

    from ml_models.feature_engineering import PoliticianTradeFeatureExtractor

    # Sample trades
    sample_trades = [
        {
            'ticker': 'AAPL',
            'politician_name': 'Senator A',
            'transaction_date': '2024-12-15',
            'transaction_type': 'purchase',
            'amount_min': 15000,
            'amount_max': 50000,
            'party': 'Democrat',
            'chamber': 'Senate'
        },
        {
            'ticker': 'AAPL',
            'politician_name': 'Senator B',
            'transaction_date': '2024-12-16',
            'transaction_type': 'purchase',
            'amount_min': 15000,
            'amount_max': 50000,
            'party': 'Republican',
            'chamber': 'Senate'
        },
        {
            'ticker': 'AAPL',
            'politician_name': 'Rep C',
            'transaction_date': '2024-12-17',
            'transaction_type': 'purchase',
            'amount_min': 50000,
            'amount_max': 100000,
            'party': 'Democrat',
            'chamber': 'House'
        }
    ]

    extractor = PoliticianTradeFeatureExtractor(lookback_days=30)

    features = extractor.extract_features_for_ticker(
        'AAPL',
        sample_trades,
        datetime(2024, 12, 20)
    )

    logger.info(f"Extracted {len(features)} features")
    logger.info(f"Feature sample: trade_count={features['trade_count']}, "
                f"consensus_strength={features['consensus_strength']:.2f}, "
                f"buy_ratio={features['buy_ratio']:.2f}")

    assert features['trade_count'] == 3.0, "Should have 3 trades"
    assert features['buy_ratio'] == 1.0, "All trades are purchases"
    assert features['num_politicians'] == 3.0, "3 unique politicians"

    logger.info("✅ Feature Engineering: PASSED\n")
    return True


def test_baseline_predictor():
    """Test baseline predictor (no ML required)"""
    logger.info("Testing Baseline Predictor...")

    from ml_models.stock_predictor import BaselinePredictor

    predictor = BaselinePredictor()

    # Sample trades (bullish signal)
    bullish_trades = [
        {
            'ticker': 'NVDA',
            'politician_name': f'Politician {i}',
            'transaction_date': (datetime.now() - timedelta(days=i)).isoformat(),
            'transaction_type': 'purchase',
            'amount_min': 50000,
            'amount_max': 100000
        }
        for i in range(5)
    ]

    prediction = predictor.predict(
        'NVDA',
        bullish_trades,
        datetime.now()
    )

    logger.info(f"Prediction: {prediction['prediction']}")
    logger.info(f"Confidence: {prediction['confidence']:.2%}")
    logger.info(f"Probability UP: {prediction['probability_up']:.2%}")

    assert prediction['prediction'] == 'UP', "Should predict UP with all buys"
    assert prediction['confidence'] > 0, "Should have some confidence"

    logger.info("✅ Baseline Predictor: PASSED\n")
    return True


def test_ml_predictor_initialization():
    """Test ML predictor can initialize"""
    logger.info("Testing ML Predictor Initialization...")

    try:
        from ml_models.stock_predictor import StockPricePredictor

        predictor = StockPricePredictor(
            prediction_horizon_days=30,
            model_dir='data/models'
        )

        logger.info(f"Initialized predictor with {len(predictor.models)} models")
        logger.info(f"Models: {list(predictor.models.keys())}")

        logger.info("✅ ML Predictor Initialization: PASSED\n")
        return True

    except ImportError as e:
        logger.warning(f"ML libraries not available: {e}")
        logger.info("⚠️  ML Predictor: SKIPPED (will use baseline)\n")
        return True


def test_prediction_service():
    """Test prediction service"""
    logger.info("Testing Prediction Service...")

    from services.prediction_service import PredictionService

    service = PredictionService(model_dir='data/models')

    # Sample data
    sample_trades = [
        {
            'ticker': 'MSFT',
            'politician_name': f'Senator {i}',
            'transaction_date': (datetime.now() - timedelta(days=i*3)).isoformat(),
            'transaction_type': 'purchase' if i % 2 == 0 else 'sale',
            'amount_min': 15000 + (i * 5000),
            'amount_max': 50000 + (i * 10000)
        }
        for i in range(10)
    ]

    # Test single prediction
    prediction = service.predict_ticker(
        'MSFT',
        sample_trades,
        datetime.now()
    )

    logger.info(f"Single prediction: {prediction['ticker']} - {prediction['prediction']}")
    logger.info(f"Confidence: {prediction['confidence']:.2%}")

    assert 'ticker' in prediction
    assert 'prediction' in prediction
    assert 'confidence' in prediction

    # Test batch prediction
    predictions = service.predict_batch(
        ['AAPL', 'MSFT', 'GOOGL'],
        sample_trades,
        datetime.now(),
        min_confidence=0.0,
        top_n=3
    )

    logger.info(f"Batch predictions: {len(predictions)} tickers")

    logger.info("✅ Prediction Service: PASSED\n")
    return True


def test_trading_strategy():
    """Test ML trading strategy"""
    logger.info("Testing ML Trading Strategy...")

    from analysis.backtesting.prediction_strategy import MLPredictionStrategy

    strategy = MLPredictionStrategy(
        hold_days=30,
        confidence_threshold=0.3,
        max_positions=5
    )

    # Sample trades
    sample_trades = [
        {
            'ticker': 'AAPL',
            'politician_name': 'Senator A',
            'transaction_date': (datetime.now() - timedelta(days=5)).isoformat(),
            'transaction_type': 'purchase',
            'amount_min': 50000,
            'amount_max': 100000
        },
        {
            'ticker': 'MSFT',
            'politician_name': 'Senator B',
            'transaction_date': (datetime.now() - timedelta(days=3)).isoformat(),
            'transaction_type': 'purchase',
            'amount_min': 50000,
            'amount_max': 100000
        }
    ]

    signals = strategy.generate_signals(
        sample_trades,
        {},  # Empty price data for test
        datetime.now()
    )

    logger.info(f"Generated {len(signals)} trading signals")

    if signals:
        for signal in signals[:3]:
            logger.info(f"  {signal['action'].upper()} {signal['ticker']} "
                       f"(strength: {signal['signal_strength']:.2f})")

    logger.info("✅ Trading Strategy: PASSED\n")
    return True


def test_integration():
    """Test full integration"""
    logger.info("Testing Full Integration...")

    from services.prediction_service import PredictionService
    from analysis.backtesting.prediction_strategy import ConsensusBoostStrategy

    # Create service
    service = PredictionService()

    # Create strategy
    strategy = ConsensusBoostStrategy(
        hold_days=30,
        confidence_threshold=0.4,
        max_positions=10
    )

    # Sample realistic trades
    trades = []
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']
    politicians = ['Warren', 'Pelosi', 'McConnell', 'Cruz', 'Schumer']

    for day in range(30):
        for _ in range(np.random.poisson(2)):  # ~2 trades per day
            trades.append({
                'ticker': np.random.choice(tickers),
                'politician_name': np.random.choice(politicians),
                'transaction_date': (datetime.now() - timedelta(days=30-day)).isoformat(),
                'transaction_type': 'purchase' if np.random.random() > 0.3 else 'sale',
                'amount_min': np.random.randint(15, 50) * 1000,
                'amount_max': np.random.randint(50, 250) * 1000,
                'party': np.random.choice(['Democrat', 'Republican']),
                'chamber': np.random.choice(['Senate', 'House'])
            })

    logger.info(f"Generated {len(trades)} sample trades")

    # Get predictions
    predictions = service.predict_from_politician_activity(
        trades,
        current_date=datetime.now(),
        lookback_days=30,
        min_trade_count=2,
        min_confidence=0.0,
        top_n=10
    )

    logger.info(f"Generated {len(predictions)} predictions")

    if predictions:
        logger.info("\nTop 5 Predictions:")
        for i, pred in enumerate(predictions[:5], 1):
            logger.info(f"  {i}. {pred['ticker']:<6} {pred['prediction']:<5} "
                       f"Confidence: {pred['confidence']:.2%}  "
                       f"Trades: {pred.get('recent_trade_count', 0)}")

    # Generate trading signals
    signals = strategy.generate_signals(trades, {}, datetime.now())

    logger.info(f"\nGenerated {len(signals)} trading signals")

    if signals:
        logger.info("\nTrading Signals:")
        for signal in signals[:5]:
            logger.info(f"  {signal['action'].upper():<5} {signal['ticker']:<6} "
                       f"Strength: {signal['signal_strength']:.2f}")

    logger.info("\n✅ Full Integration: PASSED\n")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("STOCK PREDICTION SYSTEM - TEST SUITE")
    print("="*80 + "\n")

    tests = [
        ("Feature Engineering", test_feature_engineering),
        ("Baseline Predictor", test_baseline_predictor),
        ("ML Predictor Init", test_ml_predictor_initialization),
        ("Prediction Service", test_prediction_service),
        ("Trading Strategy", test_trading_strategy),
        ("Full Integration", test_integration)
    ]

    results = []

    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            logger.error(f"❌ {name}: FAILED")
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:<25} {status}")

    print("-"*80)
    print(f"TOTAL: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready to use.\n")
        print("Next steps:")
        print("  python scripts/train_and_predict.py  # Train models and generate predictions")
        print("  cat data/predictions/predictions_latest.json  # View predictions")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.\n")

    print("="*80 + "\n")


if __name__ == "__main__":
    main()
