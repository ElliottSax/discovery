"""
Cyclical Pattern Detection Module

This module provides advanced pattern detection for quantitative trading analytics:
- Fourier Analysis: Detect periodic patterns in trading behavior
- Hidden Markov Models: Identify market regimes and state transitions
- Dynamic Time Warping: Match current patterns to historical patterns
- MLFlow Experiment Tracking: Comprehensive experiment tracking and visualization

Author: Claude
"""

from .fourier import FourierCyclicalDetector
from .hmm import RegimeDetector
from .dtw import DynamicTimeWarpingMatcher
from .experiment_tracker import CyclicalExperimentTracker, track_complete_cyclical_analysis

__all__ = [
    'FourierCyclicalDetector',
    'RegimeDetector',
    'DynamicTimeWarpingMatcher',
    'CyclicalExperimentTracker',
    'track_complete_cyclical_analysis',
]
