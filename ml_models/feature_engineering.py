"""
Feature Engineering for Stock Price Prediction
Extracts predictive features from politician trading data
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class PoliticianTradeFeatureExtractor:
    """Extract predictive features from politician trading activity"""

    def __init__(self, lookback_days: int = 30):
        """
        Initialize feature extractor

        Args:
            lookback_days: Days to look back for feature calculation
        """
        self.lookback_days = lookback_days

    def extract_features_for_ticker(
        self,
        ticker: str,
        trades: List[Dict[str, Any]],
        current_date: datetime,
        price_history: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """
        Extract all features for a single ticker at a given date

        Args:
            ticker: Stock ticker symbol
            trades: All politician trades
            current_date: Date to extract features for
            price_history: Optional price data for technical indicators

        Returns:
            Dictionary of feature name -> value
        """
        features = {}

        # Filter trades for this ticker and lookback window
        ticker_trades = self._filter_trades(ticker, trades, current_date)

        if len(ticker_trades) == 0:
            return self._get_zero_features()

        # 1. Volume features
        features.update(self._extract_volume_features(ticker_trades))

        # 2. Timing features
        features.update(self._extract_timing_features(ticker_trades, current_date))

        # 3. Consensus features
        features.update(self._extract_consensus_features(ticker_trades))

        # 4. Politician quality features
        features.update(self._extract_politician_features(ticker_trades))

        # 5. Trade direction features
        features.update(self._extract_direction_features(ticker_trades))

        # 6. Technical features (if price data available)
        if price_history is not None:
            features.update(self._extract_technical_features(price_history, current_date))

        # 7. Pattern features
        features.update(self._extract_pattern_features(ticker_trades))

        return features

    def _filter_trades(
        self,
        ticker: str,
        trades: List[Dict[str, Any]],
        current_date: datetime
    ) -> List[Dict[str, Any]]:
        """Filter trades for ticker within lookback window"""

        cutoff_date = current_date - timedelta(days=self.lookback_days)

        filtered = []
        for trade in trades:
            if trade.get('ticker', '').upper() != ticker.upper():
                continue

            trade_date_str = trade.get('transaction_date')
            if not trade_date_str:
                continue

            try:
                if isinstance(trade_date_str, str):
                    trade_date = datetime.fromisoformat(trade_date_str)
                elif isinstance(trade_date_str, datetime):
                    trade_date = trade_date_str
                else:
                    trade_date = datetime.combine(trade_date_str, datetime.min.time())

                if cutoff_date <= trade_date <= current_date:
                    filtered.append({**trade, 'parsed_date': trade_date})
            except:
                continue

        return sorted(filtered, key=lambda x: x['parsed_date'])

    def _extract_volume_features(self, trades: List[Dict]) -> Dict[str, float]:
        """Extract trade volume features"""

        features = {}

        # Total number of trades
        features['trade_count'] = float(len(trades))

        # Total trading volume (estimated)
        total_volume = 0
        for trade in trades:
            amt_min = trade.get('amount_min', 0)
            amt_max = trade.get('amount_max', 0)
            if amt_min and amt_max:
                avg_amount = (amt_min + amt_max) / 2
                total_volume += avg_amount

        features['total_volume'] = float(total_volume)
        features['avg_trade_size'] = total_volume / len(trades) if trades else 0.0

        # Volume trend (recent vs. older)
        if len(trades) >= 6:
            mid_point = len(trades) // 2
            recent_volume = sum(
                (t.get('amount_min', 0) + t.get('amount_max', 0)) / 2
                for t in trades[mid_point:]
            )
            older_volume = sum(
                (t.get('amount_min', 0) + t.get('amount_max', 0)) / 2
                for t in trades[:mid_point]
            )

            if older_volume > 0:
                features['volume_trend'] = (recent_volume - older_volume) / older_volume
            else:
                features['volume_trend'] = 1.0 if recent_volume > 0 else 0.0
        else:
            features['volume_trend'] = 0.0

        return features

    def _extract_timing_features(
        self,
        trades: List[Dict],
        current_date: datetime
    ) -> Dict[str, float]:
        """Extract timing-based features"""

        features = {}

        if not trades:
            return {
                'days_since_last_trade': float(self.lookback_days),
                'trade_frequency': 0.0,
                'recency_score': 0.0
            }

        # Days since most recent trade
        last_trade_date = trades[-1]['parsed_date']
        days_since = (current_date - last_trade_date).days
        features['days_since_last_trade'] = float(days_since)

        # Trading frequency (trades per day)
        date_range = (trades[-1]['parsed_date'] - trades[0]['parsed_date']).days
        if date_range > 0:
            features['trade_frequency'] = len(trades) / date_range
        else:
            features['trade_frequency'] = float(len(trades))

        # Recency score (exponentially weighted by recency)
        recency_score = 0.0
        for trade in trades:
            days_ago = (current_date - trade['parsed_date']).days
            weight = np.exp(-days_ago / 10)  # Decay with 10-day half-life
            recency_score += weight

        features['recency_score'] = float(recency_score)

        # Clustering score (are trades clustered or spread out?)
        if len(trades) >= 3:
            intervals = []
            for i in range(1, len(trades)):
                interval = (trades[i]['parsed_date'] - trades[i-1]['parsed_date']).days
                intervals.append(interval)

            avg_interval = np.mean(intervals)
            std_interval = np.std(intervals)

            # Low CV = clustered, High CV = spread out
            features['timing_clustering'] = (std_interval / avg_interval) if avg_interval > 0 else 0.0
        else:
            features['timing_clustering'] = 0.0

        return features

    def _extract_consensus_features(self, trades: List[Dict]) -> Dict[str, float]:
        """Extract consensus features (multiple politicians trading)"""

        features = {}

        # Number of unique politicians
        politicians = set(
            t.get('politician_name', t.get('politician', ''))
            for t in trades
        )
        features['num_politicians'] = float(len(politicians))

        # Consensus strength (multiple politicians in short window)
        # Check if 3+ politicians traded within 7 days
        consensus_windows = 0
        if len(trades) >= 3:
            for i in range(len(trades) - 2):
                window_start = trades[i]['parsed_date']
                window_end = window_start + timedelta(days=7)

                window_pols = set()
                for trade in trades[i:]:
                    if trade['parsed_date'] <= window_end:
                        pol = trade.get('politician_name', trade.get('politician', ''))
                        window_pols.add(pol)
                    else:
                        break

                if len(window_pols) >= 3:
                    consensus_windows += 1

        features['consensus_windows'] = float(consensus_windows)
        features['consensus_strength'] = float(consensus_windows) / max(1, len(trades) - 2)

        # Directional consensus (all buying or all selling?)
        buy_count = sum(
            1 for t in trades
            if 'purchase' in t.get('transaction_type', '').lower() or
               'buy' in t.get('transaction_type', '').lower()
        )
        sell_count = len(trades) - buy_count

        # Ratio from -1 (all selling) to +1 (all buying)
        if len(trades) > 0:
            features['directional_consensus'] = (buy_count - sell_count) / len(trades)
        else:
            features['directional_consensus'] = 0.0

        return features

    def _extract_politician_features(self, trades: List[Dict]) -> Dict[str, float]:
        """Extract features about politician quality/performance"""

        features = {}

        # TODO: In production, this would use historical performance data
        # For now, use placeholder based on activity

        # Average "importance" based on trade size
        avg_importance = 0.0
        for trade in trades:
            amt_min = trade.get('amount_min', 0)
            amt_max = trade.get('amount_max', 0)

            if amt_min and amt_max:
                avg_amt = (amt_min + amt_max) / 2
                # Normalize to 0-1 scale (assuming $1M is very important)
                importance = min(avg_amt / 1000000, 1.0)
                avg_importance += importance

        features['avg_politician_importance'] = avg_importance / len(trades) if trades else 0.0

        # Party diversity (cross-party agreement is stronger signal)
        parties = set(t.get('party', 'Unknown') for t in trades)
        features['party_diversity'] = float(len(parties)) / len(trades) if trades else 0.0

        # Chamber diversity (Senate + House agreement)
        chambers = set(t.get('chamber', 'Unknown') for t in trades)
        features['chamber_diversity'] = float(len(chambers)) / len(trades) if trades else 0.0

        return features

    def _extract_direction_features(self, trades: List[Dict]) -> Dict[str, float]:
        """Extract buy/sell direction features"""

        features = {}

        if not trades:
            return {
                'buy_ratio': 0.5,
                'buy_volume_ratio': 0.5,
                'recent_buy_bias': 0.0
            }

        # Overall buy/sell ratio
        buy_count = sum(
            1 for t in trades
            if 'purchase' in t.get('transaction_type', '').lower() or
               'buy' in t.get('transaction_type', '').lower()
        )

        features['buy_ratio'] = buy_count / len(trades)

        # Volume-weighted buy ratio
        buy_volume = 0.0
        total_volume = 0.0

        for trade in trades:
            amt_min = trade.get('amount_min', 0)
            amt_max = trade.get('amount_max', 0)

            if amt_min and amt_max:
                avg_amt = (amt_min + amt_max) / 2
                total_volume += avg_amt

                if 'purchase' in trade.get('transaction_type', '').lower() or \
                   'buy' in trade.get('transaction_type', '').lower():
                    buy_volume += avg_amt

        features['buy_volume_ratio'] = buy_volume / total_volume if total_volume > 0 else 0.5

        # Recent buy bias (last 1/3 of trades)
        if len(trades) >= 3:
            recent_start = int(len(trades) * 2 / 3)
            recent_trades = trades[recent_start:]

            recent_buys = sum(
                1 for t in recent_trades
                if 'purchase' in t.get('transaction_type', '').lower() or
                   'buy' in t.get('transaction_type', '').lower()
            )

            features['recent_buy_bias'] = recent_buys / len(recent_trades) - 0.5
        else:
            features['recent_buy_bias'] = features['buy_ratio'] - 0.5

        return features

    def _extract_technical_features(
        self,
        price_df: pd.DataFrame,
        current_date: datetime
    ) -> Dict[str, float]:
        """Extract technical indicator features from price data"""

        features = {}

        try:
            # Get price data up to current_date
            if price_df.empty:
                return self._get_zero_technical_features()

            # Filter to dates before current_date
            mask = price_df.index <= current_date.strftime('%Y-%m-%d')
            recent_prices = price_df[mask].tail(50)  # Last 50 days

            if len(recent_prices) < 10:
                return self._get_zero_technical_features()

            closes = recent_prices['close'].values

            # 1. Moving averages
            if len(closes) >= 20:
                ma_20 = np.mean(closes[-20:])
                features['price_vs_ma20'] = (closes[-1] - ma_20) / ma_20
            else:
                features['price_vs_ma20'] = 0.0

            # 2. Momentum (20-day return)
            if len(closes) >= 20:
                features['momentum_20d'] = (closes[-1] - closes[-20]) / closes[-20]
            else:
                features['momentum_20d'] = 0.0

            # 3. Volatility (20-day std of returns)
            if len(closes) >= 20:
                returns = np.diff(closes[-20:]) / closes[-20:-1]
                features['volatility_20d'] = float(np.std(returns))
            else:
                features['volatility_20d'] = 0.0

            # 4. RSI (Relative Strength Index)
            if len(closes) >= 14:
                deltas = np.diff(closes[-15:])
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)

                avg_gain = np.mean(gains)
                avg_loss = np.mean(losses)

                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    features['rsi'] = float(rsi) / 100  # Normalize to 0-1
                else:
                    features['rsi'] = 1.0
            else:
                features['rsi'] = 0.5

            # 5. Price trend (linear regression slope)
            if len(closes) >= 20:
                x = np.arange(20)
                y = closes[-20:]
                slope = np.polyfit(x, y, 1)[0]
                features['price_trend'] = slope / closes[-1]  # Normalized
            else:
                features['price_trend'] = 0.0

        except Exception as e:
            logger.warning(f"Error extracting technical features: {e}")
            return self._get_zero_technical_features()

        return features

    def _extract_pattern_features(self, trades: List[Dict]) -> Dict[str, float]:
        """Extract pattern-based features"""

        features = {}

        if len(trades) < 2:
            return {'pattern_strength': 0.0}

        # Burst pattern: Are trades clustered in time?
        intervals = []
        for i in range(1, len(trades)):
            interval = (trades[i]['parsed_date'] - trades[i-1]['parsed_date']).days
            intervals.append(interval)

        if intervals:
            avg_interval = np.mean(intervals)
            # Short intervals = burst pattern
            burst_score = max(0, 1 - (avg_interval / 30))  # 30 days = no burst
            features['burst_pattern'] = float(burst_score)
        else:
            features['burst_pattern'] = 0.0

        # Synchronized pattern: Multiple politicians on same day?
        date_counts = defaultdict(int)
        for trade in trades:
            date_key = trade['parsed_date'].strftime('%Y-%m-%d')
            date_counts[date_key] += 1

        max_same_day = max(date_counts.values()) if date_counts else 1
        features['synchronization'] = float(max_same_day) / len(trades)

        # Overall pattern strength (combination)
        features['pattern_strength'] = (features['burst_pattern'] + features['synchronization']) / 2

        return features

    def _get_zero_features(self) -> Dict[str, float]:
        """Return all features with zero values"""
        return {
            # Volume
            'trade_count': 0.0,
            'total_volume': 0.0,
            'avg_trade_size': 0.0,
            'volume_trend': 0.0,

            # Timing
            'days_since_last_trade': float(self.lookback_days),
            'trade_frequency': 0.0,
            'recency_score': 0.0,
            'timing_clustering': 0.0,

            # Consensus
            'num_politicians': 0.0,
            'consensus_windows': 0.0,
            'consensus_strength': 0.0,
            'directional_consensus': 0.0,

            # Politician quality
            'avg_politician_importance': 0.0,
            'party_diversity': 0.0,
            'chamber_diversity': 0.0,

            # Direction
            'buy_ratio': 0.5,
            'buy_volume_ratio': 0.5,
            'recent_buy_bias': 0.0,

            # Patterns
            'burst_pattern': 0.0,
            'synchronization': 0.0,
            'pattern_strength': 0.0,

            # Technical (if available)
            **self._get_zero_technical_features()
        }

    def _get_zero_technical_features(self) -> Dict[str, float]:
        """Return technical features with neutral values"""
        return {
            'price_vs_ma20': 0.0,
            'momentum_20d': 0.0,
            'volatility_20d': 0.0,
            'rsi': 0.5,
            'price_trend': 0.0
        }

    def get_feature_names(self) -> List[str]:
        """Get list of all feature names"""
        return list(self._get_zero_features().keys())


__all__ = ['PoliticianTradeFeatureExtractor']
