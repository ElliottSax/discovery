"""
Machine Learning Models for Advanced Analytics
Anomaly detection, pattern recognition, and predictive modeling
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from typing import Dict, List, Tuple, Optional
import joblib
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """Detect unusual trading patterns using ML"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_features(self, trades_df: pd.DataFrame) -> np.ndarray:
        """
        Prepare feature matrix from trades data
        
        Args:
            trades_df: DataFrame with trade data
            
        Returns:
            Feature matrix
        """
        features = []
        
        # Group by politician
        for politician in trades_df['politician_name'].unique():
            politician_trades = trades_df[trades_df['politician_name'] == politician]
            
            if len(politician_trades) > 0:
                # Calculate features
                feature_vector = [
                    len(politician_trades),  # Number of trades
                    politician_trades['amount_max'].mean() if 'amount_max' in politician_trades else 0,
                    politician_trades['amount_max'].std() if 'amount_max' in politician_trades else 0,
                    politician_trades['return_pct'].mean() if 'return_pct' in politician_trades else 0,
                    len(politician_trades['ticker'].unique()) if 'ticker' in politician_trades else 0,  # Diversity
                    (politician_trades['transaction_type'] == 'Purchase').mean() if 'transaction_type' in politician_trades else 0.5,  # Buy ratio
                ]
                features.append(feature_vector)
                
        return np.array(features) if features else np.array([]).reshape(0, 6)
        
    def train(self, trades_df: pd.DataFrame):
        """
        Train anomaly detection model
        
        Args:
            trades_df: Historical trades data
        """
        logger.info("Training anomaly detection model")
        
        # Prepare features
        X = self.prepare_features(trades_df)
        
        if len(X) > 0:
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Isolation Forest
            self.isolation_forest.fit(X_scaled)
            self.is_trained = True
            
            logger.info(f"Model trained on {len(X)} samples")
        else:
            logger.warning("No data available for training")
            
    def detect_anomalies(self, trades_df: pd.DataFrame) -> List[Dict]:
        """
        Detect anomalies in trading data
        
        Args:
            trades_df: Recent trades data
            
        Returns:
            List of detected anomalies
        """
        if not self.is_trained:
            logger.warning("Model not trained, training now")
            self.train(trades_df)
            
        anomalies = []
        
        # Prepare features
        X = self.prepare_features(trades_df)
        
        if len(X) > 0:
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Predict anomalies
            predictions = self.isolation_forest.predict(X_scaled)
            anomaly_scores = self.isolation_forest.score_samples(X_scaled)
            
            # Get politician names
            politicians = trades_df['politician_name'].unique()
            
            # Identify anomalies
            for i, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
                if pred == -1 and i < len(politicians):  # -1 indicates anomaly
                    politician_name = politicians[i]
                    politician_trades = trades_df[trades_df['politician_name'] == politician_name]
                    
                    anomaly = {
                        'type': 'unusual_trading_pattern',
                        'politician': politician_name,
                        'anomaly_score': float(-score),  # Convert to positive score
                        'details': {
                            'trade_count': len(politician_trades),
                            'avg_amount': float(politician_trades['amount_max'].mean()) if 'amount_max' in politician_trades else 0,
                            'unique_stocks': len(politician_trades['ticker'].unique()) if 'ticker' in politician_trades else 0,
                            'recent_trades': politician_trades.head(3).to_dict('records')
                        },
                        'severity': 'high' if -score > 0.5 else 'medium',
                        'timestamp': datetime.now().isoformat()
                    }
                    anomalies.append(anomaly)
                    
        # Additional anomaly checks
        anomalies.extend(self._detect_timing_anomalies(trades_df))
        anomalies.extend(self._detect_volume_anomalies(trades_df))
        
        return anomalies
        
    def _detect_timing_anomalies(self, trades_df: pd.DataFrame) -> List[Dict]:
        """Detect suspicious timing patterns"""
        anomalies = []
        
        # Check for trades before major events
        # In production, would correlate with news/earnings data
        
        # Example: Detect clustering of trades
        if 'transaction_date' in trades_df:
            trades_df['date'] = pd.to_datetime(trades_df['transaction_date'])
            
            # Group by date and stock
            daily_trades = trades_df.groupby(['date', 'ticker']).size()
            
            # Find days with unusual activity
            threshold = daily_trades.mean() + 2 * daily_trades.std()
            
            for (date, ticker), count in daily_trades.items():
                if count > threshold:
                    anomalies.append({
                        'type': 'unusual_trading_volume',
                        'date': date.isoformat(),
                        'ticker': ticker,
                        'trade_count': int(count),
                        'severity': 'medium',
                        'message': f'Unusual number of trades ({count}) for {ticker} on {date.date()}'
                    })
                    
        return anomalies
        
    def _detect_volume_anomalies(self, trades_df: pd.DataFrame) -> List[Dict]:
        """Detect unusual trade volumes"""
        anomalies = []
        
        if 'amount_max' in trades_df:
            # Calculate z-scores for trade amounts
            mean_amount = trades_df['amount_max'].mean()
            std_amount = trades_df['amount_max'].std()
            
            if std_amount > 0:
                trades_df['z_score'] = (trades_df['amount_max'] - mean_amount) / std_amount
                
                # Find outliers (z-score > 3)
                outliers = trades_df[trades_df['z_score'] > 3]
                
                for _, trade in outliers.iterrows():
                    anomalies.append({
                        'type': 'large_transaction',
                        'politician': trade.get('politician_name'),
                        'ticker': trade.get('ticker'),
                        'amount': float(trade.get('amount_max', 0)),
                        'z_score': float(trade.get('z_score', 0)),
                        'severity': 'high',
                        'date': trade.get('transaction_date'),
                        'message': f'Unusually large transaction: ${trade.get("amount_max", 0):,.0f}'
                    })
                    
        return anomalies


class PatternRecognizer:
    """Recognize trading patterns using clustering and classification"""
    
    def __init__(self):
        self.dbscan = DBSCAN(eps=0.5, min_samples=5)
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.pca = PCA(n_components=2)
        self.patterns = []
        
    def identify_patterns(self, trades_df: pd.DataFrame) -> List[Dict]:
        """
        Identify trading patterns in the data
        
        Args:
            trades_df: Trade data
            
        Returns:
            List of identified patterns
        """
        patterns = []
        
        # Pattern 1: Sector rotation
        sector_pattern = self._detect_sector_rotation(trades_df)
        if sector_pattern:
            patterns.append(sector_pattern)
            
        # Pattern 2: Momentum trading
        momentum_pattern = self._detect_momentum_trading(trades_df)
        if momentum_pattern:
            patterns.append(momentum_pattern)
            
        # Pattern 3: Insider coordination
        coordination_pattern = self._detect_coordination(trades_df)
        if coordination_pattern:
            patterns.append(coordination_pattern)
            
        # Pattern 4: Pre-announcement trading
        pre_announcement = self._detect_pre_announcement_trading(trades_df)
        if pre_announcement:
            patterns.append(pre_announcement)
            
        return patterns
        
    def _detect_sector_rotation(self, trades_df: pd.DataFrame) -> Optional[Dict]:
        """Detect sector rotation patterns"""
        
        if 'sector' not in trades_df or 'transaction_date' not in trades_df:
            return None
            
        trades_df['date'] = pd.to_datetime(trades_df['transaction_date'])
        
        # Analyze sector trends over time
        sector_trends = trades_df.groupby([
            pd.Grouper(key='date', freq='W'),
            'sector'
        ]).size().unstack(fill_value=0)
        
        if len(sector_trends) > 4:  # Need at least 4 weeks of data
            # Calculate week-over-week changes
            sector_changes = sector_trends.diff()
            
            # Identify sectors with increasing activity
            trending_sectors = []
            for sector in sector_changes.columns:
                recent_trend = sector_changes[sector].tail(3).mean()
                if recent_trend > 2:  # More than 2 additional trades per week
                    trending_sectors.append({
                        'sector': sector,
                        'trend': float(recent_trend),
                        'direction': 'increasing'
                    })
                    
            if trending_sectors:
                return {
                    'pattern': 'sector_rotation',
                    'description': 'Politicians rotating into specific sectors',
                    'trending_sectors': trending_sectors,
                    'confidence': 0.75,
                    'timestamp': datetime.now().isoformat()
                }
                
        return None
        
    def _detect_momentum_trading(self, trades_df: pd.DataFrame) -> Optional[Dict]:
        """Detect momentum trading patterns"""
        
        if 'return_pct' not in trades_df:
            return None
            
        # Find stocks with consistent positive returns
        stock_performance = trades_df.groupby('ticker')['return_pct'].agg(['mean', 'count'])
        
        # Identify momentum stocks (positive returns and multiple trades)
        momentum_stocks = stock_performance[
            (stock_performance['mean'] > 5) & 
            (stock_performance['count'] > 3)
        ]
        
        if len(momentum_stocks) > 0:
            top_momentum = momentum_stocks.nlargest(5, 'mean')
            
            return {
                'pattern': 'momentum_trading',
                'description': 'Politicians following momentum in certain stocks',
                'momentum_stocks': [
                    {
                        'ticker': ticker,
                        'avg_return': float(row['mean']),
                        'trade_count': int(row['count'])
                    }
                    for ticker, row in top_momentum.iterrows()
                ],
                'confidence': 0.65,
                'timestamp': datetime.now().isoformat()
            }
            
        return None
        
    def _detect_coordination(self, trades_df: pd.DataFrame) -> Optional[Dict]:
        """Detect potential coordination between politicians"""
        
        if 'transaction_date' not in trades_df:
            return None
            
        trades_df['date'] = pd.to_datetime(trades_df['transaction_date'])
        
        # Look for multiple politicians trading same stock on same day
        same_day_trades = trades_df.groupby(['date', 'ticker'])['politician_name'].apply(list)
        
        coordinated_trades = []
        for (date, ticker), politicians in same_day_trades.items():
            if len(set(politicians)) > 2:  # More than 2 different politicians
                coordinated_trades.append({
                    'date': date.isoformat(),
                    'ticker': ticker,
                    'politicians': list(set(politicians)),
                    'count': len(set(politicians))
                })
                
        if coordinated_trades:
            return {
                'pattern': 'potential_coordination',
                'description': 'Multiple politicians trading same stocks on same days',
                'instances': coordinated_trades[:5],  # Top 5 instances
                'total_instances': len(coordinated_trades),
                'confidence': 0.55,
                'timestamp': datetime.now().isoformat()
            }
            
        return None
        
    def _detect_pre_announcement_trading(self, trades_df: pd.DataFrame) -> Optional[Dict]:
        """Detect trading before major announcements"""
        
        # This would require news/earnings data integration
        # For now, detect unusual clustering before specific dates
        
        if 'transaction_date' not in trades_df:
            return None
            
        trades_df['date'] = pd.to_datetime(trades_df['transaction_date'])
        
        # Look for spikes in trading activity
        daily_volume = trades_df.groupby('date').size()
        
        if len(daily_volume) > 10:
            mean_volume = daily_volume.mean()
            std_volume = daily_volume.std()
            
            # Find days with unusual volume
            spike_days = daily_volume[daily_volume > mean_volume + 2 * std_volume]
            
            if len(spike_days) > 0:
                return {
                    'pattern': 'volume_spikes',
                    'description': 'Unusual trading volume on specific days',
                    'spike_days': [
                        {
                            'date': date.isoformat(),
                            'trade_count': int(count),
                            'deviation': float((count - mean_volume) / std_volume)
                        }
                        for date, count in spike_days.head(5).items()
                    ],
                    'confidence': 0.60,
                    'timestamp': datetime.now().isoformat()
                }
                
        return None


class PredictiveModel:
    """Predict future trading behavior and performance"""
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.feature_columns = []
        self.is_trained = False
        
    def prepare_training_data(self, trades_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data for predictive model
        
        Args:
            trades_df: Historical trades data
            
        Returns:
            Feature matrix and target vector
        """
        # Create features
        features = []
        targets = []
        
        # Group by politician and calculate features
        for politician in trades_df['politician_name'].unique():
            politician_trades = trades_df[trades_df['politician_name'] == politician]
            
            if len(politician_trades) > 5:  # Need enough data
                # Features
                feature_vector = [
                    len(politician_trades),
                    politician_trades['amount_max'].mean() if 'amount_max' in politician_trades else 0,
                    len(politician_trades['ticker'].unique()) if 'ticker' in politician_trades else 0,
                    (politician_trades['transaction_type'] == 'Purchase').mean() if 'transaction_type' in politician_trades else 0.5,
                    politician_trades['return_pct'].std() if 'return_pct' in politician_trades else 0,
                ]
                
                # Target: Will this politician be profitable? (binary)
                avg_return = politician_trades['return_pct'].mean() if 'return_pct' in politician_trades else 0
                target = 1 if avg_return > 0 else 0
                
                features.append(feature_vector)
                targets.append(target)
                
        return np.array(features), np.array(targets)
        
    def train(self, trades_df: pd.DataFrame):
        """
        Train predictive model
        
        Args:
            trades_df: Historical trades data
        """
        logger.info("Training predictive model")
        
        X, y = self.prepare_training_data(trades_df)
        
        if len(X) > 10:  # Need minimum samples
            self.model.fit(X, y)
            self.is_trained = True
            logger.info(f"Model trained on {len(X)} samples")
        else:
            logger.warning("Insufficient data for training")
            
    def predict_performance(self, politician_name: str, trades_df: pd.DataFrame) -> Dict:
        """
        Predict future performance for a politician
        
        Args:
            politician_name: Name of politician
            trades_df: Recent trades data
            
        Returns:
            Prediction results
        """
        if not self.is_trained:
            return {
                'politician': politician_name,
                'prediction': 'unknown',
                'confidence': 0,
                'message': 'Model not trained'
            }
            
        politician_trades = trades_df[trades_df['politician_name'] == politician_name]
        
        if len(politician_trades) == 0:
            return {
                'politician': politician_name,
                'prediction': 'unknown',
                'confidence': 0,
                'message': 'No trading history'
            }
            
        # Prepare features
        features = [[
            len(politician_trades),
            politician_trades['amount_max'].mean() if 'amount_max' in politician_trades else 0,
            len(politician_trades['ticker'].unique()) if 'ticker' in politician_trades else 0,
            (politician_trades['transaction_type'] == 'Purchase').mean() if 'transaction_type' in politician_trades else 0.5,
            politician_trades['return_pct'].std() if 'return_pct' in politician_trades else 0,
        ]]
        
        # Make prediction
        prediction_proba = self.model.predict_proba(features)[0]
        prediction = self.model.predict(features)[0]
        
        return {
            'politician': politician_name,
            'prediction': 'profitable' if prediction == 1 else 'unprofitable',
            'confidence': float(max(prediction_proba)),
            'probability_profitable': float(prediction_proba[1]),
            'recent_performance': {
                'avg_return': float(politician_trades['return_pct'].mean()) if 'return_pct' in politician_trades else 0,
                'trade_count': len(politician_trades),
                'favorite_sector': politician_trades['sector'].mode()[0] if 'sector' in politician_trades and len(politician_trades['sector'].mode()) > 0 else 'Unknown'
            }
        }


# Main analytics engine
class MLAnalyticsEngine:
    """Main engine combining all ML models"""
    
    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.pattern_recognizer = PatternRecognizer()
        self.predictive_model = PredictiveModel()
        
    def analyze(self, trades_df: pd.DataFrame) -> Dict:
        """
        Run complete ML analysis on trades data
        
        Args:
            trades_df: Trade data
            
        Returns:
            Complete analysis results
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'data_points': len(trades_df),
            'anomalies': [],
            'patterns': [],
            'predictions': []
        }
        
        # Detect anomalies
        try:
            results['anomalies'] = self.anomaly_detector.detect_anomalies(trades_df)
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            
        # Recognize patterns
        try:
            results['patterns'] = self.pattern_recognizer.identify_patterns(trades_df)
        except Exception as e:
            logger.error(f"Error in pattern recognition: {e}")
            
        # Generate predictions for top traders
        try:
            if 'politician_name' in trades_df:
                top_traders = trades_df['politician_name'].value_counts().head(5).index
                
                for politician in top_traders:
                    prediction = self.predictive_model.predict_performance(politician, trades_df)
                    results['predictions'].append(prediction)
        except Exception as e:
            logger.error(f"Error in predictions: {e}")
            
        return results


# Example usage
if __name__ == "__main__":
    # Load sample data
    sample_data = pd.DataFrame({
        'politician_name': ['John Doe'] * 10 + ['Jane Smith'] * 8 + ['Bob Johnson'] * 12,
        'ticker': ['AAPL', 'GOOGL', 'MSFT'] * 10,
        'transaction_type': ['Purchase', 'Sale'] * 15,
        'amount_max': np.random.uniform(1000, 100000, 30),
        'return_pct': np.random.uniform(-10, 20, 30),
        'sector': ['Technology'] * 15 + ['Healthcare'] * 15,
        'transaction_date': pd.date_range(start='2024-01-01', periods=30)
    })
    
    # Initialize engine
    engine = MLAnalyticsEngine()
    
    # Run analysis
    results = engine.analyze(sample_data)
    
    print("ML Analysis Results:")
    print(f"Anomalies detected: {len(results['anomalies'])}")
    print(f"Patterns identified: {len(results['patterns'])}")
    print(f"Predictions generated: {len(results['predictions'])}")