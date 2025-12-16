"""
ML Prediction-Based Trading Strategy
Uses trained ML models to generate trading signals
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd

from services.prediction_service import PredictionService

logger = logging.getLogger(__name__)


class MLPredictionStrategy:
    """
    Trading strategy based on ML price predictions

    Strategy:
    1. Use ML models to predict stock price direction
    2. Buy stocks predicted to go UP (with high confidence)
    3. Sell after holding period or when prediction changes
    4. Only trade on high-confidence predictions
    """

    def __init__(
        self,
        hold_days: int = 30,
        confidence_threshold: float = 0.5,
        max_positions: int = 10,
        position_size_pct: float = 0.1,
        model_dir: str = 'data/models'
    ):
        """
        Initialize ML prediction strategy

        Args:
            hold_days: Days to hold positions
            confidence_threshold: Minimum prediction confidence (0-1)
            max_positions: Maximum concurrent positions
            position_size_pct: Position size as % of capital
            model_dir: Directory with trained models
        """
        self.hold_days = hold_days
        self.confidence_threshold = confidence_threshold
        self.max_positions = max_positions
        self.position_size_pct = position_size_pct

        # Initialize prediction service
        self.prediction_service = PredictionService(model_dir=model_dir)

        # Track open positions and entry dates
        self.positions = {}  # ticker -> entry_date

    def generate_signals(
        self,
        trades: List[Dict],
        price_data: Dict[str, pd.DataFrame],
        current_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Generate trading signals for a given date

        Args:
            trades: All politician trades
            price_data: Price history
            current_date: Current backtest date

        Returns:
            List of trading signals (buy/sell)
        """
        signals = []

        # 1. Check if we should close any positions (holding period expired)
        positions_to_close = []
        for ticker, entry_date in list(self.positions.items()):
            days_held = (current_date - entry_date).days

            if days_held >= self.hold_days:
                positions_to_close.append(ticker)

        # Generate sell signals for expired positions
        for ticker in positions_to_close:
            signals.append({
                'ticker': ticker,
                'action': 'sell',
                'quantity': 999999,  # Sell all (backtest engine will limit to actual position)
                'reason': 'holding_period_expired',
                'signal_strength': 1.0
            })

            # Remove from tracking
            del self.positions[ticker]

        # 2. If we have capacity, look for new buy opportunities
        if len(self.positions) < self.max_positions:
            # Get predictions for stocks with recent politician activity
            predictions = self.prediction_service.predict_from_politician_activity(
                trades=trades,
                current_date=current_date,
                price_data=price_data,
                lookback_days=30,
                min_trade_count=2,
                min_confidence=self.confidence_threshold,
                top_n=self.max_positions * 2  # Get more than we need
            )

            # Filter predictions
            buy_candidates = []
            for pred in predictions:
                # Only buy if:
                # 1. Prediction is UP
                # 2. Not already holding
                # 3. Meets confidence threshold

                if pred['prediction'] != 'UP':
                    continue

                if pred['ticker'] in self.positions:
                    continue

                if pred['confidence'] < self.confidence_threshold:
                    continue

                buy_candidates.append(pred)

            # Sort by confidence and take top N
            buy_candidates.sort(key=lambda x: x['confidence'], reverse=True)

            slots_available = self.max_positions - len(self.positions)
            new_positions = buy_candidates[:slots_available]

            # Generate buy signals
            for pred in new_positions:
                ticker = pred['ticker']

                # Calculate quantity based on position size %
                # This is handled by backtest engine, we just signal intent
                signals.append({
                    'ticker': ticker,
                    'action': 'buy',
                    'quantity': 1,  # Backtest engine will calculate based on position_size_pct
                    'politician': 'ML_Model',
                    'signal_strength': pred['confidence'],
                    'metadata': {
                        'prediction': pred['prediction'],
                        'confidence': pred['confidence'],
                        'probability_up': pred['probability_up'],
                        'model': 'ML_Ensemble'
                    }
                })

                # Track position
                self.positions[ticker] = current_date

        return signals


class AdaptivePredictionStrategy(MLPredictionStrategy):
    """
    Adaptive version that adjusts confidence threshold based on performance

    Increases threshold if losing, decreases if winning
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.initial_threshold = self.confidence_threshold
        self.recent_results = []  # Track recent trade outcomes
        self.lookback_trades = 20

    def adjust_threshold(self):
        """Adjust confidence threshold based on recent performance"""

        if len(self.recent_results) < 10:
            return  # Need minimum history

        recent = self.recent_results[-self.lookback_trades:]
        win_rate = sum(recent) / len(recent)

        # If win rate < 45%, increase threshold (be more selective)
        if win_rate < 0.45:
            self.confidence_threshold = min(0.9, self.confidence_threshold + 0.05)
            logger.info(f"Increasing confidence threshold to {self.confidence_threshold:.2f}")

        # If win rate > 60%, decrease threshold (be more aggressive)
        elif win_rate > 0.60:
            self.confidence_threshold = max(self.initial_threshold, self.confidence_threshold - 0.05)
            logger.info(f"Decreasing confidence threshold to {self.confidence_threshold:.2f}")

    def record_trade_result(self, won: bool):
        """Record outcome of a completed trade"""
        self.recent_results.append(1 if won else 0)

        # Periodically adjust
        if len(self.recent_results) % 10 == 0:
            self.adjust_threshold()


class ConsensusBoostStrategy(MLPredictionStrategy):
    """
    Boosts position size when ML prediction agrees with politician consensus

    Combines:
    - ML model predictions
    - Politician consensus signals
    - Position sizing based on agreement strength
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.consensus_boost_multiplier = 1.5

    def generate_signals(
        self,
        trades: List[Dict],
        price_data: Dict[str, pd.DataFrame],
        current_date: datetime
    ) -> List[Dict[str, Any]]:
        """Generate signals with consensus boost"""

        # Get base signals from parent
        signals = super().generate_signals(trades, price_data, current_date)

        # Enhance buy signals with consensus info
        for signal in signals:
            if signal['action'] != 'buy':
                continue

            ticker = signal['ticker']

            # Get recent trades for this ticker
            recent_trades = []
            cutoff = current_date - timedelta(days=30)

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
                        continue

                    if cutoff <= trade_date <= current_date:
                        recent_trades.append(trade)

                except:
                    continue

            # Calculate consensus
            if len(recent_trades) >= 3:
                # Count unique politicians
                politicians = set(
                    t.get('politician_name', t.get('politician', ''))
                    for t in recent_trades
                )

                # Count buy vs sell
                buys = sum(
                    1 for t in recent_trades
                    if 'purchase' in t.get('transaction_type', '').lower() or
                       'buy' in t.get('transaction_type', '').lower()
                )

                buy_ratio = buys / len(recent_trades) if recent_trades else 0

                # Boost if strong consensus
                if len(politicians) >= 3 and buy_ratio > 0.7:
                    signal['signal_strength'] *= self.consensus_boost_multiplier
                    signal['metadata']['consensus_boost'] = True
                    signal['metadata']['num_politicians'] = len(politicians)
                    signal['metadata']['buy_ratio'] = buy_ratio

        return signals


__all__ = [
    'MLPredictionStrategy',
    'AdaptivePredictionStrategy',
    'ConsensusBoostStrategy'
]
