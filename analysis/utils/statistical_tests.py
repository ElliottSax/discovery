"""
Statistical Significance Testing

Provides rigorous statistical tests for pattern detection to reduce
false positives and increase confidence in findings.

Key Tests:
- Bootstrap significance testing for Fourier cycles
- Permutation tests for regime detection
- Cross-validation for model reliability
- Multiple testing correction (Bonferroni, FDR)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Callable
from scipy import stats, signal
from scipy.fft import fft, fftfreq
import logging
from config.ml_config import ml_settings

logger = logging.getLogger(__name__)


class BootstrapTest:
    """
    Bootstrap hypothesis testing for pattern significance.

    Uses resampling to generate null distribution and test whether
    detected patterns are statistically significant vs random noise.
    """

    def __init__(self, n_bootstrap: int = None, alpha: float = 0.05):
        """
        Initialize bootstrap test.

        Args:
            n_bootstrap: Number of bootstrap samples (None = use config)
            alpha: Significance level (default: 0.05 for 95% confidence)
        """
        self.n_bootstrap = n_bootstrap or ml_settings.BOOTSTRAP_N_SAMPLES
        self.alpha = alpha

    def test_fourier_cycle(
        self,
        time_series: np.ndarray,
        period: float,
        strength: float,
        method: str = 'shuffle'
    ) -> Dict:
        """
        Test if detected Fourier cycle is statistically significant.

        Generates null distribution by destroying temporal structure
        (shuffling or phase randomization) and comparing detected
        strength to null distribution.

        Args:
            time_series: Original time series
            period: Detected cycle period
            strength: Detected cycle strength (FFT power)
            method: 'shuffle' or 'phase_randomization'

        Returns:
            {
                'p_value': float,  # Probability under null hypothesis
                'is_significant': bool,  # p < alpha
                'null_mean': float,  # Mean of null distribution
                'null_std': float,  # Std of null distribution
                'percentile_95': float,  # 95th percentile of null
                'z_score': float  # Standardized effect size
            }

        Example:
            >>> tester = BootstrapTest(n_bootstrap=1000)
            >>> result = tester.test_fourier_cycle(
            ...     time_series=data,
            ...     period=30,
            ...     strength=0.85
            ... )
            >>> print(f"Significant: {result['is_significant']}, p={result['p_value']:.4f}")
        """
        null_strengths = []

        for i in range(self.n_bootstrap):
            if method == 'shuffle':
                # Shuffle to destroy temporal structure
                shuffled = np.random.permutation(time_series)
            elif method == 'phase_randomization':
                # Phase randomization (preserves power spectrum)
                shuffled = self._phase_randomization(time_series)
            else:
                raise ValueError(f"Unknown method: {method}")

            # Detrend and FFT
            detrended = signal.detrend(shuffled)
            N = len(detrended)
            yf = fft(detrended)
            xf = fftfreq(N, 1)[:N//2]
            power = 2.0/N * np.abs(yf[0:N//2])

            # Find power at the detected period's frequency
            freq = 1 / period
            freq_idx = np.argmin(np.abs(xf - freq))
            null_strengths.append(power[freq_idx])

        null_strengths = np.array(null_strengths)

        # Calculate statistics
        p_value = (null_strengths >= strength).mean()
        null_mean = np.mean(null_strengths)
        null_std = np.std(null_strengths)
        percentile_95 = np.percentile(null_strengths, 95)

        # Z-score (standardized effect size)
        z_score = (strength - null_mean) / (null_std + 1e-10)

        return {
            'p_value': float(p_value),
            'is_significant': p_value < self.alpha,
            'null_mean': float(null_mean),
            'null_std': float(null_std),
            'percentile_95': float(percentile_95),
            'z_score': float(z_score),
            'n_bootstrap': self.n_bootstrap,
            'alpha': self.alpha
        }

    def _phase_randomization(self, time_series: np.ndarray) -> np.ndarray:
        """
        Generate surrogate data via phase randomization.

        Preserves power spectrum but destroys phase relationships.
        More conservative than shuffling.
        """
        # FFT
        fft_vals = fft(time_series)

        # Randomize phases
        phases = np.angle(fft_vals)
        random_phases = np.random.uniform(0, 2*np.pi, len(phases))

        # Reconstruct with random phases
        randomized_fft = np.abs(fft_vals) * np.exp(1j * random_phases)

        # Inverse FFT
        surrogate = np.fft.ifft(randomized_fft).real

        return surrogate

    def test_multiple_cycles(
        self,
        time_series: np.ndarray,
        cycles: List[Dict],
        correction: str = 'bonferroni'
    ) -> List[Dict]:
        """
        Test multiple cycles with correction for multiple comparisons.

        Args:
            time_series: Original time series
            cycles: List of cycle dicts with 'period' and 'strength'
            correction: 'bonferroni', 'fdr', or 'none'

        Returns:
            List of test results with corrected p-values
        """
        results = []

        # Test each cycle
        for cycle in cycles:
            result = self.test_fourier_cycle(
                time_series,
                cycle['period_days'],
                cycle['strength']
            )
            result['raw_p_value'] = result['p_value']
            results.append(result)

        # Apply multiple testing correction
        if correction == 'bonferroni' and len(results) > 0:
            for result in results:
                result['p_value'] = min(result['raw_p_value'] * len(results), 1.0)
                result['is_significant'] = result['p_value'] < self.alpha

        elif correction == 'fdr' and len(results) > 0:
            # Benjamini-Hochberg FDR correction
            p_values = [r['raw_p_value'] for r in results]
            corrected = self._fdr_correction(p_values, self.alpha)

            for result, is_sig in zip(results, corrected):
                result['is_significant'] = is_sig

        return results

    def _fdr_correction(self, p_values: List[float], alpha: float) -> List[bool]:
        """
        Benjamini-Hochberg FDR correction.

        Controls false discovery rate instead of family-wise error rate.
        """
        n = len(p_values)
        if n == 0:
            return []

        # Sort p-values
        sorted_idx = np.argsort(p_values)
        sorted_p = np.array(p_values)[sorted_idx]

        # Benjamini-Hochberg critical values
        critical_values = (np.arange(1, n+1) / n) * alpha

        # Find largest i where p(i) <= critical_value(i)
        significant = sorted_p <= critical_values

        if not np.any(significant):
            return [False] * n

        max_idx = np.where(significant)[0][-1]

        # All p-values up to max_idx are significant
        is_significant = np.zeros(n, dtype=bool)
        is_significant[sorted_idx[:max_idx+1]] = True

        return is_significant.tolist()


class PermutationTest:
    """
    Permutation tests for regime detection.

    Tests whether detected regimes are significantly different from
    random partitioning of the data.
    """

    def __init__(self, n_permutations: int = 1000, alpha: float = 0.05):
        """
        Initialize permutation test.

        Args:
            n_permutations: Number of random permutations
            alpha: Significance level
        """
        self.n_permutations = n_permutations
        self.alpha = alpha

    def test_regime_separation(
        self,
        returns: np.ndarray,
        regimes: np.ndarray,
        metric: str = 'variance_ratio'
    ) -> Dict:
        """
        Test if regimes have significantly different characteristics.

        Args:
            returns: Return time series
            regimes: Regime labels for each time point
            metric: 'variance_ratio', 'mean_difference', or 'log_likelihood'

        Returns:
            Test results with p-value
        """
        # Calculate observed statistic
        observed = self._calculate_statistic(returns, regimes, metric)

        # Generate null distribution
        null_stats = []

        for _ in range(self.n_permutations):
            # Random permutation of regime labels
            shuffled_regimes = np.random.permutation(regimes)

            # Calculate statistic under null
            null_stat = self._calculate_statistic(returns, shuffled_regimes, metric)
            null_stats.append(null_stat)

        null_stats = np.array(null_stats)

        # Calculate p-value (two-tailed)
        p_value = (np.abs(null_stats) >= np.abs(observed)).mean()

        return {
            'observed_statistic': float(observed),
            'p_value': float(p_value),
            'is_significant': p_value < self.alpha,
            'null_mean': float(np.mean(null_stats)),
            'null_std': float(np.std(null_stats)),
            'metric': metric
        }

    def _calculate_statistic(
        self,
        returns: np.ndarray,
        regimes: np.ndarray,
        metric: str
    ) -> float:
        """Calculate test statistic for regime separation."""
        unique_regimes = np.unique(regimes)

        if metric == 'variance_ratio':
            # Ratio of between-regime to within-regime variance
            overall_mean = np.mean(returns)

            # Between-regime variance
            regime_means = []
            regime_sizes = []

            for regime in unique_regimes:
                mask = regimes == regime
                regime_means.append(np.mean(returns[mask]))
                regime_sizes.append(np.sum(mask))

            regime_means = np.array(regime_means)
            regime_sizes = np.array(regime_sizes)

            between_var = np.sum(regime_sizes * (regime_means - overall_mean)**2) / len(returns)

            # Within-regime variance
            within_var = 0
            for regime in unique_regimes:
                mask = regimes == regime
                within_var += np.sum((returns[mask] - np.mean(returns[mask]))**2)

            within_var /= len(returns)

            return between_var / (within_var + 1e-10)

        elif metric == 'mean_difference':
            # Maximum pairwise difference in regime means
            regime_means = []

            for regime in unique_regimes:
                mask = regimes == regime
                regime_means.append(np.mean(returns[mask]))

            if len(regime_means) < 2:
                return 0

            return np.max(np.abs(np.diff(regime_means)))

        else:
            raise ValueError(f"Unknown metric: {metric}")


class CrossValidator:
    """
    Time-series cross-validation for model reliability.

    Uses expanding or rolling window to validate model performance
    without look-ahead bias.
    """

    def __init__(self, n_splits: int = None, method: str = 'expanding'):
        """
        Initialize cross-validator.

        Args:
            n_splits: Number of CV splits (None = use config)
            method: 'expanding' or 'rolling'
        """
        self.n_splits = n_splits or ml_settings.CROSS_VALIDATION_SPLITS
        self.method = method

    def validate_hmm(
        self,
        detector,
        returns: np.ndarray,
        **fit_kwargs
    ) -> Dict:
        """
        Cross-validate HMM regime detector.

        Args:
            detector: RegimeDetector instance
            returns: Return time series
            **fit_kwargs: Additional arguments for fit

        Returns:
            Validation results
        """
        from sklearn.model_selection import TimeSeriesSplit

        tscv = TimeSeriesSplit(n_splits=self.n_splits)

        log_likelihoods = []
        regime_consistencies = []

        for train_idx, test_idx in tscv.split(returns):
            # Fit on train
            detector_cv = detector.__class__(
                n_states=detector.n_states,
                covariance_type=detector.model.covariance_type,
                n_iter=detector.model.n_iter
            )

            detector_cv.fit(returns[train_idx], **fit_kwargs)

            # Evaluate on test
            X_test = detector_cv._create_feature_matrix(
                returns[test_idx],
                fit_kwargs.get('volumes', None),
                fit_kwargs.get('additional_features', None)
            )

            ll = detector_cv.model.score(X_test)
            log_likelihoods.append(ll)

            # Measure regime consistency
            train_regimes = detector_cv.model.predict(
                detector_cv._create_feature_matrix(returns[train_idx], None, None)
            )
            test_regimes = detector_cv.model.predict(X_test)

            consistency = self._measure_consistency(train_regimes, test_regimes, detector.n_states)
            regime_consistencies.append(consistency)

        return {
            'mean_log_likelihood': float(np.mean(log_likelihoods)),
            'std_log_likelihood': float(np.std(log_likelihoods)),
            'mean_regime_consistency': float(np.mean(regime_consistencies)),
            'std_regime_consistency': float(np.std(regime_consistencies)),
            'cv_scores': log_likelihoods,
            'n_splits': self.n_splits
        }

    def _measure_consistency(
        self,
        train_regimes: np.ndarray,
        test_regimes: np.ndarray,
        n_states: int
    ) -> float:
        """
        Measure regime distribution consistency between train and test.

        Uses Jensen-Shannon divergence (symmetric KL divergence).
        """
        # Calculate regime distributions
        train_dist = np.bincount(train_regimes, minlength=n_states) / len(train_regimes)
        test_dist = np.bincount(test_regimes, minlength=n_states) / len(test_regimes)

        # Jensen-Shannon divergence (1 = identical, 0 = completely different)
        return 1.0 - self._jensen_shannon_divergence(train_dist, test_dist)

    def _jensen_shannon_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """Calculate Jensen-Shannon divergence."""
        epsilon = 1e-10
        p = p + epsilon
        q = q + epsilon

        m = 0.5 * (p + q)

        return 0.5 * (self._kl_divergence(p, m) + self._kl_divergence(q, m))

    def _kl_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """Calculate KL divergence."""
        return np.sum(p * np.log(p / q))


# Convenience functions
def test_cycle_significance(
    time_series: np.ndarray,
    period: float,
    strength: float,
    n_bootstrap: int = 1000,
    alpha: float = 0.05
) -> Dict:
    """
    Quick test for cycle significance.

    Example:
        >>> result = test_cycle_significance(data, period=30, strength=0.85)
        >>> if result['is_significant']:
        ...     print(f"Cycle is significant (p={result['p_value']:.4f})")
    """
    tester = BootstrapTest(n_bootstrap=n_bootstrap, alpha=alpha)
    return tester.test_fourier_cycle(time_series, period, strength)
