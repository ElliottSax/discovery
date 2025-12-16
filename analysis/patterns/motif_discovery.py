"""
Motif Discovery for Politician Trading Patterns

Discovers recurring motifs (templates) in politician trading behavior
and builds a library of common patterns for classification and prediction.

Key Features:
- Automatic pattern template extraction
- Cross-politician motif matching
- Pattern evolution tracking
- Template-based prediction

Author: Claude
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from analysis.patterns.matrix_profile import MatrixProfileAnalyzer

logger = logging.getLogger(__name__)


class MotifLibrary:
    """
    Build and maintain a library of discovered trading motifs

    Motifs are recurring patterns that can be used for:
    - Pattern classification (which template does this match?)
    - Prediction (what happens after this pattern?)
    - Anomaly detection (patterns that don't match any template)
    """

    def __init__(self):
        self.motifs = []
        self.politician_motifs = defaultdict(list)
        self.cross_politician_motifs = []

    def add_motif(
        self,
        motif: Dict,
        politician: str = None,
        metadata: Dict = None
    ):
        """Add a motif to the library"""
        motif_entry = {
            **motif,
            'politician': politician,
            'discovered_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

        self.motifs.append(motif_entry)

        if politician:
            self.politician_motifs[politician].append(motif_entry)

    def find_similar_motifs(
        self,
        pattern: np.ndarray,
        similarity_threshold: float = 0.8
    ) -> List[Dict]:
        """
        Find motifs in library similar to given pattern

        Args:
            pattern: Pattern to match
            similarity_threshold: Minimum similarity (0-1)

        Returns:
            List of matching motifs with similarity scores
        """
        matches = []

        for motif in self.motifs:
            # Get motif pattern
            if 'pattern_1' in motif:
                motif_pattern = np.array(motif['pattern_1'])
            elif 'pattern' in motif:
                motif_pattern = np.array(motif['pattern'])
            else:
                continue

            # Compute similarity
            similarity = self._compute_similarity(pattern, motif_pattern)

            if similarity >= similarity_threshold:
                matches.append({
                    **motif,
                    'similarity_to_query': similarity
                })

        # Sort by similarity
        matches.sort(key=lambda x: x['similarity_to_query'], reverse=True)

        return matches

    def _compute_similarity(
        self,
        pattern1: np.ndarray,
        pattern2: np.ndarray
    ) -> float:
        """
        Compute normalized similarity between two patterns

        Uses normalized Euclidean distance
        """
        # Normalize patterns
        p1 = (pattern1 - np.mean(pattern1)) / (np.std(pattern1) + 1e-8)
        p2 = (pattern2 - np.mean(pattern2)) / (np.std(pattern2) + 1e-8)

        # Handle different lengths
        if len(p1) != len(p2):
            min_len = min(len(p1), len(p2))
            p1 = p1[:min_len]
            p2 = p2[:min_len]

        # Euclidean distance
        dist = np.sqrt(np.sum((p1 - p2) ** 2))

        # Convert to similarity (0-1)
        similarity = 1.0 / (1.0 + dist)

        return similarity

    def get_statistics(self) -> Dict:
        """Get library statistics"""
        return {
            'total_motifs': len(self.motifs),
            'politicians_covered': len(self.politician_motifs),
            'motifs_per_politician': {
                pol: len(motifs)
                for pol, motifs in self.politician_motifs.items()
            },
            'cross_politician_motifs': len(self.cross_politician_motifs)
        }


class MotifDiscoveryEngine:
    """
    Discover and analyze recurring motifs in politician trading data

    Performs:
    1. Individual politician motif discovery
    2. Cross-politician pattern matching
    3. Pattern template extraction
    4. Motif-based prediction
    """

    def __init__(
        self,
        window_sizes: List[int] = [7, 14, 30, 60, 90],
        k_motifs: int = 5
    ):
        """
        Initialize motif discovery engine

        Args:
            window_sizes: Multiple time scales to analyze (days)
            k_motifs: Number of top motifs to extract per scale
        """
        self.window_sizes = window_sizes
        self.k_motifs = k_motifs
        self.motif_library = MotifLibrary()

    def discover_all_motifs(
        self,
        trades: List[Dict],
        by_politician: bool = True,
        by_ticker: bool = True
    ) -> Dict:
        """
        Comprehensive motif discovery across all dimensions

        Args:
            trades: All politician trades
            by_politician: Discover motifs per politician
            by_ticker: Discover motifs per ticker

        Returns:
            {
                'politician_motifs': {...},
                'ticker_motifs': {...},
                'cross_politician_motifs': [...],
                'motif_library': MotifLibrary,
                'summary': {...}
            }
        """
        results = {
            'politician_motifs': {},
            'ticker_motifs': {},
            'cross_politician_motifs': [],
            'summary': {}
        }

        # Group trades
        if by_politician:
            trades_by_pol = defaultdict(list)
            for trade in trades:
                pol = trade.get('politician_name', trade.get('politician', 'Unknown'))
                trades_by_pol[pol].append(trade)

            # Discover motifs for each politician
            for politician, pol_trades in trades_by_pol.items():
                logger.info(f"Discovering motifs for {politician} ({len(pol_trades)} trades)")

                pol_motifs = self._discover_politician_motifs(politician, pol_trades)
                results['politician_motifs'][politician] = pol_motifs

                # Add to library
                for motif in pol_motifs.get('motifs', []):
                    self.motif_library.add_motif(motif, politician=politician)

        if by_ticker:
            trades_by_ticker = defaultdict(list)
            for trade in trades:
                ticker = trade.get('ticker', '').upper()
                if ticker:
                    trades_by_ticker[ticker].append(trade)

            # Discover motifs for each ticker
            for ticker, ticker_trades in trades_by_ticker.items():
                if len(ticker_trades) < 10:
                    continue

                logger.info(f"Discovering motifs for {ticker} ({len(ticker_trades)} trades)")

                ticker_motifs = self._discover_ticker_motifs(ticker, ticker_trades)
                results['ticker_motifs'][ticker] = ticker_motifs

        # Find cross-politician motifs (patterns shared across politicians)
        results['cross_politician_motifs'] = self._find_cross_politician_motifs(
            results['politician_motifs']
        )

        # Generate summary
        results['summary'] = {
            'total_motifs_discovered': len(self.motif_library.motifs),
            'politicians_analyzed': len(results['politician_motifs']),
            'tickers_analyzed': len(results['ticker_motifs']),
            'cross_politician_patterns': len(results['cross_politician_motifs']),
            'motif_library_stats': self.motif_library.get_statistics()
        }

        results['motif_library'] = self.motif_library

        return results

    def _discover_politician_motifs(
        self,
        politician: str,
        trades: List[Dict]
    ) -> Dict:
        """Discover motifs in a single politician's trading history"""

        # Create time series from trades
        time_series = self._trades_to_time_series(trades)

        if time_series is None or len(time_series) < 30:
            return {
                'politician': politician,
                'status': 'insufficient_data',
                'num_trades': len(trades)
            }

        all_motifs = []
        all_discords = []

        # Analyze at multiple time scales
        for window_size in self.window_sizes:
            if len(time_series) < 2 * window_size:
                continue

            try:
                analyzer = MatrixProfileAnalyzer(window_size=window_size)

                # Discover motifs
                motif_result = analyzer.discover_motifs(
                    time_series,
                    k_motifs=self.k_motifs
                )

                for motif in motif_result['motifs']:
                    motif['time_scale'] = window_size
                    motif['politician'] = politician
                    all_motifs.append(motif)

                # Discover discords (anomalies)
                discord_result = analyzer.find_discords(
                    time_series,
                    k_discords=3
                )

                for discord in discord_result['discords']:
                    discord['time_scale'] = window_size
                    discord['politician'] = politician
                    all_discords.append(discord)

            except Exception as e:
                logger.warning(f"Error discovering motifs at window={window_size}: {e}")
                continue

        return {
            'politician': politician,
            'num_trades': len(trades),
            'motifs': all_motifs,
            'num_motifs': len(all_motifs),
            'discords': all_discords,
            'num_discords': len(all_discords),
            'time_scales_analyzed': [w for w in self.window_sizes if len(time_series) >= 2 * w]
        }

    def _discover_ticker_motifs(
        self,
        ticker: str,
        trades: List[Dict]
    ) -> Dict:
        """Discover motifs in trading activity for a specific ticker"""

        # Create time series from trades (number of trades per day)
        time_series = self._trades_to_time_series(trades, group_by_date=True)

        if time_series is None or len(time_series) < 30:
            return {
                'ticker': ticker,
                'status': 'insufficient_data',
                'num_trades': len(trades)
            }

        # Use smaller window sizes for ticker analysis
        ticker_windows = [w for w in self.window_sizes if w <= 30]

        all_motifs = []

        for window_size in ticker_windows:
            if len(time_series) < 2 * window_size:
                continue

            try:
                analyzer = MatrixProfileAnalyzer(window_size=window_size)

                motif_result = analyzer.discover_motifs(
                    time_series,
                    k_motifs=self.k_motifs
                )

                for motif in motif_result['motifs']:
                    motif['time_scale'] = window_size
                    motif['ticker'] = ticker
                    all_motifs.append(motif)

            except Exception as e:
                logger.warning(f"Error discovering ticker motifs: {e}")
                continue

        return {
            'ticker': ticker,
            'num_trades': len(trades),
            'motifs': all_motifs,
            'num_motifs': len(all_motifs)
        }

    def _find_cross_politician_motifs(
        self,
        politician_motifs: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Find motifs that appear across multiple politicians

        These are potentially coordinated patterns
        """
        cross_motifs = []

        # Get all politician names
        politicians = list(politician_motifs.keys())

        if len(politicians) < 2:
            return []

        # Compare motifs between politicians
        for i in range(len(politicians)):
            for j in range(i + 1, len(politicians)):
                pol1 = politicians[i]
                pol2 = politicians[j]

                motifs1 = politician_motifs[pol1].get('motifs', [])
                motifs2 = politician_motifs[pol2].get('motifs', [])

                # Find similar motifs
                for m1 in motifs1:
                    for m2 in motifs2:
                        # Must be same time scale
                        if m1.get('time_scale') != m2.get('time_scale'):
                            continue

                        # Compute similarity
                        pattern1 = np.array(m1.get('pattern_1', []))
                        pattern2 = np.array(m2.get('pattern_1', []))

                        if len(pattern1) != len(pattern2):
                            continue

                        similarity = self.motif_library._compute_similarity(pattern1, pattern2)

                        if similarity >= 0.7:  # 70% similarity threshold
                            cross_motifs.append({
                                'politician_1': pol1,
                                'politician_2': pol2,
                                'similarity': similarity,
                                'time_scale': m1.get('time_scale'),
                                'pattern': pattern1.tolist(),
                                'motif_1_location': m1.get('location_1'),
                                'motif_2_location': m2.get('location_1'),
                                'significance': 'HIGH' if similarity > 0.9 else 'MEDIUM'
                            })

        return cross_motifs

    def _trades_to_time_series(
        self,
        trades: List[Dict],
        group_by_date: bool = False
    ) -> Optional[pd.Series]:
        """
        Convert trades to time series for motif discovery

        Args:
            trades: List of trades
            group_by_date: If True, count trades per day. If False, use trade amounts

        Returns:
            Time series (pandas Series) or None if insufficient data
        """
        if not trades:
            return None

        # Sort by date
        sorted_trades = sorted(
            trades,
            key=lambda x: x.get('transaction_date', x.get('date', '1970-01-01'))
        )

        # Extract dates and values
        dates = []
        values = []

        for trade in sorted_trades:
            date_str = trade.get('transaction_date', trade.get('date'))
            if not date_str:
                continue

            try:
                if isinstance(date_str, str):
                    date = pd.to_datetime(date_str)
                else:
                    date = pd.to_datetime(date_str)

                dates.append(date)

                if group_by_date:
                    values.append(1)  # Count
                else:
                    # Use average of amount range
                    amt_min = trade.get('amount_min', 0)
                    amt_max = trade.get('amount_max', 0)
                    if amt_min and amt_max:
                        values.append((amt_min + amt_max) / 2)
                    else:
                        values.append(1)

            except Exception as e:
                logger.debug(f"Error parsing date {date_str}: {e}")
                continue

        if not dates:
            return None

        # Create series
        if group_by_date:
            # Aggregate by date (count trades per day)
            df = pd.DataFrame({'date': dates, 'value': values})
            df = df.groupby('date').sum()
            time_series = df['value']
        else:
            time_series = pd.Series(values, index=dates)

        # Fill missing dates with 0
        full_range = pd.date_range(start=time_series.index.min(), end=time_series.index.max(), freq='D')
        time_series = time_series.reindex(full_range, fill_value=0)

        return time_series


__all__ = ['MotifLibrary', 'MotifDiscoveryEngine']
