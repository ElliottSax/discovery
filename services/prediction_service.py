"""
Stock Prediction Service
Coordinates distributed prediction across workers
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

# Import predictors
from ml_models.stock_predictor import StockPricePredictor, BaselinePredictor
from ml_models.feature_engineering import PoliticianTradeFeatureExtractor

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Centralized prediction service

    Handles:
    - Model training
    - Batch predictions
    - Result caching
    - Worker coordination (future)
    """

    def __init__(
        self,
        model_dir: str = 'data/models',
        use_distributed: bool = False
    ):
        """
        Initialize prediction service

        Args:
            model_dir: Directory for model storage
            use_distributed: Whether to use distributed workers
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.use_distributed = use_distributed

        # Initialize predictor
        try:
            self.predictor = StockPricePredictor(
                prediction_horizon_days=30,
                model_dir=str(self.model_dir)
            )
            logger.info("Initialized StockPricePredictor")

            # Try to load existing models
            if not self.predictor.load_models():
                logger.warning("No pre-trained models found - will need to train first")

        except Exception as e:
            logger.warning(f"Could not initialize ML predictor: {e}")
            logger.info("Falling back to BaselinePredictor")
            self.predictor = BaselinePredictor()

        self.prediction_cache = {}

    def train_models(
        self,
        trades: List[Dict[str, Any]],
        price_data: Dict[str, pd.DataFrame],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        save_models: bool = True
    ) -> Dict[str, Any]:
        """
        Train prediction models

        Args:
            trades: Historical politician trades
            price_data: Historical price data
            start_date: Training start (default: 2 years ago)
            end_date: Training end (default: 6 months ago)
            save_models: Whether to save after training

        Returns:
            Training metrics
        """
        logger.info("Training prediction models...")

        # Check if predictor supports training
        if isinstance(self.predictor, BaselinePredictor):
            logger.warning("BaselinePredictor doesn't require training")
            return {'status': 'baseline_model', 'message': 'No training needed'}

        # Default date range
        if not start_date:
            start_date = datetime.now() - timedelta(days=730)  # 2 years

        if not end_date:
            end_date = datetime.now() - timedelta(days=180)  # 6 months ago

        # Prepare training data
        X, y, tickers = self.predictor.prepare_training_data(
            trades,
            price_data,
            start_date,
            end_date
        )

        if len(X) == 0:
            logger.error("No training data generated")
            return {'status': 'error', 'message': 'No training data'}

        # Train
        accuracies = self.predictor.train(X, y, validation_split=0.2)

        # Save if requested
        if save_models:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.predictor.save_models(suffix=f'_{timestamp}')
            self.predictor.save_models(suffix='_latest')  # Also save as latest

        results = {
            'status': 'success',
            'training_samples': int(len(X)),
            'positive_ratio': float(sum(y) / len(y)),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'model_accuracies': accuracies,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Training complete: {len(X)} samples, accuracies: {accuracies}")

        return results

    def predict_ticker(
        self,
        ticker: str,
        trades: List[Dict[str, Any]],
        current_date: Optional[datetime] = None,
        price_history: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Predict price direction for a single ticker

        Args:
            ticker: Stock ticker symbol
            trades: All politician trades
            current_date: Date to predict from (default: today)
            price_history: Historical price data

        Returns:
            Prediction dictionary
        """
        if current_date is None:
            current_date = datetime.now()

        # Check cache
        cache_key = f"{ticker}_{current_date.strftime('%Y-%m-%d')}"
        if cache_key in self.prediction_cache:
            logger.debug(f"Returning cached prediction for {cache_key}")
            return self.prediction_cache[cache_key]

        # Make prediction
        prediction = self.predictor.predict(
            ticker,
            trades,
            current_date,
            price_history
        )

        # Cache result
        self.prediction_cache[cache_key] = prediction

        return prediction

    def predict_batch(
        self,
        tickers: List[str],
        trades: List[Dict[str, Any]],
        current_date: Optional[datetime] = None,
        price_data: Optional[Dict[str, pd.DataFrame]] = None,
        min_confidence: float = 0.0,
        top_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Predict for multiple tickers

        Args:
            tickers: List of ticker symbols
            trades: All politician trades
            current_date: Prediction date (default: today)
            price_data: Price history by ticker
            min_confidence: Minimum confidence threshold
            top_n: Return only top N predictions

        Returns:
            List of predictions sorted by confidence
        """
        if current_date is None:
            current_date = datetime.now()

        if price_data is None:
            price_data = {}

        logger.info(f"Predicting for {len(tickers)} tickers")

        predictions = []

        for ticker in tickers:
            try:
                price_history = price_data.get(ticker)

                prediction = self.predict_ticker(
                    ticker,
                    trades,
                    current_date,
                    price_history
                )

                # Filter by confidence
                if prediction['confidence'] >= min_confidence:
                    predictions.append(prediction)

            except Exception as e:
                logger.error(f"Error predicting {ticker}: {e}")

        # Sort by confidence
        predictions.sort(key=lambda x: x['confidence'], reverse=True)

        # Limit to top N
        if top_n:
            predictions = predictions[:top_n]

        logger.info(f"Generated {len(predictions)} predictions (min confidence: {min_confidence})")

        return predictions

    def predict_from_politician_activity(
        self,
        trades: List[Dict[str, Any]],
        current_date: Optional[datetime] = None,
        price_data: Optional[Dict[str, pd.DataFrame]] = None,
        lookback_days: int = 30,
        min_trade_count: int = 2,
        min_confidence: float = 0.3,
        top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Predict stocks based on recent politician activity

        Args:
            trades: All politician trades
            current_date: Prediction date
            price_data: Price history
            lookback_days: Only consider trades in last N days
            min_trade_count: Minimum trades needed for prediction
            min_confidence: Minimum confidence threshold
            top_n: Return top N predictions

        Returns:
            Top predictions sorted by confidence
        """
        if current_date is None:
            current_date = datetime.now()

        if price_data is None:
            price_data = {}

        # Find tickers with recent activity
        logger.info(f"Finding tickers with activity in last {lookback_days} days")

        cutoff_date = current_date - timedelta(days=lookback_days)
        ticker_counts = {}

        for trade in trades:
            ticker = trade.get('ticker', '').upper()
            if not ticker:
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

                if cutoff_date <= trade_date <= current_date:
                    ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1

            except (ValueError, TypeError, KeyError) as e:
                logger.debug(f"Skipping trade due to parse error: {e}")
                continue

        # Filter by minimum trade count
        active_tickers = [
            ticker for ticker, count in ticker_counts.items()
            if count >= min_trade_count
        ]

        logger.info(f"Found {len(active_tickers)} tickers with {min_trade_count}+ trades")

        if not active_tickers:
            logger.warning("No active tickers found")
            return []

        # Predict for active tickers
        predictions = self.predict_batch(
            active_tickers,
            trades,
            current_date,
            price_data,
            min_confidence=min_confidence,
            top_n=top_n
        )

        # Add activity context
        for pred in predictions:
            ticker = pred['ticker']
            pred['recent_trade_count'] = ticker_counts.get(ticker, 0)

        return predictions

    def generate_trading_signals(
        self,
        predictions: List[Dict[str, Any]],
        confidence_threshold: float = 0.5,
        max_positions: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Convert predictions to trading signals

        Args:
            predictions: List of predictions
            confidence_threshold: Minimum confidence for trading
            max_positions: Maximum number of positions

        Returns:
            List of trading signals
        """
        signals = []

        for pred in predictions:
            if pred['confidence'] < confidence_threshold:
                continue

            if len(signals) >= max_positions:
                break

            signal = {
                'ticker': pred['ticker'],
                'action': 'BUY' if pred['prediction'] == 'UP' else 'SELL',
                'confidence': pred['confidence'],
                'probability': pred['probability_up'] if pred['prediction'] == 'UP' else pred['probability_down'],
                'prediction_date': pred['prediction_date'],
                'signal_strength': pred['confidence'],  # Can be adjusted based on features
                'metadata': {
                    'prediction': pred['prediction'],
                    'model_predictions': pred.get('model_predictions', {}),
                    'features': pred.get('features', {})
                }
            }

            signals.append(signal)

        logger.info(f"Generated {len(signals)} trading signals")

        return signals

    def evaluate_predictions(
        self,
        predictions: List[Dict[str, Any]],
        price_data: Dict[str, pd.DataFrame],
        evaluation_date: datetime
    ) -> Dict[str, Any]:
        """
        Evaluate prediction accuracy against actual price movements

        Args:
            predictions: List of predictions made earlier
            price_data: Price data including evaluation period
            evaluation_date: Date to evaluate at (should be prediction_date + horizon)

        Returns:
            Evaluation metrics
        """
        logger.info(f"Evaluating {len(predictions)} predictions")

        results = {
            'total_predictions': len(predictions),
            'correct': 0,
            'incorrect': 0,
            'no_data': 0,
            'accuracy': 0.0,
            'precision_up': 0.0,
            'precision_down': 0.0,
            'details': []
        }

        true_positives_up = 0
        false_positives_up = 0
        true_positives_down = 0
        false_positives_down = 0

        for pred in predictions:
            ticker = pred['ticker']
            pred_date = datetime.fromisoformat(pred['prediction_date'])
            predicted_direction = pred['prediction']

            # Get actual price movement
            if ticker not in price_data:
                results['no_data'] += 1
                continue

            ticker_df = price_data[ticker]

            try:
                # Get price at prediction date and evaluation date
                pred_str = pred_date.strftime('%Y-%m-%d')
                eval_str = evaluation_date.strftime('%Y-%m-%d')

                pred_mask = ticker_df.index <= pred_str
                eval_mask = ticker_df.index <= eval_str

                pred_prices = ticker_df[pred_mask]
                eval_prices = ticker_df[eval_mask]

                if pred_prices.empty or eval_prices.empty:
                    results['no_data'] += 1
                    continue

                start_price = pred_prices.iloc[-1]['close']
                end_price = eval_prices.iloc[-1]['close']

                actual_return = (end_price - start_price) / start_price
                actual_direction = 'UP' if actual_return > 0 else 'DOWN'

                # Check if correct
                correct = (predicted_direction == actual_direction)

                if correct:
                    results['correct'] += 1

                    if predicted_direction == 'UP':
                        true_positives_up += 1
                    else:
                        true_positives_down += 1
                else:
                    results['incorrect'] += 1

                    if predicted_direction == 'UP':
                        false_positives_up += 1
                    else:
                        false_positives_down += 1

                results['details'].append({
                    'ticker': ticker,
                    'predicted': predicted_direction,
                    'actual': actual_direction,
                    'correct': correct,
                    'actual_return': float(actual_return),
                    'confidence': pred['confidence']
                })

            except Exception as e:
                logger.debug(f"Error evaluating {ticker}: {e}")
                results['no_data'] += 1

        # Calculate metrics
        total_evaluated = results['correct'] + results['incorrect']

        if total_evaluated > 0:
            results['accuracy'] = results['correct'] / total_evaluated

        if true_positives_up + false_positives_up > 0:
            results['precision_up'] = true_positives_up / (true_positives_up + false_positives_up)

        if true_positives_down + false_positives_down > 0:
            results['precision_down'] = true_positives_down / (true_positives_down + false_positives_down)

        logger.info(f"Evaluation: {results['accuracy']*100:.1f}% accuracy on {total_evaluated} predictions")

        return results

    def clear_cache(self):
        """Clear prediction cache"""
        self.prediction_cache = {}
        logger.info("Cleared prediction cache")


__all__ = ['PredictionService']
