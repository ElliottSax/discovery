"""
MLFlow Experiment Tracker for Cyclical Models

Provides comprehensive experiment tracking for all cyclical pattern detection models.
Logs parameters, metrics, artifacts, and model versions to MLFlow.

Key Features:
- Automatic experiment creation and organization
- Parameter and metric logging
- Artifact storage (plots, predictions, reports)
- Model versioning and registry integration

Author: Claude
"""

import mlflow
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Union
import json
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

from app.ml.utils.mlflow_tracker import MLFlowTracker
from .fourier import FourierCyclicalDetector
from .hmm import RegimeDetector
from .dtw import DynamicTimeWarpingMatcher

logger = logging.getLogger(__name__)


class CyclicalExperimentTracker:
    """
    Track cyclical model experiments with MLFlow.

    Handles logging for:
    - Fourier cycle detection
    - HMM regime detection
    - DTW pattern matching
    """

    def __init__(
        self,
        experiment_name: str = "cyclical_pattern_detection",
        tracking_uri: Optional[str] = None
    ):
        """
        Initialize experiment tracker.

        Args:
            experiment_name: Name of MLFlow experiment
            tracking_uri: MLFlow tracking server URI (default: from config)
        """
        self.experiment_name = experiment_name
        self.tracker = MLFlowTracker()

        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)

        # Create or get experiment
        try:
            self.experiment_id = mlflow.create_experiment(experiment_name)
        except Exception:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            self.experiment_id = experiment.experiment_id

        mlflow.set_experiment(experiment_name)

    def track_fourier_detection(
        self,
        detector: FourierCyclicalDetector,
        data: Union[pd.Series, np.ndarray],
        result: Dict,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Track Fourier cycle detection experiment.

        Args:
            detector: FourierCyclicalDetector instance
            data: Input time series data
            result: Detection results from detector.detect_cycles()
            run_name: Optional run name
            tags: Optional tags for the run

        Returns:
            Run ID
        """
        if run_name is None:
            run_name = f"fourier_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with mlflow.start_run(run_name=run_name) as run:
            # Log parameters
            mlflow.log_param("model_type", "fourier_cyclical_detector")
            mlflow.log_param("min_strength", detector.min_strength)
            mlflow.log_param("min_confidence", detector.min_confidence)
            mlflow.log_param("data_length", len(data))

            # Log tags
            if tags:
                mlflow.set_tags(tags)

            mlflow.set_tag("model_family", "cyclical")
            mlflow.set_tag("algorithm", "fourier_transform")

            # Log metrics
            mlflow.log_metric("total_cycles_found", result.get('total_cycles_found', 0))

            if result['dominant_cycles']:
                top_cycle = result['dominant_cycles'][0]
                mlflow.log_metric("top_cycle_period", top_cycle['period_days'])
                mlflow.log_metric("top_cycle_strength", top_cycle['strength'])
                mlflow.log_metric("top_cycle_confidence", top_cycle['confidence'])

                # Average metrics across top 5 cycles
                top_5 = result['dominant_cycles'][:5]
                avg_confidence = np.mean([c['confidence'] for c in top_5])
                mlflow.log_metric("avg_confidence_top5", avg_confidence)

            # Log forecast metrics if available
            if 'cycle_forecast' in result:
                forecast = result['cycle_forecast']
                if 'residual_std' in forecast:
                    mlflow.log_metric("forecast_uncertainty", forecast['residual_std'])

            # Log artifacts
            # 1. Cycle summary as JSON
            cycles_json = json.dumps(result['dominant_cycles'], indent=2)
            mlflow.log_text(cycles_json, "cycles.json")

            # 2. Human-readable summary
            summary = detector.get_cycle_summary()
            mlflow.log_text(summary, "cycle_summary.txt")

            # 3. Visualization (if we have decomposition)
            if result.get('seasonal_decomposition'):
                try:
                    fig = self._plot_fourier_results(data, result)
                    mlflow.log_figure(fig, "fourier_analysis.png")
                    plt.close(fig)
                except Exception as e:
                    logger.warning(f"Failed to create Fourier plot: {e}")

            logger.info(f"Fourier experiment tracked: {run.info.run_id}")
            return run.info.run_id

    def track_hmm_detection(
        self,
        detector: RegimeDetector,
        result: Dict,
        returns: Union[pd.Series, np.ndarray],
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Track HMM regime detection experiment.

        Args:
            detector: RegimeDetector instance
            result: Detection results from detector.fit_and_predict()
            returns: Input returns data
            run_name: Optional run name
            tags: Optional tags for the run

        Returns:
            Run ID
        """
        if run_name is None:
            run_name = f"hmm_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with mlflow.start_run(run_name=run_name) as run:
            # Log parameters
            mlflow.log_param("model_type", "hmm_regime_detector")
            mlflow.log_param("n_states", detector.n_states)
            mlflow.log_param("covariance_type", detector.model.covariance_type)
            mlflow.log_param("data_length", len(returns))
            mlflow.log_param("n_features", len(detector.feature_names))

            # Log feature names
            mlflow.log_param("features", ",".join(detector.feature_names))

            # Log tags
            if tags:
                mlflow.set_tags(tags)

            mlflow.set_tag("model_family", "cyclical")
            mlflow.set_tag("algorithm", "hidden_markov_model")

            # Log metrics
            current_regime = result['current_regime']
            current_prob = result['regime_probabilities'][current_regime]

            mlflow.log_metric("current_regime", current_regime)
            mlflow.log_metric("current_regime_confidence", current_prob)
            mlflow.log_metric("expected_duration", result['expected_duration'][current_regime])

            # Log regime characteristics
            for state, chars in result['regime_characteristics'].items():
                prefix = f"regime_{state}"
                mlflow.log_metric(f"{prefix}_avg_return", chars['avg_return'])
                mlflow.log_metric(f"{prefix}_volatility", chars['volatility'])
                mlflow.log_metric(f"{prefix}_frequency", chars['frequency'])

            # Log artifacts
            # 1. Regime characteristics as JSON
            chars_json = json.dumps(result['regime_characteristics'], indent=2)
            mlflow.log_text(chars_json, "regime_characteristics.json")

            # 2. Transition matrix as JSON
            trans_json = json.dumps(result['transition_matrix'], indent=2)
            mlflow.log_text(trans_json, "transition_matrix.json")

            # 3. Human-readable summary
            summary = detector.get_regime_summary(result)
            mlflow.log_text(summary, "regime_summary.txt")

            # 4. Visualization
            try:
                fig = self._plot_hmm_results(returns, result)
                mlflow.log_figure(fig, "regime_analysis.png")
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Failed to create HMM plot: {e}")

            logger.info(f"HMM experiment tracked: {run.info.run_id}")
            return run.info.run_id

    def track_dtw_matching(
        self,
        matcher: DynamicTimeWarpingMatcher,
        matches: List[Dict],
        prediction: Dict,
        current_pattern: Union[pd.Series, np.ndarray],
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Track DTW pattern matching experiment.

        Args:
            matcher: DynamicTimeWarpingMatcher instance
            matches: Match results from matcher.find_similar_patterns()
            prediction: Prediction from matcher.predict_from_matches()
            current_pattern: Current pattern being matched
            run_name: Optional run name
            tags: Optional tags for the run

        Returns:
            Run ID
        """
        if run_name is None:
            run_name = f"dtw_matching_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with mlflow.start_run(run_name=run_name) as run:
            # Log parameters
            mlflow.log_param("model_type", "dtw_pattern_matcher")
            mlflow.log_param("similarity_threshold", matcher.similarity_threshold)
            mlflow.log_param("pattern_length", len(current_pattern))

            # Log tags
            if tags:
                mlflow.set_tags(tags)

            mlflow.set_tag("model_family", "cyclical")
            mlflow.set_tag("algorithm", "dynamic_time_warping")

            # Log metrics
            mlflow.log_metric("num_matches", len(matches))

            if matches:
                top_match = matches[0]
                mlflow.log_metric("top_match_similarity", top_match['similarity_score'])
                mlflow.log_metric("top_match_distance", top_match['dtw_distance'])

                # Average similarity
                avg_sim = np.mean([m['similarity_score'] for m in matches])
                mlflow.log_metric("avg_similarity", avg_sim)

            # Log prediction metrics
            mlflow.log_metric("predicted_return_30d", prediction['predicted_return'])
            mlflow.log_metric("prediction_confidence", prediction['confidence'])
            mlflow.log_metric("prediction_std", prediction['return_distribution']['std'])

            # Log artifacts
            # 1. Matches as JSON
            matches_json = json.dumps(matches, indent=2, default=str)
            mlflow.log_text(matches_json, "matches.json")

            # 2. Prediction details as JSON
            prediction_json = json.dumps(prediction, indent=2)
            mlflow.log_text(prediction_json, "prediction.json")

            # 3. Human-readable summary
            summary = matcher.get_pattern_summary(matches)
            mlflow.log_text(summary, "pattern_summary.txt")

            # 4. Visualization
            try:
                fig = self._plot_dtw_results(current_pattern, matches, prediction)
                mlflow.log_figure(fig, "pattern_matching.png")
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Failed to create DTW plot: {e}")

            logger.info(f"DTW experiment tracked: {run.info.run_id}")
            return run.info.run_id

    def _plot_fourier_results(self, data: np.ndarray, result: Dict) -> plt.Figure:
        """Create visualization of Fourier analysis results."""
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))

        # Original signal
        axes[0].plot(data)
        axes[0].set_title("Original Time Series")
        axes[0].set_xlabel("Time")
        axes[0].set_ylabel("Value")
        axes[0].grid(True, alpha=0.3)

        # Seasonal decomposition
        if result.get('seasonal_decomposition'):
            decomp = result['seasonal_decomposition']

            axes[1].plot(decomp['trend'], label='Trend', linewidth=2)
            axes[1].set_title("Trend Component")
            axes[1].set_xlabel("Time")
            axes[1].set_ylabel("Value")
            axes[1].grid(True, alpha=0.3)

            axes[2].plot(decomp['seasonal'], label='Seasonal', color='orange')
            axes[2].set_title("Seasonal Component")
            axes[2].set_xlabel("Time")
            axes[2].set_ylabel("Value")
            axes[2].grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def _plot_hmm_results(self, returns: np.ndarray, result: Dict) -> plt.Figure:
        """Create visualization of HMM regime detection results."""
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        # Returns with regime coloring
        regimes = result['all_regimes']
        axes[0].scatter(range(len(returns)), returns, c=regimes, cmap='viridis', alpha=0.6, s=10)
        axes[0].set_title("Returns Colored by Regime")
        axes[0].set_xlabel("Time")
        axes[0].set_ylabel("Returns")
        axes[0].grid(True, alpha=0.3)

        # Regime probabilities over time
        state_probs = np.array(result['state_probabilities'])
        for i in range(state_probs.shape[1]):
            axes[1].plot(state_probs[:, i], label=f"State {i}", alpha=0.7)

        axes[1].set_title("Regime Probabilities Over Time")
        axes[1].set_xlabel("Time")
        axes[1].set_ylabel("Probability")
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def _plot_dtw_results(
        self,
        current_pattern: np.ndarray,
        matches: List[Dict],
        prediction: Dict
    ) -> plt.Figure:
        """Create visualization of DTW pattern matching results."""
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        # Current pattern vs top matches
        axes[0].plot(current_pattern, label='Current Pattern', linewidth=2, color='black')

        for i, match in enumerate(matches[:3]):  # Top 3 matches
            pattern = np.array(match['pattern'])
            sim = match['similarity_score']
            axes[0].plot(pattern, label=f"Match {i+1} (sim={sim:.2f})", alpha=0.6)

        axes[0].set_title("Current Pattern vs Historical Matches")
        axes[0].set_xlabel("Time")
        axes[0].set_ylabel("Normalized Value")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Prediction distribution
        if matches:
            outcomes = [m['outcome_30d']['total_return'] for m in matches if m.get('outcome_30d')]
            if outcomes:
                axes[1].hist(outcomes, bins=20, alpha=0.7, color='blue', edgecolor='black')
                axes[1].axvline(prediction['predicted_return'], color='red',
                               linestyle='--', linewidth=2, label='Predicted')
                axes[1].set_title("Distribution of Historical Outcomes (30d)")
                axes[1].set_xlabel("Return")
                axes[1].set_ylabel("Frequency")
                axes[1].legend()
                axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        return fig


# Convenience function for tracking complete cyclical analysis
def track_complete_cyclical_analysis(
    data: pd.DataFrame,
    experiment_name: str = "cyclical_analysis",
    tags: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Run and track complete cyclical analysis with all three models.

    Args:
        data: DataFrame with 'returns' and optionally 'volumes'
        experiment_name: MLFlow experiment name
        tags: Optional tags for all runs

    Returns:
        Dict mapping model type to run ID
    """
    tracker = CyclicalExperimentTracker(experiment_name)

    run_ids = {}

    # Fourier analysis
    try:
        fourier = FourierCyclicalDetector()
        fourier_result = fourier.detect_cycles(data['returns'])
        run_id = tracker.track_fourier_detection(fourier, data['returns'], fourier_result, tags=tags)
        run_ids['fourier'] = run_id
    except Exception as e:
        logger.error(f"Fourier tracking failed: {e}")

    # HMM regime detection
    try:
        hmm = RegimeDetector(n_states=4)
        volumes = data.get('volumes')
        hmm_result = hmm.fit_and_predict(data['returns'], volumes)
        run_id = tracker.track_hmm_detection(hmm, hmm_result, data['returns'], tags=tags)
        run_ids['hmm'] = run_id
    except Exception as e:
        logger.error(f"HMM tracking failed: {e}")

    # DTW pattern matching
    try:
        dtw = DynamicTimeWarpingMatcher()
        matches = dtw.find_similar_patterns(data['returns'], data['returns'], window_size=30, top_k=10)
        prediction = dtw.predict_from_matches(matches)
        run_id = tracker.track_dtw_matching(dtw, matches, prediction, data['returns'][-30:], tags=tags)
        run_ids['dtw'] = run_id
    except Exception as e:
        logger.error(f"DTW tracking failed: {e}")

    return run_ids
