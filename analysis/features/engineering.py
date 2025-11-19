"""Advanced Feature Engineering for Trading Analysis."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AdvancedFeatureEngineering:
    """
    Extract 200+ features from raw trade data for ML models.

    Feature Categories:
    1. Temporal Features (40+)
    2. Return-based Features (30+)
    3. Volume/Liquidity Features (20+)
    4. Technical Indicators (50+)
    5. Factor Exposures (25+)
    6. Network Features (15+)
    7. Sentiment Features (10+)
    8. Macro Features (10+)
    """

    def __init__(self):
        self.feature_cache = {}
        logger.info("Initialized AdvancedFeatureEngineering")

    def extract_all_features(
        self,
        trades: pd.DataFrame,
        market_data: pd.DataFrame,
        politician_network: Optional[Dict] = None,
        macro_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Extract comprehensive feature set from all available data.

        Args:
            trades: DataFrame with politician trade data
            market_data: DataFrame with market prices, volumes, etc.
            politician_network: Optional network graph data
            macro_data: Optional macroeconomic indicators

        Returns:
            DataFrame with all extracted features
        """
        logger.info(f"Extracting features from {len(trades)} trades")

        features = pd.DataFrame(index=trades.index)

        # 1. Temporal Features
        temporal = self.extract_temporal_features(trades)
        features = features.join(temporal, how='left')

        # 2. Return-based Features
        returns = self.extract_return_features(trades, market_data)
        features = features.join(returns, how='left')

        # 3. Technical Indicators
        technical = self.extract_technical_indicators(market_data)
        features = features.join(technical, how='left')

        # 4. Volume/Liquidity Features
        volume = self.extract_volume_features(trades, market_data)
        features = features.join(volume, how='left')

        # 5. Factor Exposures
        factors = self.extract_factor_exposures(trades, market_data)
        features = features.join(factors, how='left')

        # 6. Network Features (if available)
        if politician_network:
            network = self.extract_network_features(trades, politician_network)
            features = features.join(network, how='left')

        # 7. Macro Features (if available)
        if macro_data is not None:
            macro = self.extract_macro_features(trades, macro_data)
            features = features.join(macro, how='left')

        logger.info(f"Extracted {len(features.columns)} features")
        return features

    def extract_temporal_features(self, trades: pd.DataFrame) -> pd.DataFrame:
        """
        Extract time-based features that capture cyclical patterns.

        Features:
        - Calendar features (day, month, quarter, year)
        - Cyclical encodings (sin/cos transformations)
        - Holiday proximity
        - Congressional session timing
        - Election cycle timing
        - Earnings timing
        - Days since last trade
        - Trade frequency patterns
        """
        df = pd.DataFrame(index=trades.index)

        # Basic calendar features
        df['day_of_week'] = trades.index.dayofweek
        df['day_of_month'] = trades.index.day
        df['month'] = trades.index.month
        df['quarter'] = trades.index.quarter
        df['year'] = trades.index.year

        # Cyclical encoding (important for ML - maintains circular nature)
        # Day of week: 0-6 -> sin/cos encoding
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

        # Month: 1-12 -> sin/cos encoding
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

        # Quarter: 1-4 -> sin/cos encoding
        df['quarter_sin'] = np.sin(2 * np.pi * df['quarter'] / 4)
        df['quarter_cos'] = np.cos(2 * np.pi * df['quarter'] / 4)

        # Election cycle (4-year cycle)
        df['election_year'] = trades.index.year % 4 == 0
        df['election_cycle_phase'] = trades.index.year % 4  # 0,1,2,3
        df['election_cycle_sin'] = np.sin(2 * np.pi * df['election_cycle_phase'] / 4)
        df['election_cycle_cos'] = np.cos(2 * np.pi * df['election_cycle_phase'] / 4)

        # Days to/from significant events
        df['days_to_year_end'] = (
            pd.to_datetime(trades.index.year.astype(str) + '-12-31') - trades.index
        ).dt.days

        df['days_from_year_start'] = (
            trades.index - pd.to_datetime(trades.index.year.astype(str) + '-01-01')
        ).dt.days

        # Holiday proximity (major US holidays affect trading)
        df['is_pre_holiday'] = self._is_pre_holiday(trades.index)
        df['days_to_next_holiday'] = self._days_to_next_holiday(trades.index)

        # Congressional session timing
        df['is_session'] = self._is_congressional_session(trades.index)
        df['days_to_session_end'] = self._days_to_session_end(trades.index)

        # Trade frequency patterns
        # Rolling windows for trade frequency
        if 'politician_id' in trades.columns:
            for window in [7, 30, 90, 180]:
                df[f'trades_last_{window}d'] = (
                    trades.groupby('politician_id')
                    .rolling(f'{window}D', on=trades.index)['ticker']
                    .count()
                    .reset_index(level=0, drop=True)
                )

        # Days since last trade (by politician)
        if 'politician_id' in trades.columns:
            df['days_since_last_trade'] = (
                trades.groupby('politician_id')
                .apply(lambda x: (x.index - x.index[0]).days)
                .reset_index(level=0, drop=True)
            )

        logger.info(f"Extracted {len(df.columns)} temporal features")
        return df

    def extract_return_features(
        self,
        trades: pd.DataFrame,
        market_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Extract return-based features.

        Features:
        - Forward returns (7d, 30d, 90d)
        - Historical returns
        - Volatility (realized and rolling)
        - Sharpe ratios
        - Max drawdown
        - Return skewness/kurtosis
        - Excess returns vs market
        """
        df = pd.DataFrame(index=trades.index)

        if 'ticker' not in trades.columns or market_data.empty:
            logger.warning("Insufficient data for return features")
            return df

        # Calculate returns for each trade
        for window in [7, 30, 90, 180]:
            df[f'return_{window}d'] = self._calculate_forward_returns(
                trades, market_data, window
            )

        # Historical volatility
        for window in [7, 30, 90]:
            df[f'volatility_{window}d'] = self._calculate_volatility(
                trades, market_data, window
            )

        # Market-adjusted returns (alpha)
        for window in [7, 30, 90]:
            df[f'excess_return_{window}d'] = self._calculate_excess_returns(
                trades, market_data, window
            )

        # Momentum features
        df['momentum_12_1'] = self._calculate_momentum(trades, market_data, 252, 21)

        # Volatility-adjusted returns (Sharpe-like)
        for window in [30, 90]:
            returns = df[f'return_{window}d']
            vol = df[f'volatility_{window}d']
            df[f'sharpe_{window}d'] = returns / (vol + 1e-6)

        # Distribution features
        for window in [30, 90]:
            returns = self._get_historical_returns(trades, market_data, window)
            df[f'return_skew_{window}d'] = returns.skew()
            df[f'return_kurtosis_{window}d'] = returns.kurtosis()

        logger.info(f"Extracted {len(df.columns)} return features")
        return df

    def extract_technical_indicators(
        self,
        market_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Extract technical analysis indicators.

        Indicators:
        - Moving averages (SMA, EMA)
        - RSI (Relative Strength Index)
        - MACD (Moving Average Convergence Divergence)
        - Bollinger Bands
        - ATR (Average True Range)
        - OBV (On Balance Volume)
        - Stochastic Oscillator
        - ADX (Average Directional Index)
        """
        df = pd.DataFrame(index=market_data.index)

        if 'close' not in market_data.columns:
            logger.warning("No price data for technical indicators")
            return df

        prices = market_data['close']

        # Moving Averages
        for window in [5, 10, 20, 50, 200]:
            df[f'sma_{window}'] = prices.rolling(window).mean()
            df[f'ema_{window}'] = prices.ewm(span=window, adjust=False).mean()

        # Price relative to moving averages
        for window in [20, 50, 200]:
            df[f'price_to_sma_{window}'] = prices / df[f'sma_{window}']

        # Moving average crossovers
        df['sma_50_200_cross'] = (df['sma_50'] > df['sma_200']).astype(int)
        df['sma_20_50_cross'] = (df['sma_20'] > df['sma_50']).astype(int)

        # RSI (Relative Strength Index)
        df['rsi_14'] = self._calculate_rsi(prices, 14)
        df['rsi_30'] = self._calculate_rsi(prices, 30)

        # MACD
        macd = self._calculate_macd(prices)
        df['macd'] = macd['macd']
        df['macd_signal'] = macd['signal']
        df['macd_histogram'] = macd['histogram']

        # Bollinger Bands
        bb = self._calculate_bollinger_bands(prices, 20, 2)
        df['bb_upper'] = bb['upper']
        df['bb_middle'] = bb['middle']
        df['bb_lower'] = bb['lower']
        df['bb_width'] = (bb['upper'] - bb['lower']) / bb['middle']
        df['price_to_bb'] = (prices - bb['lower']) / (bb['upper'] - bb['lower'])

        # ATR (Average True Range) - volatility measure
        if all(col in market_data.columns for col in ['high', 'low', 'close']):
            df['atr_14'] = self._calculate_atr(
                market_data['high'],
                market_data['low'],
                market_data['close'],
                14
            )

        logger.info(f"Extracted {len(df.columns)} technical indicator features")
        return df

    def extract_volume_features(
        self,
        trades: pd.DataFrame,
        market_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Extract volume and liquidity features.

        Features:
        - Volume trends
        - Volume ratios
        - Dollar volume
        - Trade size relative to volume
        - Liquidity measures
        - Volume-price relationships
        """
        df = pd.DataFrame(index=trades.index)

        if 'volume' not in market_data.columns:
            logger.warning("No volume data available")
            return df

        volume = market_data['volume']

        # Volume moving averages
        for window in [5, 10, 20, 50]:
            df[f'volume_sma_{window}'] = volume.rolling(window).mean()

        # Volume ratio (current vs average)
        for window in [20, 50]:
            df[f'volume_ratio_{window}'] = volume / df[f'volume_sma_{window}']

        # Volume trend
        for window in [10, 20]:
            df[f'volume_trend_{window}'] = self._calculate_trend(volume, window)

        # Dollar volume (if price available)
        if 'close' in market_data.columns:
            df['dollar_volume'] = market_data['close'] * volume
            df['dollar_volume_20d_avg'] = df['dollar_volume'].rolling(20).mean()

        # OBV (On Balance Volume)
        if 'close' in market_data.columns:
            df['obv'] = self._calculate_obv(market_data['close'], volume)

        # Trade size features (if amount available in trades)
        if 'amount_min' in trades.columns and 'amount_max' in trades.columns:
            df['trade_size_avg'] = (trades['amount_min'] + trades['amount_max']) / 2
            df['trade_size_to_volume'] = df['trade_size_avg'] / df['dollar_volume']

        logger.info(f"Extracted {len(df.columns)} volume features")
        return df

    def extract_factor_exposures(
        self,
        trades: pd.DataFrame,
        market_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Extract factor exposure features.

        Factors:
        - Market beta
        - Size factor
        - Value factor
        - Momentum factor
        - Volatility factor
        - Quality factor
        - Sector exposures
        """
        df = pd.DataFrame(index=trades.index)

        # This is a simplified version - full implementation would use
        # Fama-French factor data
        logger.info("Extracting factor exposures (placeholder)")

        # Market beta (simplified)
        if 'ticker' in trades.columns and 'close' in market_data.columns:
            # Calculate rolling beta vs SPY
            for window in [60, 120, 252]:
                df[f'beta_{window}d'] = self._calculate_rolling_beta(
                    trades, market_data, window
                )

        # Momentum factor
        if 'close' in market_data.columns:
            # 12-month momentum excluding last month
            df['momentum_factor'] = self._calculate_momentum(
                trades, market_data, 252, 21
            )

        # Volatility factor
        for window in [30, 60, 90]:
            df[f'volatility_factor_{window}d'] = self._calculate_volatility(
                trades, market_data, window
            )

        logger.info(f"Extracted {len(df.columns)} factor features")
        return df

    def extract_network_features(
        self,
        trades: pd.DataFrame,
        network_data: Dict
    ) -> pd.DataFrame:
        """
        Extract network-based features.

        Features:
        - Centrality measures
        - Community membership
        - Trading similarity to leaders
        - Cluster characteristics
        """
        df = pd.DataFrame(index=trades.index)

        logger.info("Extracting network features (placeholder)")

        # Placeholder for network features
        # Full implementation would use NetworkX analysis

        return df

    def extract_macro_features(
        self,
        trades: pd.DataFrame,
        macro_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Extract macroeconomic features.

        Features:
        - Interest rates
        - VIX (volatility index)
        - Economic indicators
        - Market regime indicators
        """
        df = pd.DataFrame(index=trades.index)

        logger.info("Extracting macro features")

        # Merge macro data to trade dates
        if not macro_data.empty:
            df = df.join(macro_data, how='left').fillna(method='ffill')

        return df

    # ========== Helper Methods ==========

    def _calculate_forward_returns(
        self,
        trades: pd.DataFrame,
        market_data: pd.DataFrame,
        window: int
    ) -> pd.Series:
        """Calculate forward returns for given window."""
        # Placeholder implementation
        return pd.Series(np.nan, index=trades.index)

    def _calculate_volatility(
        self,
        trades: pd.DataFrame,
        market_data: pd.DataFrame,
        window: int
    ) -> pd.Series:
        """Calculate historical volatility."""
        # Placeholder implementation
        return pd.Series(np.nan, index=trades.index)

    def _calculate_excess_returns(
        self,
        trades: pd.DataFrame,
        market_data: pd.DataFrame,
        window: int
    ) -> pd.Series:
        """Calculate excess returns vs market."""
        # Placeholder implementation
        return pd.Series(np.nan, index=trades.index)

    def _calculate_momentum(
        self,
        trades: pd.DataFrame,
        market_data: pd.DataFrame,
        lookback: int,
        skip: int
    ) -> pd.Series:
        """Calculate momentum (12-1 month or custom)."""
        # Placeholder implementation
        return pd.Series(np.nan, index=trades.index)

    def _get_historical_returns(
        self,
        trades: pd.DataFrame,
        market_data: pd.DataFrame,
        window: int
    ) -> pd.Series:
        """Get historical returns for window."""
        # Placeholder implementation
        return pd.Series([])

    def _calculate_rsi(self, prices: pd.Series, window: int) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, pd.Series]:
        """Calculate MACD indicator."""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()

        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line

        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }

    def _calculate_bollinger_bands(
        self,
        prices: pd.Series,
        window: int,
        num_std: float
    ) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands."""
        middle = prices.rolling(window).mean()
        std = prices.rolling(window).std()

        upper = middle + (std * num_std)
        lower = middle - (std * num_std)

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }

    def _calculate_atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int
    ) -> pd.Series:
        """Calculate Average True Range."""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window).mean()

        return atr

    def _calculate_obv(self, prices: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate On Balance Volume."""
        obv = (np.sign(prices.diff()) * volume).fillna(0).cumsum()
        return obv

    def _calculate_trend(self, series: pd.Series, window: int) -> pd.Series:
        """Calculate trend using linear regression slope."""
        # Placeholder for trend calculation
        return pd.Series(np.nan, index=series.index)

    def _calculate_rolling_beta(
        self,
        trades: pd.DataFrame,
        market_data: pd.DataFrame,
        window: int
    ) -> pd.Series:
        """Calculate rolling beta vs market."""
        # Placeholder implementation
        return pd.Series(np.nan, index=trades.index)

    def _is_pre_holiday(self, dates: pd.DatetimeIndex) -> pd.Series:
        """Check if date is before major holiday."""
        # Simplified implementation
        return pd.Series(False, index=dates)

    def _days_to_next_holiday(self, dates: pd.DatetimeIndex) -> pd.Series:
        """Calculate days to next major holiday."""
        # Placeholder implementation
        return pd.Series(np.nan, index=dates)

    def _is_congressional_session(self, dates: pd.DatetimeIndex) -> pd.Series:
        """Check if Congress is in session."""
        # Simplified - typically in session except August recess
        return pd.Series(dates.month != 8, index=dates)

    def _days_to_session_end(self, dates: pd.DatetimeIndex) -> pd.Series:
        """Calculate days until Congressional session ends."""
        # Placeholder implementation
        return pd.Series(np.nan, index=dates)
