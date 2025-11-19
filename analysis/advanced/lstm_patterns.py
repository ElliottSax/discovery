"""
LSTM Pattern Recognition for Financial Time Series

Uses Long Short-Term Memory networks with attention mechanism to detect
complex, non-linear patterns that traditional methods may miss.

Key Advantages:
- Learns patterns directly from data (no manual feature engineering)
- Captures long-term dependencies
- Handles non-linear relationships
- Attention mechanism provides interpretability
- Transfer learning from pre-trained models

Use Cases:
- Complex multi-factor pattern detection
- Regime prediction (not just detection)
- Anomaly detection in sequences
- Next-period forecasting with pattern context
- Feature importance via attention weights

References:
- Hochreiter & Schmidhuber (1997) - Long Short-Term Memory
- Bahdanau et al. (2015) - Neural Machine Translation by Jointly Learning to Align
- Fischer & Krauss (2018) - Deep learning with long short-term memory for financial market predictions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. LSTM functionality will be limited.")


@dataclass
class LSTMConfig:
    """Configuration for LSTM model."""
    input_size: int = 1
    hidden_size: int = 64
    num_layers: int = 2
    dropout: float = 0.2
    sequence_length: int = 30
    learning_rate: float = 0.001
    batch_size: int = 32
    num_epochs: int = 50
    use_attention: bool = True
    bidirectional: bool = False


class TimeSeriesDataset(Dataset):
    """PyTorch dataset for time series sequences."""

    def __init__(self, data: np.ndarray, sequence_length: int, target_offset: int = 1):
        """
        Create dataset from time series.

        Args:
            data: Time series data (N, features)
            sequence_length: Length of input sequences
            target_offset: How many steps ahead to predict
        """
        self.data = data
        self.sequence_length = sequence_length
        self.target_offset = target_offset

    def __len__(self):
        return len(self.data) - self.sequence_length - self.target_offset + 1

    def __getitem__(self, idx):
        X = self.data[idx:idx + self.sequence_length]
        y = self.data[idx + self.sequence_length + self.target_offset - 1]
        return torch.FloatTensor(X), torch.FloatTensor(y)


class Attention(nn.Module):
    """Attention mechanism for LSTM."""

    def __init__(self, hidden_size: int):
        super(Attention, self).__init__()
        self.hidden_size = hidden_size
        self.attn = nn.Linear(hidden_size, 1)

    def forward(self, lstm_output):
        """
        Compute attention weights and context vector.

        Args:
            lstm_output: LSTM outputs (batch, seq_len, hidden_size)

        Returns:
            context: Weighted sum of LSTM outputs
            attention_weights: Attention weights for interpretability
        """
        # Compute attention scores
        attn_scores = self.attn(lstm_output)  # (batch, seq_len, 1)
        attn_weights = torch.softmax(attn_scores, dim=1)  # (batch, seq_len, 1)

        # Compute context vector
        context = torch.sum(attn_weights * lstm_output, dim=1)  # (batch, hidden_size)

        return context, attn_weights.squeeze(-1)


class LSTMPatternRecognizer(nn.Module):
    """LSTM network with optional attention for pattern recognition."""

    def __init__(self, config: LSTMConfig):
        super(LSTMPatternRecognizer, self).__init__()
        self.config = config

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=config.input_size,
            hidden_size=config.hidden_size,
            num_layers=config.num_layers,
            dropout=config.dropout if config.num_layers > 1 else 0,
            batch_first=True,
            bidirectional=config.bidirectional
        )

        # Attention
        lstm_output_size = config.hidden_size * 2 if config.bidirectional else config.hidden_size

        if config.use_attention:
            self.attention = Attention(lstm_output_size)
            self.fc = nn.Linear(lstm_output_size, config.input_size)
        else:
            self.fc = nn.Linear(lstm_output_size, config.input_size)

    def forward(self, x):
        """
        Forward pass.

        Args:
            x: Input sequences (batch, seq_len, features)

        Returns:
            output: Predictions
            attention_weights: Attention weights (if enabled)
        """
        # LSTM
        lstm_out, (h_n, c_n) = self.lstm(x)

        # Attention or last hidden state
        if self.config.use_attention:
            context, attn_weights = self.attention(lstm_out)
            output = self.fc(context)
            return output, attn_weights
        else:
            # Use last hidden state
            if self.config.bidirectional:
                h_n = torch.cat((h_n[-2], h_n[-1]), dim=1)
            else:
                h_n = h_n[-1]
            output = self.fc(h_n)
            return output, None


class LSTMPatternDetector:
    """
    High-level interface for LSTM pattern detection.

    Provides:
    - Training on historical data
    - Pattern prediction
    - Anomaly detection
    - Feature importance via attention
    - Model persistence
    """

    def __init__(self, config: Optional[LSTMConfig] = None):
        """
        Initialize LSTM detector.

        Args:
            config: LSTM configuration
        """
        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch is required for LSTM pattern detection. "
                "Install with: pip install torch"
            )

        self.config = config or LSTMConfig()
        self.model = None
        self.scaler_mean = None
        self.scaler_std = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.training_history = []

    def _normalize(self, data: np.ndarray, fit: bool = False) -> np.ndarray:
        """Normalize data using z-score."""
        if fit:
            self.scaler_mean = np.mean(data, axis=0)
            self.scaler_std = np.std(data, axis=0) + 1e-8

        return (data - self.scaler_mean) / self.scaler_std

    def _denormalize(self, data: np.ndarray) -> np.ndarray:
        """Denormalize data."""
        return data * self.scaler_std + self.scaler_mean

    def train(
        self,
        time_series: Union[pd.Series, np.ndarray],
        validation_split: float = 0.2,
        verbose: bool = True
    ) -> Dict:
        """
        Train LSTM on time series data.

        Args:
            time_series: Training data
            validation_split: Fraction for validation
            verbose: Whether to print progress

        Returns:
            Training history with losses and metrics
        """
        # Convert to numpy
        if isinstance(time_series, pd.Series):
            data = time_series.values.reshape(-1, 1)
        else:
            data = np.array(time_series).reshape(-1, 1)

        # Normalize
        data_normalized = self._normalize(data, fit=True)

        # Train/validation split
        split_idx = int(len(data_normalized) * (1 - validation_split))
        train_data = data_normalized[:split_idx]
        val_data = data_normalized[split_idx:]

        # Create datasets
        train_dataset = TimeSeriesDataset(train_data, self.config.sequence_length)
        val_dataset = TimeSeriesDataset(val_data, self.config.sequence_length)

        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False
        )

        # Initialize model
        self.model = LSTMPatternRecognizer(self.config).to(self.device)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.config.learning_rate)

        # Training loop
        self.training_history = []

        for epoch in range(self.config.num_epochs):
            # Train
            self.model.train()
            train_loss = 0.0

            for X_batch, y_batch in train_loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device)

                optimizer.zero_grad()
                output, _ = self.model(X_batch)
                loss = criterion(output, y_batch)
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            train_loss /= len(train_loader)

            # Validation
            self.model.eval()
            val_loss = 0.0

            with torch.no_grad():
                for X_batch, y_batch in val_loader:
                    X_batch = X_batch.to(self.device)
                    y_batch = y_batch.to(self.device)

                    output, _ = self.model(X_batch)
                    loss = criterion(output, y_batch)
                    val_loss += loss.item()

            val_loss /= len(val_loader)

            self.training_history.append({
                'epoch': epoch + 1,
                'train_loss': train_loss,
                'val_loss': val_loss
            })

            if verbose and (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{self.config.num_epochs} - "
                      f"Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")

        return {
            'history': self.training_history,
            'final_train_loss': train_loss,
            'final_val_loss': val_loss
        }

    def predict(
        self,
        time_series: Union[pd.Series, np.ndarray],
        return_attention: bool = False
    ) -> Dict:
        """
        Predict next values and detect patterns.

        Args:
            time_series: Input time series
            return_attention: Whether to return attention weights

        Returns:
            Dictionary with predictions and pattern information
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Convert to numpy
        if isinstance(time_series, pd.Series):
            data = time_series.values.reshape(-1, 1)
            index = time_series.index
        else:
            data = np.array(time_series).reshape(-1, 1)
            index = None

        # Normalize
        data_normalized = self._normalize(data, fit=False)

        # Create sequences
        sequences = []
        for i in range(len(data_normalized) - self.config.sequence_length + 1):
            sequences.append(data_normalized[i:i + self.config.sequence_length])

        sequences = np.array(sequences)
        X = torch.FloatTensor(sequences).to(self.device)

        # Predict
        self.model.eval()
        predictions = []
        attention_weights = []

        with torch.no_grad():
            output, attn = self.model(X)
            predictions = output.cpu().numpy()
            if return_attention and attn is not None:
                attention_weights = attn.cpu().numpy()

        # Denormalize predictions
        predictions = self._denormalize(predictions)

        result = {
            'predictions': predictions.flatten(),
            'sequence_length': self.config.sequence_length
        }

        if return_attention and len(attention_weights) > 0:
            result['attention_weights'] = attention_weights

        # Add index if available
        if index is not None and len(index) > self.config.sequence_length:
            result['prediction_index'] = index[self.config.sequence_length:]

        return result

    def detect_anomalies(
        self,
        time_series: Union[pd.Series, np.ndarray],
        threshold: float = 3.0
    ) -> Dict:
        """
        Detect anomalies using prediction errors.

        Args:
            time_series: Input time series
            threshold: Number of standard deviations for anomaly threshold

        Returns:
            Dictionary with anomaly detection results
        """
        # Get predictions
        pred_result = self.predict(time_series)
        predictions = pred_result['predictions']

        # Get actual values (excluding first sequence_length)
        if isinstance(time_series, pd.Series):
            actuals = time_series.values[self.config.sequence_length:]
        else:
            actuals = np.array(time_series)[self.config.sequence_length:]

        # Compute prediction errors
        errors = np.abs(actuals - predictions)
        mean_error = np.mean(errors)
        std_error = np.std(errors)

        # Detect anomalies
        anomaly_threshold = mean_error + threshold * std_error
        anomaly_mask = errors > anomaly_threshold
        anomaly_indices = np.where(anomaly_mask)[0] + self.config.sequence_length

        return {
            'anomaly_indices': anomaly_indices.tolist(),
            'anomaly_scores': errors[anomaly_mask].tolist(),
            'threshold': float(anomaly_threshold),
            'n_anomalies': len(anomaly_indices),
            'mean_error': float(mean_error),
            'std_error': float(std_error)
        }

    def get_feature_importance(
        self,
        time_series: Union[pd.Series, np.ndarray],
        window_size: int = 50
    ) -> Dict:
        """
        Get feature importance using attention weights.

        Args:
            time_series: Input time series
            window_size: Window size for averaging attention

        Returns:
            Dictionary with feature importance information
        """
        if not self.config.use_attention:
            raise ValueError("Attention must be enabled to get feature importance")

        pred_result = self.predict(time_series, return_attention=True)

        if 'attention_weights' not in pred_result:
            raise ValueError("No attention weights available")

        attention_weights = pred_result['attention_weights']

        # Average attention weights across time
        avg_attention = np.mean(attention_weights, axis=0)

        # Time step importance (which historical time steps are most important)
        time_importance = {
            'lookback_importance': avg_attention.tolist(),
            'most_important_lookback': int(np.argmax(avg_attention)),
            'attention_entropy': float(-np.sum(avg_attention * np.log(avg_attention + 1e-10)))
        }

        return time_importance

    def save(self, path: str):
        """Save model and configuration."""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for saving")

        if self.model is None:
            raise ValueError("No model to save")

        torch.save({
            'model_state_dict': self.model.state_dict(),
            'config': self.config,
            'scaler_mean': self.scaler_mean,
            'scaler_std': self.scaler_std,
            'training_history': self.training_history
        }, path)

    def load(self, path: str):
        """Load model and configuration."""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for loading")

        checkpoint = torch.load(path, map_location=self.device)

        self.config = checkpoint['config']
        self.scaler_mean = checkpoint['scaler_mean']
        self.scaler_std = checkpoint['scaler_std']
        self.training_history = checkpoint.get('training_history', [])

        self.model = LSTMPatternRecognizer(self.config).to(self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()


# Convenience function
def quick_lstm_predict(
    time_series: Union[pd.Series, np.ndarray],
    config: Optional[LSTMConfig] = None,
    **kwargs
) -> Dict:
    """
    Quick LSTM prediction with default configuration.

    Args:
        time_series: Input time series
        config: Optional LSTM configuration
        **kwargs: Additional arguments passed to train()

    Returns:
        Predictions and pattern information

    Example:
        >>> import pandas as pd
        >>> data = pd.Series([...])  # Your time series
        >>> result = quick_lstm_predict(data, num_epochs=30)
        >>> predictions = result['predictions']
    """
    detector = LSTMPatternDetector(config)
    detector.train(time_series, verbose=kwargs.get('verbose', False), **kwargs)
    return detector.predict(time_series, return_attention=True)


if __name__ == "__main__":
    # Example usage
    if TORCH_AVAILABLE:
        print("Example: LSTM Pattern Recognition")

        # Create synthetic data
        t = np.linspace(0, 100, 500)
        signal = 10 + 5 * np.sin(2 * np.pi * t / 20) + np.random.normal(0, 0.5, 500)
        data = pd.Series(signal)

        # Create detector
        config = LSTMConfig(
            hidden_size=32,
            num_layers=2,
            sequence_length=20,
            num_epochs=50,
            use_attention=True
        )

        detector = LSTMPatternDetector(config)

        # Train
        print("Training LSTM...")
        history = detector.train(data, verbose=True)
        print(f"Final validation loss: {history['final_val_loss']:.6f}")

        # Predict
        print("\nMaking predictions...")
        result = detector.predict(data, return_attention=True)
        print(f"Predictions shape: {result['predictions'].shape}")

        # Detect anomalies
        print("\nDetecting anomalies...")
        anomalies = detector.detect_anomalies(data)
        print(f"Found {anomalies['n_anomalies']} anomalies")

        # Feature importance
        print("\nGetting feature importance...")
        importance = detector.get_feature_importance(data)
        print(f"Most important lookback: {importance['most_important_lookback']} steps")

        print("\n✅ LSTM pattern recognition complete!")
    else:
        print("PyTorch not available. Install with: pip install torch")
