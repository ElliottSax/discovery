"""MLFlow experiment tracking and logging utilities."""

import mlflow
from mlflow.tracking import MlflowClient
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from app.core.ml_config import ml_settings

logger = logging.getLogger(__name__)


class MLFlowTracker:
    """
    Wrapper for MLFlow tracking with convenience methods.

    Usage:
        tracker = MLFlowTracker()
        with tracker.start_run("my_experiment"):
            tracker.log_params({"learning_rate": 0.001})
            tracker.log_metrics({"accuracy": 0.95})
            tracker.log_model(model, "my_model")
    """

    def __init__(self, experiment_name: Optional[str] = None):
        """
        Initialize MLFlow tracker.

        Args:
            experiment_name: Name of experiment (default from settings)
        """
        self.experiment_name = experiment_name or ml_settings.MLFLOW_EXPERIMENT_NAME

        # Set tracking URI
        mlflow.set_tracking_uri(ml_settings.MLFLOW_TRACKING_URI)

        # Create or get experiment
        try:
            self.experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if self.experiment is None:
                self.experiment_id = mlflow.create_experiment(
                    self.experiment_name,
                    artifact_location=ml_settings.MLFLOW_ARTIFACT_LOCATION
                )
            else:
                self.experiment_id = self.experiment.experiment_id

            mlflow.set_experiment(self.experiment_name)
            logger.info(f"MLFlow experiment set: {self.experiment_name}")

        except Exception as e:
            logger.error(f"Failed to initialize MLFlow: {e}")
            self.experiment_id = None

        self.client = MlflowClient()
        self.active_run = None

    def start_run(self, run_name: Optional[str] = None) -> mlflow.ActiveRun:
        """
        Start a new MLFlow run.

        Args:
            run_name: Name for the run

        Returns:
            Active MLFlow run context manager
        """
        tags = {
            "timestamp": datetime.now().isoformat(),
            "environment": "development",  # Could be from settings
        }

        self.active_run = mlflow.start_run(run_name=run_name, tags=tags)
        return self.active_run

    def end_run(self):
        """End the current MLFlow run."""
        if self.active_run:
            mlflow.end_run()
            self.active_run = None

    def log_params(self, params: Dict[str, Any]):
        """
        Log parameters to MLFlow.

        Args:
            params: Dictionary of parameters
        """
        try:
            mlflow.log_params(params)
            logger.debug(f"Logged {len(params)} parameters to MLFlow")
        except Exception as e:
            logger.error(f"Failed to log parameters: {e}")

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """
        Log metrics to MLFlow.

        Args:
            metrics: Dictionary of metrics
            step: Optional step number for time series metrics
        """
        try:
            mlflow.log_metrics(metrics, step=step)
            logger.debug(f"Logged {len(metrics)} metrics to MLFlow")
        except Exception as e:
            logger.error(f"Failed to log metrics: {e}")

    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """
        Log an artifact (file) to MLFlow.

        Args:
            local_path: Path to local file
            artifact_path: Path within artifact store
        """
        try:
            mlflow.log_artifact(local_path, artifact_path)
            logger.debug(f"Logged artifact: {local_path}")
        except Exception as e:
            logger.error(f"Failed to log artifact: {e}")

    def log_model(
        self,
        model: Any,
        artifact_path: str,
        registered_model_name: Optional[str] = None,
        **kwargs
    ):
        """
        Log a model to MLFlow.

        Args:
            model: Model object to log
            artifact_path: Path to store model in artifacts
            registered_model_name: Name for model registry
            **kwargs: Additional arguments for mlflow.log_model
        """
        try:
            # Auto-detect model type and use appropriate logging
            if hasattr(model, 'predict'):  # sklearn-like
                mlflow.sklearn.log_model(
                    model,
                    artifact_path,
                    registered_model_name=registered_model_name,
                    **kwargs
                )
            else:
                # Generic python model
                mlflow.pyfunc.log_model(
                    artifact_path,
                    python_model=model,
                    registered_model_name=registered_model_name,
                    **kwargs
                )

            logger.info(f"Logged model: {artifact_path}")

        except Exception as e:
            logger.error(f"Failed to log model: {e}")

    def log_figure(self, figure, artifact_path: str):
        """
        Log a matplotlib/plotly figure.

        Args:
            figure: Figure object
            artifact_path: Path to store figure
        """
        try:
            mlflow.log_figure(figure, artifact_path)
            logger.debug(f"Logged figure: {artifact_path}")
        except Exception as e:
            logger.error(f"Failed to log figure: {e}")

    def set_tags(self, tags: Dict[str, str]):
        """
        Set tags for the current run.

        Args:
            tags: Dictionary of tags
        """
        try:
            mlflow.set_tags(tags)
            logger.debug(f"Set {len(tags)} tags")
        except Exception as e:
            logger.error(f"Failed to set tags: {e}")

    def get_best_run(
        self,
        metric_name: str,
        ascending: bool = False
    ) -> Optional[mlflow.entities.Run]:
        """
        Get the best run based on a metric.

        Args:
            metric_name: Name of metric to optimize
            ascending: True for minimizing, False for maximizing

        Returns:
            Best run or None
        """
        try:
            runs = self.client.search_runs(
                experiment_ids=[self.experiment_id],
                order_by=[f"metrics.{metric_name} {'ASC' if ascending else 'DESC'}"],
                max_results=1
            )

            if runs:
                return runs[0]

        except Exception as e:
            logger.error(f"Failed to get best run: {e}")

        return None

    def load_model(self, model_uri: str) -> Any:
        """
        Load a model from MLFlow.

        Args:
            model_uri: URI to model (e.g., "models:/my_model/1")

        Returns:
            Loaded model
        """
        try:
            model = mlflow.pyfunc.load_model(model_uri)
            logger.info(f"Loaded model from: {model_uri}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None

    def register_model(
        self,
        model_uri: str,
        name: str,
        description: Optional[str] = None
    ) -> Optional[str]:
        """
        Register a model to MLFlow Model Registry.

        Args:
            model_uri: URI of model run
            name: Name for registered model
            description: Optional description

        Returns:
            Version of registered model or None
        """
        try:
            result = mlflow.register_model(model_uri, name)

            if description:
                self.client.update_model_version(
                    name=name,
                    version=result.version,
                    description=description
                )

            logger.info(f"Registered model '{name}' version {result.version}")
            return result.version

        except Exception as e:
            logger.error(f"Failed to register model: {e}")
            return None

    def transition_model_stage(
        self,
        name: str,
        version: str,
        stage: str
    ):
        """
        Transition a model to a different stage.

        Args:
            name: Model name
            version: Model version
            stage: Target stage ('Staging', 'Production', 'Archived')
        """
        try:
            self.client.transition_model_version_stage(
                name=name,
                version=version,
                stage=stage
            )
            logger.info(f"Transitioned {name} v{version} to {stage}")
        except Exception as e:
            logger.error(f"Failed to transition model stage: {e}")

    def log_experiment_summary(self, summary: Dict[str, Any]):
        """
        Log a comprehensive experiment summary.

        Args:
            summary: Dictionary containing experiment results
        """
        # Log as both metrics and params
        for key, value in summary.items():
            try:
                if isinstance(value, (int, float)):
                    self.log_metrics({key: value})
                else:
                    self.log_params({key: str(value)})
            except Exception as e:
                logger.warning(f"Failed to log {key}: {e}")
