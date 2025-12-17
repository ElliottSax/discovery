"""
Model Explainability with SHAP Values

Provides interpretability for ML predictions using SHAP (SHapley Additive exPlanations):
- Feature importance (global and local)
- Prediction explanations
- Force plots and waterfall charts
- Feature contribution breakdown

SHAP provides consistent and locally accurate attribution of predictions
to input features.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Import SHAP with fallback
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    logger.warning("SHAP not available - using fallback explanations")


class ModelExplainer:
    """
    Explains ML model predictions using SHAP values

    Supports:
    - Tree-based models (XGBoost, RandomForest, GradientBoosting)
    - Linear models (LogisticRegression)
    - Deep learning models (with approximations)
    """

    def __init__(self, model, feature_names: List[str]):
        """
        Initialize explainer

        Args:
            model: Trained model to explain
            feature_names: List of feature names
        """
        self.model = model
        self.feature_names = feature_names
        self.explainer = None

        if HAS_SHAP:
            self._initialize_explainer()
        else:
            logger.warning("SHAP not available - using fallback")

    def _initialize_explainer(self):
        """Initialize SHAP explainer based on model type"""
        try:
            # Tree-based explainer for XGBoost, RandomForest, GradientBoosting
            if hasattr(self.model, 'predict_proba') and hasattr(self.model, 'estimators_'):
                self.explainer = shap.TreeExplainer(self.model)
                logger.info("Using TreeExplainer for ensemble model")

            # Linear explainer for LogisticRegression
            elif hasattr(self.model, 'coef_'):
                # Use LinearExplainer with training data
                self.explainer = shap.LinearExplainer(self.model, np.zeros((1, len(self.feature_names))))
                logger.info("Using LinearExplainer for linear model")

            # Kernel explainer as fallback (model-agnostic but slower)
            else:
                # Create background dataset (all zeros)
                background = np.zeros((100, len(self.feature_names)))
                self.explainer = shap.KernelExplainer(self.model.predict_proba, background)
                logger.info("Using KernelExplainer (model-agnostic)")

        except Exception as e:
            logger.error(f"Failed to initialize SHAP explainer: {e}")
            self.explainer = None

    def explain_prediction(
        self,
        features: np.ndarray,
        base_values: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Explain a single prediction

        Args:
            features: Feature vector for prediction
            base_values: Optional base values (expected prediction without features)

        Returns:
            Dictionary with:
            - 'shap_values': SHAP values for each feature
            - 'feature_contributions': Dict mapping feature names to contributions
            - 'base_value': Expected value (baseline)
            - 'prediction': Model prediction
        """
        if not HAS_SHAP or self.explainer is None:
            return self._fallback_explanation(features)

        try:
            # Reshape if needed
            if features.ndim == 1:
                features = features.reshape(1, -1)

            # Calculate SHAP values
            shap_values = self.explainer.shap_values(features)

            # Handle multi-class output
            if isinstance(shap_values, list):
                # For binary classification, use class 1 (positive class)
                shap_values = shap_values[1]

            # Get base value
            if hasattr(self.explainer, 'expected_value'):
                if isinstance(self.explainer.expected_value, list):
                    base_value = self.explainer.expected_value[1]
                else:
                    base_value = self.explainer.expected_value
            else:
                base_value = 0.0

            # Create feature contributions dict
            feature_contributions = {}
            for i, name in enumerate(self.feature_names):
                contribution = float(shap_values[0][i]) if shap_values.ndim > 1 else float(shap_values[i])
                feature_contributions[name] = contribution

            # Get model prediction
            if hasattr(self.model, 'predict_proba'):
                prediction_proba = self.model.predict_proba(features)[0]
                prediction = int(np.argmax(prediction_proba))
            else:
                prediction = int(self.model.predict(features)[0])

            return {
                'shap_values': shap_values.tolist() if isinstance(shap_values, np.ndarray) else shap_values,
                'feature_contributions': feature_contributions,
                'base_value': float(base_value),
                'prediction': prediction,
                'top_positive': self._get_top_features(feature_contributions, positive=True),
                'top_negative': self._get_top_features(feature_contributions, positive=False)
            }

        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            return self._fallback_explanation(features)

    def _get_top_features(
        self,
        contributions: Dict[str, float],
        positive: bool = True,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """Get top contributing features"""
        # Sort by contribution
        sorted_features = sorted(
            contributions.items(),
            key=lambda x: x[1],
            reverse=positive
        )

        # Filter by sign
        if positive:
            filtered = [(name, val) for name, val in sorted_features if val > 0]
        else:
            filtered = [(name, val) for name, val in sorted_features if val < 0]

        # Take top N
        top_features = []
        for name, contribution in filtered[:top_n]:
            top_features.append({
                'feature': name,
                'contribution': contribution,
                'direction': 'positive' if contribution > 0 else 'negative'
            })

        return top_features

    def _fallback_explanation(self, features: np.ndarray) -> Dict[str, Any]:
        """Fallback explanation when SHAP is not available"""
        # Use simple feature importance from model (if available)
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            importances = np.abs(self.model.coef_[0])
        else:
            # Equal importance as last resort
            importances = np.ones(len(self.feature_names)) / len(self.feature_names)

        # Create feature contributions
        feature_contributions = {}
        for i, name in enumerate(self.feature_names):
            # Scale importance by feature value
            contribution = float(importances[i] * features.flatten()[i])
            feature_contributions[name] = contribution

        return {
            'shap_values': None,
            'feature_contributions': feature_contributions,
            'base_value': 0.0,
            'prediction': int(self.model.predict(features.reshape(1, -1))[0]),
            'top_positive': self._get_top_features(feature_contributions, positive=True),
            'top_negative': self._get_top_features(feature_contributions, positive=False),
            'fallback': True
        }

    def get_global_importance(
        self,
        X: np.ndarray,
        sample_size: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Get global feature importance across all samples

        Args:
            X: Feature matrix
            sample_size: Number of samples to use (None = all)

        Returns:
            Dict mapping feature names to importance scores
        """
        if not HAS_SHAP or self.explainer is None:
            # Fallback to model's feature importance
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
            elif hasattr(self.model, 'coef_'):
                importances = np.abs(self.model.coef_[0])
            else:
                importances = np.ones(len(self.feature_names))

            return {name: float(imp) for name, imp in zip(self.feature_names, importances)}

        try:
            # Sample if needed
            if sample_size and len(X) > sample_size:
                indices = np.random.choice(len(X), sample_size, replace=False)
                X_sample = X[indices]
            else:
                X_sample = X

            # Calculate SHAP values
            shap_values = self.explainer.shap_values(X_sample)

            # Handle multi-class
            if isinstance(shap_values, list):
                shap_values = shap_values[1]

            # Calculate mean absolute SHAP value per feature
            importance = np.abs(shap_values).mean(axis=0)

            return {name: float(imp) for name, imp in zip(self.feature_names, importance)}

        except Exception as e:
            logger.error(f"Global importance calculation failed: {e}")
            return {}

    def explain_prediction_text(
        self,
        features: np.ndarray,
        ticker: str = 'STOCK',
        politician: str = 'Politician'
    ) -> str:
        """
        Generate human-readable explanation text

        Args:
            features: Feature vector
            ticker: Stock ticker
            politician: Politician name

        Returns:
            Text explanation
        """
        explanation = self.explain_prediction(features)

        # Build text
        lines = []
        lines.append(f"Prediction Explanation for {ticker}")
        lines.append("=" * 50)
        lines.append("")

        # Prediction
        pred = 'UP' if explanation['prediction'] == 1 else 'DOWN'
        lines.append(f"Prediction: {pred}")
        lines.append("")

        # Top positive factors
        if explanation['top_positive']:
            lines.append("Top factors supporting this prediction:")
            for item in explanation['top_positive']:
                feature = item['feature'].replace('_', ' ').title()
                contrib = item['contribution']
                lines.append(f"  • {feature}: +{contrib:.3f}")
            lines.append("")

        # Top negative factors
        if explanation['top_negative']:
            lines.append("Top factors against this prediction:")
            for item in explanation['top_negative']:
                feature = item['feature'].replace('_', ' ').title()
                contrib = item['contribution']
                lines.append(f"  • {feature}: {contrib:.3f}")
            lines.append("")

        # Base value
        lines.append(f"Base prediction (no features): {explanation['base_value']:.3f}")

        return '\n'.join(lines)


def create_explainer_for_predictor(predictor, feature_names: List[str]) -> ModelExplainer:
    """
    Create explainer for a stock predictor

    Args:
        predictor: StockPricePredictor instance
        feature_names: List of feature names

    Returns:
        ModelExplainer instance
    """
    # Use the best performing model from ensemble
    if hasattr(predictor, 'models') and predictor.models:
        # Try to use XGBoost or RandomForest (best for SHAP)
        for model_name in ['xgboost', 'random_forest', 'gradient_boost']:
            if model_name in predictor.models:
                model = predictor.models[model_name]
                logger.info(f"Creating explainer for {model_name}")
                return ModelExplainer(model, feature_names)

        # Fallback to first available model
        first_model_name = list(predictor.models.keys())[0]
        model = predictor.models[first_model_name]
        logger.info(f"Creating explainer for {first_model_name}")
        return ModelExplainer(model, feature_names)

    else:
        raise ValueError("Predictor has no trained models")


# Export
__all__ = ['ModelExplainer', 'create_explainer_for_predictor']
