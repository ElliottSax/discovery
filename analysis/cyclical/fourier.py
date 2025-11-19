"""
Fourier Cyclical Pattern Detector

Detects periodic patterns in trading behavior using Fourier analysis.
Identifies dominant cycles at various timeframes from weekly to election cycles.

Key Features:
- Fast Fourier Transform (FFT) for frequency domain analysis
- Seasonal decomposition (trend, seasonal, residual)
- Cycle-based forecasting
- Confidence scoring for detected patterns

Author: Claude
"""

import numpy as np
import pandas as pd
from scipy import signal
from scipy.fft import fft, fftfreq
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class FourierCyclicalDetector:
    """
    Detect cyclical patterns using Fourier analysis.

    Detects:
    - Weekly cycles (5-7 days)
    - Monthly cycles (21-30 days)
    - Quarterly cycles (60-90 days)
    - Annual cycles (250-260 trading days)
    - Election cycles (2-4 years)
    """

    def __init__(self, min_strength: float = 0.1, min_confidence: float = 0.6):
        """
        Initialize Fourier detector.

        Args:
            min_strength: Minimum FFT power to consider a cycle significant
            min_confidence: Minimum confidence threshold (0-1)
        """
        self.min_strength = min_strength
        self.min_confidence = min_confidence
        self.cycles_detected = []

    def detect_cycles(
        self,
        time_series: Union[pd.Series, np.ndarray],
        sampling_rate: str = 'daily',
        return_details: bool = True
    ) -> Dict:
        """
        Identify dominant cycles in trading patterns.

        Args:
            time_series: Trade frequency or returns time series
            sampling_rate: 'daily', 'weekly', 'monthly'
            return_details: Whether to include detailed decomposition

        Returns:
            {
                'dominant_cycles': List of cycle information dicts,
                'seasonal_decomposition': Trend + Seasonal + Residual (if return_details),
                'cycle_forecast': Predicted next values based on cycles
            }
        """
        # Convert to numpy array if pandas Series
        if isinstance(time_series, pd.Series):
            ts_array = time_series.values
            ts_index = time_series.index
        else:
            ts_array = np.array(time_series)
            ts_index = None

        # Validate input
        if len(ts_array) < 30:
            raise ValueError(f"Time series too short: {len(ts_array)} < 30. Need at least 30 observations.")

        # Handle NaN values
        if np.any(np.isnan(ts_array)):
            logger.warning("NaN values detected in time series. Interpolating...")
            ts_array = self._interpolate_nan(ts_array)

        # Remove trend
        detrended = signal.detrend(ts_array)

        # Apply FFT
        N = len(detrended)
        yf = fft(detrended)
        xf = fftfreq(N, 1)[:N//2]

        # Calculate power spectrum
        power = 2.0/N * np.abs(yf[0:N//2])

        # Find peaks in frequency domain
        peaks, properties = signal.find_peaks(
            power,
            height=self.min_strength,
            prominence=self.min_strength * 0.5
        )

        # Convert frequencies to periods
        cycles = []
        for peak in peaks:
            if xf[peak] > 0:
                period = 1 / xf[peak]
                strength = power[peak]
                confidence = self._calculate_confidence(period, strength, N)

                if confidence >= self.min_confidence:
                    cycle_info = {
                        'period_days': float(period),
                        'strength': float(strength),
                        'confidence': float(confidence),
                        'frequency': float(xf[peak]),
                        'category': self._categorize_cycle(period, sampling_rate)
                    }
                    cycles.append(cycle_info)

        # Sort by strength
        cycles.sort(key=lambda x: x['strength'], reverse=True)
        self.cycles_detected = cycles

        result = {
            'dominant_cycles': cycles[:10],  # Top 10 cycles
            'total_cycles_found': len(cycles),
            'cycle_forecast': self._forecast_from_cycles(cycles, ts_array, forecast_periods=30)
        }

        # Add detailed decomposition if requested
        if return_details and len(ts_array) >= 42:  # Need at least 2 periods for seasonal decompose
            try:
                result['seasonal_decomposition'] = self._seasonal_decompose(
                    ts_array, ts_index, sampling_rate
                )
            except Exception as e:
                logger.warning(f"Seasonal decomposition failed: {e}")
                result['seasonal_decomposition'] = None

        return result

    def _interpolate_nan(self, arr: np.ndarray) -> np.ndarray:
        """Interpolate NaN values using linear interpolation."""
        if not np.any(np.isnan(arr)):
            return arr

        # Create a copy
        result = arr.copy()

        # Find valid indices
        valid = ~np.isnan(result)

        if not np.any(valid):
            raise ValueError("All values are NaN")

        # Interpolate
        indices = np.arange(len(result))
        result[~valid] = np.interp(indices[~valid], indices[valid], result[valid])

        return result

    def _calculate_confidence(self, period: float, strength: float, N: int) -> float:
        """
        Calculate confidence score for detected cycle.

        Considers:
        - Strength of the cycle in power spectrum
        - Number of complete cycles in the data
        - Whether period makes sense (not too short/long)
        """
        # Number of complete cycles in data
        n_cycles = N / period

        # Base confidence from strength (normalized)
        strength_confidence = min(strength / 1.0, 1.0)

        # Confidence from having enough cycles
        cycles_confidence = min(n_cycles / 3.0, 1.0)  # Want at least 3 complete cycles

        # Penalize very short or very long periods
        period_confidence = 1.0
        if period < 3:  # Too short to be meaningful
            period_confidence = 0.3
        elif period > N / 2:  # Period longer than half the data
            period_confidence = 0.5

        # Combined confidence
        confidence = (strength_confidence * 0.5 +
                     cycles_confidence * 0.3 +
                     period_confidence * 0.2)

        return confidence

    def _categorize_cycle(self, period: float, sampling_rate: str) -> str:
        """Categorize cycle by period length."""
        # Adjust for sampling rate
        if sampling_rate == 'weekly':
            period = period * 5  # Convert to approximate daily
        elif sampling_rate == 'monthly':
            period = period * 21

        if 3 <= period <= 7:
            return 'weekly'
        elif 20 <= period <= 31:
            return 'monthly'
        elif 60 <= period <= 95:
            return 'quarterly'
        elif 240 <= period <= 270:
            return 'annual'
        elif 480 <= period <= 1500:
            return 'election_cycle'
        else:
            return 'other'

    def _seasonal_decompose(
        self,
        time_series: np.ndarray,
        ts_index: Optional[pd.Index],
        sampling_rate: str
    ) -> Dict:
        """
        Decompose into trend, seasonal, and residual components.
        """
        from statsmodels.tsa.seasonal import seasonal_decompose

        # Determine period based on sampling rate
        period_map = {
            'daily': 21,  # Monthly cycle for daily data
            'weekly': 4,  # Monthly cycle for weekly data
            'monthly': 12  # Annual cycle for monthly data
        }
        period = period_map.get(sampling_rate, 21)

        # Ensure we have enough data
        if len(time_series) < 2 * period:
            period = max(2, len(time_series) // 4)

        # Create pandas Series for decomposition
        if ts_index is not None:
            ts = pd.Series(time_series, index=ts_index)
        else:
            ts = pd.Series(time_series)

        try:
            result = seasonal_decompose(ts, model='additive', period=period, extrapolate_trend='freq')

            return {
                'trend': result.trend.values.tolist(),
                'seasonal': result.seasonal.values.tolist(),
                'residual': result.resid.values.tolist(),
                'period': period
            }
        except Exception as e:
            logger.error(f"Seasonal decomposition failed: {e}")
            return None

    def _forecast_from_cycles(
        self,
        cycles: List[Dict],
        historical_data: np.ndarray,
        forecast_periods: int = 30
    ) -> Dict:
        """
        Generate forecast based on detected cycles.

        Uses top cycles to reconstruct signal and project forward.
        """
        if not cycles or len(historical_data) == 0:
            return {
                'forecast': [],
                'lower_bound': [],
                'upper_bound': []
            }

        # Use top 3-5 cycles for forecasting
        top_cycles = cycles[:min(5, len(cycles))]

        # Reconstruct signal from cycles
        N = len(historical_data)
        t = np.arange(N)
        reconstructed = np.zeros(N)

        for cycle in top_cycles:
            frequency = cycle['frequency']
            strength = cycle['strength']
            reconstructed += strength * np.sin(2 * np.pi * frequency * t)

        # Add mean
        reconstructed += np.mean(historical_data)

        # Forecast future periods
        t_future = np.arange(N, N + forecast_periods)
        forecast = np.zeros(forecast_periods)

        for cycle in top_cycles:
            frequency = cycle['frequency']
            strength = cycle['strength']
            forecast += strength * np.sin(2 * np.pi * frequency * t_future)

        forecast += np.mean(historical_data)

        # Estimate uncertainty (based on residual variance)
        residual = historical_data - reconstructed
        residual_std = np.std(residual)

        # Confidence intervals (95%)
        lower_bound = forecast - 1.96 * residual_std
        upper_bound = forecast + 1.96 * residual_std

        return {
            'forecast': forecast.tolist(),
            'lower_bound': lower_bound.tolist(),
            'upper_bound': upper_bound.tolist(),
            'confidence_interval': 0.95,
            'residual_std': float(residual_std)
        }

    def get_cycle_summary(self) -> str:
        """Get human-readable summary of detected cycles."""
        if not self.cycles_detected:
            return "No significant cycles detected."

        summary = f"Found {len(self.cycles_detected)} significant cycles:\n\n"

        for i, cycle in enumerate(self.cycles_detected[:5], 1):
            period = cycle['period_days']
            category = cycle['category']
            confidence = cycle['confidence']

            summary += f"{i}. {category.replace('_', ' ').title()}: "
            summary += f"{period:.1f} days (confidence: {confidence:.1%})\n"

        return summary
