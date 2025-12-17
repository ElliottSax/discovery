"""
Stock Price Prediction Models
Uses politician trading data as signals for stock price prediction
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging
import pickle
from pathlib import Path

# ML libraries (with fallbacks)
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logging.warning("scikit-learn not available - using baseline models")

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    logging.warning("XGBoost not available - using alternatives")

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logging.warning("PyTorch not available - LSTM disabled")

from ml_models.feature_engineering import PoliticianTradeFeatureExtractor

logger = logging.getLogger(__name__)


class StockPricePredictor:
    """
    Predicts stock price direction (up/down) using politician trading signals

    Uses ensemble of:
    - XGBoost (gradient boosting)
    - Random Forest
    - Logistic Regression
    - LSTM (if PyTorch available)
    """

    def __init__(
        self,
        prediction_horizon_days: int = 30,
        model_dir: str = 'data/models'
    ):
        """
        Initialize predictor

        Args:
            prediction_horizon_days: Days ahead to predict
            model_dir: Directory to save/load trained models
        """
        self.prediction_horizon = prediction_horizon_days
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.feature_extractor = PoliticianTradeFeatureExtractor(lookback_days=30)
        self.scaler = StandardScaler() if HAS_SKLEARN else None

        # Models
        self.models = {}
        self.model_weights = {}

        self._initialize_models()

    def _initialize_models(self):
        """Initialize all ML models"""

        if HAS_SKLEARN:
            # Logistic Regression (baseline)
            self.models['logistic'] = LogisticRegression(
                max_iter=1000,
                random_state=42
            )
            self.model_weights['logistic'] = 0.15

            # Random Forest
            self.models['random_forest'] = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=10,
                random_state=42,
                n_jobs=-1
            )
            self.model_weights['random_forest'] = 0.25

            # Gradient Boosting
            self.models['gradient_boost'] = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            self.model_weights['gradient_boost'] = 0.25

        if HAS_XGBOOST:
            # XGBoost
            self.models['xgboost'] = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            )
            self.model_weights['xgboost'] = 0.35

        # Normalize weights
        total_weight = sum(self.model_weights.values())
        if total_weight > 0:
            for name in self.model_weights:
                self.model_weights[name] /= total_weight

        logger.info(f"Initialized {len(self.models)} models: {list(self.models.keys())}")

    def prepare_training_data(
        self,
        trades: List[Dict[str, Any]],
        price_data: Dict[str, pd.DataFrame],
        start_date: datetime,
        end_date: datetime
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare training data from historical trades and prices

        Args:
            trades: All politician trades
            price_data: Historical price data by ticker
            start_date: Training start date
            end_date: Training end date

        Returns:
            Tuple of (features, labels, tickers)
        """
        logger.info(f"Preparing training data from {start_date.date()} to {end_date.date()}")

        X_list = []
        y_list = []
        ticker_list = []

        # Get all tickers
        tickers = set(t.get('ticker', '').upper() for t in trades if t.get('ticker'))
        logger.info(f"Processing {len(tickers)} tickers")

        for ticker in tickers:
            if ticker not in price_data:
                continue

            ticker_price_df = price_data[ticker]

            # Generate training samples: one per trading day
            current_date = start_date

            while current_date <= end_date:
                # Skip weekends
                if current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                    continue

                # Extract features at this date
                features = self.feature_extractor.extract_features_for_ticker(
                    ticker,
                    trades,
                    current_date,
                    ticker_price_df
                )

                # Get future price for label
                future_date = current_date + timedelta(days=self.prediction_horizon)
                label = self._get_price_change_label(
                    ticker_price_df,
                    current_date,
                    future_date
                )

                if label is not None:
                    # Convert features dict to array
                    feature_array = self._features_dict_to_array(features)

                    X_list.append(feature_array)
                    y_list.append(label)
                    ticker_list.append(ticker)

                current_date += timedelta(days=1)

        if len(X_list) == 0:
            logger.error("No training samples generated!")
            return np.array([]), np.array([]), []

        X = np.array(X_list)
        y = np.array(y_list)

        logger.info(f"Generated {len(X)} training samples")
        logger.info(f"Positive samples: {sum(y)} ({sum(y)/len(y)*100:.1f}%)")

        return X, y, ticker_list

    def _get_price_change_label(
        self,
        price_df: pd.DataFrame,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[int]:
        """
        Get binary label: 1 if price went up, 0 if down

        Args:
            price_df: Price dataframe
            start_date: Start date
            end_date: End date

        Returns:
            1 (price up), 0 (price down), or None (no data)
        """
        try:
            # Get price at start
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            # Find nearest dates
            start_mask = price_df.index <= start_str
            end_mask = price_df.index <= end_str

            start_prices = price_df[start_mask]
            end_prices = price_df[end_mask]

            if start_prices.empty or end_prices.empty:
                return None

            start_price = start_prices.iloc[-1]['close']
            end_price = end_prices.iloc[-1]['close']

            # Calculate return
            price_return = (end_price - start_price) / start_price

            # Binary classification: >0% return = 1, <=0% return = 0
            return 1 if price_return > 0 else 0

        except Exception as e:
            logger.debug(f"Error getting price label: {e}")
            return None

    def _features_dict_to_array(self, features: Dict[str, float]) -> np.ndarray:
        """Convert features dictionary to numpy array in consistent order"""

        feature_names = self.feature_extractor.get_feature_names()
        return np.array([features.get(name, 0.0) for name in feature_names])

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        validation_split: float = 0.2
    ) -> Dict[str, float]:
        """
        Train all models

        Args:
            X: Feature matrix
            y: Labels
            validation_split: Fraction for validation

        Returns:
            Dictionary of model accuracies
        """
        logger.info(f"Training models on {len(X)} samples")

        if len(X) == 0:
            logger.error("Cannot train with empty dataset")
            return {}

        # Split train/validation
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y
        )

        # Scale features
        if self.scaler:
            X_train = self.scaler.fit_transform(X_train)
            X_val = self.scaler.transform(X_val)

        accuracies = {}

        # Train each model
        for name, model in self.models.items():
            logger.info(f"Training {name}...")

            try:
                model.fit(X_train, y_train)

                # Evaluate
                train_acc = model.score(X_train, y_train)
                val_acc = model.score(X_val, y_val)

                accuracies[name] = {
                    'train_accuracy': float(train_acc),
                    'val_accuracy': float(val_acc)
                }

                logger.info(f"  {name}: Train={train_acc:.3f}, Val={val_acc:.3f}")

            except Exception as e:
                logger.error(f"Error training {name}: {e}")

        return accuracies

    def predict(
        self,
        ticker: str,
        trades: List[Dict[str, Any]],
        current_date: datetime,
        price_history: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Predict price direction for a ticker

        Args:
            ticker: Stock ticker
            trades: All politician trades
            current_date: Date to predict from
            price_history: Historical price data

        Returns:
            Prediction dictionary with probabilities and confidence
        """
        # Extract features
        features = self.feature_extractor.extract_features_for_ticker(
            ticker,
            trades,
            current_date,
            price_history
        )

        feature_array = self._features_dict_to_array(features).reshape(1, -1)

        # Scale if scaler available and fitted
        if self.scaler is not None:
            try:
                feature_array = self.scaler.transform(feature_array)
            except:
                # Scaler not fitted - skip scaling
                logger.debug("Scaler not fitted, skipping scaling")

        # Get predictions from all models
        predictions = {}
        probabilities = {}

        # Check if models are trained
        if not self.models:
            logger.warning("No models available - using baseline prediction")
            # Return baseline prediction
            baseline = BaselinePredictor()
            return baseline.predict(ticker, trades, current_date, price_history)

        for name, model in self.models.items():
            try:
                # Predict
                pred = model.predict(feature_array)[0]
                predictions[name] = int(pred)

                # Get probability if available
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(feature_array)[0]
                    probabilities[name] = {
                        'down': float(proba[0]),
                        'up': float(proba[1])
                    }
                else:
                    probabilities[name] = {
                        'down': 0.0 if pred == 1 else 1.0,
                        'up': 1.0 if pred == 1 else 0.0
                    }

            except Exception as e:
                logger.error(f"Error predicting with {name}: {e}")
                # Skip this model if it fails

        # Ensemble prediction (weighted vote)
        ensemble_up_prob = 0.0
        for name, proba in probabilities.items():
            weight = self.model_weights.get(name, 0.0)
            ensemble_up_prob += proba['up'] * weight

        ensemble_prediction = 1 if ensemble_up_prob > 0.5 else 0

        # Calculate confidence (distance from 0.5)
        confidence = abs(ensemble_up_prob - 0.5) * 2  # 0-1 scale

        return {
            'ticker': ticker,
            'prediction_date': current_date.isoformat(),
            'prediction_horizon_days': self.prediction_horizon,
            'prediction': 'UP' if ensemble_prediction == 1 else 'DOWN',
            'confidence': float(confidence),
            'probability_up': float(ensemble_up_prob),
            'probability_down': float(1 - ensemble_up_prob),
            'model_predictions': predictions,
            'model_probabilities': probabilities,
            'features': features
        }

    def predict_batch(
        self,
        tickers: List[str],
        trades: List[Dict[str, Any]],
        current_date: datetime,
        price_data: Dict[str, pd.DataFrame]
    ) -> List[Dict[str, Any]]:
        """
        Predict for multiple tickers in batch

        Args:
            tickers: List of tickers to predict
            trades: All politician trades
            current_date: Prediction date
            price_data: Price history by ticker

        Returns:
            List of predictions
        """
        logger.info(f"Predicting for {len(tickers)} tickers")

        predictions = []

        for ticker in tickers:
            price_history = price_data.get(ticker)

            prediction = self.predict(
                ticker,
                trades,
                current_date,
                price_history
            )

            predictions.append(prediction)

        # Sort by confidence
        predictions.sort(key=lambda x: x['confidence'], reverse=True)

        return predictions

    def save_models(self, suffix: str = ''):
        """Save trained models to disk"""

        if not self.models:
            logger.warning("No models to save")
            return

        filename = f'predictor_models{suffix}.pkl'
        filepath = self.model_dir / filename

        model_data = {
            'models': self.models,
            'scaler': self.scaler,
            'model_weights': self.model_weights,
            'feature_names': self.feature_extractor.get_feature_names(),
            'prediction_horizon': self.prediction_horizon
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        logger.info(f"Saved models to {filepath}")

    def load_models(self, suffix: str = ''):
        """Load trained models from disk"""

        filename = f'predictor_models{suffix}.pkl'
        filepath = self.model_dir / filename

        if not filepath.exists():
            logger.error(f"Model file not found: {filepath}")
            return False

        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)

            self.models = model_data['models']
            self.scaler = model_data['scaler']
            self.model_weights = model_data['model_weights']
            self.prediction_horizon = model_data['prediction_horizon']

            logger.info(f"Loaded models from {filepath}")
            logger.info(f"Loaded {len(self.models)} models: {list(self.models.keys())}")

            return True

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False


class BaselinePredictor:
    """Simple baseline predictor (for when ML libraries unavailable)"""

    def __init__(self):
        self.feature_extractor = PoliticianTradeFeatureExtractor()

    def predict(
        self,
        ticker: str,
        trades: List[Dict[str, Any]],
        current_date: datetime,
        price_history: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Simple rule-based prediction

        Rules:
        - If buy_ratio > 0.6 and consensus strong → UP
        - If buy_ratio < 0.4 and consensus strong → DOWN
        - Else → UP if buy_ratio > 0.5, else DOWN
        """
        features = self.feature_extractor.extract_features_for_ticker(
            ticker,
            trades,
            current_date,
            price_history
        )

        buy_ratio = features.get('buy_ratio', 0.5)
        consensus = features.get('consensus_strength', 0.0)
        recency = features.get('recency_score', 0.0)

        # Simple scoring
        score = buy_ratio  # Start with buy ratio

        # Boost if consensus
        if consensus > 0.3:
            score += 0.1

        # Boost if recent activity
        if recency > 5:
            score += 0.1

        # Predict
        prediction = 'UP' if score > 0.5 else 'DOWN'
        confidence = abs(score - 0.5) * 2

        return {
            'ticker': ticker,
            'prediction_date': current_date.isoformat(),
            'prediction': prediction,
            'confidence': float(confidence),
            'probability_up': float(score),
            'probability_down': float(1 - score),
            'model': 'baseline',
            'features': features
        }


class MultiHorizonPredictor:
    """
    Multi-horizon stock price predictor

    Predicts stock price direction at multiple time horizons:
    - 7 days
    - 14 days
    - 30 days
    - 60 days
    - 90 days

    Each horizon has a separate trained model with horizon-specific features.
    """

    def __init__(self, model_dir: str = 'data/models'):
        """
        Initialize multi-horizon predictor

        Args:
            model_dir: Directory to save/load trained models
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.horizons = [7, 14, 30, 60, 90]
        self.predictors = {}

        # Initialize predictor for each horizon
        for horizon in self.horizons:
            self.predictors[horizon] = StockPricePredictor(
                prediction_horizon_days=horizon,
                model_dir=str(self.model_dir)
            )

        logger.info(f"Initialized multi-horizon predictor with {len(self.horizons)} horizons")

    def train_all_horizons(
        self,
        trades: List[Dict],
        price_data: Dict[str, pd.DataFrame],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[int, Dict]:
        """
        Train models for all horizons

        Args:
            trades: Politician trades
            price_data: Historical price data
            start_date: Training start date
            end_date: Training end date

        Returns:
            Dict mapping horizon to training results
        """
        results = {}

        for horizon in self.horizons:
            logger.info(f"Training {horizon}-day horizon model...")

            predictor = self.predictors[horizon]

            # Prepare training data
            X, y, tickers = predictor.prepare_training_data(
                trades,
                price_data,
                start_date,
                end_date
            )

            if len(X) < 10:
                logger.warning(f"Insufficient data for {horizon}-day horizon")
                results[horizon] = {'error': 'insufficient_data'}
                continue

            # Train models
            accuracies = predictor.train(X, y)

            results[horizon] = {
                'accuracies': accuracies,
                'samples': len(X),
                'horizon_days': horizon
            }

            logger.info(f"{horizon}-day horizon trained: {accuracies}")

        return results

    def predict_all_horizons(
        self,
        ticker: str,
        trades: List[Dict],
        current_date: datetime,
        price_history: Optional[pd.DataFrame] = None
    ) -> Dict[str, Dict]:
        """
        Make predictions for all horizons

        Args:
            ticker: Stock ticker
            trades: Politician trades
            current_date: Current date
            price_history: Optional price history

        Returns:
            Dict mapping horizon string (e.g., '7d') to prediction
        """
        predictions = {}

        for horizon in self.horizons:
            predictor = self.predictors[horizon]

            try:
                pred = predictor.predict(
                    ticker,
                    trades,
                    current_date,
                    price_history
                )

                # Add horizon info
                pred['horizon_days'] = horizon
                predictions[f'{horizon}d'] = pred

            except Exception as e:
                logger.error(f"Prediction failed for {horizon}-day horizon: {e}")
                predictions[f'{horizon}d'] = {
                    'error': str(e),
                    'horizon_days': horizon
                }

        # Calculate confidence decay
        predictions = self._apply_confidence_decay(predictions)

        return predictions

    def _apply_confidence_decay(self, predictions: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Apply confidence decay for longer horizons

        Confidence naturally decreases with prediction horizon due to uncertainty.
        """
        for horizon_str, pred in predictions.items():
            if 'error' in pred:
                continue

            horizon_days = pred.get('horizon_days', 30)

            # Decay factor: 0% decay at 7 days, 30% decay at 90 days
            decay_factor = 1.0 - (horizon_days - 7) / (90 - 7) * 0.3
            decay_factor = max(0.7, min(1.0, decay_factor))

            # Apply decay to confidence
            original_confidence = pred.get('confidence', 0.5)
            decayed_confidence = original_confidence * decay_factor

            pred['confidence_original'] = original_confidence
            pred['confidence'] = decayed_confidence
            pred['confidence_decay_factor'] = decay_factor

        return predictions

    def save_all_models(self, suffix: str = ''):
        """Save all horizon models"""
        for horizon, predictor in self.predictors.items():
            predictor.save_models(suffix=f'_{horizon}d{suffix}')

        logger.info(f"Saved all multi-horizon models with suffix '{suffix}'")

    def load_all_models(self, suffix: str = ''):
        """Load all horizon models"""
        for horizon, predictor in self.predictors.items():
            predictor.load_models(suffix=f'_{horizon}d{suffix}')

        logger.info(f"Loaded all multi-horizon models with suffix '{suffix}'")

    def get_horizon_summary(self, predictions: Dict[str, Dict]) -> Dict:
        """
        Get summary of multi-horizon predictions

        Returns:
            {
                'consensus': 'UP' | 'DOWN' | 'MIXED',
                'confidence_avg': float,
                'short_term': '7d prediction',
                'long_term': '90d prediction',
                'agreement_score': float  # 0-1, how much horizons agree
            }
        """
        if not predictions:
            return {'error': 'no predictions'}

        # Filter out errors
        valid_preds = {k: v for k, v in predictions.items() if 'error' not in v}

        if not valid_preds:
            return {'error': 'all predictions failed'}

        # Count UP vs DOWN
        up_count = sum(1 for p in valid_preds.values() if p.get('prediction') == 'UP')
        down_count = len(valid_preds) - up_count

        # Consensus
        if up_count > down_count:
            consensus = 'UP'
        elif down_count > up_count:
            consensus = 'DOWN'
        else:
            consensus = 'MIXED'

        # Agreement score (1.0 = all agree, 0.5 = split)
        agreement_score = max(up_count, down_count) / len(valid_preds)

        # Average confidence
        confidences = [p.get('confidence', 0) for p in valid_preds.values()]
        confidence_avg = np.mean(confidences) if confidences else 0.0

        return {
            'consensus': consensus,
            'confidence_avg': float(confidence_avg),
            'agreement_score': float(agreement_score),
            'short_term': valid_preds.get('7d', {}).get('prediction', 'UNKNOWN'),
            'long_term': valid_preds.get('90d', {}).get('prediction', 'UNKNOWN'),
            'num_horizons': len(valid_preds),
            'up_count': up_count,
            'down_count': down_count
        }


__all__ = ['StockPricePredictor', 'BaselinePredictor', 'MultiHorizonPredictor']
