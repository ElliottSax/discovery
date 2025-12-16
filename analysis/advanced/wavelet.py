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


class MultiResolutionWaveletAnalyzer:
    """
    Multi-Resolution Wavelet Analysis using Discrete Wavelet Transform.

    Decomposes signal into multiple scales simultaneously using wavelet pyramid,
    revealing hierarchical patterns and cross-scale dependencies.

    Key Features:
    - Pyramid decomposition (coarse to fine scales)
    - Cross-scale correlations
    - Scale-specific pattern extraction
    - Hierarchical anomaly detection

    Use Cases:
    - Multi-timescale trading patterns (daily + weekly + monthly)
    - Scale-dependent correlations (intraday vs long-term)
    - Hierarchical regime detection
    - Cross-scale causality
    """

    def __init__(
        self,
        wavelet: str = 'db4',
        max_level: Optional[int] = None,
        mode: str = 'symmetric'
    ):
        """
        Initialize multi-resolution analyzer.

        Args:
            wavelet: Discrete wavelet family
                - 'db4' (Daubechies 4, good for finance)
                - 'sym5' (Symlets, symmetric)
                - 'coif3' (Coiflets, smooth)
                - 'bior3.5' (Biorthogonal, good for edges)
            max_level: Maximum decomposition level (None = auto)
            mode: Signal extension mode ('symmetric', 'periodic', 'zero')
        """
        self.wavelet = wavelet
        self.max_level = max_level
        self.mode = mode

        logger.info(f"Initialized MultiResolutionWaveletAnalyzer with {wavelet}")

    def decompose(
        self,
        time_series: Union[pd.Series, np.ndarray]
    ) -> Dict:
        """
        Perform multi-resolution decomposition.

        Decomposes signal into approximation (low-frequency trend) and
        details (high-frequency fluctuations) at multiple scales.

        Returns:
            {
                'approximations': [A1, A2, ..., An] (coarse to fine),
                'details': [D1, D2, ..., Dn] (coarse to fine),
                'reconstruction_error': Numerical error in reconstruction,
                'energy_distribution': Energy at each scale,
                'level_names': ['D1 (2-4 days)', 'D2 (4-8 days)', ...],
                'max_level': Number of decomposition levels
            }
        """
        # Convert to array
        if isinstance(time_series, pd.Series):
            data = time_series.values
            index = time_series.index
        else:
            data = np.array(time_series)
            index = None

        # Determine max level if not specified
        if self.max_level is None:
            max_level = pywt.dwt_max_level(len(data), self.wavelet)
        else:
            max_level = min(self.max_level, pywt.dwt_max_level(len(data), self.wavelet))

        # Perform multi-level decomposition
        coeffs = pywt.wavedec(data, self.wavelet, level=max_level, mode=self.mode)

        # coeffs = [cAn, cDn, cDn-1, ..., cD1]
        # cAn = approximation at level n (coarsest)
        # cDi = details at level i

        approximation = coeffs[0]
        details = coeffs[1:][::-1]  # Reverse to go from coarse to fine

        # Reconstruct each level separately
        approximations = []
        detail_reconstructions = []

        for level in range(1, max_level + 1):
            # Reconstruct approximation at this level
            approx_coeffs = [coeffs[0]] + [np.zeros_like(c) for c in coeffs[1:level]] + coeffs[level:]
            approx_recon = pywt.waverec(approx_coeffs, self.wavelet, mode=self.mode)
            approximations.append(approx_recon[:len(data)])

            # Reconstruct detail at this level
            detail_coeffs = [np.zeros_like(coeffs[0])] + [np.zeros_like(c) for c in coeffs[1:level]] + [coeffs[level]] + [np.zeros_like(c) for c in coeffs[level+1:]]
            detail_recon = pywt.waverec(detail_coeffs, self.wavelet, mode=self.mode)
            detail_reconstructions.append(detail_recon[:len(data)])

        # Calculate reconstruction error
        reconstructed = sum(detail_reconstructions) + approximations[-1]
        reconstruction_error = np.linalg.norm(data - reconstructed[:len(data)]) / np.linalg.norm(data)

        # Calculate energy distribution
        total_energy = np.sum(data**2)
        energy_dist = []
        for detail in detail_reconstructions:
            energy = np.sum(detail**2) / total_energy
            energy_dist.append(energy)

        # Generate level names with time scale interpretations
        level_names = []
        for i in range(1, max_level + 1):
            scale_days = 2**i
            level_names.append(f"D{i} ({scale_days//2}-{scale_days} days)")

        return {
            'approximations': approximations,
            'details': detail_reconstructions,
            'raw_coeffs': coeffs,
            'reconstruction_error': float(reconstruction_error),
            'energy_distribution': energy_dist,
            'level_names': level_names,
            'max_level': max_level,
            'time_index': index
        }

    def detect_cross_scale_correlations(
        self,
        decomposition: Dict,
        significance_threshold: float = 0.3
    ) -> Dict:
        """
        Detect correlations between different scales.

        Cross-scale correlations indicate hierarchical dependencies,
        e.g., monthly patterns modulating weekly patterns.

        Args:
            decomposition: Result from decompose()
            significance_threshold: Minimum correlation to report

        Returns:
            {
                'correlation_matrix': NxN matrix of scale correlations,
                'significant_pairs': [(scale_i, scale_j, correlation)],
                'interpretation': Human-readable description
            }
        """
        details = decomposition['details']
        n_levels = len(details)

        # Correlation matrix
        corr_matrix = np.zeros((n_levels, n_levels))

        for i in range(n_levels):
            for j in range(n_levels):
                if i == j:
                    corr_matrix[i, j] = 1.0
                else:
                    # Align lengths (use shorter length)
                    min_len = min(len(details[i]), len(details[j]))
                    corr = np.corrcoef(details[i][:min_len], details[j][:min_len])[0, 1]
                    corr_matrix[i, j] = corr

        # Find significant correlations
        significant_pairs = []
        for i in range(n_levels):
            for j in range(i + 1, n_levels):
                if abs(corr_matrix[i, j]) >= significance_threshold:
                    significant_pairs.append({
                        'scale_1': decomposition['level_names'][i],
                        'scale_2': decomposition['level_names'][j],
                        'correlation': float(corr_matrix[i, j]),
                        'interpretation': self._interpret_cross_scale(
                            i, j, corr_matrix[i, j], decomposition['level_names']
                        )
                    })

        # Sort by absolute correlation
        significant_pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)

        return {
            'correlation_matrix': corr_matrix.tolist(),
            'significant_pairs': significant_pairs,
            'n_significant': len(significant_pairs),
            'level_names': decomposition['level_names']
        }

    def _interpret_cross_scale(
        self,
        i: int,
        j: int,
        correlation: float,
        level_names: List[str]
    ) -> str:
        """Interpret cross-scale correlation."""
        if correlation > 0.5:
            relationship = "strong positive coupling"
        elif correlation > 0.3:
            relationship = "moderate positive coupling"
        elif correlation < -0.5:
            relationship = "strong negative coupling"
        elif correlation < -0.3:
            relationship = "moderate negative coupling"
        else:
            relationship = "weak coupling"

        return f"{level_names[i]} and {level_names[j]} show {relationship}"

    def extract_scale_specific_patterns(
        self,
        decomposition: Dict,
        scale_level: int
    ) -> Dict:
        """
        Extract patterns from specific scale.

        Args:
            decomposition: Result from decompose()
            scale_level: Level to analyze (1 = finest, max_level = coarsest)

        Returns:
            {
                'level': Level number,
                'level_name': Time scale description,
                'detail_signal': Reconstructed detail at this level,
                'peaks': Local maxima locations,
                'troughs': Local minima locations,
                'energy': Total energy at this scale,
                'dominant_frequency': Main frequency component
            }
        """
        if scale_level < 1 or scale_level > decomposition['max_level']:
            raise ValueError(f"Invalid scale_level: {scale_level}")

        detail = decomposition['details'][scale_level - 1]

        # Find peaks and troughs
        from scipy.signal import find_peaks

        peaks, peak_properties = find_peaks(detail, prominence=np.std(detail) * 0.5)
        troughs, trough_properties = find_peaks(-detail, prominence=np.std(detail) * 0.5)

        # Calculate energy
        energy = np.sum(detail**2)

        # Dominant frequency (from peak spacing)
        if len(peaks) > 1:
            peak_spacing = np.diff(peaks)
            dominant_period = np.median(peak_spacing) if len(peak_spacing) > 0 else 0
        else:
            dominant_period = 0

        return {
            'level': scale_level,
            'level_name': decomposition['level_names'][scale_level - 1],
            'detail_signal': detail.tolist(),
            'peaks': peaks.tolist(),
            'troughs': troughs.tolist(),
            'n_peaks': len(peaks),
            'n_troughs': len(troughs),
            'energy': float(energy),
            'relative_energy': float(decomposition['energy_distribution'][scale_level - 1]),
            'dominant_period': float(dominant_period),
            'std': float(np.std(detail))
        }

    def detect_multiscale_anomalies(
        self,
        decomposition: Dict,
        threshold_std: float = 3.0
    ) -> Dict:
        """
        Detect anomalies across multiple scales.

        An event is a multi-scale anomaly if it appears as an outlier
        at multiple resolution levels simultaneously.

        Args:
            decomposition: Result from decompose()
            threshold_std: Standard deviations for anomaly threshold

        Returns:
            {
                'scale_specific_anomalies': Anomalies at each scale,
                'multiscale_anomalies': Anomalies present at multiple scales,
                'severity': Severity score for each anomaly
            }
        """
        details = decomposition['details']

        # Detect anomalies at each scale
        scale_anomalies = []
        for i, detail in enumerate(details):
            threshold = np.std(detail) * threshold_std
            anomaly_mask = np.abs(detail) > threshold
            anomaly_indices = np.where(anomaly_mask)[0]

            scale_anomalies.append({
                'level': i + 1,
                'level_name': decomposition['level_names'][i],
                'anomaly_indices': anomaly_indices.tolist(),
                'n_anomalies': len(anomaly_indices),
                'threshold': float(threshold)
            })

        # Find multiscale anomalies (present at multiple scales)
        # Look for temporal proximity across scales
        multiscale = []
        n_levels = len(details)

        for level in range(n_levels):
            for idx in scale_anomalies[level]['anomaly_indices']:
                # Check if nearby anomalies exist at other scales
                scales_present = [level]

                for other_level in range(n_levels):
                    if other_level == level:
                        continue

                    # Check for anomalies within ±10% of signal length
                    tolerance = len(details[other_level]) // 10
                    other_indices = scale_anomalies[other_level]['anomaly_indices']

                    for other_idx in other_indices:
                        if abs(other_idx - idx) <= tolerance:
                            scales_present.append(other_level)
                            break

                # If present at multiple scales, it's a multiscale anomaly
                if len(scales_present) >= 2:
                    multiscale.append({
                        'time_index': idx,
                        'scales_affected': [decomposition['level_names'][s] for s in scales_present],
                        'n_scales': len(scales_present),
                        'severity': len(scales_present) / n_levels  # More scales = more severe
                    })

        # Remove duplicates
        seen = set()
        unique_multiscale = []
        for anomaly in multiscale:
            key = anomaly['time_index']
            if key not in seen:
                seen.add(key)
                unique_multiscale.append(anomaly)

        # Sort by severity
        unique_multiscale.sort(key=lambda x: x['severity'], reverse=True)

        return {
            'scale_specific_anomalies': scale_anomalies,
            'multiscale_anomalies': unique_multiscale,
            'n_multiscale': len(unique_multiscale)
        }


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


def quick_multiscale_analysis(
    time_series: Union[pd.Series, np.ndarray],
    wavelet: str = 'db4'
) -> Dict:
    """
    Convenience function for quick multi-resolution analysis.

    Example:
        >>> result = quick_multiscale_analysis(stock_prices)
        >>> print(f"Found {result['n_multiscale_anomalies']} multi-scale anomalies")
    """
    analyzer = MultiResolutionWaveletAnalyzer(wavelet=wavelet)
    decomposition = analyzer.decompose(time_series)

    # Add cross-scale correlations
    correlations = analyzer.detect_cross_scale_correlations(decomposition)

    # Add multiscale anomalies
    anomalies = analyzer.detect_multiscale_anomalies(decomposition)

    return {
        **decomposition,
        'cross_scale_correlations': correlations,
        'anomalies': anomalies,
        'n_multiscale_anomalies': anomalies['n_multiscale']
    }
