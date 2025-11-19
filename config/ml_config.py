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

    # Cyclical Pattern Detection - Fourier
    FOURIER_MIN_DATA_POINTS: int = Field(
        default=30,
        description="Minimum data points required for Fourier analysis"
    )
    FOURIER_MIN_PERIOD: int = Field(
        default=5,
        description="Minimum period (days) to detect in Fourier analysis"
    )
    FOURIER_MAX_PERIOD: int = Field(
        default=365,
        description="Maximum period (days) to detect in Fourier analysis"
    )
    FOURIER_MIN_STRENGTH: float = Field(
        default=0.1,
        description="Minimum FFT power to consider a cycle significant"
    )
    FOURIER_MIN_CONFIDENCE: float = Field(
        default=0.6,
        description="Minimum confidence threshold for cycle detection (0-1)"
    )
    FOURIER_FORECAST_PERIODS: int = Field(
        default=30,
        description="Number of periods to forecast ahead"
    )
    FOURIER_TOP_CYCLES: int = Field(
        default=10,
        description="Number of top cycles to return"
    )
    FOURIER_PEAK_PROMINENCE: float = Field(
        default=0.05,
        description="Peak prominence for cycle detection (relative to min_strength)"
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
    HMM_MIN_DATA_POINTS: int = Field(
        default=100,
        description="Minimum data points for reliable HMM training"
    )
    HMM_COVARIANCE_TYPE: str = Field(
        default="full",
        description="Type of covariance parameters (spherical, diag, full, tied)"
    )
    HMM_VOLATILITY_WINDOW: int = Field(
        default=20,
        description="Window size for rolling volatility calculation"
    )
    HMM_MOMENTUM_WINDOW: int = Field(
        default=20,
        description="Window size for rolling momentum calculation"
    )
    HMM_HIGH_VOL_THRESHOLD: float = Field(
        default=0.025,
        description="Threshold for high volatility regime classification"
    )
    HMM_LOW_VOL_THRESHOLD: float = Field(
        default=0.01,
        description="Threshold for low volatility regime classification"
    )
    HMM_POSITIVE_RETURN_THRESHOLD: float = Field(
        default=0.001,
        description="Threshold for positive return classification"
    )
    HMM_NEGATIVE_RETURN_THRESHOLD: float = Field(
        default=-0.001,
        description="Threshold for negative return classification"
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
    DTW_MIN_DATA_POINTS: int = Field(
        default=120,
        description="Minimum data points for DTW (window_size + outcome horizon)"
    )
    DTW_OUTCOME_HORIZON_30D: int = Field(
        default=30,
        description="Short-term outcome horizon in days"
    )
    DTW_OUTCOME_HORIZON_90D: int = Field(
        default=90,
        description="Long-term outcome horizon in days"
    )
    DTW_MAX_LAG: int = Field(
        default=30,
        description="Maximum lag for correlation analysis"
    )
    DTW_DISTANCE_SCALE: float = Field(
        default=2.0,
        description="Scale factor for distance-to-similarity conversion"
    )

    # Ensemble Configuration
    ENSEMBLE_FOURIER_WEIGHT: float = Field(
        default=0.35,
        description="Base weight for Fourier predictions"
    )
    ENSEMBLE_HMM_WEIGHT: float = Field(
        default=0.35,
        description="Base weight for HMM predictions"
    )
    ENSEMBLE_DTW_WEIGHT: float = Field(
        default=0.30,
        description="Base weight for DTW predictions"
    )
    ENSEMBLE_MIN_CONFIDENCE: float = Field(
        default=0.5,
        description="Minimum confidence threshold for predictions"
    )
    ENSEMBLE_MIN_MODELS: int = Field(
        default=1,
        description="Minimum number of models required for ensemble"
    )
    ENSEMBLE_REGIME_CHANGE_THRESHOLD: int = Field(
        default=7,
        description="Days threshold for regime change prediction"
    )
    ENSEMBLE_CYCLE_PEAK_THRESHOLD: float = Field(
        default=1.5,
        description="Multiplier threshold for cycle peak detection"
    )
    ENSEMBLE_LARGE_CHANGE_THRESHOLD: float = Field(
        default=10.0,
        description="Threshold for large change alerts"
    )
    ENSEMBLE_ANOMALY_AGREEMENT_THRESHOLD: float = Field(
        default=0.5,
        description="Low agreement threshold for anomaly detection"
    )

    # Correlation Analysis
    CORRELATION_SIGNIFICANCE_THRESHOLD: float = Field(
        default=0.05,
        description="P-value threshold for statistical significance"
    )
    CORRELATION_MIN_CORRELATION: float = Field(
        default=0.5,
        description="Minimum correlation for clustering/network edges"
    )
    CORRELATION_MIN_OVERLAP: int = Field(
        default=30,
        description="Minimum overlapping data points for correlation"
    )
    CORRELATION_CLUSTERING_METHOD: str = Field(
        default="ward",
        description="Hierarchical clustering linkage method"
    )

    # Numerical Stability
    EPSILON: float = Field(
        default=1e-8,
        description="Small constant for numerical stability"
    )
    MIN_VARIANCE_THRESHOLD: float = Field(
        default=1e-10,
        description="Minimum variance threshold for valid time series"
    )

    # Statistical Testing
    BOOTSTRAP_N_SAMPLES: int = Field(
        default=1000,
        description="Number of bootstrap samples for significance testing"
    )
    CONFIDENCE_INTERVAL: float = Field(
        default=0.95,
        description="Confidence interval level (0-1)"
    )
    CROSS_VALIDATION_SPLITS: int = Field(
        default=5,
        description="Number of cross-validation splits"
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
