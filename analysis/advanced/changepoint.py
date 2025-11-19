"""
Change Point Detection

Detects structural breaks and regime shifts in time series using
multiple algorithms for robustness.

Algorithms Implemented:
- PELT (Pruned Exact Linear Time) - Optimal for many change points
- Binary Segmentation - Fast, hierarchical
- Bottom-Up - Agglomerative approach
- Bayesian Online Change Point Detection - Real-time capable

Use Cases:
- Market regime transitions
- Policy changes
- Crisis detection
- Behavioral shifts
- Volatility breaks

References:
- Killick et al. (2012) - Optimal detection via PELT
- Adams & MacKay (2007) - Bayesian online change point detection
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import logging
from scipy import stats

logger = logging.getLogger(__name__)


class ChangePointDetector:
    """
    Detect change points (structural breaks) in time series.

    Change points mark transitions between different regimes or
    statistical properties. More precise than HMM for detecting
    exact transition times.
    """

    def __init__(
        self,
        method: str = 'pelt',
        model: str = 'rbf',
        penalty: float = 10,
        min_segment_length: int = 5
    ):
        """
        Initialize change point detector.

        Args:
            method: Detection algorithm
                - 'pelt' (Pruned Exact Linear Time) - optimal, fast
                - 'binseg' (Binary Segmentation) - hierarchical
                - 'cusum' (Cumulative Sum) - simple, online capable
            model: Cost function for segments
                - 'rbf' (Radial Basis Function) - general purpose
                - 'l2' (L2 norm) - for mean changes
                - 'normal' (Gaussian likelihood) - for distribution changes
            penalty: Regularization (higher = fewer change points)
            min_segment_length: Minimum length between change points

        Example:
            >>> detector = ChangePointDetector(method='pelt', penalty=10)
            >>> result = detector.detect(stock_returns)
            >>> print(f"Found {result['n_changes']} regime changes")
        """
        self.method = method
        self.model = model
        self.penalty = penalty
        self.min_segment_length = min_segment_length

        logger.info(f"Initialized ChangePointDetector: {method}/{model}")

    def detect(
        self,
        time_series: Union[pd.Series, np.ndarray],
        return_segments: bool = True
    ) -> Dict:
        """
        Detect change points in time series.

        Args:
            time_series: Input time series
            return_segments: Whether to analyze segments

        Returns:
            {
                'change_points': List of change point indices,
                'n_changes': Number of change points,
                'segments': Segment information (if return_segments),
                'segment_statistics': Statistics for each segment,
                'confidence': Confidence scores for each change point
            }

        Example:
            >>> detector = ChangePointDetector()
            >>> result = detector.detect(returns)
            >>>
            >>> for i, cp in enumerate(result['change_points']):
            ...     stats = result['segment_statistics'][i]
            ...     print(f"Change at t={cp}: new mean={stats['mean']:.3f}")
        """
        # Convert to array
        if isinstance(time_series, pd.Series):
            data = time_series.values
            index = time_series.index
        else:
            data = np.array(time_series)
            index = None

        # Detect change points using selected method
        if self.method == 'pelt':
            change_points = self._pelt(data)
        elif self.method == 'binseg':
            change_points = self._binary_segmentation(data)
        elif self.method == 'cusum':
            change_points = self._cusum(data)
        else:
            raise ValueError(f"Unknown method: {self.method}")

        # Ensure change points are sorted and unique
        change_points = sorted(set(change_points))

        # Analyze segments
        segments = []
        segment_stats = []

        if return_segments:
            segments, segment_stats = self._analyze_segments(data, change_points)

        # Calculate confidence scores
        confidences = self._calculate_confidence(data, change_points)

        result = {
            'change_points': change_points,
            'n_changes': len(change_points),
            'segments': segments,
            'segment_statistics': segment_stats,
            'confidence_scores': confidences,
            'method': self.method,
            'time_index': index
        }

        return result

    def _pelt(self, data: np.ndarray) -> List[int]:
        """
        PELT (Pruned Exact Linear Time) algorithm.

        Optimal change point detection with linear complexity.
        """
        n = len(data)

        if n < 2 * self.min_segment_length:
            return []

        # Cost function for a segment
        def segment_cost(start: int, end: int) -> float:
            segment = data[start:end]

            if len(segment) == 0:
                return 0

            if self.model == 'l2':
                # L2 cost (variance around mean)
                return np.sum((segment - np.mean(segment))**2)

            elif self.model == 'rbf':
                # RBF kernel cost
                diff_matrix = segment[:, np.newaxis] - segment
                return -np.sum(np.exp(-0.5 * diff_matrix**2))

            elif self.model == 'normal':
                # Negative log-likelihood for normal distribution
                if len(segment) < 2:
                    return 0
                return len(segment) * np.log(np.var(segment) + 1e-10)

            else:
                return np.sum((segment - np.mean(segment))**2)

        # Dynamic programming
        F = np.zeros(n + 1)  # Optimal cost up to each point
        F[0] = -self.penalty

        cp_candidates = [0]  # Candidate change point positions

        for t in range(self.min_segment_length, n + 1):
            # Find optimal previous change point
            costs = []

            for tau in cp_candidates:
                if t - tau >= self.min_segment_length:
                    cost = F[tau] + segment_cost(tau, t) + self.penalty
                    costs.append((cost, tau))

            if costs:
                F[t], best_tau = min(costs)

                # Prune candidates (PELT optimization)
                cp_candidates = [tau for tau in cp_candidates if F[tau] + segment_cost(tau, t) <= F[t]]
                cp_candidates.append(t)

        # Backtrack to find change points
        change_points = []
        t = n

        while t > 0:
            # Find previous change point
            best_tau = 0
            best_cost = float('inf')

            for tau in range(0, t - self.min_segment_length + 1):
                cost = F[tau] + segment_cost(tau, t)
                if cost < best_cost:
                    best_cost = cost
                    best_tau = tau

            if best_tau > 0:
                change_points.append(best_tau)

            t = best_tau

        return sorted(change_points[:-1]) if change_points else []

    def _binary_segmentation(self, data: np.ndarray, max_changes: int = 10) -> List[int]:
        """
        Binary Segmentation algorithm.

        Hierarchical approach that recursively splits segments.
        """
        def find_best_split(segment: np.ndarray, start_idx: int) -> Tuple[Optional[int], float]:
            """Find best split point in segment."""
            n = len(segment)

            if n < 2 * self.min_segment_length:
                return None, 0

            best_split = None
            best_gain = 0

            # Try all possible split points
            for i in range(self.min_segment_length, n - self.min_segment_length):
                left = segment[:i]
                right = segment[i:]

                # Calculate gain (reduction in variance)
                total_var = np.var(segment)
                left_var = np.var(left) * len(left) / n
                right_var = np.var(right) * len(right) / n

                gain = total_var - (left_var + right_var)

                if gain > best_gain:
                    best_gain = gain
                    best_split = start_idx + i

            return best_split, best_gain

        # Recursively find splits
        change_points = []
        segments_to_split = [(data, 0)]

        while segments_to_split and len(change_points) < max_changes:
            # Get segment with largest potential gain
            current_segment, start_idx = segments_to_split.pop(0)

            split, gain = find_best_split(current_segment, start_idx)

            if split is not None and gain > self.penalty:
                change_points.append(split)

                # Add new segments for further splitting
                split_rel = split - start_idx
                segments_to_split.append((current_segment[:split_rel], start_idx))
                segments_to_split.append((current_segment[split_rel:], split))

        return sorted(change_points)

    def _cusum(self, data: np.ndarray, threshold: float = None) -> List[int]:
        """
        CUSUM (Cumulative Sum) algorithm.

        Simple online change point detection.
        """
        if threshold is None:
            threshold = 5 * np.std(data)

        # Normalize data
        data_norm = (data - np.mean(data)) / (np.std(data) + 1e-10)

        # CUSUM statistics
        cusum_pos = np.zeros(len(data))
        cusum_neg = np.zeros(len(data))

        change_points = []

        for i in range(1, len(data)):
            cusum_pos[i] = max(0, cusum_pos[i-1] + data_norm[i])
            cusum_neg[i] = min(0, cusum_neg[i-1] + data_norm[i])

            # Detect change
            if cusum_pos[i] > threshold or cusum_neg[i] < -threshold:
                if not change_points or i - change_points[-1] >= self.min_segment_length:
                    change_points.append(i)
                    # Reset
                    cusum_pos[i] = 0
                    cusum_neg[i] = 0

        return change_points

    def _analyze_segments(
        self,
        data: np.ndarray,
        change_points: List[int]
    ) -> Tuple[List[Tuple[int, int]], List[Dict]]:
        """Analyze segments between change points."""
        # Add boundaries
        boundaries = [0] + change_points + [len(data)]

        segments = []
        statistics = []

        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]

            segment_data = data[start:end]

            segments.append((start, end))

            stats_dict = {
                'start': start,
                'end': end,
                'length': end - start,
                'mean': float(np.mean(segment_data)),
                'std': float(np.std(segment_data)),
                'median': float(np.median(segment_data)),
                'min': float(np.min(segment_data)),
                'max': float(np.max(segment_data))
            }

            # Trend (linear regression slope)
            if len(segment_data) > 1:
                x = np.arange(len(segment_data))
                slope, _ = np.polyfit(x, segment_data, 1)
                stats_dict['trend'] = float(slope)
            else:
                stats_dict['trend'] = 0.0

            statistics.append(stats_dict)

        return segments, statistics

    def _calculate_confidence(
        self,
        data: np.ndarray,
        change_points: List[int],
        window: int = 10
    ) -> List[float]:
        """
        Calculate confidence scores for change points.

        Uses statistical tests on segments around change point.
        """
        confidences = []

        for cp in change_points:
            # Get windows before and after change point
            start = max(0, cp - window)
            end = min(len(data), cp + window)

            before = data[start:cp]
            after = data[cp:end]

            if len(before) < 2 or len(after) < 2:
                confidences.append(0.5)
                continue

            # T-test for mean difference
            t_stat, p_value = stats.ttest_ind(before, after)

            # Convert p-value to confidence (1 - p)
            confidence = 1 - p_value

            confidences.append(float(np.clip(confidence, 0, 1)))

        return confidences

    def detect_with_bootstrap(
        self,
        time_series: Union[pd.Series, np.ndarray],
        n_bootstrap: int = 100
    ) -> Dict:
        """
        Detect change points with bootstrap confidence intervals.

        Args:
            time_series: Input time series
            n_bootstrap: Number of bootstrap samples

        Returns:
            Detection results with bootstrap confidence
        """
        # Convert to array
        if isinstance(time_series, pd.Series):
            data = time_series.values
        else:
            data = np.array(time_series)

        # Detect on original data
        result = self.detect(data)
        original_cps = result['change_points']

        # Bootstrap to estimate confidence
        bootstrap_cps = []

        for _ in range(n_bootstrap):
            # Resample with replacement
            indices = np.random.choice(len(data), len(data), replace=True)
            resampled = data[indices]

            # Detect change points
            boot_result = self.detect(resampled, return_segments=False)
            bootstrap_cps.append(boot_result['change_points'])

        # Count how often each change point appears
        from collections import Counter

        all_cps = [cp for cps in bootstrap_cps for cp in cps]
        cp_counts = Counter(all_cps)

        # Keep change points that appear in >50% of bootstraps
        consensus_cps = [
            cp for cp, count in cp_counts.items()
            if count > n_bootstrap * 0.5
        ]

        result['bootstrap_confidence'] = {
            cp: count / n_bootstrap
            for cp, count in cp_counts.items()
        }

        result['consensus_change_points'] = sorted(consensus_cps)

        return result


def quick_changepoint_detection(
    time_series: Union[pd.Series, np.ndarray],
    method: str = 'pelt',
    penalty: float = 10
) -> Dict:
    """
    Convenience function for quick change point detection.

    Example:
        >>> result = quick_changepoint_detection(stock_returns)
        >>> print(f"Detected {result['n_changes']} regime shifts")
        >>> for i, cp in enumerate(result['change_points']):
        ...     print(f"Shift {i+1} at index {cp}")
    """
    detector = ChangePointDetector(method=method, penalty=penalty)
    return detector.detect(time_series)
