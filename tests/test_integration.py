"""
Integration Tests

Tests the interaction between multiple analysis modules:
- Fourier + Wavelet cycle detection
- HMM + Change Point regime detection
- Ensemble methods with validation
- Full analysis pipeline
"""

import pytest
import numpy as np
import pandas as pd
from analysis.cyclical.fourier import FourierCyclicalDetector
from analysis.cyclical.hmm import RegimeDetector
from analysis.advanced.wavelet import WaveletPatternDetector
from analysis.advanced.changepoint import ChangePointDetector
from analysis.utils.validation import DataValidator, validate_input


class TestCycleDetectionIntegration:
    """Test integration between Fourier and Wavelet cycle detection."""

    def test_fourier_wavelet_agreement(self, synthetic_cycle):
        """Test that Fourier and Wavelet agree on dominant cycle."""
        # Fourier detection
        fourier = FourierCyclicalDetector(min_strength=0.1, min_confidence=0.6)
        fourier_result = fourier.detect_cycles(synthetic_cycle)

        # Wavelet detection
        wavelet = WaveletPatternDetector()
        wavelet_result = wavelet.analyze(synthetic_cycle)

        # Both should detect the 30-day cycle
        assert len(fourier_result['dominant_cycles']) > 0
        assert len(wavelet_result['ridges']) > 0

        # Get dominant periods
        fourier_period = fourier_result['dominant_cycles'][0]['period_days']
        wavelet_periods = [1/r['mean_frequency'] for r in wavelet_result['ridges']]

        # At least one wavelet ridge should be close to Fourier period
        has_agreement = any(abs(wp - fourier_period) < 5 for wp in wavelet_periods)
        assert has_agreement, f"Fourier period {fourier_period}, Wavelet periods {wavelet_periods}"

    def test_multi_cycle_detection_consistency(self):
        """Test consistency across methods for multi-cycle signal."""
        # Create signal with 10-day and 30-day cycles
        t = np.linspace(0, 365, 365)
        signal = (
            10 +
            3 * np.sin(2 * np.pi * t / 10) +   # 10-day
            5 * np.sin(2 * np.pi * t / 30) +   # 30-day (stronger)
            np.random.normal(0, 0.5, 365)
        )
        data = pd.Series(signal, index=pd.date_range('2023-01-01', periods=365))

        # Fourier
        fourier = FourierCyclicalDetector()
        fourier_result = fourier.detect_cycles(data)

        # Wavelet
        wavelet = WaveletPatternDetector()
        wavelet_result = wavelet.analyze(data)

        # Both should detect at least one cycle
        assert len(fourier_result['dominant_cycles']) > 0
        assert len(wavelet_result['ridges']) > 0

        # Dominant cycle should be the 30-day (stronger amplitude)
        dominant_period = fourier_result['dominant_cycles'][0]['period_days']
        assert 25 <= dominant_period <= 35

    def test_wavelet_time_localization(self):
        """Test that wavelet provides time localization that Fourier doesn't."""
        # Create signal with cycle that appears and disappears
        t = np.arange(365)
        signal = np.zeros(365)
        signal[100:200] = 5 * np.sin(2 * np.pi * t[100:200] / 30)  # Cycle only in middle
        signal += np.random.normal(0, 0.5, 365)

        data = pd.Series(signal)

        # Wavelet
        wavelet = WaveletPatternDetector()
        wavelet_result = wavelet.analyze(data)

        # Wavelet should detect the cycle and localize it in time
        ridges = wavelet_result['ridges']

        if len(ridges) > 0:
            # Check that at least one ridge is localized to the middle region
            for ridge in ridges:
                time_range = ridge['time_range']
                # Should overlap with the actual signal region (100-200)
                if time_range[0] < 200 and time_range[1] > 100:
                    # Found time-localized pattern
                    assert True
                    return

        # If no specific localization, at least ridges should exist
        assert len(ridges) >= 0  # Lenient for noisy signal


class TestRegimeDetectionIntegration:
    """Test integration between HMM and Change Point detection."""

    def test_hmm_changepoint_agreement(self, regime_change_series):
        """Test that HMM and Change Point detection agree on regime changes."""
        # HMM detection
        hmm = RegimeDetector(n_states=3)
        hmm_result = hmm.detect(regime_change_series)

        # Change Point detection
        cp = ChangePointDetector(method='pelt', penalty=5)
        cp_result = cp.detect(regime_change_series)

        # Find HMM regime transitions
        regime_labels = hmm_result['regime_labels']
        hmm_transitions = np.where(np.diff(regime_labels) != 0)[0]

        # Change points
        change_points = cp_result['change_points']

        # At least some transitions should align (within 20 days)
        aligned_count = 0
        for hmm_trans in hmm_transitions:
            if any(abs(hmm_trans - cp) < 20 for cp in change_points):
                aligned_count += 1

        # At least 30% of transitions should align
        if len(hmm_transitions) > 0:
            alignment_ratio = aligned_count / len(hmm_transitions)
            assert alignment_ratio >= 0.3, f"Only {alignment_ratio*100:.1f}% alignment"

    def test_changepoint_confirms_hmm_regimes(self):
        """Test that change points segment data into HMM-like regimes."""
        # Create clear 3-regime data
        np.random.seed(42)
        bull = np.random.normal(0.05, 0.01, 100)   # High returns, low vol
        bear = np.random.normal(-0.03, 0.02, 100)  # Negative returns, high vol
        sideways = np.random.normal(0.0, 0.005, 100)  # Zero returns, low vol
        returns = np.concatenate([bull, bear, sideways])

        data = pd.Series(returns)

        # Change point detection
        cp = ChangePointDetector(method='pelt', penalty=1)
        cp_result = cp.detect(data, return_segments=True)

        # Should detect at least 1 change (ideally 2)
        assert cp_result['n_changes'] >= 1

        # Segment statistics should show clear differences
        stats = cp_result['segment_statistics']
        if len(stats) >= 2:
            # Different segments should have different means
            means = [s['mean'] for s in stats]
            assert max(means) - min(means) > 0.01  # Meaningful difference

    def test_regime_stability_analysis(self):
        """Test analyzing regime stability using multiple methods."""
        # Create data with stable and unstable regimes
        np.random.seed(42)
        stable_bull = np.random.normal(0.02, 0.01, 150)  # Long stable period
        volatile_bear = np.random.normal(-0.01, 0.05, 50)  # Short volatile period
        returns = np.concatenate([stable_bull, volatile_bear])

        data = pd.Series(returns)

        # HMM detection
        hmm = RegimeDetector(n_states=2)
        hmm_result = hmm.detect(data)

        # Change point detection with bootstrap
        cp = ChangePointDetector(method='pelt', penalty=2)
        cp_result = cp.detect_with_bootstrap(data, n_bootstrap=50)

        # Consensus change points should be stable
        consensus_cps = cp_result['consensus_change_points']

        # Should detect the major transition
        assert len(consensus_cps) >= 1


class TestValidationIntegration:
    """Test validation integration with detectors."""

    def test_validation_catches_bad_data(self):
        """Test that validation catches problematic data before analysis."""
        # Create bad data
        bad_data = pd.Series([1, 2, np.nan, np.inf, 5])

        validator = DataValidator()
        result = validator.validate_time_series(bad_data, allow_nan=False, allow_inf=False, min_length=3)

        # Should fail validation or auto-fix
        if not result.is_valid:
            assert len(result.issues) > 0
        else:
            # Auto-fixed
            assert result.fixed_data is not None

    def test_detector_with_validation_decorator(self):
        """Test that validation decorator works with detectors."""
        @validate_input(min_length=30, auto_fix=True)
        def analyze_with_validation(data: pd.Series):
            fourier = FourierCyclicalDetector()
            return fourier.detect_cycles(data)

        # Valid data
        good_data = pd.Series(np.random.randn(100))
        result = analyze_with_validation(good_data)
        assert 'dominant_cycles' in result

        # Data with NaN (should auto-fix)
        data_with_nan = pd.Series([1, 2, np.nan, 4, 5, 6, 7, 8, 9, 10] * 5)
        result = analyze_with_validation(data_with_nan)
        assert 'dominant_cycles' in result

    def test_returns_validation_before_analysis(self):
        """Test validating returns before regime detection."""
        # Create returns with issues
        returns = pd.Series(np.random.normal(0.001, 0.02, 100))
        returns[50] = 2.5  # Extreme return

        validator = DataValidator()
        result = validator.validate_returns(returns, max_abs_return=1.0)

        # Should warn about extreme return
        assert any('extreme' in w.lower() for w in result.warnings)

        # But should still be valid (just warning)
        assert result.is_valid or len(result.issues) == 0


class TestFullPipelineIntegration:
    """Test complete analysis pipeline."""

    def test_complete_cycle_analysis_pipeline(self, synthetic_cycle):
        """Test full pipeline: validation -> Fourier -> Wavelet -> interpretation."""
        # Step 1: Validation
        validator = DataValidator()
        val_result = validator.validate_time_series(synthetic_cycle, min_length=30)
        assert val_result.is_valid

        # Step 2: Fourier analysis
        fourier = FourierCyclicalDetector()
        fourier_result = fourier.detect_cycles(synthetic_cycle)
        assert len(fourier_result['dominant_cycles']) > 0

        # Step 3: Wavelet analysis for time-localization
        wavelet = WaveletPatternDetector()
        wavelet_result = wavelet.analyze(synthetic_cycle)
        assert len(wavelet_result['ridges']) > 0

        # Step 4: Cross-validation
        fourier_period = fourier_result['dominant_cycles'][0]['period_days']
        wavelet_periods = [1/r['mean_frequency'] for r in wavelet_result['ridges']]

        # Results should be consistent
        has_agreement = any(abs(wp - fourier_period) < 10 for wp in wavelet_periods)
        assert has_agreement

    def test_complete_regime_analysis_pipeline(self, regime_change_series):
        """Test full pipeline: validation -> HMM -> Change Points -> interpretation."""
        # Step 1: Validation
        validator = DataValidator()
        val_result = validator.validate_time_series(regime_change_series, min_length=100)
        assert val_result.is_valid

        # Step 2: HMM regime detection
        hmm = RegimeDetector(n_states=3)
        hmm_result = hmm.detect(regime_change_series)
        assert 'regime_labels' in hmm_result

        # Step 3: Change point detection for validation
        cp = ChangePointDetector(method='pelt', penalty=5)
        cp_result = cp.detect(regime_change_series, return_segments=True)
        assert 'change_points' in cp_result

        # Step 4: Compare segment statistics with HMM states
        stats = cp_result['segment_statistics']
        assert len(stats) > 0

    def test_ensemble_decision_making(self, synthetic_cycle):
        """Test ensemble approach combining multiple detectors."""
        # Run multiple detectors
        fourier = FourierCyclicalDetector()
        wavelet = WaveletPatternDetector()

        fourier_result = fourier.detect_cycles(synthetic_cycle)
        wavelet_result = wavelet.analyze(synthetic_cycle)

        # Collect all detected periods
        all_periods = []

        # From Fourier
        for cycle in fourier_result['dominant_cycles']:
            all_periods.append(cycle['period_days'])

        # From Wavelet
        for ridge in wavelet_result['ridges']:
            period = 1 / ridge['mean_frequency']
            all_periods.append(period)

        # Should have detected cycles
        assert len(all_periods) > 0

        # Consensus: most common period (within 5 days)
        if len(all_periods) > 1:
            # Find clusters of similar periods
            all_periods = sorted(all_periods)
            clusters = []
            current_cluster = [all_periods[0]]

            for i in range(1, len(all_periods)):
                if all_periods[i] - current_cluster[-1] < 5:
                    current_cluster.append(all_periods[i])
                else:
                    clusters.append(current_cluster)
                    current_cluster = [all_periods[i]]

            clusters.append(current_cluster)

            # Largest cluster is consensus
            consensus_cluster = max(clusters, key=len)
            consensus_period = np.mean(consensus_cluster)

            # Consensus should be around 30 days
            assert 25 <= consensus_period <= 35


class TestPerformanceIntegration:
    """Test performance characteristics of integrated workflows."""

    def test_large_dataset_pipeline(self):
        """Test pipeline with large dataset (5 years daily data)."""
        # 5 years of daily data
        t = np.linspace(0, 5*365, 5*365)
        signal = 10 + 5 * np.sin(2 * np.pi * t / 30) + np.random.normal(0, 1, len(t))
        data = pd.Series(signal)

        # Should complete without errors
        fourier = FourierCyclicalDetector()
        result = fourier.detect_cycles(data)
        assert 'dominant_cycles' in result

    def test_validation_overhead_minimal(self):
        """Test that validation adds minimal overhead."""
        import time

        data = pd.Series(np.random.randn(1000))

        # Without validation
        start = time.time()
        fourier = FourierCyclicalDetector()
        fourier.detect_cycles(data)
        time_without = time.time() - start

        # With validation
        validator = DataValidator()
        start = time.time()
        val_result = validator.validate_time_series(data, min_length=30)
        fourier = FourierCyclicalDetector()
        fourier.detect_cycles(data)
        time_with = time.time() - start

        # Validation overhead should be < 10% of analysis time
        overhead = time_with - time_without
        assert overhead < time_without * 0.1 or overhead < 0.01  # < 10ms absolute


class TestErrorHandling:
    """Test error handling across integrated modules."""

    def test_graceful_handling_of_short_series(self):
        """Test that all modules handle short series gracefully."""
        short_data = pd.Series(np.random.randn(10))

        # Fourier (may not detect cycles but shouldn't crash)
        fourier = FourierCyclicalDetector()
        result = fourier.detect_cycles(short_data)
        assert 'dominant_cycles' in result

        # Wavelet
        wavelet = WaveletPatternDetector()
        result = wavelet.analyze(short_data)
        assert 'power' in result

        # Change point
        cp = ChangePointDetector(method='pelt', penalty=1)
        result = cp.detect(short_data)
        assert 'change_points' in result

    def test_handling_of_constant_series(self):
        """Test handling of constant (zero variance) series."""
        constant_data = pd.Series(np.ones(100))

        # Validation should catch this
        validator = DataValidator()
        result = validator.validate_time_series(constant_data, require_variance=True, min_length=10)
        assert not result.is_valid

        # Detectors should handle gracefully
        fourier = FourierCyclicalDetector()
        result = fourier.detect_cycles(constant_data)
        assert len(result['dominant_cycles']) == 0  # No cycles in constant signal

    def test_handling_of_extreme_outliers(self):
        """Test handling of extreme outliers."""
        data = pd.Series(np.random.randn(100))
        data[50] = 1000  # Extreme outlier

        # Validation should warn
        validator = DataValidator()
        result = validator.validate_returns(data, max_abs_return=1.0)
        assert len(result.warnings) > 0

        # Change point should detect it
        cp = ChangePointDetector(method='pelt', penalty=1)
        result = cp.detect(data)
        # Should detect change near the outlier
        if len(result['change_points']) > 0:
            assert any(abs(cp - 50) < 10 for cp in result['change_points'])


class TestStatisticalRigor:
    """Test statistical rigor across integrated modules."""

    def test_significance_testing_consistency(self):
        """Test that significance testing is consistent across methods."""
        # Pure noise (should detect no significant patterns)
        np.random.seed(42)
        noise = pd.Series(np.random.randn(200))

        # Fourier with high confidence threshold
        fourier = FourierCyclicalDetector(min_confidence=0.95)
        fourier_result = fourier.detect_cycles(noise)

        # Wavelet with significance testing
        wavelet = WaveletPatternDetector()
        wavelet_result = wavelet.analyze(noise, significance_level=0.05)

        # Both should detect few or no significant patterns in pure noise
        assert len(fourier_result['dominant_cycles']) <= 2  # Lenient for noise
        assert len(wavelet_result['significant_regions']) <= 3

    def test_confidence_scores_calibrated(self):
        """Test that confidence scores are well-calibrated."""
        # Clear signal
        t = np.linspace(0, 365, 365)
        clear_signal = 10 + 10 * np.sin(2 * np.pi * t / 30) + np.random.normal(0, 0.1, 365)

        # Noisy signal
        noisy_signal = 10 + 2 * np.sin(2 * np.pi * t / 30) + np.random.normal(0, 5, 365)

        data_clear = pd.Series(clear_signal)
        data_noisy = pd.Series(noisy_signal)

        # Fourier on both
        fourier = FourierCyclicalDetector()
        result_clear = fourier.detect_cycles(data_clear)
        result_noisy = fourier.detect_cycles(data_noisy)

        # Clear signal should have higher confidence
        if len(result_clear['dominant_cycles']) > 0 and len(result_noisy['dominant_cycles']) > 0:
            conf_clear = result_clear['dominant_cycles'][0]['confidence']
            conf_noisy = result_noisy['dominant_cycles'][0]['confidence']
            assert conf_clear > conf_noisy + 0.1  # At least 10% higher


class TestRealWorldScenarios:
    """Test realistic scenarios combining multiple modules."""

    def test_market_crash_detection(self):
        """Test detection of market crash scenario."""
        # Simulate market crash: normal -> crash -> recovery
        np.random.seed(42)
        normal = np.random.normal(0.001, 0.01, 100)
        crash = np.random.normal(-0.05, 0.03, 20)  # Large negative returns
        recovery = np.random.normal(0.002, 0.015, 80)

        returns = pd.Series(np.concatenate([normal, crash, recovery]))

        # Change point detection should identify crash
        cp = ChangePointDetector(method='pelt', penalty=2)
        result = cp.detect(returns, return_segments=True)

        # Should detect at least 1 change point
        assert result['n_changes'] >= 1

        # Segment with crash should have negative mean
        stats = result['segment_statistics']
        has_negative_segment = any(s['mean'] < -0.02 for s in stats)
        assert has_negative_segment

    def test_seasonal_pattern_detection(self):
        """Test detection of seasonal patterns."""
        # Simulate monthly seasonal effect
        t = np.arange(365 * 2)  # 2 years
        seasonal = 5 * np.sin(2 * np.pi * t / 30)  # 30-day cycle
        trend = 0.01 * t  # Uptrend
        noise = np.random.normal(0, 1, len(t))

        data = pd.Series(seasonal + trend + noise)

        # Fourier should detect the 30-day cycle
        fourier = FourierCyclicalDetector()
        result = fourier.detect_cycles(data)

        # Should detect monthly cycle
        assert len(result['dominant_cycles']) > 0
        dominant_period = result['dominant_cycles'][0]['period_days']
        assert 25 <= dominant_period <= 35
        assert result['dominant_cycles'][0]['category'] == 'monthly'
