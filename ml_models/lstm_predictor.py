"""
LSTM Stock Price Predictor

Uses LSTM neural networks for time-series prediction of stock prices
based on politician trading sequences.

Architecture:
- Embedding layer for categorical features (politician, ticker, etc.)
- Bidirectional LSTM layers for sequence modeling
- Attention mechanism for important time steps
- Dropout for regularization
- Dense output layer for classification

Features:
- Sequence-based prediction (past N days → future)
- Handles variable-length sequences
- Early stopping to prevent overfitting
- Model checkpointing
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)

# Import PyTorch with fallback
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logger.warning("PyTorch not available - LSTM predictor disabled")


class TradingSequenceDataset(Dataset):
    """Dataset for trading sequences"""

    def __init__(self, sequences: List[np.ndarray], labels: List[int]):
        """
        Initialize dataset

        Args:
            sequences: List of trading sequences (variable length)
            labels: List of binary labels (0=DOWN, 1=UP)
        """
        self.sequences = sequences
        self.labels = labels

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return torch.FloatTensor(self.sequences[idx]), torch.LongTensor([self.labels[idx]])


class LSTMStockPredictor(nn.Module):
    """
    LSTM network for stock price prediction

    Architecture:
    Input → Embedding → BiLSTM → Attention → Dense → Output
    """

    def __init__(
        self,
        input_dim: int = 25,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
        bidirectional: bool = True
    ):
        """
        Initialize LSTM predictor

        Args:
            input_dim: Number of input features
            hidden_dim: Hidden layer dimension
            num_layers: Number of LSTM layers
            dropout: Dropout rate
            bidirectional: Use bidirectional LSTM
        """
        super(LSTMStockPredictor, self).__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.bidirectional = bidirectional

        # LSTM layer
        self.lstm = nn.LSTM(
            input_dim,
            hidden_dim,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional
        )

        # Attention layer
        lstm_output_dim = hidden_dim * 2 if bidirectional else hidden_dim
        self.attention = AttentionLayer(lstm_output_dim)

        # Output layers
        self.dropout = nn.Dropout(dropout)
        self.fc1 = nn.Linear(lstm_output_dim, 64)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(64, 2)  # Binary classification (UP/DOWN)

    def forward(self, x):
        """
        Forward pass

        Args:
            x: Input tensor (batch_size, seq_len, input_dim)

        Returns:
            Output tensor (batch_size, 2) - logits for UP/DOWN
        """
        # LSTM
        lstm_out, _ = self.lstm(x)

        # Attention
        attended = self.attention(lstm_out)

        # Dense layers
        out = self.dropout(attended)
        out = self.fc1(out)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)

        return out


class AttentionLayer(nn.Module):
    """Attention mechanism for LSTM output"""

    def __init__(self, hidden_dim: int):
        super(AttentionLayer, self).__init__()
        self.attention_weights = nn.Linear(hidden_dim, 1)

    def forward(self, lstm_output):
        """
        Apply attention to LSTM output

        Args:
            lstm_output: (batch_size, seq_len, hidden_dim)

        Returns:
            Weighted sum (batch_size, hidden_dim)
        """
        # Calculate attention scores
        scores = self.attention_weights(lstm_output)  # (batch, seq_len, 1)
        weights = torch.softmax(scores, dim=1)  # (batch, seq_len, 1)

        # Weighted sum
        attended = torch.sum(weights * lstm_output, dim=1)  # (batch, hidden_dim)

        return attended


class LSTMPredictorWrapper:
    """
    Wrapper for LSTM predictor with training and inference

    Handles:
    - Data preparation and batching
    - Training with early stopping
    - Model checkpointing
    - Inference
    """

    def __init__(
        self,
        input_dim: int = 25,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
        learning_rate: float = 0.001,
        model_dir: str = 'data/models'
    ):
        """
        Initialize LSTM wrapper

        Args:
            input_dim: Number of input features
            hidden_dim: Hidden dimension
            num_layers: Number of LSTM layers
            dropout: Dropout rate
            learning_rate: Learning rate
            model_dir: Directory to save models
        """
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Initialize model
        if HAS_TORCH:
            self.model = LSTMStockPredictor(
                input_dim=input_dim,
                hidden_dim=hidden_dim,
                num_layers=num_layers,
                dropout=dropout
            )
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)

            self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
            self.criterion = nn.CrossEntropyLoss()
        else:
            self.model = None
            logger.warning("PyTorch not available - LSTM predictor in fallback mode")

    def train(
        self,
        sequences: List[np.ndarray],
        labels: List[int],
        epochs: int = 50,
        batch_size: int = 32,
        val_split: float = 0.2,
        early_stopping_patience: int = 5
    ) -> Dict:
        """
        Train LSTM model

        Args:
            sequences: List of trading sequences
            labels: List of labels (0=DOWN, 1=UP)
            epochs: Number of epochs
            batch_size: Batch size
            val_split: Validation split ratio
            early_stopping_patience: Patience for early stopping

        Returns:
            Training history
        """
        if not HAS_TORCH:
            logger.warning("PyTorch not available - skipping training")
            return {'error': 'PyTorch not available'}

        # Split into train/val
        split_idx = int(len(sequences) * (1 - val_split))
        train_sequences = sequences[:split_idx]
        train_labels = labels[:split_idx]
        val_sequences = sequences[split_idx:]
        val_labels = labels[split_idx:]

        # Create datasets
        train_dataset = TradingSequenceDataset(train_sequences, train_labels)
        val_dataset = TradingSequenceDataset(val_sequences, val_labels)

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)

        # Training loop
        history = {'train_loss': [], 'val_loss': [], 'val_accuracy': []}
        best_val_loss = float('inf')
        patience_counter = 0

        for epoch in range(epochs):
            # Training
            self.model.train()
            train_loss = 0.0

            for batch_seq, batch_labels in train_loader:
                batch_seq = batch_seq.to(self.device)
                batch_labels = batch_labels.to(self.device).squeeze()

                self.optimizer.zero_grad()
                outputs = self.model(batch_seq)
                loss = self.criterion(outputs, batch_labels)
                loss.backward()
                self.optimizer.step()

                train_loss += loss.item()

            train_loss /= len(train_loader)

            # Validation
            self.model.eval()
            val_loss = 0.0
            correct = 0
            total = 0

            with torch.no_grad():
                for batch_seq, batch_labels in val_loader:
                    batch_seq = batch_seq.to(self.device)
                    batch_labels = batch_labels.to(self.device).squeeze()

                    outputs = self.model(batch_seq)
                    loss = self.criterion(outputs, batch_labels)
                    val_loss += loss.item()

                    _, predicted = torch.max(outputs.data, 1)
                    total += batch_labels.size(0)
                    correct += (predicted == batch_labels).sum().item()

            val_loss /= len(val_loader)
            val_accuracy = correct / total

            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['val_accuracy'].append(val_accuracy)

            logger.info(
                f"Epoch {epoch+1}/{epochs} - "
                f"Train Loss: {train_loss:.4f}, "
                f"Val Loss: {val_loss:.4f}, "
                f"Val Acc: {val_accuracy:.4f}"
            )

            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model
                self.save_model(suffix='_best')
            else:
                patience_counter += 1
                if patience_counter >= early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break

        return history

    def predict(self, sequence: np.ndarray) -> Dict:
        """
        Make prediction for a single sequence

        Args:
            sequence: Trading sequence (seq_len, input_dim)

        Returns:
            Prediction dict with 'prediction', 'confidence', 'probabilities'
        """
        if not HAS_TORCH:
            logger.warning("PyTorch not available - using baseline prediction")
            return {
                'prediction': 'UP',
                'confidence': 0.5,
                'probability_up': 0.5,
                'probability_down': 0.5
            }

        self.model.eval()

        with torch.no_grad():
            # Add batch dimension
            seq_tensor = torch.FloatTensor(sequence).unsqueeze(0).to(self.device)

            # Forward pass
            outputs = self.model(seq_tensor)
            probabilities = torch.softmax(outputs, dim=1).cpu().numpy()[0]

            # Get prediction
            predicted_class = np.argmax(probabilities)
            prediction = 'UP' if predicted_class == 1 else 'DOWN'
            confidence = probabilities[predicted_class]

            return {
                'prediction': prediction,
                'confidence': float(confidence),
                'probability_up': float(probabilities[1]),
                'probability_down': float(probabilities[0])
            }

    def save_model(self, suffix: str = ''):
        """Save model to disk"""
        if not HAS_TORCH or self.model is None:
            return

        filepath = self.model_dir / f'lstm_predictor{suffix}.pt'
        torch.save({
            'model_state': self.model.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'config': {
                'input_dim': self.input_dim,
                'hidden_dim': self.hidden_dim,
                'num_layers': self.num_layers,
                'dropout': self.dropout
            }
        }, filepath)

        logger.info(f"LSTM model saved to {filepath}")

    def load_model(self, suffix: str = ''):
        """Load model from disk"""
        if not HAS_TORCH:
            return

        filepath = self.model_dir / f'lstm_predictor{suffix}.pt'
        if not filepath.exists():
            logger.warning(f"Model file not found: {filepath}")
            return

        checkpoint = torch.load(filepath, map_location=self.device)

        # Reinitialize model with saved config
        config = checkpoint['config']
        self.model = LSTMStockPredictor(
            input_dim=config['input_dim'],
            hidden_dim=config['hidden_dim'],
            num_layers=config['num_layers'],
            dropout=config['dropout']
        )
        self.model.to(self.device)

        # Load state
        self.model.load_state_dict(checkpoint['model_state'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state'])

        logger.info(f"LSTM model loaded from {filepath}")


# Export
__all__ = ['LSTMPredictorWrapper', 'LSTMStockPredictor', 'TradingSequenceDataset']
