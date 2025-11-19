"""
Automated Backtesting Engine

Provides walk-forward validation and performance metrics for pattern detection strategies.

Key Features:
- Walk-forward validation (expanding/rolling windows)
- Transaction cost modeling
- Risk-adjusted performance metrics (Sharpe, Calmar, Sortino)
- Drawdown analysis
- Win rate and profit factor
- Monte Carlo simulation for robustness
- Strategy comparison and ranking

Performance Metrics:
- Total return
- Annualized return
- Volatility (annualized)
- Sharpe ratio
- Sortino ratio
- Calmar ratio
- Maximum drawdown
- Win rate
- Profit factor
- Average trade duration

References:
- Pardo (2008) - The Evaluation and Optimization of Trading Strategies
- Lopez de Prado (2018) - Advances in Financial Machine Learning
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""
    # Validation strategy
    validation_type: str = 'expanding'  # expanding, rolling
    train_size: int = 252  # Initial training period (trading days)
    test_size: int = 63  # Test period (trading days)
    step_size: int = 21  # Step between tests (trading days)

    # Trading costs
    transaction_cost: float = 0.001  # 0.1% per trade
    slippage: float = 0.0005  # 0.05% slippage

    # Risk management
    max_leverage: float = 1.0  # Maximum leverage
    stop_loss: Optional[float] = None  # Stop loss percentage
    take_profit: Optional[float] = None  # Take profit percentage

    # Performance calculation
    risk_free_rate: float = 0.02  # Annual risk-free rate
    trading_days_per_year: int = 252


@dataclass
class BacktestResult:
    """Results from backtesting."""
    # Returns
    returns: pd.Series
    cumulative_returns: pd.Series
    equity_curve: pd.Series

    # Performance metrics
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # Risk metrics
    max_drawdown: float
    max_drawdown_duration: int
    var_95: float  # Value at Risk
    cvar_95: float  # Conditional VaR

    # Trade statistics
    n_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    avg_trade_duration: float

    # Additional info
    config: BacktestConfig = field(default_factory=BacktestConfig)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        result = asdict(self)
        # Convert Series to lists for JSON serialization
        result['returns'] = self.returns.tolist()
        result['cumulative_returns'] = self.cumulative_returns.tolist()
        result['equity_curve'] = self.equity_curve.tolist()
        return result

    def summary(self) -> str:
        """Generate summary report."""
        return f"""
Backtest Summary
================

Performance Metrics:
  Total Return:        {self.total_return*100:.2f}%
  Annualized Return:   {self.annualized_return*100:.2f}%
  Annualized Volatility: {self.annualized_volatility*100:.2f}%
  Sharpe Ratio:        {self.sharpe_ratio:.2f}
  Sortino Ratio:       {self.sortino_ratio:.2f}
  Calmar Ratio:        {self.calmar_ratio:.2f}

Risk Metrics:
  Maximum Drawdown:    {self.max_drawdown*100:.2f}%
  Max DD Duration:     {self.max_drawdown_duration} days
  VaR (95%):           {self.var_95*100:.2f}%
  CVaR (95%):          {self.cvar_95*100:.2f}%

Trade Statistics:
  Number of Trades:    {self.n_trades}
  Win Rate:            {self.win_rate*100:.2f}%
  Profit Factor:       {self.profit_factor:.2f}
  Avg Win:             {self.avg_win*100:.2f}%
  Avg Loss:            {self.avg_loss*100:.2f}%
  Avg Trade Duration:  {self.avg_trade_duration:.1f} days
"""


class BacktestEngine:
    """
    Automated backtesting engine for pattern detection strategies.

    Supports walk-forward validation with realistic transaction costs.
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        Initialize backtest engine.

        Args:
            config: Backtest configuration
        """
        self.config = config or BacktestConfig()
        self.results = None

    def run(
        self,
        prices: pd.Series,
        strategy: Callable,
        **strategy_kwargs
    ) -> BacktestResult:
        """
        Run backtest with walk-forward validation.

        Args:
            prices: Price time series
            strategy: Strategy function that takes (train_data, test_data) and returns signals
            **strategy_kwargs: Additional arguments for strategy

        Returns:
            Backtest results

        Example:
            >>> def my_strategy(train_data, test_data):
            ...     # Detect patterns in train_data
            ...     # Generate signals for test_data
            ...     # Return signals (1=long, -1=short, 0=neutral)
            ...     return signals
            >>> engine = BacktestEngine()
            >>> results = engine.run(prices, my_strategy)
        """
        # Convert to DataFrame for easier handling
        if isinstance(prices, pd.Series):
            df = pd.DataFrame({'price': prices})
        else:
            df = pd.DataFrame({'price': prices.values}, index=prices.index)

        # Generate signals using walk-forward validation
        signals = self._walk_forward_validation(df, strategy, **strategy_kwargs)

        # Calculate returns
        returns = self._calculate_returns(df, signals)

        # Calculate performance metrics
        result = self._calculate_metrics(returns, signals)

        self.results = result
        return result

    def _walk_forward_validation(
        self,
        df: pd.DataFrame,
        strategy: Callable,
        **strategy_kwargs
    ) -> pd.Series:
        """
        Perform walk-forward validation.

        Args:
            df: Price DataFrame
            strategy: Strategy function
            **strategy_kwargs: Strategy arguments

        Returns:
            Signal series (1=long, -1=short, 0=neutral)
        """
        signals = pd.Series(0, index=df.index)
        train_start = 0
        train_end = self.config.train_size

        while train_end + self.config.test_size <= len(df):
            # Define train/test periods
            test_end = min(train_end + self.config.test_size, len(df))

            train_data = df.iloc[train_start:train_end]
            test_data = df.iloc[train_end:test_end]

            # Generate signals for test period
            try:
                test_signals = strategy(train_data, test_data, **strategy_kwargs)

                # Ensure signals are valid
                if isinstance(test_signals, (pd.Series, np.ndarray, list)):
                    test_signals = pd.Series(test_signals, index=test_data.index)
                    signals.loc[test_data.index] = test_signals.clip(-1, 1)
                else:
                    logger.warning(f"Invalid signals returned by strategy at {test_data.index[0]}")

            except Exception as e:
                logger.warning(f"Strategy failed at {test_data.index[0]}: {e}")

            # Move window
            if self.config.validation_type == 'expanding':
                # Expanding window: train_start stays at 0
                train_end += self.config.step_size
            else:  # rolling
                # Rolling window: both move forward
                train_start += self.config.step_size
                train_end += self.config.step_size

        return signals

    def _calculate_returns(
        self,
        df: pd.DataFrame,
        signals: pd.Series
    ) -> pd.Series:
        """
        Calculate strategy returns with transaction costs.

        Args:
            df: Price DataFrame
            signals: Signal series

        Returns:
            Return series
        """
        # Calculate price returns
        price_returns = df['price'].pct_change()

        # Calculate strategy returns (signal * return)
        strategy_returns = signals.shift(1) * price_returns

        # Apply transaction costs
        position_changes = signals.diff().abs()
        transaction_costs = position_changes * self.config.transaction_cost
        slippage_costs = position_changes * self.config.slippage

        # Net returns
        net_returns = strategy_returns - transaction_costs - slippage_costs

        # Apply stop loss and take profit if configured
        if self.config.stop_loss is not None or self.config.take_profit is not None:
            net_returns = self._apply_risk_management(net_returns, signals)

        return net_returns.fillna(0)

    def _apply_risk_management(
        self,
        returns: pd.Series,
        signals: pd.Series
    ) -> pd.Series:
        """Apply stop loss and take profit rules."""
        # Track cumulative P&L for each trade
        managed_returns = returns.copy()
        in_position = False
        entry_price = 0
        cumulative_pnl = 0

        for i in range(len(returns)):
            if signals.iloc[i] != 0 and not in_position:
                # Enter position
                in_position = True
                entry_price = 0
                cumulative_pnl = 0

            if in_position:
                cumulative_pnl += returns.iloc[i]

                # Check stop loss
                if self.config.stop_loss and cumulative_pnl <= -self.config.stop_loss:
                    managed_returns.iloc[i] = -self.config.stop_loss - cumulative_pnl
                    in_position = False
                    cumulative_pnl = 0

                # Check take profit
                elif self.config.take_profit and cumulative_pnl >= self.config.take_profit:
                    managed_returns.iloc[i] = self.config.take_profit - cumulative_pnl
                    in_position = False
                    cumulative_pnl = 0

        return managed_returns

    def _calculate_metrics(
        self,
        returns: pd.Series,
        signals: pd.Series
    ) -> BacktestResult:
        """Calculate performance metrics."""
        # Cumulative returns
        cumulative_returns = (1 + returns).cumprod() - 1
        equity_curve = (1 + returns).cumprod()

        # Total return
        total_return = cumulative_returns.iloc[-1] if len(cumulative_returns) > 0 else 0

        # Annualized metrics
        n_periods = len(returns)
        years = n_periods / self.config.trading_days_per_year

        if years > 0:
            annualized_return = (1 + total_return) ** (1 / years) - 1
            annualized_volatility = returns.std() * np.sqrt(self.config.trading_days_per_year)
        else:
            annualized_return = 0
            annualized_volatility = 0

        # Sharpe ratio
        if annualized_volatility > 0:
            sharpe_ratio = (annualized_return - self.config.risk_free_rate) / annualized_volatility
        else:
            sharpe_ratio = 0

        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_std = downside_returns.std() * np.sqrt(self.config.trading_days_per_year)
            sortino_ratio = (annualized_return - self.config.risk_free_rate) / downside_std if downside_std > 0 else 0
        else:
            sortino_ratio = 0

        # Maximum drawdown
        running_max = equity_curve.cummax()
        drawdown = (equity_curve - running_max) / running_max
        max_drawdown = abs(drawdown.min()) if len(drawdown) > 0 else 0

        # Calmar ratio
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0

        # Drawdown duration
        is_drawdown = drawdown < 0
        if is_drawdown.any():
            drawdown_periods = is_drawdown.astype(int).groupby((~is_drawdown).cumsum()).sum()
            max_drawdown_duration = drawdown_periods.max() if len(drawdown_periods) > 0 else 0
        else:
            max_drawdown_duration = 0

        # VaR and CVaR
        var_95 = returns.quantile(0.05)
        cvar_95 = returns[returns <= var_95].mean() if len(returns[returns <= var_95]) > 0 else 0

        # Trade statistics
        position_changes = signals.diff().fillna(0)
        trade_entries = (position_changes != 0).sum()

        # Win rate
        winning_trades = (returns > 0).sum()
        losing_trades = (returns < 0).sum()
        total_trades = max(trade_entries, 1)  # Avoid division by zero

        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # Profit factor
        gross_profit = returns[returns > 0].sum()
        gross_loss = abs(returns[returns < 0].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Average win/loss
        avg_win = returns[returns > 0].mean() if winning_trades > 0 else 0
        avg_loss = returns[returns < 0].mean() if losing_trades > 0 else 0

        # Average trade duration
        in_trade = (signals != 0).astype(int)
        trade_durations = in_trade.groupby((in_trade != in_trade.shift()).cumsum()).sum()
        avg_trade_duration = trade_durations[trade_durations > 0].mean() if len(trade_durations[trade_durations > 0]) > 0 else 0

        return BacktestResult(
            returns=returns,
            cumulative_returns=cumulative_returns,
            equity_curve=equity_curve,
            total_return=float(total_return),
            annualized_return=float(annualized_return),
            annualized_volatility=float(annualized_volatility),
            sharpe_ratio=float(sharpe_ratio),
            sortino_ratio=float(sortino_ratio),
            calmar_ratio=float(calmar_ratio),
            max_drawdown=float(max_drawdown),
            max_drawdown_duration=int(max_drawdown_duration),
            var_95=float(var_95),
            cvar_95=float(cvar_95),
            n_trades=int(total_trades),
            win_rate=float(win_rate),
            profit_factor=float(profit_factor),
            avg_win=float(avg_win),
            avg_loss=float(avg_loss),
            avg_trade_duration=float(avg_trade_duration),
            config=self.config
        )

    def compare_strategies(
        self,
        prices: pd.Series,
        strategies: Dict[str, Callable],
        **strategy_kwargs
    ) -> pd.DataFrame:
        """
        Compare multiple strategies.

        Args:
            prices: Price time series
            strategies: Dictionary of strategy_name -> strategy_function
            **strategy_kwargs: Additional arguments for strategies

        Returns:
            DataFrame comparing strategy performance
        """
        results = {}

        for name, strategy in strategies.items():
            logger.info(f"Backtesting strategy: {name}")
            result = self.run(prices, strategy, **strategy_kwargs)
            results[name] = {
                'Total Return': result.total_return,
                'Ann. Return': result.annualized_return,
                'Ann. Volatility': result.annualized_volatility,
                'Sharpe Ratio': result.sharpe_ratio,
                'Sortino Ratio': result.sortino_ratio,
                'Calmar Ratio': result.calmar_ratio,
                'Max Drawdown': result.max_drawdown,
                'Win Rate': result.win_rate,
                'Profit Factor': result.profit_factor,
                'N Trades': result.n_trades
            }

        return pd.DataFrame(results).T

    def monte_carlo_simulation(
        self,
        prices: pd.Series,
        strategy: Callable,
        n_simulations: int = 1000,
        **strategy_kwargs
    ) -> Dict:
        """
        Run Monte Carlo simulation for robustness testing.

        Args:
            prices: Price time series
            strategy: Strategy function
            n_simulations: Number of simulations
            **strategy_kwargs: Strategy arguments

        Returns:
            Dictionary with simulation results
        """
        sharpe_ratios = []
        total_returns = []
        max_drawdowns = []

        for i in range(n_simulations):
            # Bootstrap resample
            bootstrap_prices = prices.sample(n=len(prices), replace=True).sort_index()

            try:
                result = self.run(bootstrap_prices, strategy, **strategy_kwargs)
                sharpe_ratios.append(result.sharpe_ratio)
                total_returns.append(result.total_return)
                max_drawdowns.append(result.max_drawdown)
            except Exception as e:
                logger.warning(f"Simulation {i} failed: {e}")

        return {
            'sharpe_ratios': sharpe_ratios,
            'total_returns': total_returns,
            'max_drawdowns': max_drawdowns,
            'sharpe_mean': np.mean(sharpe_ratios),
            'sharpe_std': np.std(sharpe_ratios),
            'sharpe_percentile_5': np.percentile(sharpe_ratios, 5),
            'sharpe_percentile_95': np.percentile(sharpe_ratios, 95),
            'return_mean': np.mean(total_returns),
            'return_percentile_5': np.percentile(total_returns, 5),
            'return_percentile_95': np.percentile(total_returns, 95)
        }


# Convenience function
def quick_backtest(
    prices: pd.Series,
    strategy: Callable,
    **kwargs
) -> BacktestResult:
    """
    Quick backtest with default configuration.

    Args:
        prices: Price time series
        strategy: Strategy function
        **kwargs: Additional arguments

    Returns:
        Backtest results

    Example:
        >>> def simple_strategy(train, test):
        ...     # Simple moving average crossover
        ...     return pd.Series(1, index=test.index)  # Always long
        >>> result = quick_backtest(prices, simple_strategy)
        >>> print(result.summary())
    """
    engine = BacktestEngine()
    return engine.run(prices, strategy, **kwargs)


if __name__ == "__main__":
    print("Example: Automated Backtesting")

    # Create synthetic price data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=1000, freq='D')
    returns = np.random.normal(0.0005, 0.02, 1000)
    prices = pd.Series(100 * (1 + returns).cumprod(), index=dates)

    # Define a simple strategy
    def moving_average_strategy(train_data, test_data):
        """Simple moving average crossover strategy."""
        # Calculate moving averages on training data to get parameters
        # Then apply to test data
        ma_short = train_data['price'].rolling(20).mean().iloc[-1]
        ma_long = train_data['price'].rolling(50).mean().iloc[-1]

        # Generate signals for test period
        if ma_short > ma_long:
            return pd.Series(1, index=test_data.index)  # Long
        else:
            return pd.Series(-1, index=test_data.index)  # Short

    # Run backtest
    print("Running backtest...")
    config = BacktestConfig(
        train_size=252,
        test_size=63,
        step_size=21,
        transaction_cost=0.001
    )

    engine = BacktestEngine(config)
    result = engine.run(prices, moving_average_strategy)

    # Print results
    print(result.summary())

    print("\n✅ Backtesting complete!")
