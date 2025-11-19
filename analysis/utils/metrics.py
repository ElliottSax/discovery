"""ML evaluation metrics and performance tracking."""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
import logging

logger = logging.getLogger(__name__)


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_pred_proba: Optional[np.ndarray] = None,
    task_type: str = "regression"
) -> Dict[str, float]:
    """
    Calculate comprehensive metrics for model evaluation.

    Args:
        y_true: True labels/values
        y_pred: Predicted labels/values
        y_pred_proba: Predicted probabilities (for classification)
        task_type: 'regression' or 'classification'

    Returns:
        Dictionary of metric names and values
    """
    metrics = {}

    try:
        if task_type == "regression":
            metrics.update(_calculate_regression_metrics(y_true, y_pred))
        elif task_type == "classification":
            metrics.update(_calculate_classification_metrics(
                y_true, y_pred, y_pred_proba
            ))
        else:
            raise ValueError(f"Unknown task_type: {task_type}")

        # Add trading-specific metrics
        metrics.update(_calculate_trading_metrics(y_true, y_pred))

    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        metrics["error"] = str(e)

    return metrics


def _calculate_regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Dict[str, float]:
    """Calculate regression metrics."""
    return {
        "mse": mean_squared_error(y_true, y_pred),
        "rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
        "mae": mean_absolute_error(y_true, y_pred),
        "r2": r2_score(y_true, y_pred),
        "mape": np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8))) * 100,
    }


def _calculate_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_pred_proba: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """Calculate classification metrics."""
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, average='weighted', zero_division=0),
        "recall": recall_score(y_true, y_pred, average='weighted', zero_division=0),
        "f1": f1_score(y_true, y_pred, average='weighted', zero_division=0),
    }

    # Add AUC if probabilities provided
    if y_pred_proba is not None:
        try:
            n_classes = y_pred_proba.shape[1] if len(y_pred_proba.shape) > 1 else 2
            if n_classes == 2:
                # Binary classification
                metrics["auc"] = roc_auc_score(y_true, y_pred_proba[:, 1])
            else:
                # Multi-class
                metrics["auc"] = roc_auc_score(
                    y_true, y_pred_proba, multi_class='ovr', average='weighted'
                )
        except Exception as e:
            logger.warning(f"Could not calculate AUC: {e}")

    return metrics


def _calculate_trading_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Dict[str, float]:
    """
    Calculate trading-specific metrics.

    Metrics:
    - Directional accuracy
    - Sharpe ratio
    - Max drawdown
    - Win rate
    - Profit factor
    """
    metrics = {}

    try:
        # Directional accuracy (did we predict direction correctly?)
        directions_true = np.sign(y_true)
        directions_pred = np.sign(y_pred)
        metrics["directional_accuracy"] = (directions_true == directions_pred).mean()

        # Sharpe ratio (assuming daily returns)
        if len(y_pred) > 1:
            returns = y_pred
            sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
            metrics["sharpe_ratio"] = sharpe

        # Max drawdown
        cumulative_returns = np.cumsum(y_pred)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / (running_max + 1e-8)
        metrics["max_drawdown"] = np.min(drawdown)

        # Win rate
        positive_predictions = y_pred > 0
        correct_positive = (y_true > 0) & positive_predictions
        if positive_predictions.sum() > 0:
            metrics["win_rate"] = correct_positive.sum() / positive_predictions.sum()

        # Profit factor
        profits = y_pred[y_pred > 0].sum()
        losses = abs(y_pred[y_pred < 0].sum())
        if losses > 0:
            metrics["profit_factor"] = profits / losses

    except Exception as e:
        logger.warning(f"Error calculating trading metrics: {e}")

    return metrics


def calculate_ic(predictions: pd.Series, actuals: pd.Series) -> float:
    """
    Calculate Information Coefficient (IC) - correlation between predictions and actuals.

    IC is a key metric in quantitative finance for evaluating alpha.

    Args:
        predictions: Predicted returns/rankings
        actuals: Actual returns/rankings

    Returns:
        IC value (-1 to 1)
    """
    return predictions.corr(actuals)


def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sharpe ratio.

    Args:
        returns: Array of returns
        risk_free_rate: Risk-free rate (annualized)

    Returns:
        Sharpe ratio (annualized)
    """
    excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
    if len(returns) > 1 and excess_returns.std() > 0:
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    return 0.0


def calculate_max_drawdown(returns: np.ndarray) -> float:
    """
    Calculate maximum drawdown.

    Args:
        returns: Array of returns

    Returns:
        Maximum drawdown (negative value)
    """
    cumulative = np.cumsum(returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = cumulative - running_max
    return np.min(drawdown)


def calculate_sortino_ratio(
    returns: np.ndarray,
    risk_free_rate: float = 0.0,
    target_return: float = 0.0
) -> float:
    """
    Calculate Sortino ratio (like Sharpe but only penalizes downside volatility).

    Args:
        returns: Array of returns
        risk_free_rate: Risk-free rate (annualized)
        target_return: Target return threshold

    Returns:
        Sortino ratio (annualized)
    """
    excess_returns = returns - risk_free_rate / 252
    downside_returns = returns[returns < target_return]

    if len(downside_returns) > 1:
        downside_std = np.std(downside_returns)
        if downside_std > 0:
            return np.mean(excess_returns) / downside_std * np.sqrt(252)

    return 0.0


def calculate_calmar_ratio(
    returns: np.ndarray,
    risk_free_rate: float = 0.0
) -> float:
    """
    Calculate Calmar ratio (return / max drawdown).

    Args:
        returns: Array of returns
        risk_free_rate: Risk-free rate (annualized)

    Returns:
        Calmar ratio
    """
    annualized_return = np.mean(returns) * 252
    max_dd = calculate_max_drawdown(returns)

    if max_dd < 0:
        return (annualized_return - risk_free_rate) / abs(max_dd)

    return 0.0
