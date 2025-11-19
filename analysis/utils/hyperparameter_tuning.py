"""
Hyperparameter Optimization Framework

Automated hyperparameter tuning using Optuna for all analysis modules.

Key Features:
- Bayesian optimization for efficient search
- Multi-objective optimization (accuracy + speed)
- Parallel trial execution
- Pruning of unpromising trials
- Study persistence and resumption
- Hyperparameter importance analysis

Supported Modules:
- Fourier Cyclical Detection
- HMM Regime Detection
- Wavelet Pattern Detection
- Change Point Detection
- LSTM Pattern Recognition

References:
- Akiba et al. (2019) - Optuna: A Next-generation Hyperparameter Optimization Framework
- Bergstra & Bengio (2012) - Random Search for Hyper-Parameter Optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Callable
import logging
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

try:
    import optuna
    from optuna.pruners import MedianPruner
    from optuna.samplers import TPESampler
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    logger.warning("Optuna not available. Hyperparameter tuning will be limited.")


@dataclass
class OptimizationConfig:
    """Configuration for hyperparameter optimization."""
    n_trials: int = 100
    timeout: Optional[int] = None  # seconds
    n_jobs: int = 1  # parallel trials
    sampler: str = 'tpe'  # tpe, random, grid
    pruner: str = 'median'  # median, none
    direction: str = 'minimize'  # minimize, maximize
    study_name: Optional[str] = None
    storage: Optional[str] = None  # database URL for persistence


class FourierOptimizer:
    """Optimize Fourier Cyclical Detector hyperparameters."""

    @staticmethod
    def objective(trial, time_series: pd.Series, validation_metric: Callable):
        """
        Objective function for Fourier hyperparameter optimization.

        Args:
            trial: Optuna trial
            time_series: Time series data
            validation_metric: Function to compute validation score

        Returns:
            Score to minimize/maximize
        """
        from analysis.cyclical.fourier import FourierCyclicalDetector

        # Suggest hyperparameters
        min_strength = trial.suggest_float('min_strength', 0.05, 0.5)
        min_confidence = trial.suggest_float('min_confidence', 0.5, 0.95)

        # Create detector
        detector = FourierCyclicalDetector(
            min_strength=min_strength,
            min_confidence=min_confidence
        )

        # Detect cycles
        result = detector.detect_cycles(time_series)

        # Compute validation metric
        score = validation_metric(result, time_series)

        return score


class HMMOptimizer:
    """Optimize HMM Regime Detector hyperparameters."""

    @staticmethod
    def objective(trial, returns: pd.Series, validation_metric: Callable):
        """
        Objective function for HMM hyperparameter optimization.

        Args:
            trial: Optuna trial
            returns: Return time series
            validation_metric: Function to compute validation score

        Returns:
            Score to minimize/maximize
        """
        from analysis.cyclical.hmm import RegimeDetector

        # Suggest hyperparameters
        n_states = trial.suggest_int('n_states', 2, 6)
        volatility_window = trial.suggest_int('volatility_window', 10, 40)

        # Create detector
        detector = RegimeDetector(
            n_states=n_states,
            volatility_window=volatility_window
        )

        # Detect regimes
        result = detector.detect(returns)

        # Compute validation metric
        score = validation_metric(result, returns)

        return score


class WaveletOptimizer:
    """Optimize Wavelet Pattern Detector hyperparameters."""

    @staticmethod
    def objective(trial, time_series: pd.Series, validation_metric: Callable):
        """
        Objective function for Wavelet hyperparameter optimization.

        Args:
            trial: Optuna trial
            time_series: Time series data
            validation_metric: Function to compute validation score

        Returns:
            Score to minimize/maximize
        """
        from analysis.advanced.wavelet import WaveletPatternDetector

        # Suggest hyperparameters
        wavelet = trial.suggest_categorical('wavelet', ['morlet', 'mexican_hat'])
        n_scales = trial.suggest_int('n_scales', 32, 128, step=32)
        significance_level = trial.suggest_float('significance_level', 0.01, 0.1)

        # Create detector
        scales = np.arange(1, n_scales + 1)
        detector = WaveletPatternDetector(wavelet=wavelet, scales=scales)

        # Analyze
        result = detector.analyze(time_series, significance_level=significance_level)

        # Compute validation metric
        score = validation_metric(result, time_series)

        return score


class ChangePointOptimizer:
    """Optimize Change Point Detector hyperparameters."""

    @staticmethod
    def objective(trial, time_series: Union[pd.Series, np.ndarray], validation_metric: Callable):
        """
        Objective function for Change Point hyperparameter optimization.

        Args:
            trial: Optuna trial
            time_series: Time series data
            validation_metric: Function to compute validation score

        Returns:
            Score to minimize/maximize
        """
        from analysis.advanced.changepoint import ChangePointDetector

        # Suggest hyperparameters
        method = trial.suggest_categorical('method', ['pelt', 'binseg', 'cusum'])
        penalty = trial.suggest_float('penalty', 0.5, 20.0)
        min_segment_length = trial.suggest_int('min_segment_length', 5, 50)
        model = trial.suggest_categorical('model', ['l2', 'rbf', 'normal'])

        # Create detector
        detector = ChangePointDetector(
            method=method,
            penalty=penalty,
            min_segment_length=min_segment_length,
            model=model
        )

        # Detect change points
        result = detector.detect(time_series)

        # Compute validation metric
        score = validation_metric(result, time_series)

        return score


class LSTMOptimizer:
    """Optimize LSTM Pattern Recognizer hyperparameters."""

    @staticmethod
    def objective(trial, time_series: pd.Series, validation_metric: Callable):
        """
        Objective function for LSTM hyperparameter optimization.

        Args:
            trial: Optuna trial
            time_series: Time series data
            validation_metric: Function to compute validation score

        Returns:
            Score to minimize/maximize
        """
        from analysis.advanced.lstm_patterns import LSTMPatternDetector, LSTMConfig

        # Suggest hyperparameters
        hidden_size = trial.suggest_int('hidden_size', 16, 128, step=16)
        num_layers = trial.suggest_int('num_layers', 1, 3)
        dropout = trial.suggest_float('dropout', 0.1, 0.5)
        sequence_length = trial.suggest_int('sequence_length', 10, 60, step=10)
        learning_rate = trial.suggest_float('learning_rate', 1e-4, 1e-2, log=True)
        use_attention = trial.suggest_categorical('use_attention', [True, False])

        # Create config
        config = LSTMConfig(
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            sequence_length=sequence_length,
            learning_rate=learning_rate,
            use_attention=use_attention,
            num_epochs=30  # Fixed for speed
        )

        # Create detector
        detector = LSTMPatternDetector(config)

        # Train
        try:
            history = detector.train(time_series, verbose=False)

            # Compute validation metric
            score = validation_metric(history, detector, time_series)

            # Prune if validation loss is not improving
            if 'final_val_loss' in history:
                trial.report(history['final_val_loss'], step=config.num_epochs)

            return score

        except Exception as e:
            logger.warning(f"Trial failed: {e}")
            return float('inf')  # Return worst score on failure


class HyperparameterTuner:
    """
    High-level interface for hyperparameter tuning.

    Provides unified interface for all module optimization.
    """

    def __init__(self, config: Optional[OptimizationConfig] = None):
        """
        Initialize tuner.

        Args:
            config: Optimization configuration
        """
        if not OPTUNA_AVAILABLE:
            raise ImportError(
                "Optuna is required for hyperparameter tuning. "
                "Install with: pip install optuna"
            )

        self.config = config or OptimizationConfig()
        self.study = None
        self.best_params = None

    def optimize_fourier(
        self,
        time_series: pd.Series,
        validation_metric: Optional[Callable] = None
    ) -> Dict:
        """
        Optimize Fourier Cyclical Detector.

        Args:
            time_series: Time series data
            validation_metric: Custom validation metric (optional)

        Returns:
            Best hyperparameters and study results
        """
        if validation_metric is None:
            # Default: maximize number of significant cycles with high confidence
            def default_metric(result, data):
                cycles = result['dominant_cycles']
                if len(cycles) == 0:
                    return 0.0
                # Score = number of cycles * average confidence
                avg_confidence = np.mean([c['confidence'] for c in cycles])
                return -(len(cycles) * avg_confidence)  # Negative for minimization

            validation_metric = default_metric

        # Create study
        self.study = optuna.create_study(
            direction=self.config.direction,
            sampler=TPESampler(),
            pruner=MedianPruner() if self.config.pruner == 'median' else None,
            study_name=self.config.study_name,
            storage=self.config.storage,
            load_if_exists=True
        )

        # Optimize
        self.study.optimize(
            lambda trial: FourierOptimizer.objective(trial, time_series, validation_metric),
            n_trials=self.config.n_trials,
            timeout=self.config.timeout,
            n_jobs=self.config.n_jobs
        )

        self.best_params = self.study.best_params

        return {
            'best_params': self.best_params,
            'best_value': self.study.best_value,
            'n_trials': len(self.study.trials),
            'study': self.study
        }

    def optimize_hmm(
        self,
        returns: pd.Series,
        validation_metric: Optional[Callable] = None
    ) -> Dict:
        """
        Optimize HMM Regime Detector.

        Args:
            returns: Return time series
            validation_metric: Custom validation metric (optional)

        Returns:
            Best hyperparameters and study results
        """
        if validation_metric is None:
            # Default: maximize BIC (lower is better)
            def default_metric(result, data):
                return result.get('bic', float('inf'))

            validation_metric = default_metric

        self.study = optuna.create_study(
            direction=self.config.direction,
            sampler=TPESampler(),
            study_name=self.config.study_name,
            storage=self.config.storage,
            load_if_exists=True
        )

        self.study.optimize(
            lambda trial: HMMOptimizer.objective(trial, returns, validation_metric),
            n_trials=self.config.n_trials,
            timeout=self.config.timeout,
            n_jobs=self.config.n_jobs
        )

        self.best_params = self.study.best_params

        return {
            'best_params': self.best_params,
            'best_value': self.study.best_value,
            'n_trials': len(self.study.trials),
            'study': self.study
        }

    def optimize_wavelet(
        self,
        time_series: pd.Series,
        validation_metric: Optional[Callable] = None
    ) -> Dict:
        """
        Optimize Wavelet Pattern Detector.

        Args:
            time_series: Time series data
            validation_metric: Custom validation metric (optional)

        Returns:
            Best hyperparameters and study results
        """
        if validation_metric is None:
            # Default: maximize number of significant ridges
            def default_metric(result, data):
                return -len(result.get('ridges', []))  # Negative for minimization

            validation_metric = default_metric

        self.study = optuna.create_study(
            direction=self.config.direction,
            sampler=TPESampler(),
            study_name=self.config.study_name,
            storage=self.config.storage,
            load_if_exists=True
        )

        self.study.optimize(
            lambda trial: WaveletOptimizer.objective(trial, time_series, validation_metric),
            n_trials=self.config.n_trials,
            timeout=self.config.timeout,
            n_jobs=self.config.n_jobs
        )

        self.best_params = self.study.best_params

        return {
            'best_params': self.best_params,
            'best_value': self.study.best_value,
            'n_trials': len(self.study.trials),
            'study': self.study
        }

    def optimize_changepoint(
        self,
        time_series: Union[pd.Series, np.ndarray],
        validation_metric: Optional[Callable] = None
    ) -> Dict:
        """
        Optimize Change Point Detector.

        Args:
            time_series: Time series data
            validation_metric: Custom validation metric (optional)

        Returns:
            Best hyperparameters and study results
        """
        if validation_metric is None:
            # Default: find optimal number of change points (not too many, not too few)
            def default_metric(result, data):
                n_changes = result['n_changes']
                data_length = len(data)
                # Penalize both too many and too few changes
                # Optimal: 1 change per 50-100 data points
                optimal_changes = data_length / 75
                penalty = abs(n_changes - optimal_changes)
                return penalty

            validation_metric = default_metric

        self.study = optuna.create_study(
            direction=self.config.direction,
            sampler=TPESampler(),
            study_name=self.config.study_name,
            storage=self.config.storage,
            load_if_exists=True
        )

        self.study.optimize(
            lambda trial: ChangePointOptimizer.objective(trial, time_series, validation_metric),
            n_trials=self.config.n_trials,
            timeout=self.config.timeout,
            n_jobs=self.config.n_jobs
        )

        self.best_params = self.study.best_params

        return {
            'best_params': self.best_params,
            'best_value': self.study.best_value,
            'n_trials': len(self.study.trials),
            'study': self.study
        }

    def optimize_lstm(
        self,
        time_series: pd.Series,
        validation_metric: Optional[Callable] = None
    ) -> Dict:
        """
        Optimize LSTM Pattern Recognizer.

        Args:
            time_series: Time series data
            validation_metric: Custom validation metric (optional)

        Returns:
            Best hyperparameters and study results
        """
        if validation_metric is None:
            # Default: minimize validation loss
            def default_metric(history, detector, data):
                return history.get('final_val_loss', float('inf'))

            validation_metric = default_metric

        self.study = optuna.create_study(
            direction=self.config.direction,
            sampler=TPESampler(),
            pruner=MedianPruner(),
            study_name=self.config.study_name,
            storage=self.config.storage,
            load_if_exists=True
        )

        self.study.optimize(
            lambda trial: LSTMOptimizer.objective(trial, time_series, validation_metric),
            n_trials=self.config.n_trials,
            timeout=self.config.timeout,
            n_jobs=self.config.n_jobs
        )

        self.best_params = self.study.best_params

        return {
            'best_params': self.best_params,
            'best_value': self.study.best_value,
            'n_trials': len(self.study.trials),
            'study': self.study
        }

    def get_param_importance(self) -> Dict[str, float]:
        """
        Get hyperparameter importance from study.

        Returns:
            Dictionary mapping parameter names to importance scores
        """
        if self.study is None:
            raise ValueError("No study available. Run optimization first.")

        importance = optuna.importance.get_param_importances(self.study)
        return importance

    def plot_optimization_history(self, save_path: Optional[str] = None):
        """Plot optimization history."""
        if self.study is None:
            raise ValueError("No study available. Run optimization first.")

        import matplotlib.pyplot as plt

        # Optimization history
        fig = optuna.visualization.matplotlib.plot_optimization_history(self.study)
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()

    def plot_param_importances(self, save_path: Optional[str] = None):
        """Plot hyperparameter importances."""
        if self.study is None:
            raise ValueError("No study available. Run optimization first.")

        import matplotlib.pyplot as plt

        fig = optuna.visualization.matplotlib.plot_param_importances(self.study)
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()


# Convenience functions
def quick_optimize_fourier(
    time_series: pd.Series,
    n_trials: int = 50,
    **kwargs
) -> Dict:
    """Quick Fourier optimization with defaults."""
    config = OptimizationConfig(n_trials=n_trials, **kwargs)
    tuner = HyperparameterTuner(config)
    return tuner.optimize_fourier(time_series)


def quick_optimize_hmm(
    returns: pd.Series,
    n_trials: int = 50,
    **kwargs
) -> Dict:
    """Quick HMM optimization with defaults."""
    config = OptimizationConfig(n_trials=n_trials, **kwargs)
    tuner = HyperparameterTuner(config)
    return tuner.optimize_hmm(returns)


if __name__ == "__main__":
    # Example usage
    if OPTUNA_AVAILABLE:
        print("Example: Hyperparameter Optimization")

        # Create synthetic data
        t = np.linspace(0, 365, 365)
        signal = 10 + 5 * np.sin(2 * np.pi * t / 30) + np.random.normal(0, 1, 365)
        data = pd.Series(signal)

        # Optimize Fourier
        print("Optimizing Fourier detector...")
        config = OptimizationConfig(n_trials=20, direction='minimize')
        tuner = HyperparameterTuner(config)
        result = tuner.optimize_fourier(data)

        print(f"\nBest parameters: {result['best_params']}")
        print(f"Best value: {result['best_value']:.4f}")
        print(f"Number of trials: {result['n_trials']}")

        # Parameter importance
        importance = tuner.get_param_importance()
        print(f"\nParameter importance:")
        for param, imp in importance.items():
            print(f"  {param}: {imp:.4f}")

        print("\n✅ Hyperparameter optimization complete!")
    else:
        print("Optuna not available. Install with: pip install optuna")
