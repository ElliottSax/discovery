# Stock Analysis Research Framework

A comprehensive Python framework for analyzing stock trading patterns, detecting cycles, identifying recurring models, and generating actionable insights from time-series data.

## Overview

This repository contains sophisticated analysis algorithms extracted from the `elliottsax/quant` research project, focused purely on pattern detection and quantitative analysis. The framework combines multiple complementary techniques to provide robust pattern recognition and prediction capabilities.

## Core Analysis Capabilities

### 1. **Cyclical Pattern Detection** (`analysis/cyclical/`)

#### Fourier Cyclical Analysis (`fourier.py`)
- **Algorithm**: Fast Fourier Transform (FFT) for frequency domain analysis
- **Detects**:
  - Weekly cycles (5-7 days)
  - Monthly cycles (21-30 days)
  - Quarterly cycles (60-90 days)
  - Annual cycles (250-260 trading days)
  - Election cycles (2-4 years)
- **Outputs**: Dominant cycles with period, strength, confidence scores, and forecasts

#### Hidden Markov Model Regime Detection (`hmm.py`)
- **Algorithm**: Gaussian HMM using Baum-Welch (EM) algorithm
- **Identifies Trading Regimes**:
  - Bull Market (high returns, low volatility)
  - Bear Market (negative returns, high volatility)
  - Sideways/Choppy (low returns, high volatility)
  - Low Volatility (stable, predictable)
- **Outputs**: Current regime, transition probabilities, expected duration, regime characteristics

#### Dynamic Time Warping Pattern Matching (`dtw.py`)
- **Algorithm**: DTW distance metric for time series similarity
- **Use Cases**:
  - Find historical patterns similar to current market conditions
  - Predict outcomes based on historical precedents
  - Detect anomalies (patterns with no historical match)
- **Outputs**: Top-K similar patterns with similarity scores, DTW distances, and outcome predictions

#### Experiment Tracking (`experiment_tracker.py`)
- **Purpose**: MLFlow integration for comprehensive experiment tracking
- **Tracks**: Model parameters, detected patterns, predictions, performance metrics, artifacts

### 2. **Multi-Model Ensemble** (`analysis/ensemble.py`)

Combines predictions from Fourier, HMM, and DTW models using weighted voting:
- **Default Weights**: Fourier (35%), HMM (35%), DTW (30%)
- **Prediction Types**: Trade increase/decrease, regime changes, cycle peaks, anomalies
- **Meta-Learning**: Dynamically adjusts weights based on historical accuracy
- **Outputs**: Combined predictions with confidence, model agreement, and anomaly scores

### 3. **Correlation Analysis** (`analysis/correlation.py`)

Detects synchronized patterns across multiple entities:
- **Cycle Correlation**: Pearson correlation with lag optimization (-30 to +30 days)
- **Network Analysis**: Build relationship graphs with centrality and clustering metrics
- **Coordinated Detection**: Identify groups with similar behavior patterns
- **Regime Synchronization**: Measure how often entities are in the same regime
- **Sector Analysis**: Detect sector preferences and rotation patterns

### 4. **Feature Engineering** (`analysis/features/engineering.py`)

Extracts 200+ features across 8 categories:
- **Temporal Features** (40+): Calendar features, cyclical encodings, election cycles
- **Return-Based Features** (30+): Forward returns, volatility, Sharpe ratios, momentum
- **Technical Indicators** (50+): Moving averages, RSI, MACD, Bollinger Bands, ATR
- **Volume/Liquidity** (20+): Volume trends, ratios, dollar volume
- **Factor Exposures** (25+): Market beta, size, value, momentum, volatility factors
- **Network Features** (15+): Centrality measures, community membership
- **Macro Features** (10+): Interest rates, VIX, economic indicators

### 5. **Insight Generation** (`analysis/insights.py`)

Generates human-readable insights from analysis results:
- **Insight Types**: Patterns, anomalies, predictions, correlations, regime changes, sector analysis, risk signals
- **Severity Levels**: Critical, high, medium, low, info
- **Sources**: Fourier, HMM, DTW, ensemble, correlation, sector analysis
- **Output**: Prioritized insights with confidence scores and recommendations

### 6. **Utilities** (`analysis/utils/`)

#### Metrics (`metrics.py`)
- **Regression**: MSE, RMSE, MAE, R², MAPE
- **Classification**: Accuracy, Precision, Recall, F1, AUC
- **Trading-Specific**: Sharpe ratio, max drawdown, win rate, information coefficient, Sortino ratio

#### MLFlow Tracker (`mlflow_tracker.py`)
- Experiment creation and management
- Parameter, metrics, and artifact logging
- Model versioning and comparison

#### Model Registry (`model_registry.py`)
- Local model caching and versioning
- Fast model loading with metadata tracking

## Directory Structure

```
discovery/
├── analysis/                      # Core analysis modules
│   ├── cyclical/                  # Pattern detection models
│   │   ├── __init__.py
│   │   ├── fourier.py            # FFT-based cycle detection
│   │   ├── hmm.py                # Hidden Markov Model regime detection
│   │   ├── dtw.py                # Dynamic Time Warping pattern matching
│   │   └── experiment_tracker.py # MLFlow experiment tracking
│   ├── features/                  # Feature extraction
│   │   └── engineering.py        # 200+ feature engineering
│   ├── utils/                     # Analysis utilities
│   │   ├── __init__.py
│   │   ├── metrics.py            # Performance evaluation metrics
│   │   ├── mlflow_tracker.py     # MLFlow integration
│   │   └── model_registry.py     # Model caching and management
│   ├── __init__.py               # Core exports
│   ├── ensemble.py               # Multi-model ensemble predictor
│   ├── correlation.py            # Correlation and network analysis
│   └── insights.py               # Automated insight generation
├── scripts/                       # Analysis scripts
│   ├── analyze_politician_patterns.py  # Main cyclical analysis script
│   └── run_quick_analysis.py          # Lightweight analysis script
├── config/                        # Configuration
│   └── ml_config.py              # ML configuration settings
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Installation

### Prerequisites
- Python 3.9 or higher
- PostgreSQL (for scripts that use database)
- MLFlow server (optional, for experiment tracking)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/ElliottSax/discovery.git
cd discovery
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. (Optional) Set up MLFlow:
```bash
mlflow server --host 0.0.0.0 --port 5000
```

## Usage

### Basic Pattern Detection

```python
import pandas as pd
from analysis.cyclical.fourier import FourierCyclicalDetector
from analysis.cyclical.hmm import RegimeDetector
from analysis.cyclical.dtw import DynamicTimeWarpingMatcher

# Load your time series data
time_series = pd.Series([...])  # Your data here

# Detect cycles
fourier = FourierCyclicalDetector()
cycles = fourier.detect_cycles(time_series)
print(f"Detected cycles: {cycles['dominant_cycles']}")

# Detect regimes
returns = time_series.pct_change().dropna()
hmm_detector = RegimeDetector(n_states=4)
regimes = hmm_detector.fit_and_predict(returns)
print(f"Current regime: {regimes['current_regime']}")

# Find similar patterns
dtw_matcher = DynamicTimeWarpingMatcher()
current_pattern = time_series[-30:].values  # Last 30 days
historical_data = time_series[:-30].values
matches = dtw_matcher.find_similar_patterns(current_pattern, historical_data)
print(f"Top match similarity: {matches[0]['similarity_score']}")
```

### Ensemble Prediction

```python
from analysis.ensemble import EnsemblePredictor

# Combine results from all models
ensemble = EnsemblePredictor()
prediction = ensemble.predict(
    fourier_result=cycles,
    hmm_result=regimes,
    dtw_result=matches,
    current_trade_frequency=10.5
)

print(f"Prediction: {prediction.prediction_type}")
print(f"Confidence: {prediction.confidence}")
print(f"Model agreement: {prediction.model_agreement}")
```

### Correlation Analysis

```python
from analysis.correlation import CorrelationAnalyzer
import pandas as pd

# Analyze correlations across multiple entities
politician_data = {
    'politician_1': pd.Series([...]),
    'politician_2': pd.Series([...]),
    'politician_3': pd.Series([...])
}

analyzer = CorrelationAnalyzer()
correlations = analyzer.analyze_cycle_correlation(politician_data)
clusters = analyzer.detect_clusters(correlations)
network = analyzer.build_network_graph(correlations)
```

### Feature Engineering

```python
from analysis.features.engineering import AdvancedFeatureEngineering

# Extract features from trade data
trades_df = pd.DataFrame([...])  # Your trade data
feature_engineer = AdvancedFeatureEngineering()
features = feature_engineer.extract_all_features(trades_df)
print(f"Extracted {len(features.columns)} features")
```

### Generate Insights

```python
from analysis.insights import InsightGenerator

# Generate insights from all analysis results
insight_gen = InsightGenerator()
insights = insight_gen.generate_comprehensive_insights(
    fourier_result=cycles,
    hmm_result=regimes,
    dtw_result=matches,
    ensemble_prediction=prediction,
    correlation_results=correlations
)

# Print high-priority insights
for insight in insights:
    if insight.severity in ['CRITICAL', 'HIGH']:
        print(f"{insight.severity}: {insight.message}")
```

### Using Analysis Scripts

#### Full Cyclical Analysis
```bash
python scripts/analyze_politician_patterns.py
```
This script:
- Loads trading data from PostgreSQL
- Runs Fourier, HMM, and DTW analysis
- Generates ensemble predictions
- Logs all results to MLFlow

#### Quick Analysis
```bash
python scripts/run_quick_analysis.py
```
Lightweight version without full backend dependencies.

## Configuration

Edit `config/ml_config.py` to customize:

```python
# MLFlow settings
MLFLOW_TRACKING_URI = "http://localhost:5000"
MLFLOW_EXPERIMENT_NAME = "stock_analysis"

# Cyclical analysis settings
FOURIER_MIN_PERIOD = 5      # Minimum cycle period (days)
FOURIER_MAX_PERIOD = 365    # Maximum cycle period (days)
HMM_N_STATES = 4            # Number of trading regimes
DTW_WINDOW_SIZE = 30        # Pattern matching window (days)
DTW_MIN_SIMILARITY = 0.7    # Minimum similarity threshold

# Feature engineering
N_FEATURES = 200            # Target feature count
```

## Key Algorithms & Methods

### Fourier Analysis
- **Method**: Fast Fourier Transform (FFT)
- **Purpose**: Decompose time series into frequency components
- **Output**: Dominant cycles with periods, strengths, and confidence scores
- **Best For**: Detecting periodic patterns and seasonality

### Hidden Markov Models
- **Method**: Baum-Welch (EM) algorithm for parameter estimation
- **Purpose**: Identify latent states (regimes) in time series
- **Output**: Current regime, transition matrix, expected duration
- **Best For**: Regime detection and state transitions

### Dynamic Time Warping
- **Method**: Elastic distance metric for time series comparison
- **Purpose**: Find similar historical patterns with temporal flexibility
- **Output**: Similar patterns with similarity scores and outcome predictions
- **Best For**: Pattern matching and outcome prediction

### Ensemble Learning
- **Method**: Weighted voting with meta-learning
- **Purpose**: Combine multiple models for robust predictions
- **Output**: Combined prediction with confidence and agreement metrics
- **Best For**: Reducing model uncertainty and improving accuracy

## Performance Metrics

The framework provides comprehensive evaluation metrics:

- **Regression**: MSE, RMSE, MAE, R², MAPE
- **Classification**: Accuracy, Precision, Recall, F1, AUC-ROC
- **Trading**: Sharpe ratio, Sortino ratio, max drawdown, win rate, profit factor, information coefficient

## Experiment Tracking

All analysis runs can be tracked using MLFlow:

```python
from analysis.cyclical.experiment_tracker import track_complete_cyclical_analysis

# Automatically log all results
run_id = track_complete_cyclical_analysis(
    fourier_detector=fourier,
    hmm_detector=hmm_detector,
    dtw_matcher=dtw_matcher,
    data=time_series,
    fourier_result=cycles,
    hmm_result=regimes,
    dtw_result=matches,
    tags={'analyst': 'user', 'asset': 'AAPL'}
)
```

View results in MLFlow UI:
```bash
mlflow ui --host 0.0.0.0 --port 5000
```

## Dependencies

Core dependencies (see `requirements.txt` for full list):
- **numpy, pandas, scipy**: Data manipulation and scientific computing
- **scikit-learn**: Machine learning utilities
- **hmmlearn**: Hidden Markov Models
- **dtaidistance**: Dynamic Time Warping
- **mlflow**: Experiment tracking
- **networkx**: Network analysis
- **matplotlib, seaborn**: Visualization
- **psycopg2, sqlalchemy**: Database connectivity

## Research Applications

This framework is designed for:
- **Pattern Discovery**: Identify recurring patterns in trading behavior
- **Cycle Analysis**: Detect and characterize cyclical patterns
- **Regime Identification**: Classify market states and transitions
- **Anomaly Detection**: Find unusual patterns requiring investigation
- **Correlation Studies**: Analyze relationships across multiple entities
- **Predictive Modeling**: Forecast future behavior based on historical patterns
- **Risk Assessment**: Identify risk factors and volatility patterns

## Limitations & Considerations

- **Data Requirements**: Most algorithms require 100+ data points for reliable results
- **Computational Complexity**: DTW can be slow on large datasets (use windowing)
- **Stationarity**: Some methods assume stationary data (consider detrending)
- **Overfitting**: Be cautious with feature engineering on small datasets
- **Look-Ahead Bias**: Ensure proper train/test splits in validation

## Contributing

This is a research framework extracted from the `elliottsax/quant` project. For contributions or questions, please contact the repository maintainer.

## License

Please refer to the original `elliottsax/quant` repository for license information.

## Acknowledgments

This analysis framework was developed as part of the quantitative research project for analyzing trading patterns and market behavior. The algorithms combine classical signal processing (FFT), statistical learning (HMM), and pattern matching (DTW) to provide comprehensive time-series analysis capabilities.

## Citation

If you use this framework in your research, please cite:
```
Stock Analysis Research Framework
https://github.com/ElliottSax/discovery
```

---

**Version**: 1.0.0
**Last Updated**: 2025-11-19
**Status**: Active Development
