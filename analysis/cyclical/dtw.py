"""
Dynamic Time Warping Pattern Matcher

Finds historical patterns similar to current trading patterns using Dynamic Time Warping (DTW).
DTW is a robust algorithm for measuring similarity between temporal sequences that may vary in speed.

Key Features:
- Pattern matching across different time scales
- Identification of similar historical periods
- Outcome prediction based on historical matches
- Confidence scoring for pattern similarity

Use Cases:
- Find past periods similar to current market conditions
- Identify recurring trade patterns
- Predict outcomes based on historical matches
- Anomaly detection (patterns with no historical match)

Author: Claude
"""

import numpy as np
import pandas as pd
from dtaidistance import dtw
from typing import Dict, List, Optional, Union, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DynamicTimeWarpingMatcher:
    """
    Find historical patterns similar to current pattern using DTW.

    Use Cases:
    - Find past periods similar to current market
    - Identify recurring trade patterns
    - Predict outcomes based on historical matches
    """

    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialize DTW matcher.

        Args:
            similarity_threshold: Minimum similarity score (0-1) to consider a match
        """
        self.similarity_threshold = similarity_threshold
        self.matches_cache = []

    def find_similar_patterns(
        self,
        current_pattern: Union[pd.Series, np.ndarray],
        historical_data: Union[pd.Series, np.ndarray],
        window_size: int = 30,
        top_k: int = 10,
        max_distance: Optional[float] = None
    ) -> List[Dict]:
        """
        Find most similar historical patterns to current pattern.

        Args:
            current_pattern: Recent trading pattern (includes at least window_size points)
            historical_data: All historical data to search through
            window_size: Length of pattern to match (in days/periods)
            top_k: Number of best matches to return
            max_distance: Maximum DTW distance to consider (None = auto)

        Returns:
            List of match dictionaries with:
            - match_date: Date/index of similar pattern start
            - similarity_score: 0-1 (1 = perfect match)
            - outcome_30d: What happened in next 30 days
            - outcome_90d: What happened in next 90 days
            - confidence: Statistical confidence in prediction
            - pattern: The matched historical pattern
        """
        # Convert to arrays
        current_array = self._to_array(current_pattern)
        historical_array = self._to_array(historical_data)

        # Get index if available
        hist_index = historical_data.index if isinstance(historical_data, pd.Series) else None

        # Validate inputs
        if len(current_array) < window_size:
            raise ValueError(f"Current pattern length {len(current_array)} < window_size {window_size}")

        if len(historical_array) < window_size + 90:
            raise ValueError(f"Historical data too short. Need at least {window_size + 90} points")

        # Normalize current pattern
        current = self._normalize(current_array[-window_size:])

        matches = []

        # Sliding window over historical data
        # Leave room for 90-day outcome analysis
        for i in range(len(historical_array) - window_size - 90):
            historical_window = historical_array[i:i+window_size]
            historical_norm = self._normalize(historical_window)

            # Calculate DTW distance
            try:
                distance = dtw.distance(current, historical_norm)
            except Exception as e:
                logger.warning(f"DTW calculation failed at index {i}: {e}")
                continue

            # Convert to similarity score (0-1)
            similarity = self._distance_to_similarity(distance)

            # Filter by threshold
            if similarity < self.similarity_threshold:
                continue

            # Filter by max_distance if specified
            if max_distance is not None and distance > max_distance:
                continue

            # Calculate outcomes
            outcome_30d = self._calculate_outcome(
                historical_array[i+window_size:i+window_size+30]
            )
            outcome_90d = self._calculate_outcome(
                historical_array[i+window_size:i+window_size+90]
            )

            # Determine match date
            if hist_index is not None:
                match_date = hist_index[i]
            else:
                match_date = i

            match_dict = {
                'match_date': match_date,
                'match_index': i,
                'similarity_score': float(similarity),
                'dtw_distance': float(distance),
                'outcome_30d': outcome_30d,
                'outcome_90d': outcome_90d,
                'pattern': historical_window.tolist(),
                'confidence': self._calculate_match_confidence(similarity, distance, window_size)
            }

            matches.append(match_dict)

        # Sort by similarity and return top K
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        self.matches_cache = matches[:top_k]

        return self.matches_cache

    def predict_from_matches(
        self,
        matches: Optional[List[Dict]] = None,
        horizon: int = 30
    ) -> Dict:
        """
        Predict likely outcome based on historical matches.

        Weight predictions by similarity score.

        Args:
            matches: List of match dicts (uses cached matches if None)
            horizon: Prediction horizon (30 or 90 days)

        Returns:
            {
                'predicted_return': Weighted average return,
                'confidence': Overall confidence in prediction,
                'return_distribution': Statistics of matched outcomes,
                'num_matches': Number of matches used
            }
        """
        if matches is None:
            matches = self.matches_cache

        if not matches:
            return {
                'predicted_return': 0.0,
                'confidence': 0.0,
                'return_distribution': {},
                'num_matches': 0
            }

        # Select horizon
        outcome_key = f'outcome_{horizon}d'

        # Extract outcomes and weights
        outcomes = []
        weights = []

        for match in matches:
            outcome = match.get(outcome_key, {})
            if outcome and 'total_return' in outcome:
                outcomes.append(outcome['total_return'])
                # Weight by similarity score
                weights.append(match['similarity_score'])

        if not outcomes:
            return {
                'predicted_return': 0.0,
                'confidence': 0.0,
                'return_distribution': {},
                'num_matches': 0
            }

        outcomes = np.array(outcomes)
        weights = np.array(weights)

        # Normalize weights
        weights = weights / np.sum(weights)

        # Weighted average prediction
        predicted_return = np.sum(outcomes * weights)

        # Calculate confidence based on:
        # 1. Number of matches
        # 2. Consistency of outcomes (low variance = high confidence)
        # 3. Average similarity score
        match_count_confidence = min(len(matches) / 10.0, 1.0)
        outcome_consistency = 1.0 / (1.0 + np.std(outcomes))
        avg_similarity = np.mean(weights)

        confidence = (
            match_count_confidence * 0.3 +
            outcome_consistency * 0.4 +
            avg_similarity * 0.3
        )

        return {
            'predicted_return': float(predicted_return),
            'confidence': float(confidence),
            'return_distribution': {
                'mean': float(np.mean(outcomes)),
                'median': float(np.median(outcomes)),
                'std': float(np.std(outcomes)),
                'min': float(np.min(outcomes)),
                'max': float(np.max(outcomes)),
                'percentile_25': float(np.percentile(outcomes, 25)),
                'percentile_75': float(np.percentile(outcomes, 75))
            },
            'num_matches': len(matches)
        }

    def _to_array(self, data: Union[pd.Series, np.ndarray]) -> np.ndarray:
        """Convert data to numpy array."""
        if isinstance(data, pd.Series):
            return data.values
        return np.array(data)

    def _normalize(self, arr: np.ndarray) -> np.ndarray:
        """
        Normalize array to zero mean and unit variance.

        This makes patterns comparable regardless of absolute values.
        """
        mean = np.mean(arr)
        std = np.std(arr)

        if std < 1e-8:
            # Constant array
            return np.zeros_like(arr)

        return (arr - mean) / std

    def _distance_to_similarity(self, distance: float) -> float:
        """
        Convert DTW distance to similarity score (0-1).

        Uses sigmoid-like transformation.
        """
        # Scale factor (tune based on typical distances)
        scale = 2.0
        similarity = 1.0 / (1.0 + distance / scale)
        return similarity

    def _calculate_outcome(self, future_data: np.ndarray) -> Dict:
        """
        Calculate outcome statistics for a future period.

        Returns:
            {
                'total_return': Total return over period,
                'avg_return': Average per-period return,
                'volatility': Std dev of returns,
                'sharpe': Sharpe-like ratio,
                'max_drawdown': Maximum drawdown
            }
        """
        if len(future_data) == 0:
            return {}

        # Calculate returns if not already returns
        # (Assumes data is either prices or returns)
        if np.max(np.abs(future_data)) > 1.0:
            # Likely prices, convert to returns
            returns = np.diff(future_data) / future_data[:-1]
        else:
            # Likely already returns
            returns = future_data

        # Total return
        total_return = np.sum(returns)

        # Average return
        avg_return = np.mean(returns)

        # Volatility
        volatility = np.std(returns)

        # Sharpe-like ratio (assuming risk-free rate = 0)
        sharpe = avg_return / volatility if volatility > 0 else 0

        # Max drawdown
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown)

        return {
            'total_return': float(total_return),
            'avg_return': float(avg_return),
            'volatility': float(volatility),
            'sharpe': float(sharpe),
            'max_drawdown': float(max_drawdown)
        }

    def _calculate_match_confidence(
        self,
        similarity: float,
        distance: float,
        window_size: int
    ) -> float:
        """
        Calculate confidence in this match.

        Considers:
        - Similarity score
        - Absolute distance
        - Pattern length (longer = more confident)
        """
        # Base confidence from similarity
        sim_confidence = similarity

        # Confidence from distance (lower = better)
        dist_confidence = 1.0 / (1.0 + distance)

        # Confidence from window size (longer = more confident)
        size_confidence = min(window_size / 60.0, 1.0)

        # Combined
        confidence = (
            sim_confidence * 0.5 +
            dist_confidence * 0.3 +
            size_confidence * 0.2
        )

        return float(confidence)

    def get_pattern_summary(
        self,
        matches: Optional[List[Dict]] = None,
        horizon: int = 30
    ) -> str:
        """Get human-readable summary of pattern matches."""
        if matches is None:
            matches = self.matches_cache

        if not matches:
            return "No similar patterns found."

        prediction = self.predict_from_matches(matches, horizon)

        summary = f"Found {len(matches)} similar historical patterns:\n\n"

        # Top 3 matches
        for i, match in enumerate(matches[:3], 1):
            date = match['match_date']
            sim = match['similarity_score']
            outcome = match[f'outcome_{horizon}d']

            summary += f"{i}. Match at {date} (similarity: {sim:.1%})\n"
            if outcome:
                summary += f"   Outcome: {outcome['total_return']:+.2%} return\n"

        summary += f"\nPrediction ({horizon} days):\n"
        summary += f"  Expected return: {prediction['predicted_return']:+.2%}\n"
        summary += f"  Confidence: {prediction['confidence']:.1%}\n"

        dist = prediction['return_distribution']
        if dist:
            summary += f"  Range: {dist['min']:+.2%} to {dist['max']:+.2%}\n"

        return summary
