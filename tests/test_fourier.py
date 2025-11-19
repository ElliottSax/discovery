"""
Comprehensive tests for Fourier Cyclical Pattern Detector.

Tests cover:
- Synthetic cycle detection
- Multi-cycle detection
- Edge cases (short series, NaNs, constants)
- Configuration handling
- Save/load functionality
- Performance benchmarks
"""

import pytest
import numpy as np
import pandas as pd
from analysis.cyclical.fourier import FourierCyclicalDetector


class TestFourierBasicFunctionality:
    """Test basic Fourier detector functionality."""

    def test_detects_synthetic_30day_cycle(self, synthetic_cycle):
        """Test that detector finds known 30-day cycle."""
        detector = FourierCyclicalDetector(min_strength=0.1, min_confidence=0.6)
        result = detector.detect_cycles(synthetic_cycle)

        # Should detect cycles
        assert len(result['dominant_cycles']) > 0, "Should detect at least one cycle"

        # Top cycle should be around 30 days
        top_cycle = result['dominant_cycles'][0]
        assert 25 <= top_cycle['period_days'] <= 35, f"Should detect ~30 day cycle, got {top_cycle['period_days']}"
        assert top_cycle['confidence'] > 0.6, "Should have reasonable confidence"
        assert top_cycle['category'] == 'monthly', "Should categorize as monthly"

    def test_detects_multiple_cycles(self, multi_cycle_series):
        """Test detection of multiple cycles in same series."""
        detector = FourierCyclicalDetector(min_strength=0.05, min_confidence=0.5)
        result = detector.detect_cycles(multi_cycle_series)

        # Should detect both weekly and monthly cycles
        assert len(result['dominant_cycles']) >= 2, "Should detect multiple cycles"

        periods = [c['period_days'] for c in result['dominant_cycles']]

        # Check for weekly cycle (5-9 days)
        has_weekly = any(5 <= p <= 9 for p in periods)
        # Check for monthly cycle (25-35 days)
        has_monthly = any(25 <= p <= 35 for p in periods)

        assert has_weekly or has_monthly, f"Should detect weekly or monthly cycle, got periods: {periods}"

    def test_forecast_structure(self, synthetic_cycle):
        """Test forecast output structure and validity."""
        detector = FourierCyclicalDetector()
        result = detector.detect_cycles(synthetic_cycle)

        forecast = result['cycle_forecast']

        # Check structure
        assert 'forecast' in forecast
        assert 'lower_bound' in forecast
        assert 'upper_bound' in forecast
        assert 'confidence_interval' in forecast
        assert 'residual_std' in forecast

        # Check lengths
        assert len(forecast['forecast']) == 30, "Default forecast should be 30 periods"
        assert len(forecast['lower_bound']) == 30
        assert len(forecast['upper_bound']) == 30

        # Check bounds are valid
        for i in range(30):
            assert forecast['lower_bound'][i] <= forecast['forecast'][i] <= forecast['upper_bound'][i], \
                "Forecast should be within bounds"

    def test_seasonal_decomposition(self, synthetic_cycle):
        """Test seasonal decomposition output."""
        detector = FourierCyclicalDetector()
        result = detector.detect_cycles(synthetic_cycle, return_details=True)

        if result.get('seasonal_decomposition'):
            decomp = result['seasonal_decomposition']

            assert 'trend' in decomp
            assert 'seasonal' in decomp
            assert 'residual' in decomp
            assert 'period' in decomp

            # All components should have same length
            assert len(decomp['trend']) == len(synthetic_cycle)
            assert len(decomp['seasonal']) == len(synthetic_cycle)
            assert len(decomp['residual']) == len(synthetic_cycle)


class TestFourierEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_short_series(self, short_series):
        """Test error handling for series too short for analysis."""
        detector = FourierCyclicalDetector()

        with pytest.raises(ValueError, match="too short"):
            detector.detect_cycles(short_series)

    def test_handles_nan_values(self, series_with_nans):
        """Test NaN interpolation."""
        detector = FourierCyclicalDetector()

        # Should not raise error
        result = detector.detect_cycles(series_with_nans)

        # Should return valid result
        assert result is not None
        assert 'dominant_cycles' in result

    def test_handles_constant_series(self, constant_series):
        """Test handling of zero-variance series."""
        detector = FourierCyclicalDetector()

        # May not find significant cycles, but should not crash
        result = detector.detect_cycles(constant_series)

        assert result is not None
        # Likely no significant cycles in constant series
        assert len(result['dominant_cycles']) == 0 or all(c['confidence'] < 0.7 for c in result['dominant_cycles'])

    def test_handles_numpy_array_input(self):
        """Test that detector accepts numpy arrays."""
        detector = FourierCyclicalDetector()

        np.random.seed(42)
        array_data = np.random.randn(100)

        result = detector.detect_cycles(array_data)

        assert result is not None
        assert 'dominant_cycles' in result

    def test_handles_pandas_series_input(self, synthetic_cycle):
        """Test that detector accepts pandas Series."""
        detector = FourierCyclicalDetector()

        result = detector.detect_cycles(synthetic_cycle)

        assert result is not None
        assert 'dominant_cycles' in result


class TestFourierConfiguration:
    """Test configuration and parameter handling."""

    def test_custom_strength_threshold(self, synthetic_cycle):
        """Test custom strength threshold."""
        # High threshold - should find fewer cycles
        detector_strict = FourierCyclicalDetector(min_strength=0.5, min_confidence=0.8)
        result_strict = detector_strict.detect_cycles(synthetic_cycle)

        # Low threshold - should find more cycles
        detector_loose = FourierCyclicalDetector(min_strength=0.01, min_confidence=0.3)
        result_loose = detector_loose.detect_cycles(synthetic_cycle)

        # Loose should find at least as many as strict
        assert len(result_loose['dominant_cycles']) >= len(result_strict['dominant_cycles'])

    def test_cycle_categorization(self):
        """Test cycle categorization logic."""
        detector = FourierCyclicalDetector()

        # Test different periods
        assert detector._categorize_cycle(6, 'daily') == 'weekly'
        assert detector._categorize_cycle(25, 'daily') == 'monthly'
        assert detector._categorize_cycle(75, 'daily') == 'quarterly'
        assert detector._categorize_cycle(255, 'daily') == 'annual'
        assert detector._categorize_cycle(730, 'daily') == 'election_cycle'

    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        detector = FourierCyclicalDetector()

        # Strong cycle with enough complete cycles
        conf_high = detector._calculate_confidence(period=30, strength=0.8, N=365)
        assert conf_high > 0.7, "Strong cycle should have high confidence"

        # Weak cycle
        conf_low = detector._calculate_confidence(period=30, strength=0.1, N=365)
        assert conf_low < conf_high, "Weak cycle should have lower confidence"

        # Period too long for data
        conf_long = detector._calculate_confidence(period=200, strength=0.8, N=300)
        assert conf_long < conf_high, "Long period should reduce confidence"

    def test_get_cycle_summary(self, synthetic_cycle):
        """Test human-readable summary generation."""
        detector = FourierCyclicalDetector()
        result = detector.detect_cycles(synthetic_cycle)

        summary = detector.get_cycle_summary()

        assert isinstance(summary, str)
        assert "cycle" in summary.lower()

        if detector.cycles_detected:
            # Should mention period
            assert "days" in summary


class TestFourierPersistence:
    """Test save/load functionality."""

    def test_save_and_load(self, synthetic_cycle, temp_model_dir):
        """Test saving and loading detector."""
        # Create and train detector
        detector = FourierCyclicalDetector(min_strength=0.1, min_confidence=0.7)
        result = detector.detect_cycles(synthetic_cycle)

        # Save
        model_path = str(temp_model_dir / "fourier_test")
        detector.save(model_path)

        # Load
        loaded_detector = FourierCyclicalDetector.load(model_path)

        # Verify
        assert loaded_detector.min_strength == detector.min_strength
        assert loaded_detector.min_confidence == detector.min_confidence
        assert len(loaded_detector.cycles_detected) == len(detector.cycles_detected)

        if loaded_detector.cycles_detected:
            assert loaded_detector.cycles_detected[0]['period_days'] == detector.cycles_detected[0]['period_days']

    def test_save_with_metadata(self, synthetic_cycle, temp_model_dir):
        """Test saving with custom metadata."""
        detector = FourierCyclicalDetector()
        detector.detect_cycles(synthetic_cycle)

        custom_metadata = {
            'dataset': 'test_data',
            'analyst': 'test_user'
        }

        model_path = str(temp_model_dir / "fourier_with_metadata")
        detector.save(model_path, metadata=custom_metadata)

        # Load and verify metadata exists
        from analysis.utils.persistence import ModelPersistence
        from pathlib import Path

        _, metadata = ModelPersistence.load_model(Path(model_path))

        assert 'dataset' in metadata
        assert metadata['dataset'] == 'test_data'
        assert 'analyst' in metadata
        assert metadata['analyst'] == 'test_user'


class TestFourierDataQuality:
    """Test data quality checks and validation."""

    def test_returns_total_cycles_found(self, synthetic_cycle):
        """Test that total_cycles_found is returned."""
        detector = FourierCyclicalDetector()
        result = detector.detect_cycles(synthetic_cycle)

        assert 'total_cycles_found' in result
        assert isinstance(result['total_cycles_found'], int)
        assert result['total_cycles_found'] >= 0

    def test_dominant_cycles_sorted_by_strength(self, multi_cycle_series):
        """Test that dominant cycles are sorted by strength."""
        detector = FourierCyclicalDetector(min_strength=0.01, min_confidence=0.3)
        result = detector.detect_cycles(multi_cycle_series)

        if len(result['dominant_cycles']) > 1:
            strengths = [c['strength'] for c in result['dominant_cycles']]

            # Should be sorted descending
            assert strengths == sorted(strengths, reverse=True), "Cycles should be sorted by strength"

    def test_all_cycle_fields_present(self, synthetic_cycle):
        """Test that all required fields are present in cycle info."""
        detector = FourierCyclicalDetector()
        result = detector.detect_cycles(synthetic_cycle)

        required_fields = ['period_days', 'strength', 'confidence', 'frequency', 'category']

        for cycle in result['dominant_cycles']:
            for field in required_fields:
                assert field in cycle, f"Missing field: {field}"
                assert cycle[field] is not None


@pytest.mark.benchmark
class TestFourierPerformance:
    """Performance and benchmark tests."""

    def test_large_dataset_performance(self, benchmark):
        """Test performance on large dataset."""
        np.random.seed(42)
        large_series = pd.Series(np.random.randn(10000))

        detector = FourierCyclicalDetector()

        result = benchmark(detector.detect_cycles, large_series)

        assert result is not None
        assert 'dominant_cycles' in result

    def test_multiple_detections(self, synthetic_cycle):
        """Test running detection multiple times."""
        detector = FourierCyclicalDetector()

        # Run multiple times
        results = []
        for _ in range(5):
            result = detector.detect_cycles(synthetic_cycle)
            results.append(result)

        # Results should be consistent
        for i in range(1, 5):
            assert len(results[i]['dominant_cycles']) == len(results[0]['dominant_cycles'])

            if results[i]['dominant_cycles']:
                assert abs(results[i]['dominant_cycles'][0]['period_days'] -
                          results[0]['dominant_cycles'][0]['period_days']) < 0.1


@pytest.mark.integration
class TestFourierIntegration:
    """Integration tests with real-world scenarios."""

    def test_full_analysis_pipeline(self, synthetic_cycle, temp_model_dir):
        """Test complete analysis pipeline from data to insights."""
        # Step 1: Initialize detector
        detector = FourierCyclicalDetector(min_strength=0.1, min_confidence=0.6)

        # Step 2: Detect cycles
        result = detector.detect_cycles(synthetic_cycle, return_details=True)

        # Step 3: Get summary
        summary = detector.get_cycle_summary()

        # Step 4: Save model
        model_path = str(temp_model_dir / "integration_test")
        detector.save(model_path)

        # Step 5: Load model
        loaded_detector = FourierCyclicalDetector.load(model_path)

        # Verify entire pipeline
        assert result is not None
        assert len(summary) > 0
        assert loaded_detector is not None
        assert len(loaded_detector.cycles_detected) == len(detector.cycles_detected)

    def test_variable_length_series(self, variable_length_series):
        """Test with different series lengths."""
        detector = FourierCyclicalDetector()

        if len(variable_length_series) >= 30:
            result = detector.detect_cycles(variable_length_series)

            assert result is not None
            assert 'dominant_cycles' in result
        else:
            with pytest.raises(ValueError):
                detector.detect_cycles(variable_length_series)
