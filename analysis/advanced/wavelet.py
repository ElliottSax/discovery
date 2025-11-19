"""
Wavelet Transform Pattern Detector

Provides time-frequency analysis using Continuous Wavelet Transform (CWT).
Superior to Fourier for non-stationary signals with time-localized patterns.

Key Advantages over Fourier:
- Time-frequency localization (when AND what frequency)
- Better for non-stationary signals
- Detects transient patterns
- Identifies regime changes more precisely
- Variable resolution (zoom in/out)

Use Cases:
- Market regime changes
- Volatility clustering
- Crisis detection
- Pattern evolution over time

References:
- Torrence & Compo (1998) - A Practical Guide to Wavelet Analysis
- Grinsted et al. (2004) - Application of wavelet transform in geophysics
"""

import numpy as np
import pandas as pd
from scipy import signal, stats
import pywt
from typing import Dict, List, Tuple, Optional, Union
import logging
from config.ml_config import ml_settings

logger = logging.getLogger(__name__)


class WaveletPatternDetector:
    """
    Detect time-localized patterns using Continuous Wavelet Transform.

    Unlike Fourier (which gives frequency content averaged over time),
    wavelets provide time-frequency representation showing WHEN specific
    frequencies are present.

    Perfect for:
    - Non-stationary signals (changing statistics)
    - Transient events
    - Regime transitions
    - Local pattern detection
    """

    def __init__(
        self,
        wavelet: str = 'morlet',
        scales: Optional[np.ndarray] = None,
        dt: float = 1.0
    ):
        """
        Initialize wavelet detector.

        Args:
            wavelet: Wavelet type
                - 'morlet' (good for oscillations, most common)
                - 'mexican_hat' (good for peaks)
                - 'paul' (good for asymmetric patterns)
            scales: Array of scales (frequencies) to analyze
                   (None = auto-generate from 1 day to 1 year)
            dt: Time step (sampling period)

        Example:
            >>> detector = WaveletPatternDetector(wavelet='morlet')
            >>> result = detector.analyze(time_series)
            >>> print(f"Detected {len(result['ridges'])} persistent patterns")
        """
        self.wavelet = wavelet
        self.dt = dt

        # Auto-generate scales if not provided (1 to 365 days)
        if scales is None:
            self.scales = np.arange(1, 365, 1)
        else:
            self.scales = scales

        logger.info(f"Initialized WaveletPatternDetector with {wavelet} wavelet")

    def analyze(
        self,
        time_series: Union[pd.Series, np.ndarray],
        return_visualization_data: bool = True
    ) -> Dict:
        """
        Perform wavelet analysis on time series.

        Args:
            time_series: Input time series
            return_visualization_data: Whether to include data for plotting

        Returns:
            {
                'coefficients': 2D array of wavelet coefficients (scale x time),
                'frequencies': Corresponding frequencies for each scale,
                'periods': Corresponding periods (1/frequency) in days,
                'power': Time-frequency power spectrum,
                'ridges': Detected ridges (persistent patterns),
                'significant_regions': Statistically significant regions,
                'cone_of_influence': Edge effect boundary,
                'global_wavelet_spectrum': Averaged power across time,
                'scale_averaged_power': Power averaged across scales
            }

        Example:
            >>> detector = WaveletPatternDetector()
            >>> result = detector.analyze(stock_prices)
            >>>
            >>> # Check for significant patterns
            >>> for ridge in result['ridges']:
            ...     print(f"Period: {ridge['period']:.1f} days")
            ...     print(f"Duration: {ridge['duration']:.1f} days")
            ...     print(f"Strength: {ridge['strength']:.3f}")
        """
        # Convert to array
        if isinstance(time_series, pd.Series):
            data = time_series.values
            index = time_series.index
        else:
            data = np.array(time_series)
            index = None

        # Normalize (zero mean, unit variance)
        data_normalized = (data - np.mean(data)) / np.std(data)

        # Compute CWT
        coefficients, frequencies = self._cwt(data_normalized)

        # Compute power spectrum
        power = np.abs(coefficients) ** 2

        # Detect ridges (persistent patterns)
        ridges = self._detect_ridges(power, frequencies)

        # Calculate cone of influence (region affected by edge effects)
        coi = self._cone_of_influence(len(data))

        # Global wavelet spectrum (average across time)
        global_spectrum = np.mean(power, axis=1)

        # Significant regions (above background noise)
        significant_regions = self._find_significant_regions(
            power,
            data_normalized
        )

        # Scale-averaged power (average across scales/frequencies)
        scale_avg_power = np.mean(power, axis=0)

        result = {
            'frequencies': frequencies,
            'periods': 1.0 / frequencies,  # Convert frequency to period
            'power': power,
            'ridges': ridges,
            'cone_of_influence': coi,
            'global_wavelet_spectrum': global_spectrum,
            'scale_averaged_power': scale_avg_power,
            'significant_regions': significant_regions,
            'n_ridges': len(ridges)
        }

        # Include raw coefficients if requested
        if return_visualization_data:
            result['coefficients'] = coefficients
            result['time_index'] = index

        return result

    def _cwt(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute Continuous Wavelet Transform.

        Returns:
            (coefficients, frequencies) tuple
        """
        # Use pywt's cwt for wavelet analysis
        if self.wavelet == 'morlet':
            wavelet_name = 'morl'
        elif self.wavelet == 'mexican_hat':
            wavelet_name = 'mexh'
        elif self.wavelet == 'paul':
            wavelet_name = 'morl'  # pywt doesn't have Paul, use Morlet
        elif self.wavelet == 'ricker':
            wavelet_name = 'mexh'  # Ricker is same as Mexican hat
        else:
            wavelet_name = 'morl'  # Default to Morlet

        # Compute CWT using pywt
        coefficients, frequencies = pywt.cwt(data, self.scales, wavelet_name, sampling_period=self.dt)

        # pywt returns frequencies directly
        # No need to compute them separately

        return coefficients, frequencies

    def _detect_ridges(
        self,
        power: np.ndarray,
        frequencies: np.ndarray,
        min_persistence: float = 0.1
    ) -> List[Dict]:
        """
        Detect ridges in time-frequency space.

        Ridges are continuous regions of high power that persist across time,
        indicating sustained oscillatory patterns.

        Args:
            power: Time-frequency power spectrum
            frequencies: Frequency for each scale
            min_persistence: Minimum duration as fraction of total time

        Returns:
            List of detected ridges with characteristics
        """
        ridges = []

        n_scales, n_times = power.shape
        min_duration = int(n_times * min_persistence)

        for scale_idx in range(n_scales):
            # Power at this scale across time
            scale_power = power[scale_idx, :]

            # Find regions above median (local peaks)
            threshold = np.median(scale_power) + np.std(scale_power)
            above_threshold = scale_power > threshold

            # Find continuous regions
            regions = self._find_continuous_regions(above_threshold)

            for start, end in regions:
                duration = end - start

                if duration >= min_duration:
                    # This is a significant ridge
                    avg_power = np.mean(scale_power[start:end])
                    max_power = np.max(scale_power[start:end])

                    ridges.append({
                        'period': 1.0 / frequencies[scale_idx],
                        'frequency': frequencies[scale_idx],
                        'start_time': start,
                        'end_time': end,
                        'duration': duration,
                        'strength': float(avg_power),
                        'max_strength': float(max_power),
                        'persistence': float(duration / n_times)
                    })

        # Sort by strength
        ridges.sort(key=lambda x: x['strength'], reverse=True)

        return ridges

    def _find_continuous_regions(self, mask: np.ndarray) -> List[Tuple[int, int]]:
        """Find continuous True regions in boolean mask."""
        regions = []
        in_region = False
        start = 0

        for i, val in enumerate(mask):
            if val and not in_region:
                # Start of new region
                start = i
                in_region = True
            elif not val and in_region:
                # End of region
                regions.append((start, i))
                in_region = False

        # Handle region extending to end
        if in_region:
            regions.append((start, len(mask)))

        return regions

    def _cone_of_influence(self, n_times: int) -> np.ndarray:
        """
        Calculate cone of influence.

        Region near edges where edge effects are significant.
        Results in this region should be interpreted with caution.

        Returns:
            Array indicating COI boundary for each time point
        """
        # For Morlet wavelet, COI is approximately sqrt(2) * scale
        if self.wavelet == 'morlet':
            coi_factor = np.sqrt(2)
        else:
            coi_factor = 1.0

        # COI increases from edges
        coi = np.zeros(n_times)

        for t in range(n_times):
            # Distance from nearest edge
            edge_dist = min(t, n_times - t - 1)

            # COI is proportional to distance from edge
            coi[t] = edge_dist * self.dt * coi_factor

        return coi

    def _find_significant_regions(
        self,
        power: np.ndarray,
        data: np.ndarray,
        alpha: float = 0.05
    ) -> np.ndarray:
        """
        Find statistically significant regions in wavelet power spectrum.

        Uses red noise background model (AR1 process) to determine
        significance threshold.

        Args:
            power: Wavelet power spectrum
            data: Original time series
            alpha: Significance level

        Returns:
            Boolean mask of significant regions
        """
        # Estimate AR1 coefficient (lag-1 autocorrelation)
        if len(data) > 1:
            lag1_autocorr = np.corrcoef(data[:-1], data[1:])[0, 1]
        else:
            lag1_autocorr = 0

        # Clip to valid range
        lag1_autocorr = np.clip(lag1_autocorr, -0.99, 0.99)

        # Red noise spectrum
        frequencies = 1.0 / self.scales
        red_noise = (1 - lag1_autocorr**2) / \
                    (1 + lag1_autocorr**2 - 2*lag1_autocorr*np.cos(2*np.pi*frequencies))

        # Chi-squared 95th percentile (for 2 degrees of freedom)
        from scipy.stats import chi2
        chi2_95 = chi2.ppf(1 - alpha, 2)

        # Significance threshold
        significance_threshold = red_noise[:, np.newaxis] * chi2_95 / 2

        # Regions above threshold are significant
        significant = power > significance_threshold

        return significant

    def get_dominant_patterns(
        self,
        result: Dict,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Get top-k dominant patterns from wavelet analysis.

        Args:
            result: Result from analyze()
            top_k: Number of top patterns to return

        Returns:
            List of dominant pattern descriptions
        """
        ridges = result['ridges'][:top_k]

        patterns = []
        for i, ridge in enumerate(ridges, 1):
            pattern = {
                'rank': i,
                'period_days': ridge['period'],
                'duration_days': ridge['duration'],
                'strength': ridge['strength'],
                'persistence': ridge['persistence'],
                'category': self._categorize_period(ridge['period']),
                'description': self._describe_pattern(ridge)
            }
            patterns.append(pattern)

        return patterns

    def _categorize_period(self, period: float) -> str:
        """Categorize period into time scales."""
        if 3 <= period <= 7:
            return 'weekly'
        elif 20 <= period <= 31:
            return 'monthly'
        elif 60 <= period <= 95:
            return 'quarterly'
        elif 240 <= period <= 270:
            return 'annual'
        else:
            return 'other'

    def _describe_pattern(self, ridge: Dict) -> str:
        """Generate human-readable pattern description."""
        period = ridge['period']
        duration = ridge['duration']
        category = self._categorize_period(period)

        return (
            f"{category.title()} pattern ({period:.1f} days) "
            f"persisting for {duration:.0f} periods "
            f"with {ridge['persistence']:.1%} consistency"
        )

    def compare_with_fourier(
        self,
        wavelet_result: Dict,
        fourier_result: Dict
    ) -> Dict:
        """
        Compare wavelet and Fourier results.

        Args:
            wavelet_result: Result from analyze()
            fourier_result: Result from FourierCyclicalDetector

        Returns:
            Comparison summary
        """
        # Extract periods from both methods
        wavelet_periods = [r['period'] for r in wavelet_result['ridges'][:5]]
        fourier_periods = [c['period_days'] for c in fourier_result['dominant_cycles'][:5]]

        # Find overlapping patterns
        overlaps = []
        for wp in wavelet_periods:
            for fp in fourier_periods:
                if abs(wp - fp) < 3:  # Within 3 days
                    overlaps.append({
                        'wavelet_period': wp,
                        'fourier_period': fp,
                        'difference': abs(wp - fp)
                    })

        # Patterns unique to each method
        wavelet_unique = [
            p for p in wavelet_periods
            if not any(abs(p - fp) < 3 for fp in fourier_periods)
        ]

        fourier_unique = [
            p for p in fourier_periods
            if not any(abs(p - wp) < 3 for wp in wavelet_periods)
        ]

        return {
            'overlapping_patterns': overlaps,
            'wavelet_unique': wavelet_unique,
            'fourier_unique': fourier_unique,
            'agreement_rate': len(overlaps) / max(len(wavelet_periods), 1),
            'interpretation': self._interpret_comparison(overlaps, wavelet_unique, fourier_unique)
        }

    def _interpret_comparison(
        self,
        overlaps: List[Dict],
        wavelet_unique: List[float],
        fourier_unique: List[float]
    ) -> str:
        """Interpret comparison results."""
        if len(overlaps) >= 3:
            interpretation = "Strong agreement between methods - patterns are robust."
        elif len(overlaps) >= 1:
            interpretation = "Moderate agreement - some patterns confirmed."
        else:
            interpretation = "Low agreement - patterns may be time-varying or transient."

        if wavelet_unique:
            interpretation += f" Wavelet detected {len(wavelet_unique)} transient patterns."

        if fourier_unique:
            interpretation += f" Fourier detected {len(fourier_unique)} global patterns."

        return interpretation


def quick_wavelet_analysis(
    time_series: Union[pd.Series, np.ndarray],
    wavelet: str = 'morlet'
) -> Dict:
    """
    Convenience function for quick wavelet analysis.

    Example:
        >>> result = quick_wavelet_analysis(stock_prices)
        >>> for pattern in result['dominant_patterns']:
        ...     print(pattern['description'])
    """
    detector = WaveletPatternDetector(wavelet=wavelet)
    result = detector.analyze(time_series)
    result['dominant_patterns'] = detector.get_dominant_patterns(result)

    return result
