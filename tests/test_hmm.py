"""
Comprehensive tests for HMM Regime Detector.

Tests cover:
- Regime detection
- State characterization
- Transition probabilities
- Edge cases
- Save/load functionality
"""

import pytest
import numpy as np
import pandas as pd
from analysis.cyclical.hmm import RegimeDetector


class TestHMMBasicFunctionality:
    """Test basic HMM functionality."""

    def test_detects_regimes(self, regime_change_series):
        """Test that HMM detects multiple regimes."""
        detector = RegimeDetector(n_states=3)
        result = detector.fit_and_predict(regime_change_series)

        # Should detect regimes
        assert 'current_regime' in result
        assert 'all_regimes' in result
        assert len(result['all_regimes']) == len(regime_change_series)

        # Should have multiple unique regimes
        unique_regimes = set(result['all_regimes'])
        assert len(unique_regimes) >= 2, "Should detect at least 2 distinct regimes"

    def test_regime_characteristics(self, regime_change_series):
        """Test regime characterization."""
        detector = RegimeDetector(n_states=3)
        result = detector.fit_and_predict(regime_change_series)

        regime_chars = result['regime_characteristics']

        # Check all regimes have characteristics
        for state, chars in regime_chars.items():
            assert 'name' in chars
            assert 'avg_return' in chars
            assert 'volatility' in chars
            assert 'frequency' in chars
            assert 'sample_size' in chars

            # Values should be reasonable
            assert -0.1 <= chars['avg_return'] <= 0.1
            assert 0 <= chars['volatility'] <= 0.1
            assert 0 <= chars['frequency'] <= 1

    def test_transition_matrix(self, regime_change_series):
        """Test transition matrix validity."""
        detector = RegimeDetector(n_states=3)
        result = detector.fit_and_predict(regime_change_series)

        transition_matrix = np.array(result['transition_matrix'])

        # Should be square matrix
        assert transition_matrix.shape[0] == transition_matrix.shape[1]
        assert transition_matrix.shape[0] == detector.n_states

        # Each row should sum to 1 (probability distribution)
        row_sums = transition_matrix.sum(axis=1)
        np.testing.assert_array_almost_equal(row_sums, np.ones(detector.n_states), decimal=5)

        # All probabilities should be between 0 and 1
        assert np.all(transition_matrix >= 0)
        assert np.all(transition_matrix <= 1)

    def test_expected_duration(self, regime_change_series):
        """Test expected duration calculation."""
        detector = RegimeDetector(n_states=3)
        result = detector.fit_and_predict(regime_change_series)

        expected_durations = result['expected_duration']

        # Should have duration for each state
        assert len(expected_durations) == detector.n_states

        # Durations should be positive
        for duration in expected_durations:
            assert duration > 0 or duration == float('inf')


class TestHMMFeatures:
    """Test feature engineering."""

    def test_with_volumes(self, regime_change_series):
        """Test regime detection with volume data."""
        volumes = pd.Series(np.random.uniform(1e6, 1e7, len(regime_change_series)))

        detector = RegimeDetector(n_states=3)
        result = detector.fit_and_predict(regime_change_series, volumes=volumes)

        assert result is not None
        assert 'current_regime' in result

        # Volume should be included in regime characteristics
        for chars in result['regime_characteristics'].values():
            assert 'avg_volume' in chars

    def test_with_additional_features(self, regime_change_series):
        """Test with additional features."""
        additional_features = {
            'momentum': pd.Series(np.random.randn(len(regime_change_series))),
            'trend': pd.Series(np.random.randn(len(regime_change_series)))
        }

        detector = RegimeDetector(n_states=3)
        result = detector.fit_and_predict(
            regime_change_series,
            additional_features=additional_features
        )

        assert result is not None
        assert 'current_regime' in result


class TestHMMEdgeCases:
    """Test edge cases."""

    def test_handles_short_series(self, short_series):
        """Test with short series."""
        detector = RegimeDetector(n_states=2)

        # Should still work but may not be reliable
        result = detector.fit_and_predict(short_series)

        assert result is not None
        assert 'current_regime' in result

    def test_single_state(self):
        """Test with n_states=1."""
        detector = RegimeDetector(n_states=1)

        np.random.seed(42)
        series = pd.Series(np.random.randn(100))

        result = detector.fit_and_predict(series)

        # Should always be in state 0
        assert all(r == 0 for r in result['all_regimes'])

    def test_regime_probabilities(self, regime_change_series):
        """Test regime probability predictions."""
        detector = RegimeDetector(n_states=3)
        result = detector.fit_and_predict(regime_change_series)

        probs = result['regime_probabilities']

        # Probabilities should sum to 1
        assert abs(sum(probs) - 1.0) < 0.001

        # All probabilities should be between 0 and 1
        assert all(0 <= p <= 1 for p in probs)


class TestHMMClassification:
    """Test regime classification logic."""

    def test_regime_classification(self):
        """Test _classify_regime method."""
        detector = RegimeDetector()

        # Bull market
        assert "Bull" in detector._classify_regime(0.02, 0.01, 1e6)

        # Bear market
        assert "Bear" in detector._classify_regime(-0.02, 0.03, 1e6)

        # High volatility
        assert "High Volatility" in detector._classify_regime(0.001, 0.04, 1e6)

        # Low volatility
        assert "Low Volatility" in detector._classify_regime(0.0, 0.005, 1e6)


class TestHMMSummary:
    """Test summary generation."""

    def test_get_regime_summary(self, regime_change_series):
        """Test human-readable summary."""
        detector = RegimeDetector(n_states=3)
        result = detector.fit_and_predict(regime_change_series)

        summary = detector.get_regime_summary(result)

        assert isinstance(summary, str)
        assert "Current Regime" in summary
        assert "Confidence" in summary
        assert "Expected Duration" in summary

    def test_transition_probabilities(self, regime_change_series):
        """Test getting transition probabilities."""
        detector = RegimeDetector(n_states=3)
        result = detector.fit_and_predict(regime_change_series)

        current_regime = result['current_regime']
        transitions = detector.get_regime_transition_probabilities(current_regime)

        # Should return probabilities for all states
        assert len(transitions) == detector.n_states

        # Should sum to 1
        assert abs(sum(transitions.values()) - 1.0) < 0.001


@pytest.mark.integration
class TestHMMIntegration:
    """Integration tests."""

    def test_full_pipeline(self, regime_change_series):
        """Test complete analysis pipeline."""
        # Initialize
        detector = RegimeDetector(n_states=3, n_iter=100)

        # Fit and predict
        result = detector.fit_and_predict(regime_change_series)

        # Get summary
        summary = detector.get_regime_summary(result)

        # Get transitions
        transitions = detector.get_regime_transition_probabilities(
            result['current_regime']
        )

        # Verify
        assert result is not None
        assert len(summary) > 0
        assert len(transitions) == 3


@pytest.mark.benchmark
class TestHMMPerformance:
    """Performance tests."""

    def test_large_dataset(self, benchmark):
        """Test on large dataset."""
        np.random.seed(42)
        large_series = pd.Series(np.random.randn(5000))

        detector = RegimeDetector(n_states=4, n_iter=100)

        result = benchmark(detector.fit_and_predict, large_series)

        assert result is not None
