"""
Backtesting Framework

Automated backtesting for pattern detection strategies.
"""

from analysis.backtesting.engine import (
    BacktestEngine,
    BacktestConfig,
    BacktestResult,
    quick_backtest
)

__all__ = [
    'BacktestEngine',
    'BacktestConfig',
    'BacktestResult',
    'quick_backtest'
]
