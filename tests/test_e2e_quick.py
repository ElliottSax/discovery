#!/usr/bin/env python3
"""
Quick End-to-End Tests for Discovery Platform
Tests API endpoints, predictions, and WebSocket functionality
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variables for testing
os.environ.setdefault('JWT_SECRET_KEY', 'test_secret_key_12345')
os.environ.setdefault('API_USERNAME', 'demo')
os.environ.setdefault('API_PASSWORD_HASH', '$2b$12$test')


def test_api_imports():
    """Test that all API modules can be imported"""
    print("\n=== Test 1: API Imports ===")

    try:
        from fastapi import FastAPI
        print("  ✓ FastAPI imported")
    except ImportError as e:
        print(f"  ✗ FastAPI import failed: {e}")
        return False

    try:
        from api.models import Trade, Politician, Analysis, Alert
        print("  ✓ API models imported")
    except ImportError as e:
        print(f"  ✗ API models import failed: {e}")
        return False

    try:
        from api.auth import create_access_token, verify_token
        print("  ✓ API auth imported")
    except ImportError as e:
        print(f"  ✗ API auth import failed: {e}")
        return False

    try:
        from api.rate_limiter import RateLimiter
        print("  ✓ Rate limiter imported")
    except ImportError as e:
        print(f"  ✗ Rate limiter import failed: {e}")
        return False

    return True


def test_prediction_service():
    """Test prediction service initialization"""
    print("\n=== Test 2: Prediction Service ===")

    try:
        from services.prediction_service import PredictionService
        print("  ✓ PredictionService imported")
    except ImportError as e:
        print(f"  ✗ PredictionService import failed: {e}")
        return False

    try:
        service = PredictionService(model_dir='data/models')
        print(f"  ✓ PredictionService initialized")
        print(f"    - Model dir: {service.model_dir}")
        print(f"    - Predictor type: {type(service.predictor).__name__}")
    except Exception as e:
        print(f"  ✗ PredictionService init failed: {e}")
        return False

    return True


def test_ml_models():
    """Test ML model components"""
    print("\n=== Test 3: ML Models ===")

    try:
        from ml_models.stock_predictor import StockPricePredictor, BaselinePredictor
        print("  ✓ Stock predictor imported")
    except ImportError as e:
        print(f"  ✗ Stock predictor import failed: {e}")
        return False

    try:
        from ml_models.feature_engineering import PoliticianTradeFeatureExtractor
        print("  ✓ Feature extractor imported")
    except ImportError as e:
        print(f"  ✗ Feature extractor import failed: {e}")
        return False

    # Test baseline predictor
    try:
        predictor = BaselinePredictor()
        print("  ✓ BaselinePredictor created")

        # Test with mock data
        mock_trades = [
            {'ticker': 'AAPL', 'transaction_type': 'purchase', 'politician_name': 'Test', 'transaction_date': '2025-01-01'},
            {'ticker': 'AAPL', 'transaction_type': 'purchase', 'politician_name': 'Test2', 'transaction_date': '2025-01-02'},
        ]

        result = predictor.predict('AAPL', mock_trades, datetime.now())
        print(f"  ✓ BaselinePredictor prediction: {result.get('prediction')} ({result.get('confidence', 0):.2f})")
    except Exception as e:
        print(f"  ✗ BaselinePredictor test failed: {e}")
        return False

    return True


def test_feature_engineering():
    """Test feature extraction"""
    print("\n=== Test 4: Feature Engineering ===")

    try:
        from ml_models.feature_engineering import PoliticianTradeFeatureExtractor
        import pandas as pd
        import numpy as np

        extractor = PoliticianTradeFeatureExtractor(lookback_days=30)
        print("  ✓ Feature extractor created")

        # Test with mock data
        mock_trades = [
            {
                'ticker': 'AAPL',
                'transaction_type': 'purchase',
                'politician_name': 'Test Politician',
                'transaction_date': '2025-12-01',
                'amount_min': 1000,
                'amount_max': 15000
            },
            {
                'ticker': 'AAPL',
                'transaction_type': 'purchase',
                'politician_name': 'Another Politician',
                'transaction_date': '2025-12-10',
                'amount_min': 5000,
                'amount_max': 50000
            },
        ]

        features = extractor.extract_features_for_ticker('AAPL', mock_trades, datetime(2025, 12, 15))
        print(f"  ✓ Features extracted: {len(features)} features")

        # Check some key features
        key_features = ['trade_count', 'buy_ratio', 'politician_count']
        for key in key_features:
            if key in features:
                print(f"    - {key}: {features[key]}")

    except Exception as e:
        print(f"  ✗ Feature engineering test failed: {e}")
        return False

    return True


def test_websocket_manager():
    """Test WebSocket connection manager"""
    print("\n=== Test 5: WebSocket Manager ===")

    try:
        # Import the connection manager class from api.main
        # We need to import carefully to avoid starting the server
        import importlib.util

        spec = importlib.util.spec_from_file_location("api_main", "api/main.py")
        api_module = importlib.util.module_from_spec(spec)

        # Just test that ConnectionManager class exists in the code
        with open('api/main.py', 'r') as f:
            content = f.read()

        assert 'class ConnectionManager:' in content, "ConnectionManager class not found"
        print("  ✓ ConnectionManager class exists")

        assert 'async def connect' in content, "connect method not found"
        print("  ✓ connect method exists")

        assert 'def disconnect' in content, "disconnect method not found"
        print("  ✓ disconnect method exists")

        assert 'async def broadcast' in content, "broadcast method not found"
        print("  ✓ broadcast method exists")

        assert '@app.websocket("/ws/trades")' in content, "WebSocket endpoint not found"
        print("  ✓ WebSocket endpoint /ws/trades exists")

    except Exception as e:
        print(f"  ✗ WebSocket manager test failed: {e}")
        return False

    return True


def test_api_endpoints_exist():
    """Test that all expected API endpoints exist"""
    print("\n=== Test 6: API Endpoints ===")

    try:
        with open('api/main.py', 'r') as f:
            content = f.read()

        endpoints = [
            ('@app.get("/health")', 'Health check'),
            ('@app.post("/api/v1/auth/login")', 'Login'),
            ('@app.get("/api/v1/politicians"', 'List politicians'),
            ('@app.get("/api/v1/trades")', 'Get trades'),
            ('@app.get("/api/v1/analysis/patterns")', 'Get patterns'),
            ('@app.get("/api/v1/predictions")', 'Get predictions'),
            ('@app.get("/api/v1/predictions/{ticker}")', 'Get ticker prediction'),
            ('@app.websocket("/ws/trades")', 'WebSocket trades'),
            ('@app.post("/api/v1/broadcast")', 'Broadcast'),
        ]

        all_found = True
        for endpoint, name in endpoints:
            if endpoint in content:
                print(f"  ✓ {name} endpoint exists")
            else:
                print(f"  ✗ {name} endpoint NOT found")
                all_found = False

        return all_found

    except Exception as e:
        print(f"  ✗ API endpoints test failed: {e}")
        return False


def test_frontend_predictions_component():
    """Test that frontend has predictions component"""
    print("\n=== Test 7: Frontend Predictions ===")

    try:
        with open('frontend/app/page.tsx', 'r') as f:
            content = f.read()

        checks = [
            ('interface Prediction', 'Prediction interface'),
            ('predictions', 'predictions state'),
            ('fetchPredictions', 'fetchPredictions function'),
            ('ML Stock Predictions', 'Predictions section title'),
            ('probability_up', 'probability_up display'),
            ('confidence', 'confidence display'),
        ]

        all_found = True
        for check, name in checks:
            if check in content:
                print(f"  ✓ {name} found")
            else:
                print(f"  ✗ {name} NOT found")
                all_found = False

        return all_found

    except Exception as e:
        print(f"  ✗ Frontend predictions test failed: {e}")
        return False


def run_all_tests():
    """Run all end-to-end tests"""
    print("=" * 60)
    print("DISCOVERY PLATFORM - END-TO-END TESTS")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")

    results = {}

    # Run tests
    results['api_imports'] = test_api_imports()
    results['prediction_service'] = test_prediction_service()
    results['ml_models'] = test_ml_models()
    results['feature_engineering'] = test_feature_engineering()
    results['websocket_manager'] = test_websocket_manager()
    results['api_endpoints'] = test_api_endpoints_exist()
    results['frontend_predictions'] = test_frontend_predictions_component()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
