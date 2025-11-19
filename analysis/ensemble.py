"""
Ensemble Model for Pattern Analysis

Combines predictions from Fourier, HMM, and DTW models to generate
more robust and accurate insights. Uses meta-learning to weight each
model's contribution based on confidence and historical accuracy.

Key Features:
- Multi-model prediction aggregation
- Confidence-weighted voting
- Contradiction detection
- Anomaly scoring
- Automated insight generation

Author: Claude
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

from app.ml.cyclical import (
    FourierCyclicalDetector,
    RegimeDetector,
    DynamicTimeWarpingMatcher
)

logger = logging.getLogger(__name__)


class PredictionType(str, Enum):
    """Type of ensemble prediction"""
    TRADE_INCREASE = "trade_increase"
    TRADE_DECREASE = "trade_decrease"
    REGIME_CHANGE = "regime_change"
    CYCLE_PEAK = "cycle_peak"
    ANOMALY = "anomaly"


@dataclass
class ModelPrediction:
    """Prediction from a single model"""
    model_name: str
    prediction: float  # e.g., predicted trades in 30 days
    confidence: float  # 0-1
    supporting_evidence: Dict[str, Any]


@dataclass
class EnsemblePrediction:
    """Combined prediction from ensemble"""
    prediction_type: PredictionType
    value: float  # Main prediction value
    confidence: float  # Combined confidence (0-1)
    model_agreement: float  # How much models agree (0-1)
    predictions: List[ModelPrediction]  # Individual model predictions
    insights: List[str]  # Human-readable insights
    anomaly_score: float  # 0-1, higher = more anomalous


class EnsemblePredictor:
    """
    Ensemble model combining Fourier, HMM, and DTW predictions.

    Uses weighted voting based on:
    - Model confidence
    - Historical accuracy
    - Data suitability (e.g., DTW needs more data)
    - Agreement among models
    """

    def __init__(
        self,
        fourier_weight: float = 0.35,
        hmm_weight: float = 0.35,
        dtw_weight: float = 0.30
    ):
        """
        Initialize ensemble predictor.

        Args:
            fourier_weight: Base weight for Fourier predictions
            hmm_weight: Base weight for HMM predictions
            dtw_weight: Base weight for DTW predictions
        """
        self.weights = {
            'fourier': fourier_weight,
            'hmm': hmm_weight,
            'dtw': dtw_weight
        }

        # Normalize weights
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}

    def predict(
        self,
        fourier_result: Dict,
        hmm_result: Dict,
        dtw_result: Dict,
        current_trade_frequency: pd.Series
    ) -> EnsemblePrediction:
        """
        Generate ensemble prediction from all three models.

        Args:
            fourier_result: Results from Fourier analysis
            hmm_result: Results from HMM regime detection
            dtw_result: Results from DTW pattern matching
            current_trade_frequency: Recent trade frequency time series

        Returns:
            EnsemblePrediction with combined insights
        """
        predictions = []

        # Extract prediction from Fourier
        fourier_pred = self._extract_fourier_prediction(fourier_result)
        if fourier_pred:
            predictions.append(fourier_pred)

        # Extract prediction from HMM
        hmm_pred = self._extract_hmm_prediction(hmm_result)
        if hmm_pred:
            predictions.append(hmm_pred)

        # Extract prediction from DTW
        dtw_pred = self._extract_dtw_prediction(dtw_result)
        if dtw_pred:
            predictions.append(dtw_pred)

        if not predictions:
            raise ValueError("No valid predictions from any model")

        # Combine predictions
        combined_value = self._weighted_average(predictions)
        combined_confidence = self._aggregate_confidence(predictions)
        model_agreement = self._calculate_agreement(predictions)

        # Determine prediction type
        if combined_value > 2:
            pred_type = PredictionType.TRADE_INCREASE
        elif combined_value < -2:
            pred_type = PredictionType.TRADE_DECREASE
        elif self._is_regime_change_imminent(hmm_result):
            pred_type = PredictionType.REGIME_CHANGE
        elif self._is_cycle_peak(fourier_result, current_trade_frequency):
            pred_type = PredictionType.CYCLE_PEAK
        else:
            pred_type = PredictionType.ANOMALY

        # Generate insights
        insights = self._generate_insights(
            predictions,
            pred_type,
            model_agreement,
            fourier_result,
            hmm_result,
            dtw_result
        )

        # Calculate anomaly score
        anomaly_score = self._calculate_anomaly_score(
            predictions,
            model_agreement,
            current_trade_frequency
        )

        return EnsemblePrediction(
            prediction_type=pred_type,
            value=combined_value,
            confidence=combined_confidence,
            model_agreement=model_agreement,
            predictions=predictions,
            insights=insights,
            anomaly_score=anomaly_score
        )

    def _extract_fourier_prediction(self, result: Dict) -> Optional[ModelPrediction]:
        """Extract 30-day prediction from Fourier analysis"""
        if not result.get('cycle_forecast'):
            return None

        forecast = result['cycle_forecast']
        if not forecast.get('forecast'):
            return None

        # Predict based on cycle peaks
        forecast_values = forecast['forecast']
        current_avg = np.mean(forecast_values[:15])  # First half
        future_avg = np.mean(forecast_values[15:])   # Second half

        prediction = future_avg - current_avg

        # Confidence based on top cycle strength
        confidence = 0.5
        if result.get('dominant_cycles'):
            top_cycle = result['dominant_cycles'][0]
            confidence = top_cycle.get('confidence', 0.5)

        return ModelPrediction(
            model_name='fourier',
            prediction=float(prediction),
            confidence=float(confidence),
            supporting_evidence={
                'top_cycle_period': result['dominant_cycles'][0]['period_days'] if result.get('dominant_cycles') else None,
                'forecast_std': forecast.get('residual_std', 0)
            }
        )

    def _extract_hmm_prediction(self, result: Dict) -> Optional[ModelPrediction]:
        """Extract prediction from HMM regime analysis"""
        if not result.get('regime_characteristics'):
            return None

        current_regime = result.get('current_regime')
        if current_regime is None:
            return None

        # Predict based on regime characteristics
        current_chars = result['regime_characteristics'].get(current_regime, {})
        avg_return = current_chars.get('avg_return', 0)

        # Scale to 30-day prediction
        prediction = avg_return * 30

        # Confidence from regime probability
        regime_probs = result.get('regime_probabilities', [])
        confidence = regime_probs[current_regime] if current_regime < len(regime_probs) else 0.5

        return ModelPrediction(
            model_name='hmm',
            prediction=float(prediction),
            confidence=float(confidence),
            supporting_evidence={
                'current_regime': result.get('current_regime_name'),
                'expected_duration': result.get('expected_duration', [0])[current_regime] if current_regime < len(result.get('expected_duration', [])) else 0
            }
        )

    def _extract_dtw_prediction(self, result: Dict) -> Optional[ModelPrediction]:
        """Extract prediction from DTW pattern matching"""
        prediction = result.get('prediction', {})
        if not prediction:
            return None

        predicted_return = prediction.get('predicted_return', 0)
        confidence = prediction.get('confidence', 0)

        if confidence < 0.5:  # Too uncertain
            return None

        return ModelPrediction(
            model_name='dtw',
            prediction=float(predicted_return),
            confidence=float(confidence),
            supporting_evidence={
                'num_matches': result.get('matches_found', 0),
                'top_similarity': result.get('top_matches', [{}])[0].get('similarity_score', 0) if result.get('top_matches') else 0
            }
        )

    def _weighted_average(self, predictions: List[ModelPrediction]) -> float:
        """Calculate weighted average of predictions"""
        total_weight = 0
        weighted_sum = 0

        for pred in predictions:
            # Combine base weight with model confidence
            weight = self.weights[pred.model_name] * pred.confidence
            weighted_sum += pred.prediction * weight
            total_weight += weight

        if total_weight == 0:
            return 0

        return weighted_sum / total_weight

    def _aggregate_confidence(self, predictions: List[ModelPrediction]) -> float:
        """Aggregate confidence across models"""
        if not predictions:
            return 0

        # Weighted average of confidences
        weights = [self.weights[p.model_name] for p in predictions]
        confidences = [p.confidence for p in predictions]

        return np.average(confidences, weights=weights)

    def _calculate_agreement(self, predictions: List[ModelPrediction]) -> float:
        """
        Calculate how much models agree (0-1).

        1.0 = perfect agreement
        0.0 = complete disagreement
        """
        if len(predictions) < 2:
            return 1.0

        values = [p.prediction for p in predictions]

        # Check if all have same sign
        signs = [np.sign(v) for v in values]
        if len(set(signs)) > 1:
            # Models disagree on direction
            agreement = 0.3
        else:
            # Same direction, check magnitude agreement
            std = np.std(values)
            mean = np.mean(np.abs(values))

            if mean == 0:
                agreement = 1.0
            else:
                # Coefficient of variation (lower = better agreement)
                cv = std / mean
                agreement = 1.0 / (1.0 + cv)

        return float(agreement)

    def _is_regime_change_imminent(self, hmm_result: Dict) -> bool:
        """Check if regime change is likely soon"""
        if not hmm_result.get('expected_duration'):
            return False

        current_regime = hmm_result.get('current_regime')
        if current_regime is None:
            return False

        expected_duration = hmm_result['expected_duration'][current_regime]

        # Regime change likely if expected duration < 7 days
        return expected_duration < 7

    def _is_cycle_peak(self, fourier_result: Dict, current_freq: pd.Series) -> bool:
        """Check if we're near a cycle peak"""
        if not fourier_result.get('dominant_cycles'):
            return False

        top_cycle = fourier_result['dominant_cycles'][0]
        period = top_cycle['period_days']

        # Simple heuristic: check if recent activity is high
        if len(current_freq) < 7:
            return False

        recent_avg = current_freq[-7:].mean()
        overall_avg = current_freq.mean()

        # Peak if recent activity is 50% above average
        return recent_avg > overall_avg * 1.5

    def _generate_insights(
        self,
        predictions: List[ModelPrediction],
        pred_type: PredictionType,
        model_agreement: float,
        fourier_result: Dict,
        hmm_result: Dict,
        dtw_result: Dict
    ) -> List[str]:
        """Generate human-readable insights"""
        insights = []

        # Agreement insight
        if model_agreement > 0.8:
            insights.append(f"Strong consensus: All models predict {pred_type.value.replace('_', ' ')}")
        elif model_agreement < 0.5:
            insights.append("Models disagree - high uncertainty in prediction")

        # Fourier insights
        if fourier_result.get('dominant_cycles'):
            top_cycle = fourier_result['dominant_cycles'][0]
            if top_cycle['confidence'] > 0.85:
                insights.append(
                    f"Strong {top_cycle['category']} cycle detected "
                    f"({top_cycle['period_days']:.0f} days, {top_cycle['confidence']:.0%} confidence)"
                )

        # HMM insights
        if hmm_result.get('current_regime_name'):
            regime = hmm_result['current_regime_name']
            expected_dur = hmm_result.get('expected_duration', [0])[hmm_result.get('current_regime', 0)]

            if expected_dur < 7:
                insights.append(f"Regime change imminent: Currently in '{regime}' but expected to shift soon")
            else:
                insights.append(f"Stable regime: '{regime}' expected to continue for {expected_dur:.0f} days")

        # DTW insights
        if dtw_result.get('matches_found', 0) > 0:
            top_match = dtw_result.get('top_matches', [{}])[0]
            if top_match.get('similarity_score', 0) > 0.85:
                insights.append(
                    f"Strong historical precedent: {top_match['similarity_score']:.0%} similar to {top_match.get('match_date', 'N/A')}"
                )
        elif dtw_result.get('matches_found', 0) == 0:
            insights.append("⚠️ Unusual pattern: No similar historical periods found (potential anomaly)")

        # Prediction magnitude
        combined_pred = self._weighted_average(predictions)
        if abs(combined_pred) > 10:
            insights.append(f"⚠️ Large change predicted: {combined_pred:+.1f} trades in next 30 days")

        return insights[:5]  # Top 5 insights

    def _calculate_anomaly_score(
        self,
        predictions: List[ModelPrediction],
        model_agreement: float,
        current_freq: pd.Series
    ) -> float:
        """
        Calculate anomaly score (0-1).

        Higher score = more anomalous behavior
        """
        score = 0

        # Factor 1: Low model agreement suggests anomaly
        if model_agreement < 0.5:
            score += 0.3

        # Factor 2: Low DTW confidence (no historical precedent)
        dtw_pred = next((p for p in predictions if p.model_name == 'dtw'), None)
        if dtw_pred and dtw_pred.confidence < 0.6:
            score += 0.3

        # Factor 3: Recent activity very different from average
        if len(current_freq) >= 30:
            recent_avg = current_freq[-7:].mean()
            historical_avg = current_freq[-30:-7].mean()

            if historical_avg > 0:
                ratio = recent_avg / historical_avg
                if ratio > 3 or ratio < 0.33:
                    score += 0.4

        return min(score, 1.0)


class MetaLearner:
    """
    Meta-learner to dynamically adjust model weights based on performance.

    Tracks historical accuracy and adjusts weights accordingly.
    """

    def __init__(self):
        self.performance_history = {
            'fourier': [],
            'hmm': [],
            'dtw': []
        }

    def update_performance(
        self,
        model_name: str,
        predicted: float,
        actual: float,
        confidence: float
    ):
        """Record model performance"""
        error = abs(predicted - actual)

        # Weighted error (penalize high-confidence bad predictions more)
        weighted_error = error * confidence

        self.performance_history[model_name].append({
            'error': error,
            'weighted_error': weighted_error,
            'confidence': confidence
        })

        # Keep last 100 predictions
        if len(self.performance_history[model_name]) > 100:
            self.performance_history[model_name].pop(0)

    def get_optimal_weights(self) -> Dict[str, float]:
        """Calculate optimal weights based on historical performance"""
        if not any(self.performance_history.values()):
            # No history, use defaults
            return {'fourier': 0.35, 'hmm': 0.35, 'dtw': 0.30}

        # Calculate average weighted error for each model
        avg_errors = {}
        for model, history in self.performance_history.items():
            if history:
                avg_errors[model] = np.mean([h['weighted_error'] for h in history])
            else:
                avg_errors[model] = 1.0  # Default

        # Convert errors to weights (inverse relationship)
        # Lower error = higher weight
        weights = {}
        for model, error in avg_errors.items():
            weights[model] = 1.0 / (1.0 + error)

        # Normalize
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}

        return weights
