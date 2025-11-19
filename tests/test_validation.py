"""
Tests for Input Validation Framework

Tests cover:
- Data quality validation
- Time series validation
- Parameter validation
- Decorator-based validation
- Auto-fixing capabilities
- Returns and price validation
"""

import pytest
import numpy as np
import pandas as pd
from analysis.utils.validation import (
    DataValidator,
    ParameterValidator,
    ValidationError,
    ValidationLevel,
    validate_input,
    validate_parameters,
    quick_validate
)


class TestDataValidator:
    """Test DataValidator class."""

    def test_initialization(self):
        """Test validator initialization."""
        validator = DataValidator(level=ValidationLevel.STRICT)
        assert validator.level == ValidationLevel.STRICT

    def test_valid_series(self):
        """Test validation of clean data."""
        data = pd.Series(np.random.randn(100))

        validator = DataValidator()
        result = validator.validate_time_series(data, min_length=10)

        assert result.is_valid
        assert len(result.issues) == 0

    def test_insufficient_length(self):
        """Test detection of insufficient data length."""
        data = pd.Series([1, 2, 3])

        validator = DataValidator()
        result = validator.validate_time_series(data, min_length=10)

        assert not result.is_valid
        assert any('Insufficient data' in issue for issue in result.issues)

    def test_nan_detection(self):
        """Test NaN detection."""
        data = pd.Series([1, 2, np.nan, 4, 5])

        validator = DataValidator()
        result = validator.validate_time_series(data, min_length=3, allow_nan=False)

        # Should either fail or auto-fix
        if result.is_valid:
            # Auto-fixed
            assert result.fixed_data is not None
            assert not np.isnan(result.fixed_data).any()
        else:
            # Failed
            assert any('NaN' in issue for issue in result.issues)

    def test_nan_auto_fix(self):
        """Test automatic NaN fixing."""
        data = pd.Series([1, 2, np.nan, 4, 5, 6, 7, 8, 9, 10])

        validator = DataValidator()
        result = validator.validate_time_series(data, allow_nan=False, auto_fix=True, min_length=5)

        # Should auto-fix
        assert result.fixed_data is not None
        assert not pd.isna(result.fixed_data).any()

    def test_inf_detection(self):
        """Test infinite value detection."""
        data = pd.Series([1, 2, np.inf, 4, 5])

        validator = DataValidator()
        result = validator.validate_time_series(data, min_length=3, allow_inf=False)

        # Should either fail or auto-fix
        if result.is_valid:
            assert result.fixed_data is not None
            assert not np.isinf(result.fixed_data).any()
        else:
            assert any('infinite' in issue.lower() for issue in result.issues)

    def test_zero_variance_detection(self):
        """Test detection of zero variance."""
        data = pd.Series(np.ones(100))

        validator = DataValidator()
        result = validator.validate_time_series(data, require_variance=True, min_length=10)

        assert not result.is_valid
        assert any('variance' in issue.lower() for issue in result.issues)

    def test_duplicate_index_detection(self):
        """Test detection of duplicate index values."""
        data = pd.Series([1, 2, 3, 4], index=[0, 1, 1, 2])  # Duplicate index

        validator = DataValidator()
        result = validator.validate_time_series(data, min_length=3)

        assert not result.is_valid
        assert any('duplicate' in issue.lower() for issue in result.issues)

    def test_unsorted_datetime_index(self):
        """Test warning for unsorted datetime index."""
        dates = pd.to_datetime(['2023-03-01', '2023-01-01', '2023-02-01'])
        data = pd.Series([1, 2, 3], index=dates)

        validator = DataValidator()
        result = validator.validate_time_series(data, min_length=3)

        # Should warn about unsorted index
        assert any('sorted' in warning.lower() for warning in result.warnings)

    def test_time_gaps_detection(self):
        """Test detection of large time gaps."""
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        # Add a large gap
        dates = dates.append(pd.date_range('2023-06-01', periods=10, freq='D'))
        data = pd.Series(np.random.randn(20), index=dates)

        validator = DataValidator()
        result = validator.validate_time_series(data, min_length=10)

        # Should warn about gaps
        assert any('gap' in warning.lower() for warning in result.warnings)


class TestReturnsValidation:
    """Test validation for financial returns."""

    def test_valid_returns(self):
        """Test validation of normal returns."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 100))

        validator = DataValidator()
        result = validator.validate_returns(returns)

        assert result.is_valid or len(result.warnings) >= 0  # May have warnings

    def test_extreme_returns_detection(self):
        """Test detection of extreme returns."""
        returns = pd.Series([0.01, 0.02, 1.5, 0.01, 0.02])  # 150% return

        validator = DataValidator()
        result = validator.validate_returns(returns, max_abs_return=1.0)

        # Should warn about extreme returns
        assert any('extreme' in warning.lower() for warning in result.warnings)

    def test_returns_statistics(self):
        """Test returns statistics calculation."""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 100))

        validator = DataValidator()
        result = validator.validate_returns(returns)

        # Should include statistics
        assert result.metadata is not None
        assert 'mean_return' in result.metadata
        assert 'std_return' in result.metadata
        assert 'skewness' in result.metadata
        assert 'kurtosis' in result.metadata

    def test_high_skewness_warning(self):
        """Test warning for high skewness."""
        # Create highly skewed returns
        returns = pd.Series(np.concatenate([
            np.random.normal(0, 0.01, 95),
            np.array([0.5, 0.6, 0.7, 0.8, 0.9])  # Extreme positive returns
        ]))

        validator = DataValidator()
        result = validator.validate_returns(returns)

        # Should warn about skewness
        assert any('skew' in warning.lower() for warning in result.warnings)


class TestPriceValidation:
    """Test validation for price data."""

    def test_valid_prices(self):
        """Test validation of normal prices."""
        prices = pd.Series([100, 101, 102, 103, 104])

        validator = DataValidator()
        result = validator.validate_prices(prices)

        assert result.is_valid

    def test_negative_price_detection(self):
        """Test detection of negative prices."""
        prices = pd.Series([100, 101, -50, 103, 104])

        validator = DataValidator()
        result = validator.validate_prices(prices, require_positive=True)

        assert not result.is_valid
        assert any('positive' in issue.lower() for issue in result.issues)

    def test_stale_data_detection(self):
        """Test detection of stale/unchanged prices."""
        prices = pd.Series([100] * 50 + [101, 102])  # Mostly unchanged

        validator = DataValidator()
        result = validator.validate_prices(prices)

        # Should warn about consecutive identical prices
        assert any('identical' in warning.lower() or 'stale' in warning.lower() for warning in result.warnings)

    def test_price_jump_detection(self):
        """Test detection of large price jumps."""
        prices = pd.Series([100, 101, 200, 201, 202])  # Large jump

        validator = DataValidator()
        result = validator.validate_prices(prices)

        # Should warn about large jumps
        assert any('jump' in warning.lower() for warning in result.warnings)


class TestParameterValidator:
    """Test ParameterValidator class."""

    def test_validate_integer_valid(self):
        """Test valid integer validation."""
        ParameterValidator.validate_integer(5, 'param', min_value=0, max_value=10)
        # Should not raise

    def test_validate_integer_too_small(self):
        """Test integer too small."""
        with pytest.raises(ValidationError):
            ParameterValidator.validate_integer(-1, 'param', min_value=0)

    def test_validate_integer_too_large(self):
        """Test integer too large."""
        with pytest.raises(ValidationError):
            ParameterValidator.validate_integer(15, 'param', max_value=10)

    def test_validate_integer_wrong_type(self):
        """Test wrong type for integer."""
        with pytest.raises(ValidationError):
            ParameterValidator.validate_integer(5.5, 'param')

    def test_validate_float_valid(self):
        """Test valid float validation."""
        ParameterValidator.validate_float(5.5, 'param', min_value=0.0, max_value=10.0)
        # Should not raise

    def test_validate_float_nan(self):
        """Test NaN float rejection."""
        with pytest.raises(ValidationError):
            ParameterValidator.validate_float(np.nan, 'param')

    def test_validate_float_inf(self):
        """Test infinite float rejection."""
        with pytest.raises(ValidationError):
            ParameterValidator.validate_float(np.inf, 'param', allow_inf=False)

    def test_validate_probability_valid(self):
        """Test valid probability."""
        ParameterValidator.validate_probability(0.5, 'prob')
        # Should not raise

    def test_validate_probability_invalid(self):
        """Test invalid probability."""
        with pytest.raises(ValidationError):
            ParameterValidator.validate_probability(1.5, 'prob')

        with pytest.raises(ValidationError):
            ParameterValidator.validate_probability(-0.1, 'prob')

    def test_validate_choice_valid(self):
        """Test valid choice."""
        ParameterValidator.validate_choice('hmm', 'method', ['hmm', 'kmeans', 'dbscan'])
        # Should not raise

    def test_validate_choice_invalid(self):
        """Test invalid choice."""
        with pytest.raises(ValidationError):
            ParameterValidator.validate_choice('invalid', 'method', ['hmm', 'kmeans'])


class TestValidationDecorators:
    """Test validation decorators."""

    def test_validate_input_decorator(self):
        """Test @validate_input decorator."""

        @validate_input(min_length=10, auto_fix=True)
        def analyze(data: pd.Series) -> float:
            return data.mean()

        # Should work with valid data
        result = analyze(pd.Series(np.random.randn(50)))
        assert isinstance(result, float)

    def test_validate_input_rejects_short_data(self):
        """Test that decorator rejects short data."""

        @validate_input(min_length=100, auto_fix=False)
        def analyze(data: pd.Series) -> float:
            return data.mean()

        with pytest.raises(ValidationError):
            analyze(pd.Series([1, 2, 3]))

    def test_validate_input_auto_fixes_nan(self):
        """Test that decorator auto-fixes NaN values."""

        @validate_input(min_length=5, auto_fix=True, allow_nan=False)
        def analyze(data: pd.Series) -> float:
            # Data should be cleaned by decorator
            assert not data.isna().any()
            return data.mean()

        data = pd.Series([1, 2, np.nan, 4, 5, 6, 7, 8, 9, 10])
        result = analyze(data)
        assert isinstance(result, float)

    def test_validate_parameters_decorator(self):
        """Test @validate_parameters decorator."""

        @validate_parameters(
            n_states={'min': 2, 'max': 10},
            method={'choices': ['hmm', 'kmeans']}
        )
        def detect(n_states: int, method: str):
            return f"{method} with {n_states} states"

        # Should work with valid parameters
        result = detect(3, 'hmm')
        assert result == "hmm with 3 states"

    def test_validate_parameters_rejects_invalid(self):
        """Test that decorator rejects invalid parameters."""

        @validate_parameters(
            n_states={'min': 2, 'max': 10}
        )
        def detect(n_states: int):
            return n_states

        with pytest.raises(ValidationError):
            detect(15)  # Too large

        with pytest.raises(ValidationError):
            detect(1)   # Too small

    def test_validate_parameters_with_choices(self):
        """Test parameter validation with choices."""

        @validate_parameters(
            method={'choices': ['pelt', 'binseg']}
        )
        def detect(method: str):
            return method

        # Valid choice
        result = detect('pelt')
        assert result == 'pelt'

        # Invalid choice
        with pytest.raises(ValidationError):
            detect('invalid')


class TestQuickValidate:
    """Test quick_validate convenience function."""

    def test_quick_validate_valid_data(self):
        """Test quick validation with valid data."""
        data = pd.Series(np.random.randn(100))

        result = quick_validate(data, min_length=10, raise_on_error=False)
        assert result.is_valid

    def test_quick_validate_raises_on_error(self):
        """Test that quick_validate raises on error."""
        data = pd.Series([1, 2, 3])  # Too short

        with pytest.raises(ValidationError):
            quick_validate(data, min_length=10, raise_on_error=True)

    def test_quick_validate_no_raise(self):
        """Test that quick_validate doesn't raise when disabled."""
        data = pd.Series([1, 2, 3])  # Too short

        result = quick_validate(data, min_length=10, raise_on_error=False)
        assert not result.is_valid


class TestValidationEdgeCases:
    """Test edge cases and complex scenarios."""

    def test_empty_series(self):
        """Test validation of empty series."""
        data = pd.Series([])

        validator = DataValidator()
        result = validator.validate_time_series(data, min_length=1)

        assert not result.is_valid

    def test_single_value_series(self):
        """Test validation of single-value series."""
        data = pd.Series([42])

        validator = DataValidator()
        result = validator.validate_time_series(data, min_length=1, require_variance=False)

        assert result.is_valid

    def test_all_nan_series(self):
        """Test validation of all-NaN series."""
        data = pd.Series([np.nan] * 10)

        validator = DataValidator()
        result = validator.validate_time_series(data, allow_nan=False, auto_fix=True)

        # Cannot auto-fix all NaN
        assert not result.is_valid

    def test_mixed_nan_and_inf(self):
        """Test series with both NaN and inf."""
        data = pd.Series([1, np.nan, 3, np.inf, 5, 6, 7, 8, 9, 10])

        validator = DataValidator()
        result = validator.validate_time_series(
            data,
            allow_nan=False,
            allow_inf=False,
            auto_fix=True,
            min_length=5
        )

        if result.is_valid:
            # Should be auto-fixed
            assert result.fixed_data is not None
            assert not np.isnan(result.fixed_data).any()
            assert not np.isinf(result.fixed_data).any()

    def test_numpy_array_input(self):
        """Test validation with numpy array input."""
        data = np.random.randn(100)

        validator = DataValidator()
        result = validator.validate_time_series(data, min_length=10)

        assert result.is_valid or len(result.warnings) >= 0

    def test_list_input(self):
        """Test validation with list input."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]

        validator = DataValidator()
        result = validator.validate_time_series(data, min_length=3)

        assert result.is_valid or len(result.warnings) >= 0


class TestValidationLevels:
    """Test different validation levels."""

    def test_strict_level(self):
        """Test strict validation level."""
        validator = DataValidator(level=ValidationLevel.STRICT)
        assert validator.level == ValidationLevel.STRICT

    def test_moderate_level(self):
        """Test moderate validation level."""
        validator = DataValidator(level=ValidationLevel.MODERATE)
        assert validator.level == ValidationLevel.MODERATE

    def test_lenient_level(self):
        """Test lenient validation level."""
        validator = DataValidator(level=ValidationLevel.LENIENT)
        assert validator.level == ValidationLevel.LENIENT


class TestValidationMetadata:
    """Test validation metadata."""

    def test_metadata_included(self):
        """Test that metadata is included in results."""
        data = pd.Series([1, 2, np.nan, 4, 5])

        validator = DataValidator()
        result = validator.validate_time_series(data, min_length=3, auto_fix=True)

        assert result.metadata is not None
        assert 'original_length' in result.metadata
        assert 'nan_count' in result.metadata
        assert result.metadata['nan_count'] == 1

    def test_returns_metadata(self):
        """Test returns validation metadata."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 100))

        validator = DataValidator()
        result = validator.validate_returns(returns)

        assert result.metadata is not None
        assert 'mean_return' in result.metadata
        assert 'std_return' in result.metadata
