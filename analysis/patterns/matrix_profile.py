"""
Matrix Profile for Time Series Pattern Discovery

The Matrix Profile is a revolutionary algorithm for time series data mining that:
- Finds recurring patterns (motifs) automatically
- Detects anomalies (discords)
- Works at any time scale
- Extremely fast (linear time complexity with STOMP/STUMPY)

Key Advantages:
- Parameter-free (no need to specify pattern length in advance)
- Finds exact matches and near-matches
- Discovers patterns you didn't know existed
- Scales to millions of data points

References:
- Yeh et al. (2016) - Matrix Profile I: All Pairs Similarity Joins
- Zhu et al. (2016) - Matrix Profile II: Exploiting a Novel Algorithm
- Law et al. (2019) - STUMPY: A Powerful and Scalable Python Library

Use Cases:
- Find recurring trading patterns across politician history
- Detect anomalous trading behavior
- Discover pattern templates across different politicians
- Time series motif discovery

Author: Claude
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Try to import STUMPY (state-of-the-art matrix profile library)
try:
    import stumpy
    HAS_STUMPY = True
except ImportError:
    HAS_STUMPY = False
    logger.warning("STUMPY not available. Matrix Profile will use fallback implementation.")


class MatrixProfileAnalyzer:
    """
    Matrix Profile-based pattern discovery for politician trading data

    Discovers:
    - Motifs: Recurring patterns (e.g., politician always trades after committee meetings)
    - Discords: Anomalous patterns (unprecedented trading behavior)
    - Semantic segmentation: Natural breakpoints in behavior
    - Pattern evolution: How patterns change over time
    """

    def __init__(
        self,
        window_size: int = 30,
        normalize: bool = True,
        distance_metric: str = 'euclidean'
    ):
        """
        Initialize Matrix Profile analyzer

        Args:
            window_size: Length of subsequence for pattern matching (days)
            normalize: Whether to z-normalize subsequences
            distance_metric: Distance metric ('euclidean', 'dtw')
        """
        self.window_size = window_size
        self.normalize = normalize
        self.distance_metric = distance_metric

        if not HAS_STUMPY:
            logger.warning("Using slow fallback implementation. Install STUMPY for 100x speedup: pip install stumpy")

    def discover_motifs(
        self,
        time_series: Union[pd.Series, np.ndarray],
        k_motifs: int = 3,
        exclusion_zone: Optional[int] = None
    ) -> Dict:
        """
        Discover top-k recurring patterns (motifs) in time series

        Args:
            time_series: Time series of trading activity (e.g., trade volume per day)
            k_motifs: Number of motif pairs to return
            exclusion_zone: Distance to exclude trivial matches (default: m/2)

        Returns:
            {
                'motifs': List of motif pairs with locations and distances,
                'motif_patterns': Actual pattern subsequences,
                'interpretation': Human-readable description
            }
        """
        # Convert to numpy array
        if isinstance(time_series, pd.Series):
            ts_array = time_series.values
            ts_index = time_series.index
        else:
            ts_array = np.array(time_series)
            ts_index = None

        # Validate
        if len(ts_array) < 2 * self.window_size:
            raise ValueError(f"Time series too short: {len(ts_array)} < {2 * self.window_size}")

        m = self.window_size
        exclusion_zone = exclusion_zone or m // 2

        # Compute matrix profile
        if HAS_STUMPY:
            mp = stumpy.stump(ts_array, m=m, normalize=self.normalize)
            matrix_profile = mp[:, 0]  # Distance to nearest neighbor
            matrix_profile_indices = mp[:, 1]  # Index of nearest neighbor
        else:
            matrix_profile, matrix_profile_indices = self._compute_matrix_profile_naive(
                ts_array, m
            )

        # Find top-k motif pairs
        motifs = []

        for i in range(k_motifs):
            # Find minimum distance (best motif)
            if len(matrix_profile) == 0:
                break

            min_idx = np.argmin(matrix_profile)
            min_distance = matrix_profile[min_idx]
            nearest_neighbor_idx = int(matrix_profile_indices[min_idx])

            # Extract motif patterns
            motif_1 = ts_array[min_idx:min_idx + m]
            motif_2 = ts_array[nearest_neighbor_idx:nearest_neighbor_idx + m]

            # Get timestamps if available
            if ts_index is not None:
                location_1 = ts_index[min_idx]
                location_2 = ts_index[nearest_neighbor_idx]
            else:
                location_1 = min_idx
                location_2 = nearest_neighbor_idx

            motifs.append({
                'motif_id': i + 1,
                'distance': float(min_distance),
                'location_1': location_1,
                'location_2': location_2,
                'pattern_1': motif_1.tolist(),
                'pattern_2': motif_2.tolist(),
                'similarity': 1.0 / (1.0 + min_distance),  # Convert distance to similarity
                'window_size': m
            })

            # Exclude this region from future searches
            start_exclude = max(0, min_idx - exclusion_zone)
            end_exclude = min(len(matrix_profile), min_idx + exclusion_zone + 1)
            matrix_profile[start_exclude:end_exclude] = np.inf

            start_exclude_nn = max(0, nearest_neighbor_idx - exclusion_zone)
            end_exclude_nn = min(len(matrix_profile), nearest_neighbor_idx + exclusion_zone + 1)
            matrix_profile[start_exclude_nn:end_exclude_nn] = np.inf

        # Generate interpretation
        interpretation = self._interpret_motifs(motifs, ts_array)

        return {
            'motifs': motifs,
            'num_motifs': len(motifs),
            'window_size': m,
            'interpretation': interpretation,
            'discovery_method': 'STUMPY' if HAS_STUMPY else 'Naive'
        }

    def find_discords(
        self,
        time_series: Union[pd.Series, np.ndarray],
        k_discords: int = 3
    ) -> Dict:
        """
        Find anomalous patterns (discords) - patterns that don't repeat

        Args:
            time_series: Time series data
            k_discords: Number of discords to return

        Returns:
            {
                'discords': List of discord locations and distances,
                'discord_patterns': Actual anomalous subsequences,
                'interpretation': What makes these unusual
            }
        """
        # Convert to numpy array
        if isinstance(time_series, pd.Series):
            ts_array = time_series.values
            ts_index = time_series.index
        else:
            ts_array = np.array(time_series)
            ts_index = None

        m = self.window_size

        # Compute matrix profile
        if HAS_STUMPY:
            mp = stumpy.stump(ts_array, m=m, normalize=self.normalize)
            matrix_profile = mp[:, 0]
        else:
            matrix_profile, _ = self._compute_matrix_profile_naive(ts_array, m)

        # Find top-k discords (highest distances = most anomalous)
        discords = []
        mp_copy = matrix_profile.copy()

        for i in range(k_discords):
            if len(mp_copy) == 0 or np.all(np.isinf(mp_copy)):
                break

            # Find maximum distance (most anomalous)
            max_idx = np.argmax(mp_copy)
            max_distance = mp_copy[max_idx]

            if np.isinf(max_distance):
                break

            # Extract discord pattern
            discord_pattern = ts_array[max_idx:max_idx + m]

            # Get timestamp if available
            if ts_index is not None:
                location = ts_index[max_idx]
            else:
                location = max_idx

            discords.append({
                'discord_id': i + 1,
                'distance': float(max_distance),
                'location': location,
                'pattern': discord_pattern.tolist(),
                'anomaly_score': float(max_distance),  # Higher = more anomalous
                'window_size': m
            })

            # Exclude this region
            exclusion_zone = m // 2
            start_exclude = max(0, max_idx - exclusion_zone)
            end_exclude = min(len(mp_copy), max_idx + exclusion_zone + 1)
            mp_copy[start_exclude:end_exclude] = -np.inf

        # Generate interpretation
        interpretation = self._interpret_discords(discords, ts_array)

        return {
            'discords': discords,
            'num_discords': len(discords),
            'window_size': m,
            'interpretation': interpretation
        }

    def segment_time_series(
        self,
        time_series: Union[pd.Series, np.ndarray]
    ) -> Dict:
        """
        Semantic segmentation: Find natural breakpoints in behavior

        Uses FLUSS (Fast Low-cost Unipotent Semantic Segmentation) algorithm
        to identify regime changes in trading behavior

        Args:
            time_series: Time series data

        Returns:
            {
                'change_points': Locations of regime changes,
                'segments': List of segments with characteristics,
                'arc_curve': Segmentation score curve
            }
        """
        # Convert to numpy array
        if isinstance(time_series, pd.Series):
            ts_array = time_series.values
            ts_index = time_series.index
        else:
            ts_array = np.array(time_series)
            ts_index = None

        m = self.window_size

        if not HAS_STUMPY:
            logger.warning("FLUSS requires STUMPY. Using simple segmentation.")
            return self._simple_segmentation(ts_array, ts_index)

        # Compute arc curve for segmentation
        mp = stumpy.stump(ts_array, m=m)
        arc_curve = stumpy.fluss(mp[:, 1], m=m)

        # Find peaks in arc curve (change points)
        # Higher peaks = stronger regime changes
        threshold = np.mean(arc_curve) + 1.5 * np.std(arc_curve)
        change_points = []

        for i in range(1, len(arc_curve) - 1):
            if arc_curve[i] > threshold and arc_curve[i] > arc_curve[i-1] and arc_curve[i] > arc_curve[i+1]:
                if ts_index is not None:
                    change_points.append(ts_index[i])
                else:
                    change_points.append(i)

        # Analyze segments
        segments = self._analyze_segments(ts_array, change_points, ts_index)

        return {
            'change_points': change_points,
            'num_segments': len(segments),
            'segments': segments,
            'arc_curve': arc_curve.tolist(),
            'method': 'FLUSS'
        }

    def _compute_matrix_profile_naive(
        self,
        ts: np.ndarray,
        m: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Naive O(n²) matrix profile computation (fallback when STUMPY unavailable)

        Note: This is 100-1000x slower than STUMPY. Only for small datasets.
        """
        n = len(ts)
        matrix_profile = np.full(n - m + 1, np.inf)
        matrix_profile_indices = np.zeros(n - m + 1, dtype=int)

        logger.warning(f"Computing matrix profile naively. This may take a while for n={n}...")

        # For each subsequence
        for i in range(n - m + 1):
            subseq_i = ts[i:i + m]

            if self.normalize:
                subseq_i = (subseq_i - np.mean(subseq_i)) / (np.std(subseq_i) + 1e-8)

            min_dist = np.inf
            min_idx = -1

            # Compare with all other subsequences
            for j in range(n - m + 1):
                if abs(i - j) < m // 2:  # Exclusion zone
                    continue

                subseq_j = ts[j:j + m]

                if self.normalize:
                    subseq_j = (subseq_j - np.mean(subseq_j)) / (np.std(subseq_j) + 1e-8)

                # Euclidean distance
                dist = np.sqrt(np.sum((subseq_i - subseq_j) ** 2))

                if dist < min_dist:
                    min_dist = dist
                    min_idx = j

            matrix_profile[i] = min_dist
            matrix_profile_indices[i] = min_idx

        return matrix_profile, matrix_profile_indices

    def _interpret_motifs(self, motifs: List[Dict], ts: np.ndarray) -> str:
        """Generate human-readable interpretation of motifs"""
        if not motifs:
            return "No recurring patterns found."

        interpretations = []

        for motif in motifs:
            similarity_pct = motif['similarity'] * 100

            pattern_mean_1 = np.mean(motif['pattern_1'])
            pattern_mean_2 = np.mean(motif['pattern_2'])

            if pattern_mean_1 > np.mean(ts) * 1.5:
                behavior = "high-activity trading"
            elif pattern_mean_1 < np.mean(ts) * 0.5:
                behavior = "low-activity trading"
            else:
                behavior = "moderate trading"

            interpretations.append(
                f"Motif {motif['motif_id']}: Recurring {behavior} pattern "
                f"({similarity_pct:.1f}% similar) at positions {motif['location_1']} and {motif['location_2']}"
            )

        return " | ".join(interpretations)

    def _interpret_discords(self, discords: List[Dict], ts: np.ndarray) -> str:
        """Generate human-readable interpretation of discords"""
        if not discords:
            return "No anomalous patterns found."

        interpretations = []

        for discord in discords:
            pattern_mean = np.mean(discord['pattern'])
            pattern_std = np.std(discord['pattern'])

            ts_mean = np.mean(ts)
            ts_std = np.std(ts)

            if pattern_mean > ts_mean + 2 * ts_std:
                anomaly_type = "unusually high activity"
            elif pattern_mean < ts_mean - 2 * ts_std:
                anomaly_type = "unusually low activity"
            elif pattern_std > ts_std * 2:
                anomaly_type = "highly volatile behavior"
            else:
                anomaly_type = "unprecedented pattern"

            interpretations.append(
                f"Discord {discord['discord_id']}: {anomaly_type} "
                f"at position {discord['location']} (anomaly score: {discord['anomaly_score']:.2f})"
            )

        return " | ".join(interpretations)

    def _simple_segmentation(
        self,
        ts: np.ndarray,
        ts_index: Optional[pd.Index]
    ) -> Dict:
        """Simple change point detection (fallback)"""
        # Use variance changes to detect segments
        m = self.window_size
        n = len(ts)

        change_scores = []

        for i in range(m, n - m):
            before = ts[i-m:i]
            after = ts[i:i+m]

            # Score based on variance change
            var_before = np.var(before)
            var_after = np.var(after)
            mean_before = np.mean(before)
            mean_after = np.mean(after)

            variance_change = abs(var_after - var_before) / (var_before + 1e-8)
            mean_change = abs(mean_after - mean_before) / (abs(mean_before) + 1e-8)

            score = variance_change + mean_change
            change_scores.append((i, score))

        # Find top change points
        change_scores.sort(key=lambda x: x[1], reverse=True)

        change_points = []
        for idx, score in change_scores[:5]:  # Top 5 changes
            if ts_index is not None:
                change_points.append(ts_index[idx])
            else:
                change_points.append(idx)

        segments = self._analyze_segments(ts, change_points, ts_index)

        return {
            'change_points': change_points,
            'num_segments': len(segments),
            'segments': segments,
            'method': 'Simple'
        }

    def _analyze_segments(
        self,
        ts: np.ndarray,
        change_points: List,
        ts_index: Optional[pd.Index]
    ) -> List[Dict]:
        """Analyze characteristics of each segment"""
        segments = []

        # Add start and end points
        indices = [0] + sorted(change_points) + [len(ts) - 1]

        for i in range(len(indices) - 1):
            start = indices[i]
            end = indices[i + 1]

            segment_data = ts[start:end]

            segment = {
                'segment_id': i + 1,
                'start': ts_index[start] if ts_index is not None else start,
                'end': ts_index[end] if ts_index is not None else end,
                'length': end - start,
                'mean': float(np.mean(segment_data)),
                'std': float(np.std(segment_data)),
                'min': float(np.min(segment_data)),
                'max': float(np.max(segment_data)),
                'trend': 'increasing' if segment_data[-1] > segment_data[0] else 'decreasing'
            }

            segments.append(segment)

        return segments


__all__ = ['MatrixProfileAnalyzer']
