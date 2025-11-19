"""ML-specific configuration and settings."""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class MLSettings(BaseSettings):
    """Machine Learning configuration settings."""

    # MLFlow Configuration
    MLFLOW_TRACKING_URI: str = Field(
        default="http://localhost:5000",
        description="MLFlow tracking server URI"
    )
    MLFLOW_EXPERIMENT_NAME: str = Field(
        default="politician-trade-prediction",
        description="Default MLFlow experiment name"
    )
    MLFLOW_ARTIFACT_LOCATION: Optional[str] = Field(
        default=None,
        description="MLFlow artifact storage location"
    )

    # Model Configuration
    MODEL_CACHE_DIR: str = Field(
        default="./models",
        description="Directory to cache trained models"
    )
    MODEL_VERSION: str = Field(
        default="latest",
        description="Model version to use for inference"
    )
    MODEL_RELOAD_INTERVAL: int = Field(
        default=3600,
        description="Seconds between model reload checks"
    )

    # Training Configuration
    TRAIN_TEST_SPLIT: float = Field(
        default=0.8,
        description="Train/test split ratio"
    )
    VALIDATION_SPLIT: float = Field(
        default=0.1,
        description="Validation split from training data"
    )
    RANDOM_SEED: int = Field(
        default=42,
        description="Random seed for reproducibility"
    )

    # Feature Engineering
    N_FEATURES: int = Field(
        default=200,
        description="Target number of features to generate"
    )
    FEATURE_SELECTION_METHOD: str = Field(
        default="importance",
        choices=["importance", "correlation", "mutual_info", "all"],
        description="Method for feature selection"
    )

    # Model Ensemble Configuration
    ENSEMBLE_MODELS: list[str] = Field(
        default=[
            "cyclical",
            "regime",
            "factor",
            "lstm",
            "anomaly"
        ],
        description="Models to include in ensemble"
    )
    ENSEMBLE_WEIGHTS: Optional[dict[str, float]] = Field(
        default=None,
        description="Weights for ensemble models (auto if None)"
    )

    # Cyclical Pattern Detection
    FOURIER_MIN_PERIOD: int = Field(
        default=5,
        description="Minimum period (days) to detect in Fourier analysis"
    )
    FOURIER_MAX_PERIOD: int = Field(
        default=365,
        description="Maximum period (days) to detect in Fourier analysis"
    )

    # HMM Configuration
    HMM_N_STATES: int = Field(
        default=4,
        description="Number of hidden states for HMM"
    )
    HMM_N_ITERATIONS: int = Field(
        default=1000,
        description="Max iterations for HMM training"
    )

    # LSTM Configuration
    LSTM_SEQUENCE_LENGTH: int = Field(
        default=60,
        description="Input sequence length for LSTM (days)"
    )
    LSTM_HIDDEN_DIM: int = Field(
        default=128,
        description="Hidden dimension size for LSTM"
    )
    LSTM_NUM_LAYERS: int = Field(
        default=3,
        description="Number of LSTM layers"
    )
    LSTM_DROPOUT: float = Field(
        default=0.3,
        description="Dropout rate for LSTM"
    )
    LSTM_LEARNING_RATE: float = Field(
        default=0.001,
        description="Learning rate for LSTM training"
    )
    LSTM_BATCH_SIZE: int = Field(
        default=32,
        description="Batch size for LSTM training"
    )
    LSTM_EPOCHS: int = Field(
        default=100,
        description="Number of epochs for LSTM training"
    )

    # DTW Configuration
    DTW_WINDOW_SIZE: int = Field(
        default=30,
        description="Window size for DTW pattern matching"
    )
    DTW_TOP_K: int = Field(
        default=10,
        description="Number of top similar patterns to return"
    )
    DTW_MIN_SIMILARITY: float = Field(
        default=0.7,
        description="Minimum similarity threshold (0-1)"
    )

    # Hyperparameter Tuning
    OPTUNA_N_TRIALS: int = Field(
        default=100,
        description="Number of Optuna optimization trials"
    )
    OPTUNA_TIMEOUT: int = Field(
        default=3600,
        description="Timeout for Optuna optimization (seconds)"
    )

    # Caching
    PREDICTION_CACHE_TTL: int = Field(
        default=300,
        description="Prediction cache TTL in seconds (5 minutes)"
    )
    FEATURE_CACHE_TTL: int = Field(
        default=3600,
        description="Feature cache TTL in seconds (1 hour)"
    )

    # Performance
    N_JOBS: int = Field(
        default=-1,
        description="Number of parallel jobs (-1 = all CPUs)"
    )
    USE_GPU: bool = Field(
        default=False,
        description="Use GPU for deep learning if available"
    )

    # Monitoring
    LOG_PREDICTIONS: bool = Field(
        default=True,
        description="Log all predictions to MLFlow"
    )
    TRACK_FEATURE_DRIFT: bool = Field(
        default=True,
        description="Monitor feature drift over time"
    )

    # Retraining
    AUTO_RETRAIN_ENABLED: bool = Field(
        default=True,
        description="Enable automatic model retraining"
    )
    RETRAIN_INTERVAL_DAYS: int = Field(
        default=7,
        description="Days between automatic retraining"
    )
    MIN_NEW_DATA_FOR_RETRAIN: int = Field(
        default=100,
        description="Minimum new samples required for retraining"
    )

    class Config:
        env_prefix = "ML_"
        case_sensitive = True


# Global ML settings instance
ml_settings = MLSettings()
