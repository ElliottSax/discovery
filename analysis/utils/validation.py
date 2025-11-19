"""
Comprehensive Input Validation Framework

Provides robust validation for all analysis modules to ensure:
- Data quality (NaN, inf, missing values)
- Time series integrity (monotonic, duplicates, gaps)
- Parameter constraints (ranges, types)
- Statistical requirements (sufficient data, variance)
- Domain-specific rules (returns, prices)

Key Features:
- Decorator-based validation for easy integration
- Detailed error messages with actionable suggestions
- Automatic data cleaning and preprocessing
- Configurable validation levels (strict, moderate, lenient)
"""

import numpy as np
import pandas as pd
from typing import Union, Optional, List, Tuple, Dict, Any, Callable
from functools import wraps
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation strictness levels."""
    STRICT = "strict"      # Fail on any issue
    MODERATE = "moderate"  # Warn on minor issues, fail on critical
    LENIENT = "lenient"    # Warn only, auto-fix when possible


class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    fixed_data: Optional[Any] = None
    metadata: Optional[Dict] = None

    def __bool__(self):
        return self.is_valid


class DataValidator:
    """
    Comprehensive data validation for time series analysis.

    Validates data quality, time series properties, and domain constraints.
    """

    def __init__(self, level: ValidationLevel = ValidationLevel.MODERATE):
        """
        Initialize validator.

        Args:
            level: Validation strictness level
        """
        self.level = level

    def validate_time_series(
        self,
        data: Union[pd.Series, np.ndarray, List],
        min_length: int = 10,
        allow_nan: bool = False,
        allow_inf: bool = False,
        require_variance: bool = True,
        auto_fix: bool = True
    ) -> ValidationResult:
        """
        Validate time series data.

        Args:
            data: Time series data
            min_length: Minimum required length
            allow_nan: Whether to allow NaN values
            allow_inf: Whether to allow infinite values
            require_variance: Whether to require non-zero variance
            auto_fix: Whether to attempt automatic fixes

        Returns:
            ValidationResult with validation status and any fixes

        Example:
            >>> validator = DataValidator()
            >>> result = validator.validate_time_series(data, min_length=30)
            >>> if not result.is_valid:
            ...     print(f"Validation failed: {result.issues}")
            >>> else:
            ...     clean_data = result.fixed_data or data
        """
        issues = []
        warnings = []
        fixed_data = None

        # Convert to numpy array for validation
        if isinstance(data, pd.Series):
            arr = data.values
            has_index = True
        elif isinstance(data, (list, tuple)):
            arr = np.array(data)
            has_index = False
        else:
            arr = np.array(data)
            has_index = False

        # Check length
        if len(arr) < min_length:
            issues.append(
                f"Insufficient data: {len(arr)} points (minimum: {min_length}). "
                f"Suggestion: Collect more data or reduce min_length parameter."
            )

        # Check for NaN
        nan_count = np.isnan(arr).sum()
        if nan_count > 0:
            msg = f"Found {nan_count} NaN values ({nan_count/len(arr)*100:.1f}%)"

            if allow_nan:
                warnings.append(msg)
            else:
                if auto_fix and nan_count < len(arr) * 0.1:  # < 10% NaN
                    # Forward fill then backward fill
                    if isinstance(data, pd.Series):
                        fixed_data = data.fillna(method='ffill').fillna(method='bfill')
                        warnings.append(f"{msg}. Auto-fixed using forward/backward fill.")
                    else:
                        # Simple linear interpolation
                        mask = np.isnan(arr)
                        arr_fixed = arr.copy()
                        arr_fixed[mask] = np.interp(
                            np.flatnonzero(mask),
                            np.flatnonzero(~mask),
                            arr[~mask]
                        )
                        fixed_data = arr_fixed
                        warnings.append(f"{msg}. Auto-fixed using linear interpolation.")
                else:
                    issues.append(
                        f"{msg}. Suggestion: Use data.fillna() or remove NaN rows."
                    )

        # Check for inf
        inf_count = np.isinf(arr).sum()
        if inf_count > 0:
            msg = f"Found {inf_count} infinite values"

            if allow_inf:
                warnings.append(msg)
            else:
                if auto_fix:
                    # Replace inf with max/min finite values
                    arr_fixed = arr if fixed_data is None else (
                        fixed_data.values if isinstance(fixed_data, pd.Series) else fixed_data
                    )
                    arr_fixed = arr_fixed.copy()

                    finite_mask = np.isfinite(arr_fixed)
                    if finite_mask.any():
                        max_val = np.max(arr_fixed[finite_mask])
                        min_val = np.min(arr_fixed[finite_mask])

                        arr_fixed[np.isposinf(arr_fixed)] = max_val
                        arr_fixed[np.isneginf(arr_fixed)] = min_val

                        fixed_data = arr_fixed
                        warnings.append(f"{msg}. Auto-fixed by replacing with finite extremes.")
                else:
                    issues.append(
                        f"{msg}. Suggestion: Replace inf values with np.nan or clip extreme values."
                    )

        # Check variance
        if require_variance:
            test_arr = fixed_data if fixed_data is not None else arr
            if isinstance(test_arr, pd.Series):
                test_arr = test_arr.values

            variance = np.var(test_arr)
            if variance < 1e-10:
                issues.append(
                    f"Zero or near-zero variance ({variance:.2e}). "
                    f"Data appears constant. Suggestion: Check data source or use different features."
                )

        # If pandas Series, validate index
        if isinstance(data, pd.Series):
            index_result = self._validate_index(data.index)
            issues.extend(index_result.issues)
            warnings.extend(index_result.warnings)

        is_valid = len(issues) == 0

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            warnings=warnings,
            fixed_data=fixed_data,
            metadata={'original_length': len(arr), 'nan_count': nan_count, 'inf_count': inf_count}
        )

    def _validate_index(self, index: pd.Index) -> ValidationResult:
        """Validate pandas index (time series specific)."""
        issues = []
        warnings = []

        # Check for duplicates
        if index.duplicated().any():
            dup_count = index.duplicated().sum()
            issues.append(
                f"Found {dup_count} duplicate index values. "
                f"Suggestion: Use data.reset_index(drop=True) or data.groupby(level=0).mean()"
            )

        # Check if sorted (if DatetimeIndex)
        if isinstance(index, pd.DatetimeIndex):
            if not index.is_monotonic_increasing:
                warnings.append(
                    "Index is not sorted. "
                    "Suggestion: Use data.sort_index() for time series analysis."
                )

            # Check for gaps (if business days expected)
            if len(index) > 1:
                median_gap = pd.Series(index).diff().median()
                gaps = pd.Series(index).diff()
                large_gaps = gaps[gaps > median_gap * 5]

                if len(large_gaps) > 0:
                    warnings.append(
                        f"Found {len(large_gaps)} large time gaps (>5x median gap). "
                        f"Largest gap: {large_gaps.max()}. "
                        f"This may affect time series analysis."
                    )

        return ValidationResult(is_valid=len(issues) == 0, issues=issues, warnings=warnings)

    def validate_returns(
        self,
        returns: Union[pd.Series, np.ndarray],
        max_abs_return: float = 1.0,
        check_stationarity: bool = True
    ) -> ValidationResult:
        """
        Validate financial returns data.

        Args:
            returns: Return time series
            max_abs_return: Maximum absolute return allowed (1.0 = 100%)
            check_stationarity: Whether to check for stationarity

        Returns:
            ValidationResult
        """
        issues = []
        warnings = []

        # Basic validation
        result = self.validate_time_series(returns, min_length=30)
        issues.extend(result.issues)
        warnings.extend(result.warnings)

        if not result.is_valid:
            return result

        # Use fixed data if available
        data = result.fixed_data if result.fixed_data is not None else returns
        arr = data.values if isinstance(data, pd.Series) else data

        # Check for extreme returns
        extreme_mask = np.abs(arr) > max_abs_return
        if extreme_mask.any():
            extreme_count = extreme_mask.sum()
            max_return = np.max(np.abs(arr))

            warnings.append(
                f"Found {extreme_count} extreme returns (>{max_abs_return*100}%). "
                f"Maximum: {max_return*100:.2f}%. "
                f"Suggestion: Check for data errors or consider winsorizing."
            )

        # Check return distribution
        mean_return = np.mean(arr)
        std_return = np.std(arr)

        # Check for skewness
        from scipy import stats
        skewness = stats.skew(arr)
        kurtosis = stats.kurtosis(arr)

        if abs(skewness) > 3:
            warnings.append(
                f"High skewness ({skewness:.2f}). Returns distribution is highly asymmetric."
            )

        if kurtosis > 10:
            warnings.append(
                f"High kurtosis ({kurtosis:.2f}). Returns have fat tails (extreme events common)."
            )

        # Stationarity check (ADF test)
        if check_stationarity and len(arr) >= 50:
            try:
                from statsmodels.tsa.stattools import adfuller
                adf_result = adfuller(arr, autolag='AIC')
                p_value = adf_result[1]

                if p_value > 0.05:
                    warnings.append(
                        f"Returns may be non-stationary (ADF p-value: {p_value:.4f}). "
                        f"Consider differencing or detrending."
                    )
            except ImportError:
                logger.debug("statsmodels not available for stationarity test")
            except Exception as e:
                logger.debug(f"Stationarity test failed: {e}")

        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            fixed_data=result.fixed_data,
            metadata={
                'mean_return': float(mean_return),
                'std_return': float(std_return),
                'skewness': float(skewness),
                'kurtosis': float(kurtosis)
            }
        )

    def validate_prices(
        self,
        prices: Union[pd.Series, np.ndarray],
        require_positive: bool = True,
        check_monotonic: bool = False
    ) -> ValidationResult:
        """
        Validate price data.

        Args:
            prices: Price time series
            require_positive: Whether prices must be positive
            check_monotonic: Whether to check if prices are monotonic

        Returns:
            ValidationResult
        """
        issues = []
        warnings = []

        # Basic validation
        result = self.validate_time_series(prices, min_length=30)
        issues.extend(result.issues)
        warnings.extend(result.warnings)

        if not result.is_valid:
            return result

        data = result.fixed_data if result.fixed_data is not None else prices
        arr = data.values if isinstance(data, pd.Series) else data

        # Check for positive values
        if require_positive:
            if np.any(arr <= 0):
                neg_count = (arr <= 0).sum()
                issues.append(
                    f"Found {neg_count} non-positive prices. "
                    f"Prices must be positive for log returns and ratio analysis."
                )

        # Check for suspicious patterns
        # Consecutive identical values
        if len(arr) > 1:
            consecutive_same = np.where(np.diff(arr) == 0)[0]
            if len(consecutive_same) > len(arr) * 0.1:  # >10% identical
                warnings.append(
                    f"Found {len(consecutive_same)} consecutive identical prices ({len(consecutive_same)/len(arr)*100:.1f}%). "
                    f"May indicate stale data or trading halts."
                )

        # Check for price jumps
        if len(arr) > 1:
            pct_changes = np.abs(np.diff(arr) / arr[:-1])
            large_jumps = pct_changes > 0.5  # >50% change

            if large_jumps.any():
                jump_count = large_jumps.sum()
                warnings.append(
                    f"Found {jump_count} large price jumps (>50%). "
                    f"May indicate splits, dividends, or data errors."
                )

        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            fixed_data=result.fixed_data
        )


class ParameterValidator:
    """
    Validate function parameters and configuration.

    Ensures parameters are within valid ranges and compatible.
    """

    @staticmethod
    def validate_integer(
        value: Any,
        name: str,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ) -> None:
        """
        Validate integer parameter.

        Raises:
            ValidationError if invalid
        """
        if not isinstance(value, int):
            raise ValidationError(f"{name} must be an integer, got {type(value).__name__}")

        if min_value is not None and value < min_value:
            raise ValidationError(f"{name} must be >= {min_value}, got {value}")

        if max_value is not None and value > max_value:
            raise ValidationError(f"{name} must be <= {max_value}, got {value}")

    @staticmethod
    def validate_float(
        value: Any,
        name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        allow_inf: bool = False
    ) -> None:
        """Validate float parameter."""
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{name} must be numeric, got {type(value).__name__}")

        value = float(value)

        if not allow_inf and np.isinf(value):
            raise ValidationError(f"{name} cannot be infinite")

        if np.isnan(value):
            raise ValidationError(f"{name} cannot be NaN")

        if min_value is not None and value < min_value:
            raise ValidationError(f"{name} must be >= {min_value}, got {value}")

        if max_value is not None and value > max_value:
            raise ValidationError(f"{name} must be <= {max_value}, got {value}")

    @staticmethod
    def validate_probability(value: Any, name: str) -> None:
        """Validate probability (0 to 1)."""
        ParameterValidator.validate_float(value, name, min_value=0.0, max_value=1.0)

    @staticmethod
    def validate_choice(value: Any, name: str, choices: List[Any]) -> None:
        """Validate value is in allowed choices."""
        if value not in choices:
            raise ValidationError(
                f"{name} must be one of {choices}, got {value}"
            )


# Decorator-based validation
def validate_input(
    min_length: int = 10,
    allow_nan: bool = False,
    require_variance: bool = True,
    auto_fix: bool = True
):
    """
    Decorator for automatic input validation.

    Args:
        min_length: Minimum data length
        allow_nan: Whether to allow NaN
        require_variance: Whether to require non-zero variance
        auto_fix: Whether to auto-fix issues

    Example:
        >>> @validate_input(min_length=30, auto_fix=True)
        >>> def analyze_data(time_series: pd.Series):
        ...     # time_series is guaranteed to be valid
        ...     return compute_analysis(time_series)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Find time series argument (first pd.Series or np.ndarray)
            data = None
            data_idx = None

            for i, arg in enumerate(args):
                if isinstance(arg, (pd.Series, np.ndarray, list)):
                    data = arg
                    data_idx = i
                    break

            if data is None:
                # Check kwargs
                for key, value in kwargs.items():
                    if isinstance(value, (pd.Series, np.ndarray, list)):
                        data = value
                        data_idx = key
                        break

            if data is not None:
                # Validate
                validator = DataValidator()
                result = validator.validate_time_series(
                    data,
                    min_length=min_length,
                    allow_nan=allow_nan,
                    require_variance=require_variance,
                    auto_fix=auto_fix
                )

                # Log warnings
                for warning in result.warnings:
                    logger.warning(f"{func.__name__}: {warning}")

                # Raise on errors
                if not result.is_valid:
                    error_msg = f"{func.__name__} validation failed:\n" + "\n".join(result.issues)
                    raise ValidationError(error_msg)

                # Replace with fixed data if available
                if result.fixed_data is not None:
                    if isinstance(data_idx, int):
                        args = list(args)
                        args[data_idx] = result.fixed_data
                        args = tuple(args)
                    else:
                        kwargs[data_idx] = result.fixed_data

            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_parameters(**param_specs):
    """
    Decorator for parameter validation.

    Args:
        **param_specs: Parameter specifications
            - For int: {'min': value, 'max': value}
            - For float: {'min': value, 'max': value}
            - For choice: {'choices': [values]}

    Example:
        >>> @validate_parameters(
        ...     n_states={'min': 2, 'max': 10},
        ...     penalty={'min': 0.0},
        ...     method={'choices': ['pelt', 'binseg', 'cusum']}
        ... )
        >>> def detect_regimes(n_states: int, penalty: float, method: str):
        ...     # Parameters are guaranteed valid
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate each parameter
            for param_name, spec in param_specs.items():
                if param_name not in bound_args.arguments:
                    continue

                value = bound_args.arguments[param_name]

                if 'choices' in spec:
                    ParameterValidator.validate_choice(value, param_name, spec['choices'])
                elif isinstance(spec.get('min'), int) or isinstance(spec.get('max'), int):
                    ParameterValidator.validate_integer(
                        value, param_name,
                        min_value=spec.get('min'),
                        max_value=spec.get('max')
                    )
                elif 'min' in spec or 'max' in spec:
                    ParameterValidator.validate_float(
                        value, param_name,
                        min_value=spec.get('min'),
                        max_value=spec.get('max')
                    )

            return func(*args, **kwargs)

        return wrapper

    return decorator


# Convenience functions
def quick_validate(
    data: Union[pd.Series, np.ndarray],
    min_length: int = 10,
    raise_on_error: bool = True
) -> ValidationResult:
    """
    Quick validation for time series data.

    Example:
        >>> result = quick_validate(my_data, min_length=30)
        >>> if result.is_valid:
        ...     print("Data is valid!")
        >>> else:
        ...     print("Issues:", result.issues)
    """
    validator = DataValidator()
    result = validator.validate_time_series(data, min_length=min_length)

    if raise_on_error and not result.is_valid:
        error_msg = "Validation failed:\n" + "\n".join(result.issues)
        raise ValidationError(error_msg)

    return result


# Example usage and tests
if __name__ == "__main__":
    # Example 1: Basic validation
    print("Example 1: Basic validation")
    data = pd.Series([1, 2, np.nan, 4, 5, 6])

    validator = DataValidator()
    result = validator.validate_time_series(data, allow_nan=False, auto_fix=True)

    print(f"Valid: {result.is_valid}")
    print(f"Warnings: {result.warnings}")
    print(f"Fixed data: {result.fixed_data}")

    # Example 2: Decorator usage
    print("\nExample 2: Decorator usage")

    @validate_input(min_length=5, auto_fix=True)
    def analyze_series(data: pd.Series) -> float:
        return data.mean()

    try:
        result = analyze_series(pd.Series([1, 2, np.nan, 4, 5]))
        print(f"Analysis result: {result}")
    except ValidationError as e:
        print(f"Error: {e}")

    # Example 3: Parameter validation
    print("\nExample 3: Parameter validation")

    @validate_parameters(
        n_states={'min': 2, 'max': 10},
        method={'choices': ['hmm', 'kmeans']}
    )
    def detect_regimes(n_states: int, method: str):
        return f"Detecting {n_states} states using {method}"

    try:
        print(detect_regimes(3, 'hmm'))
        print(detect_regimes(15, 'hmm'))  # Should fail
    except ValidationError as e:
        print(f"Validation error: {e}")
