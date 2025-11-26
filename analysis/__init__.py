"""Machine Learning and Advanced Analytics Package."""

# Core analysis modules
from .correlation import CorrelationAnalyzer, CorrelationResult
from .insights import InsightGenerator
from .ensemble import EnsemblePredictor, EnsemblePrediction

# Base classes
from .base import (
    BaseDetector,
    BaseCyclicalDetector,
    BasePatternMatcher,
    BaseRegimeDetector,
    BaseEnsemble,
    AnalysisResult,
    AnalysisType
)

__all__ = [
    # Core classes
    'CorrelationAnalyzer',
    'CorrelationResult',
    'InsightGenerator',
    'EnsemblePredictor',
    'EnsemblePrediction',
    
    # Base classes
    'BaseDetector',
    'BaseCyclicalDetector', 
    'BasePatternMatcher',
    'BaseRegimeDetector',
    'BaseEnsemble',
    'AnalysisResult',
    'AnalysisType'
]
