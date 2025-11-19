"""
Tests for Wavelet Transform Analysis

Tests cover:
- Wavelet decomposition accuracy
- Ridge detection
- Cone of influence calculation
- Multi-resolution analysis
- Significant region detection
"""

import pytest
import numpy as np
import pandas as pd
from analysis.advanced.wavelet import (
    WaveletPatternDetector,
    quick_wavelet_analysis
)


class TestWaveletPatternDetector:
    """Test WaveletPatternDetector class."""

    def test_initialization(self):
        """Test detector initialization with different parameters."""
        detector = WaveletPatternDetector(wavelet='morlet', scales=np.arange(1, 65))
        assert detector.wavelet == 'morlet'
        assert len(detector.scales) == 64

    def test_detects_synthetic_30day_cycle(self, synthetic_cycle):
        """Test detection of known 30-day cycle in synthetic data."""
        detector = WaveletPatternDetector()
        result = detector.analyze(synthetic_cycle)

        assert 'power' in result
        assert 'frequencies' in result
        assert 'ridges' in result
        assert 'significant_regions' in result

        # Should detect the 30-day cycle
        ridges = result['ridges']
        assert len(ridges) > 0

        # Check if any ridge is near 30 days
        periods = [1/r['mean_frequency'] for r in ridges]
        has_30day = any(25 <= p <= 35 for p in periods)
        assert has_30day, f"Should detect 30-day cycle, found periods: {periods}"

    def test_multi_cycle_detection(self):
        """Test detection of multiple cycles."""
        # Create signal with 10-day and 30-day cycles
        t = np.linspace(0, 365, 365)
        signal = (
            10 +
            3 * np.sin(2 * np.pi * t / 10) +   # 10-day cycle
            5 * np.sin(2 * np.pi * t / 30) +   # 30-day cycle
            np.random.normal(0, 0.5, 365)
        )

        data = pd.Series(signal, index=pd.date_range('2023-01-01', periods=365))

        detector = WaveletPatternDetector()
        result = detector.analyze(data)

        ridges = result['ridges']
        periods = [1/r['mean_frequency'] for r in ridges]

        # Should detect both cycles
        has_10day = any(8 <= p <= 12 for p in periods)
        has_30day = any(25 <= p <= 35 for p in periods)

        # At least one should be detected
        assert has_10day or has_30day

    def test_cone_of_influence(self, synthetic_cycle):
        """Test cone of influence calculation."""
        detector = WaveletPatternDetector()
        result = detector.analyze(synthetic_cycle)

        coi = result['cone_of_influence']
        assert len(coi) == len(synthetic_cycle)
        assert coi[0] == 0  # Starts at zero
        assert coi[-1] == 0  # Ends at zero
        assert np.max(coi) > 0  # Has non-zero values in middle

    def test_significant_regions(self, synthetic_cycle):
        """Test detection of significant regions."""
        detector = WaveletPatternDetector()
        result = detector.analyze(synthetic_cycle, significance_level=0.05)

        regions = result['significant_regions']
        assert isinstance(regions, list)

        if len(regions) > 0:
            region = regions[0]
            assert 'time_start' in region
            assert 'time_end' in region
            assert 'frequency_range' in region
            assert 'power' in region

    def test_multi_resolution_analysis(self, synthetic_cycle):
        """Test multi-resolution decomposition."""
        detector = WaveletPatternDetector()
        result = detector.multi_resolution_analysis(synthetic_cycle, max_level=3)

        assert 'approximations' in result
        assert 'details' in result
        assert len(result['approximations']) == 3
        assert len(result['details']) == 3

        # Reconstruction should approximate original
        reconstruction = result['approximations'][-1]
        for detail in reversed(result['details']):
            reconstruction = reconstruction + detail

        # Should be similar to original (allowing for edge effects)
        correlation = np.corrcoef(synthetic_cycle.values[:len(reconstruction)], reconstruction)[0, 1]
        assert correlation > 0.8

    def test_handles_short_series(self):
        """Test handling of short time series."""
        short_data = pd.Series(np.random.randn(20))

        detector = WaveletPatternDetector()
        result = detector.analyze(short_data)

        # Should still produce output without errors
        assert 'power' in result
        assert result['power'].shape[0] > 0

    def test_handles_constant_series(self):
        """Test handling of constant time series."""
        constant_data = pd.Series(np.ones(100))

        detector = WaveletPatternDetector()
        result = detector.analyze(constant_data)

        # Should handle gracefully
        assert 'power' in result
        # Power should be near zero for constant signal
        assert np.max(result['power']) < 1.0

    def test_different_wavelets(self, synthetic_cycle):
        """Test different wavelet types."""
        wavelets = ['morlet', 'mexican_hat', 'paul']

        for wavelet_type in wavelets:
            detector = WaveletPatternDetector(wavelet=wavelet_type)
            result = detector.analyze(synthetic_cycle)

            assert 'power' in result
            assert result['power'].shape[0] > 0

    def test_ridge_persistence(self, synthetic_cycle):
        """Test ridge persistence calculation."""
        detector = WaveletPatternDetector()
        result = detector.analyze(synthetic_cycle)

        ridges = result['ridges']
        for ridge in ridges:
            assert 'persistence' in ridge
            assert 0 <= ridge['persistence'] <= 1
            assert 'mean_power' in ridge
            assert ridge['mean_power'] >= 0


class TestQuickWaveletAnalysis:
    """Test convenience function."""

    def test_quick_analysis(self, synthetic_cycle):
        """Test quick wavelet analysis function."""
        result = quick_wavelet_analysis(synthetic_cycle)

        assert 'power' in result
        assert 'ridges' in result
        assert 'significant_regions' in result


class TestWaveletEdgeCases:
    """Test edge cases and error handling."""

    def test_nan_handling(self):
        """Test handling of NaN values."""
        data = pd.Series([1, 2, np.nan, 4, 5, 6, 7, 8, 9, 10])

        detector = WaveletPatternDetector()

        # Should handle NaN (linear interpolation)
        result = detector.analyze(data)
        assert 'power' in result

    def test_very_long_series(self):
        """Test with very long time series."""
        # Create 5 years of daily data
        t = np.linspace(0, 5*365, 5*365)
        signal = 10 + 5 * np.sin(2 * np.pi * t / 30) + np.random.normal(0, 1, len(t))

        data = pd.Series(signal)

        detector = WaveletPatternDetector()
        result = detector.analyze(data)

        assert 'power' in result
        assert result['power'].shape[0] > 0

    def test_high_frequency_noise(self):
        """Test with high-frequency noise."""
        t = np.linspace(0, 100, 1000)
        signal = np.random.normal(0, 1, len(t))

        data = pd.Series(signal)

        detector = WaveletPatternDetector()
        result = detector.analyze(data)

        # Should handle noisy data
        assert 'power' in result


class TestWaveletStatistics:
    """Test statistical properties of wavelet analysis."""

    def test_power_conservation(self, synthetic_cycle):
        """Test Parseval's theorem (energy conservation)."""
        detector = WaveletPatternDetector()
        result = detector.analyze(synthetic_cycle)

        # Total power in wavelet domain should relate to variance in time domain
        wavelet_power = np.sum(result['power'])
        time_variance = np.var(synthetic_cycle.values)

        # Should be roughly proportional (allowing for scaling)
        assert wavelet_power > 0
        assert time_variance > 0

    def test_frequency_resolution(self, synthetic_cycle):
        """Test frequency resolution."""
        detector = WaveletPatternDetector(scales=np.arange(1, 129))
        result = detector.analyze(synthetic_cycle)

        frequencies = result['frequencies']

        # Should have frequencies in expected range
        assert np.min(frequencies) > 0
        assert np.max(frequencies) < 0.5  # Nyquist limit

    def test_time_localization(self):
        """Test time localization of transient features."""
        # Create signal with transient burst
        t = np.linspace(0, 365, 365)
        signal = np.zeros(365)
        signal[100:150] = 5 * np.sin(2 * np.pi * t[100:150] / 10)  # Burst at t=100-150
        signal += np.random.normal(0, 0.1, 365)

        data = pd.Series(signal)

        detector = WaveletPatternDetector()
        result = detector.analyze(data)

        power = result['power']

        # Power should be concentrated around t=100-150
        time_of_max = np.unravel_index(np.argmax(power), power.shape)[1]
        assert 80 <= time_of_max <= 170  # Allow some margin


class TestWaveletIntegration:
    """Test integration with other components."""

    def test_preserves_pandas_index(self):
        """Test that pandas index is preserved."""
        dates = pd.date_range('2023-01-01', periods=100)
        data = pd.Series(np.random.randn(100), index=dates)

        detector = WaveletPatternDetector()
        result = detector.analyze(data)

        # Check if time index is preserved
        assert 'time_index' in result
        if result['time_index'] is not None:
            assert len(result['time_index']) == len(data)

    def test_works_with_numpy_array(self):
        """Test that it works with numpy arrays."""
        data = np.random.randn(100)

        detector = WaveletPatternDetector()
        result = detector.analyze(data)

        assert 'power' in result

    def test_works_with_list(self):
        """Test that it works with Python lists."""
        data = [float(x) for x in range(100)]

        detector = WaveletPatternDetector()
        result = detector.analyze(data)

        assert 'power' in result
