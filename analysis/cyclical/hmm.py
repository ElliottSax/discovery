"""
Hidden Markov Model Regime Detector

Identifies market regimes and trading patterns using Hidden Markov Models.
Detects transitions between bull/bear markets, high/low volatility periods,
and other distinct market states.

Key Features:
- Multi-state regime detection (typically 3-5 states)
- Transition probability matrix
- Expected duration in each regime
- Real-time regime classification

Author: Claude
"""

import numpy as np
import pandas as pd
from hmmlearn import hmm
from typing import Dict, List, Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class RegimeDetector:
    """
    Detect market regimes and trading patterns using Hidden Markov Models.

    Regimes typically identified:
    1. Bull Market (high returns, low volatility)
    2. Bear Market (negative returns, high volatility)
    3. Sideways/Choppy (low returns, high volatility)
    4. Low Volatility (stable, predictable)
    """

    def __init__(self, n_states: int = 4, covariance_type: str = "full", n_iter: int = 1000):
        """
        Initialize HMM regime detector.

        Args:
            n_states: Number of hidden states (regimes)
            covariance_type: Type of covariance parameters ('spherical', 'diag', 'full', 'tied')
            n_iter: Maximum number of EM iterations
        """
        self.n_states = n_states
        self.model = hmm.GaussianHMM(
            n_components=n_states,
            covariance_type=covariance_type,
            n_iter=n_iter,
            random_state=42
        )
        self.is_fitted = False
        self.feature_names = []
        self.regime_characteristics = {}

    def fit(
        self,
        returns: Union[pd.Series, np.ndarray],
        volumes: Optional[Union[pd.Series, np.ndarray]] = None,
        additional_features: Optional[Dict[str, Union[pd.Series, np.ndarray]]] = None
    ) -> 'RegimeDetector':
        """
        Fit HMM to data.

        Args:
            returns: Daily/weekly returns
            volumes: Trading volumes (optional)
            additional_features: Additional features as dict (optional)

        Returns:
            self
        """
        # Create feature matrix
        X = self._create_feature_matrix(returns, volumes, additional_features)

        # Fit model
        self.model.fit(X)
        self.is_fitted = True

        logger.info(f"HMM fitted with {self.n_states} states and {X.shape[1]} features")

        return self

    def fit_and_predict(
        self,
        returns: Union[pd.Series, np.ndarray],
        volumes: Optional[Union[pd.Series, np.ndarray]] = None,
        additional_features: Optional[Dict[str, Union[pd.Series, np.ndarray]]] = None
    ) -> Dict:
        """
        Fit HMM and predict regimes.

        Args:
            returns: Daily/weekly returns
            volumes: Trading volumes (optional)
            additional_features: Additional features as dict (optional)

        Returns:
            {
                'current_regime': int (0 to n_states-1),
                'regime_probabilities': array of probabilities,
                'regime_characteristics': Dict describing each regime,
                'transition_matrix': Probability of switching regimes,
                'expected_duration': Expected days in each regime,
                'all_regimes': Array of regime predictions for all time points
            }
        """
        # Create feature matrix
        X = self._create_feature_matrix(returns, volumes, additional_features)

        # Fit model
        self.model.fit(X)
        self.is_fitted = True

        # Predict hidden states
        hidden_states = self.model.predict(X)

        # Get state probabilities
        state_probs = self.model.predict_proba(X)

        # Analyze regime characteristics
        returns_array = returns.values if isinstance(returns, pd.Series) else returns
        volumes_array = volumes.values if volumes is not None and isinstance(volumes, pd.Series) else volumes
        regime_chars = self._analyze_regimes(hidden_states, returns_array, volumes_array)

        # Current regime
        current_regime = int(hidden_states[-1])
        current_probs = state_probs[-1]

        # Transition matrix
        transition_matrix = self.model.transmat_

        # Expected duration in each state
        expected_durations = self._calculate_expected_durations(transition_matrix)

        self.regime_characteristics = regime_chars

        return {
            'current_regime': current_regime,
            'current_regime_name': regime_chars[current_regime]['name'],
            'regime_probabilities': current_probs.tolist(),
            'regime_characteristics': regime_chars,
            'transition_matrix': transition_matrix.tolist(),
            'expected_duration': expected_durations.tolist(),
            'all_regimes': hidden_states.tolist(),
            'state_probabilities': state_probs.tolist()
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict regimes for new data."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict regime probabilities for new data."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict_proba(X)

    def _create_feature_matrix(
        self,
        returns: Union[pd.Series, np.ndarray],
        volumes: Optional[Union[pd.Series, np.ndarray]],
        additional_features: Optional[Dict[str, Union[pd.Series, np.ndarray]]]
    ) -> np.ndarray:
        """
        Create feature matrix for HMM.

        Features:
        - Returns
        - Volatility (rolling std)
        - Momentum (rolling mean)
        - Volumes (if provided)
        - Additional features (if provided)
        """
        # Convert to arrays
        returns_array = returns.values if isinstance(returns, pd.Series) else np.array(returns)

        features = [returns_array]
        self.feature_names = ['returns']

        # Add volatility
        volatility = self._calculate_volatility(returns_array)
        features.append(volatility)
        self.feature_names.append('volatility')

        # Add momentum
        momentum = self._calculate_momentum(returns_array)
        features.append(momentum)
        self.feature_names.append('momentum')

        # Add volumes if provided
        if volumes is not None:
            volumes_array = volumes.values if isinstance(volumes, pd.Series) else np.array(volumes)
            # Normalize volumes
            volumes_norm = (volumes_array - np.mean(volumes_array)) / (np.std(volumes_array) + 1e-8)
            features.append(volumes_norm)
            self.feature_names.append('volume')

        # Add additional features
        if additional_features:
            for name, feature in additional_features.items():
                feature_array = feature.values if isinstance(feature, pd.Series) else np.array(feature)
                # Normalize
                feature_norm = (feature_array - np.mean(feature_array)) / (np.std(feature_array) + 1e-8)
                features.append(feature_norm)
                self.feature_names.append(name)

        # Stack features
        X = np.column_stack(features)

        return X

    def _calculate_volatility(self, returns: np.ndarray, window: int = 20) -> np.ndarray:
        """Calculate rolling volatility."""
        volatility = np.zeros_like(returns)
        for i in range(len(returns)):
            start = max(0, i - window + 1)
            volatility[i] = np.std(returns[start:i+1])
        return volatility

    def _calculate_momentum(self, returns: np.ndarray, window: int = 20) -> np.ndarray:
        """Calculate rolling momentum (mean return)."""
        momentum = np.zeros_like(returns)
        for i in range(len(returns)):
            start = max(0, i - window + 1)
            momentum[i] = np.mean(returns[start:i+1])
        return momentum

    def _analyze_regimes(
        self,
        states: np.ndarray,
        returns: np.ndarray,
        volumes: Optional[np.ndarray]
    ) -> Dict[int, Dict]:
        """
        Analyze characteristics of each regime.

        Returns dict mapping state number to characteristics.
        """
        regimes = {}

        for state in range(self.n_states):
            mask = states == state

            if not np.any(mask):
                continue

            # Calculate statistics for this regime
            state_returns = returns[mask]
            avg_return = np.mean(state_returns)
            volatility = np.std(state_returns)

            avg_volume = None
            if volumes is not None:
                state_volumes = volumes[mask]
                avg_volume = np.mean(state_volumes)

            # Classify regime based on characteristics
            name = self._classify_regime(avg_return, volatility, avg_volume)

            regimes[state] = {
                'name': name,
                'avg_return': float(avg_return),
                'volatility': float(volatility),
                'avg_volume': float(avg_volume) if avg_volume is not None else None,
                'frequency': float(np.sum(mask) / len(states)),
                'sample_size': int(np.sum(mask))
            }

        return regimes

    def _classify_regime(
        self,
        avg_return: float,
        volatility: float,
        avg_volume: Optional[float]
    ) -> str:
        """
        Classify regime based on return and volatility.

        Classification logic:
        - Bull: Positive returns, low/moderate volatility
        - Bear: Negative returns, high volatility
        - High Volatility: High volatility regardless of returns
        - Low Volatility: Low volatility, stable
        """
        # Thresholds (these can be tuned)
        high_vol_threshold = 0.025
        low_vol_threshold = 0.01
        positive_return_threshold = 0.001
        negative_return_threshold = -0.001

        if avg_return > positive_return_threshold and volatility < high_vol_threshold:
            return "Bull Market"
        elif avg_return < negative_return_threshold and volatility > low_vol_threshold:
            return "Bear Market"
        elif volatility > high_vol_threshold:
            return "High Volatility"
        else:
            return "Low Volatility"

    def _calculate_expected_durations(self, transition_matrix: np.ndarray) -> np.ndarray:
        """
        Calculate expected duration in each state.

        Expected duration = 1 / (1 - P(stay in state))
        """
        durations = np.zeros(self.n_states)

        for i in range(self.n_states):
            # Probability of staying in state i
            p_stay = transition_matrix[i, i]

            # Expected duration
            if p_stay < 1.0:
                durations[i] = 1.0 / (1.0 - p_stay)
            else:
                durations[i] = np.inf

        return durations

    def get_regime_summary(self, regime_data: Dict) -> str:
        """Get human-readable summary of current regime."""
        current = regime_data['current_regime']
        current_name = regime_data['current_regime_name']
        probs = regime_data['regime_probabilities']
        expected_dur = regime_data['expected_duration'][current]

        summary = f"Current Regime: {current_name} (State {current})\n"
        summary += f"Confidence: {probs[current]:.1%}\n"
        summary += f"Expected Duration: {expected_dur:.1f} periods\n\n"

        summary += "All Regimes:\n"
        for state, chars in regime_data['regime_characteristics'].items():
            prob = probs[state]
            summary += f"  {state}. {chars['name']}: "
            summary += f"Return={chars['avg_return']:.2%}, "
            summary += f"Vol={chars['volatility']:.2%}, "
            summary += f"Prob={prob:.1%}\n"

        return summary

    def get_regime_transition_probabilities(self, current_regime: int) -> Dict[str, float]:
        """Get probabilities of transitioning from current regime to others."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        transitions = {}
        for target_state in range(self.n_states):
            prob = self.model.transmat_[current_regime, target_state]
            regime_name = self.regime_characteristics.get(target_state, {}).get('name', f'State {target_state}')
            transitions[regime_name] = float(prob)

        return transitions
