"""
Pytest configuration and shared fixtures for all tests.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


@pytest.fixture
def synthetic_cycle():
    """Generate synthetic data with known 30-day cycle."""
    np.random.seed(42)
    t = np.linspace(0, 365, 365)

    # 30-day cycle with noise
    signal = 10 + 5 * np.sin(2 * np.pi * t / 30) + np.random.normal(0, 1, 365)

    return pd.Series(signal, index=pd.date_range('2023-01-01', periods=365))


@pytest.fixture
def multi_cycle_series():
    """Generate synthetic data with multiple cycles (weekly + monthly)."""
    np.random.seed(42)
    t = np.linspace(0, 365, 365)

    # Weekly (7-day) + Monthly (30-day) cycles + trend + noise
    weekly = 3 * np.sin(2 * np.pi * t / 7)
    monthly = 5 * np.sin(2 * np.pi * t / 30)
    trend = 0.01 * t  # Linear trend
    noise = np.random.normal(0, 1, 365)

    signal = 10 + weekly + monthly + trend + noise

    return pd.Series(signal, index=pd.date_range('2023-01-01', periods=365))


@pytest.fixture
def regime_change_series():
    """Generate synthetic data with clear regime changes."""
    np.random.seed(42)

    # Regime 1: Bull market (high return, low vol) - 120 days
    regime1 = np.random.normal(0.02, 0.01, 120)

    # Regime 2: Bear market (negative return, high vol) - 120 days
    regime2 = np.random.normal(-0.015, 0.03, 120)

    # Regime 3: Sideways (low return, medium vol) - 125 days
    regime3 = np.random.normal(0.001, 0.015, 125)

    returns = np.concatenate([regime1, regime2, regime3])

    return pd.Series(returns, index=pd.date_range('2023-01-01', periods=len(returns)))


@pytest.fixture
def similar_patterns():
    """Generate historical data with recurring similar patterns."""
    np.random.seed(42)

    # Create a specific pattern
    pattern = np.array([1, 2, 3, 5, 4, 3, 2, 1])

    # Repeat pattern with variations
    n_repeats = 10
    full_series = []

    for i in range(n_repeats):
        # Add pattern with slight noise
        variation = pattern + np.random.normal(0, 0.3, len(pattern))
        full_series.extend(variation)

        # Add random data between patterns
        random_data = np.random.normal(2.5, 1, 20)
        full_series.extend(random_data)

    return pd.Series(full_series, index=pd.date_range('2022-01-01', periods=len(full_series)))


@pytest.fixture
def short_series():
    """Generate short time series (too short for most analyses)."""
    np.random.seed(42)
    return pd.Series(np.random.randn(20))


@pytest.fixture
def series_with_nans():
    """Generate time series with NaN values."""
    np.random.seed(42)
    series = pd.Series(np.random.randn(100))

    # Inject NaNs at random positions
    nan_indices = np.random.choice(100, 10, replace=False)
    series.iloc[nan_indices] = np.nan

    return series


@pytest.fixture
def constant_series():
    """Generate constant time series (zero variance)."""
    return pd.Series([5.0] * 100)


@pytest.fixture
def mock_trade_data():
    """Generate mock politician trade data."""
    np.random.seed(42)

    dates = pd.date_range('2023-01-01', periods=100, freq='D')

    trades = pd.DataFrame({
        'transaction_date': dates,
        'ticker': np.random.choice(['AAPL', 'MSFT', 'GOOGL', 'TSLA'], 100),
        'transaction_type': np.random.choice(['purchase', 'sale'], 100),
        'amount': np.random.uniform(10000, 100000, 100),
        'politician_id': np.random.choice(['POL1', 'POL2', 'POL3'], 100),
        'party': np.random.choice(['Democratic', 'Republican'], 100)
    })

    return trades


@pytest.fixture
def mock_market_data():
    """Generate mock market price data."""
    np.random.seed(42)

    dates = pd.date_range('2023-01-01', periods=252, freq='D')

    # Simulate price with GBM
    returns = np.random.normal(0.0005, 0.02, 252)
    price = 100 * np.exp(np.cumsum(returns))

    market_data = pd.DataFrame({
        'close': price,
        'high': price * (1 + abs(np.random.normal(0, 0.01, 252))),
        'low': price * (1 - abs(np.random.normal(0, 0.01, 252))),
        'volume': np.random.uniform(1e6, 1e7, 252)
    }, index=dates)

    return market_data


@pytest.fixture
def temp_model_dir(tmp_path):
    """Create temporary directory for model storage."""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    return model_dir


# Parametrize fixtures for different data sizes
@pytest.fixture(params=[100, 500, 1000])
def variable_length_series(request):
    """Generate series of different lengths."""
    np.random.seed(42)
    n = request.param
    t = np.linspace(0, n, n)
    signal = 10 + 5 * np.sin(2 * np.pi * t / 30) + np.random.normal(0, 1, n)
    return pd.Series(signal)


# Markers for different test categories
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "benchmark: marks tests as benchmarks")
