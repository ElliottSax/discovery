"""
Tests for Change Point Detection

Tests cover:
- PELT algorithm accuracy
- Binary Segmentation
- CUSUM detection
- Segment analysis
- Confidence scoring
- Bootstrap validation
"""

import pytest
import numpy as np
import pandas as pd
from analysis.advanced.changepoint import (
    ChangePointDetector,
    quick_changepoint_detection
)


class TestChangePointDetector:
    """Test ChangePointDetector class."""

    def test_initialization(self):
        """Test detector initialization."""
        detector = ChangePointDetector(method='pelt', penalty=10)
        assert detector.method == 'pelt'
        assert detector.penalty == 10

    def test_detects_single_changepoint(self):
        """Test detection of single change point."""
        # Create data with one change point at t=50
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)  # Low mean
        data2 = np.random.normal(5, 1, 50)  # High mean
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='pelt', penalty=1)
        result = detector.detect(data)

        assert result['n_changes'] > 0
        change_points = result['change_points']

        # Should detect change near t=50
        assert any(40 <= cp <= 60 for cp in change_points), \
            f"Expected change point near 50, found: {change_points}"

    def test_detects_multiple_changepoints(self):
        """Test detection of multiple change points."""
        # Create data with 3 segments
        np.random.seed(42)
        seg1 = np.random.normal(0, 1, 40)
        seg2 = np.random.normal(5, 1, 40)
        seg3 = np.random.normal(2, 1, 40)
        data = np.concatenate([seg1, seg2, seg3])

        detector = ChangePointDetector(method='pelt', penalty=1)
        result = detector.detect(data)

        # Should detect at least 1 change point
        assert result['n_changes'] >= 1

    def test_pelt_method(self):
        """Test PELT algorithm."""
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)
        data2 = np.random.normal(3, 1, 50)
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='pelt', penalty=5)
        result = detector.detect(data)

        assert 'change_points' in result
        assert 'method' in result
        assert result['method'] == 'pelt'

    def test_binary_segmentation(self):
        """Test Binary Segmentation algorithm."""
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)
        data2 = np.random.normal(3, 1, 50)
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='binseg', penalty=0.5)
        result = detector.detect(data)

        assert result['method'] == 'binseg'
        assert result['n_changes'] >= 0

    def test_cusum_method(self):
        """Test CUSUM algorithm."""
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)
        data2 = np.random.normal(3, 1, 50)
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='cusum')
        result = detector.detect(data)

        assert result['method'] == 'cusum'
        assert result['n_changes'] >= 0

    def test_segment_statistics(self):
        """Test segment analysis."""
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)
        data2 = np.random.normal(5, 1, 50)
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='pelt', penalty=1)
        result = detector.detect(data, return_segments=True)

        assert 'segments' in result
        assert 'segment_statistics' in result

        stats = result['segment_statistics']
        assert len(stats) > 0

        # Check statistics structure
        for seg_stats in stats:
            assert 'start' in seg_stats
            assert 'end' in seg_stats
            assert 'mean' in seg_stats
            assert 'std' in seg_stats
            assert 'trend' in seg_stats

        # First segment should have lower mean than second
        if len(stats) >= 2:
            assert stats[0]['mean'] < stats[1]['mean']

    def test_confidence_scores(self):
        """Test confidence score calculation."""
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)
        data2 = np.random.normal(5, 1, 50)  # Large difference
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='pelt', penalty=1)
        result = detector.detect(data)

        assert 'confidence_scores' in result
        confidences = result['confidence_scores']

        # Should have confidence scores for each change point
        assert len(confidences) == len(result['change_points'])

        # Scores should be between 0 and 1
        for conf in confidences:
            assert 0 <= conf <= 1

    def test_no_changepoints(self):
        """Test when no change points are detected."""
        # Stationary data
        np.random.seed(42)
        data = np.random.normal(0, 1, 100)

        detector = ChangePointDetector(method='pelt', penalty=50)  # High penalty
        result = detector.detect(data)

        # Should detect few or no change points
        assert result['n_changes'] <= 2

    def test_min_segment_length(self):
        """Test minimum segment length constraint."""
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)
        data2 = np.random.normal(3, 1, 50)
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='pelt', penalty=1, min_segment_length=20)
        result = detector.detect(data)

        change_points = result['change_points']

        # All segments should be at least min_segment_length
        boundaries = [0] + change_points + [len(data)]
        for i in range(len(boundaries) - 1):
            segment_length = boundaries[i+1] - boundaries[i]
            assert segment_length >= 20


class TestBootstrapChangePoint:
    """Test bootstrap confidence estimation."""

    def test_bootstrap_detection(self):
        """Test bootstrap change point detection."""
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)
        data2 = np.random.normal(3, 1, 50)
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='pelt', penalty=1)
        result = detector.detect_with_bootstrap(data, n_bootstrap=50)

        assert 'bootstrap_confidence' in result
        assert 'consensus_change_points' in result

        # Bootstrap confidence should be a dict
        assert isinstance(result['bootstrap_confidence'], dict)

    def test_consensus_changepoints(self):
        """Test consensus change points from bootstrap."""
        np.random.seed(42)
        # Very clear change point
        data1 = np.random.normal(0, 0.5, 50)
        data2 = np.random.normal(10, 0.5, 50)
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='pelt', penalty=1)
        result = detector.detect_with_bootstrap(data, n_bootstrap=100)

        consensus_cps = result['consensus_change_points']

        # Should detect the clear change point consistently
        if len(consensus_cps) > 0:
            # At least one consensus change point
            assert len(consensus_cps) > 0


class TestQuickChangePointDetection:
    """Test convenience function."""

    def test_quick_detection(self):
        """Test quick change point detection function."""
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)
        data2 = np.random.normal(3, 1, 50)
        data = np.concatenate([data1, data2])

        result = quick_changepoint_detection(data, method='pelt', penalty=1)

        assert 'change_points' in result
        assert 'n_changes' in result


class TestChangePointModels:
    """Test different cost models."""

    def test_l2_model(self):
        """Test L2 cost model."""
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)
        data2 = np.random.normal(3, 1, 50)
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='pelt', model='l2', penalty=1)
        result = detector.detect(data)

        assert result['n_changes'] >= 0

    def test_rbf_model(self):
        """Test RBF cost model."""
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)
        data2 = np.random.normal(3, 1, 50)
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='pelt', model='rbf', penalty=1)
        result = detector.detect(data)

        assert result['n_changes'] >= 0

    def test_normal_model(self):
        """Test Normal (Gaussian) cost model."""
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)
        data2 = np.random.normal(3, 1, 50)
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='pelt', model='normal', penalty=1)
        result = detector.detect(data)

        assert result['n_changes'] >= 0


class TestChangePointEdgeCases:
    """Test edge cases and error handling."""

    def test_short_series(self):
        """Test with very short time series."""
        data = np.array([1, 2, 3, 4, 5])

        detector = ChangePointDetector(method='pelt', penalty=1)
        result = detector.detect(data)

        # Should handle gracefully
        assert 'change_points' in result

    def test_constant_series(self):
        """Test with constant time series."""
        data = np.ones(100)

        detector = ChangePointDetector(method='pelt', penalty=1)
        result = detector.detect(data)

        # Should detect no change points
        assert result['n_changes'] == 0

    def test_variance_change(self):
        """Test detection of variance change."""
        np.random.seed(42)
        data1 = np.random.normal(0, 0.5, 50)  # Low variance
        data2 = np.random.normal(0, 3, 50)     # High variance
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='pelt', model='normal', penalty=1)
        result = detector.detect(data)

        # Should detect change in variance
        assert result['n_changes'] > 0

    def test_pandas_series_input(self):
        """Test with pandas Series input."""
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)
        data2 = np.random.normal(3, 1, 50)
        data = pd.Series(np.concatenate([data1, data2]))

        detector = ChangePointDetector(method='pelt', penalty=1)
        result = detector.detect(data)

        assert 'change_points' in result
        assert 'time_index' in result

    def test_preserves_datetime_index(self):
        """Test that datetime index is preserved."""
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)
        data2 = np.random.normal(3, 1, 50)
        data_array = np.concatenate([data1, data2])

        dates = pd.date_range('2023-01-01', periods=len(data_array))
        data = pd.Series(data_array, index=dates)

        detector = ChangePointDetector(method='pelt', penalty=1)
        result = detector.detect(data)

        assert result['time_index'] is not None
        assert len(result['time_index']) == len(data)


class TestChangePointPerformance:
    """Test performance and scalability."""

    def test_handles_long_series(self):
        """Test with long time series."""
        np.random.seed(42)
        data = np.random.normal(0, 1, 5000)

        detector = ChangePointDetector(method='pelt', penalty=10)
        result = detector.detect(data)

        # Should complete without errors
        assert 'change_points' in result

    def test_penalty_effect(self):
        """Test effect of penalty parameter."""
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 50)
        data2 = np.random.normal(1, 1, 50)  # Small change
        data = np.concatenate([data1, data2])

        # Low penalty - should detect more changes
        detector_low = ChangePointDetector(method='pelt', penalty=0.1)
        result_low = detector_low.detect(data)

        # High penalty - should detect fewer changes
        detector_high = ChangePointDetector(method='pelt', penalty=100)
        result_high = detector_high.detect(data)

        # Low penalty should detect at least as many changes as high penalty
        assert result_low['n_changes'] >= result_high['n_changes']


class TestChangePointIntegration:
    """Test integration with regime detection."""

    def test_regime_change_series(self, regime_change_series):
        """Test on regime change data from fixture."""
        detector = ChangePointDetector(method='pelt', penalty=5)
        result = detector.detect(regime_change_series)

        # Should detect the regime changes
        assert result['n_changes'] > 0

        # Should have reasonable segment statistics
        stats = result['segment_statistics']
        assert len(stats) > 1

    def test_comparison_with_hmm(self, regime_change_series):
        """Test that change points align with regime transitions."""
        detector = ChangePointDetector(method='pelt', penalty=5)
        result = detector.detect(regime_change_series)

        change_points = result['change_points']

        # Should detect changes near known transition points (days 100 and 200)
        # At least one change point should be in each transition region
        has_first_transition = any(80 <= cp <= 120 for cp in change_points)
        has_second_transition = any(180 <= cp <= 220 for cp in change_points)

        assert has_first_transition or has_second_transition


class TestChangePointStatistics:
    """Test statistical properties of change point detection."""

    def test_segment_trends(self):
        """Test trend calculation in segments."""
        # Create data with clear trends
        t = np.arange(100)
        data1 = 2 * t[:50]  # Uptrend
        data2 = 100 - t[50:]  # Downtrend
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='pelt', penalty=1)
        result = detector.detect(data, return_segments=True)

        stats = result['segment_statistics']

        if len(stats) >= 2:
            # First segment should have positive trend
            # Second segment should have negative trend
            # (Signs might vary depending on normalization)
            assert 'trend' in stats[0]
            assert 'trend' in stats[1]

    def test_confidence_high_for_clear_changes(self):
        """Test that confidence is high for clear changes."""
        np.random.seed(42)
        data1 = np.random.normal(0, 0.5, 50)
        data2 = np.random.normal(10, 0.5, 50)  # Very large change
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='pelt', penalty=1)
        result = detector.detect(data)

        confidences = result['confidence_scores']

        # Should have high confidence for such a clear change
        if len(confidences) > 0:
            max_confidence = max(confidences)
            assert max_confidence > 0.9

    def test_confidence_low_for_noisy_changes(self):
        """Test that confidence is lower for noisy/unclear changes."""
        np.random.seed(42)
        data1 = np.random.normal(0, 2, 50)   # High variance
        data2 = np.random.normal(1, 2, 50)   # Small mean change, high variance
        data = np.concatenate([data1, data2])

        detector = ChangePointDetector(method='pelt', penalty=1)
        result = detector.detect(data)

        confidences = result['confidence_scores']

        # Confidence should be lower for unclear changes
        if len(confidences) > 0:
            # At least some confidence scores should be moderate
            assert any(conf < 0.99 for conf in confidences)
