"""
Base classes for analysis components.

Provides abstract base classes to ensure consistent interfaces
across all analysis modules.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum


class AnalysisType(Enum):
    """Types of analysis available."""
    CYCLICAL = "cyclical"
    PATTERN = "pattern"
    REGIME = "regime"
    CORRELATION = "correlation"
    FORECAST = "forecast"
    ANOMALY = "anomaly"


@dataclass
class AnalysisResult:
    """Standard result format for all analyzers."""
    analysis_type: AnalysisType
    confidence: float  # 0-1
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: pd.Timestamp
    
    def is_significant(self, threshold: float = 0.5) -> bool:
        """Check if result meets significance threshold."""
        return self.confidence >= threshold


class BaseDetector(ABC):
    """
    Abstract base class for all pattern/cycle detectors.
    
    All detectors must implement these core methods to ensure
    consistent interfaces across the system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize detector with optional configuration.
        
        Args:
            config: Configuration parameters specific to detector
        """
        self.config = config or {}
        self._validate_config()
    
    @abstractmethod
    def detect(self, data: pd.Series) -> AnalysisResult:
        """
        Detect patterns/cycles in the provided data.
        
        Args:
            data: Time series data to analyze
            
        Returns:
            AnalysisResult containing detected patterns
        """
        pass
    
    @abstractmethod
    def validate_input(self, data: pd.Series) -> bool:
        """
        Validate that input data meets requirements.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    def _validate_config(self):
        """Validate configuration parameters."""
        # Override in subclasses for specific validation
        pass
    
    def preprocess(self, data: pd.Series) -> pd.Series:
        """
        Preprocess data before detection.
        
        Args:
            data: Raw time series data
            
        Returns:
            Preprocessed data ready for analysis
        """
        # Default: ensure datetime index and handle missing values
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        
        # Fill missing values with interpolation
        data = data.interpolate(method='time')
        
        return data


class BaseCyclicalDetector(BaseDetector):
    """Base class for cyclical pattern detectors (Fourier, Wavelets, etc)."""
    
    @abstractmethod
    def get_dominant_cycles(self, data: pd.Series) -> List[Dict[str, float]]:
        """
        Extract dominant cycles from the data.
        
        Args:
            data: Time series data
            
        Returns:
            List of cycles with period and strength
        """
        pass
    
    @abstractmethod
    def forecast(self, data: pd.Series, periods: int) -> np.ndarray:
        """
        Forecast future values based on detected cycles.
        
        Args:
            data: Historical data
            periods: Number of periods to forecast
            
        Returns:
            Array of forecasted values
        """
        pass


class BasePatternMatcher(BaseDetector):
    """Base class for pattern matching algorithms (DTW, etc)."""
    
    @abstractmethod
    def find_similar_patterns(
        self, 
        query: pd.Series, 
        reference_data: pd.DataFrame
    ) -> List[Tuple[float, pd.Series]]:
        """
        Find patterns similar to query in reference data.
        
        Args:
            query: Pattern to search for
            reference_data: Historical data to search in
            
        Returns:
            List of (similarity_score, matching_pattern) tuples
        """
        pass
    
    @abstractmethod
    def compute_distance(self, pattern1: pd.Series, pattern2: pd.Series) -> float:
        """
        Compute distance between two patterns.
        
        Args:
            pattern1: First pattern
            pattern2: Second pattern
            
        Returns:
            Distance/dissimilarity score
        """
        pass


class BaseRegimeDetector(BaseDetector):
    """Base class for regime/state detection algorithms (HMM, etc)."""
    
    @abstractmethod
    def identify_regimes(self, data: pd.Series) -> np.ndarray:
        """
        Identify regime/state for each time point.
        
        Args:
            data: Time series data
            
        Returns:
            Array of regime labels
        """
        pass
    
    @abstractmethod
    def get_regime_characteristics(self, data: pd.Series, regimes: np.ndarray) -> Dict[int, Dict[str, float]]:
        """
        Get statistical characteristics of each regime.
        
        Args:
            data: Time series data
            regimes: Regime labels for each time point
            
        Returns:
            Dictionary mapping regime ID to characteristics
        """
        pass
    
    @abstractmethod
    def predict_regime_transition(self, current_regime: int) -> Dict[int, float]:
        """
        Predict probability of transitioning to other regimes.
        
        Args:
            current_regime: Current regime ID
            
        Returns:
            Dictionary mapping target regime to transition probability
        """
        pass


class BaseEnsemble(ABC):
    """Base class for ensemble methods combining multiple detectors."""
    
    def __init__(self, detectors: List[BaseDetector]):
        """
        Initialize ensemble with list of detectors.
        
        Args:
            detectors: List of detector instances
        """
        self.detectors = detectors
    
    @abstractmethod
    def combine_predictions(
        self, 
        predictions: List[AnalysisResult]
    ) -> AnalysisResult:
        """
        Combine predictions from multiple detectors.
        
        Args:
            predictions: List of predictions from individual detectors
            
        Returns:
            Combined prediction
        """
        pass
    
    @abstractmethod
    def calculate_weights(self, predictions: List[AnalysisResult]) -> List[float]:
        """
        Calculate weights for combining predictions.
        
        Args:
            predictions: List of predictions
            
        Returns:
            List of weights (must sum to 1)
        """
        pass
    
    def detect_all(self, data: pd.Series) -> List[AnalysisResult]:
        """
        Run all detectors on the data.
        
        Args:
            data: Time series data
            
        Returns:
            List of results from all detectors
        """
        results = []
        for detector in self.detectors:
            if detector.validate_input(data):
                try:
                    result = detector.detect(data)
                    results.append(result)
                except Exception as e:
                    # Log error but continue with other detectors
                    import logging
                    logging.error(f"Detector {detector.__class__.__name__} failed: {e}")
        
        return results


class BaseValidator(ABC):
    """Base class for data validation."""
    
    @abstractmethod
    def validate(self, data: pd.Series) -> Tuple[bool, List[str]]:
        """
        Validate data quality.
        
        Args:
            data: Data to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        pass
    
    @abstractmethod
    def clean(self, data: pd.Series) -> pd.Series:
        """
        Clean and prepare data.
        
        Args:
            data: Raw data
            
        Returns:
            Cleaned data
        """
        pass


# Concrete implementations should inherit from these base classes
# Example:
# class FourierCyclicalDetector(BaseCyclicalDetector):
#     def detect(self, data: pd.Series) -> AnalysisResult:
#         # Implementation
#         pass