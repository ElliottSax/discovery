"""
Multi-Politician Correlation Analyzer

Analyzes correlations and synchronized patterns across multiple politicians.
Detects coordinated trading, party-based patterns, and network effects.

Key Features:
- Cycle correlation analysis
- Regime synchronization detection
- Network graph generation
- Party-based clustering
- Coordinated trading detection

Author: Claude
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from scipy.cluster import hierarchy
import networkx as nx
import logging

logger = logging.getLogger(__name__)


@dataclass
class CorrelationResult:
    """Result of correlation analysis between two politicians"""
    politician1_id: str
    politician2_id: str
    correlation: float  # -1 to 1
    p_value: float  # Statistical significance
    shared_days: int  # Number of overlapping trading days
    lag: int  # Optimal time lag in days
    interpretation: str  # Human-readable meaning


@dataclass
class ClusterInfo:
    """Information about a cluster of politicians"""
    cluster_id: int
    politicians: List[str]
    avg_correlation: float
    common_characteristics: Dict[str, any]


@dataclass
class NetworkMetrics:
    """Network analysis metrics"""
    density: float  # How connected the network is (0-1)
    clustering_coefficient: float  # Tendency to form clusters
    average_path_length: float  # Average distance between nodes
    central_politicians: List[Tuple[str, float]]  # Most influential (name, centrality)


class CorrelationAnalyzer:
    """
    Analyze correlations and patterns across multiple politicians.
    """

    def __init__(self, significance_threshold: float = 0.05):
        """
        Initialize correlation analyzer.

        Args:
            significance_threshold: P-value threshold for significance (default: 0.05)
        """
        self.significance_threshold = significance_threshold

    def analyze_cycle_correlation(
        self,
        politician_data: Dict[str, pd.Series]
    ) -> List[CorrelationResult]:
        """
        Analyze cycle correlations across politicians.

        Args:
            politician_data: Dict mapping politician_id to trade frequency time series

        Returns:
            List of pairwise correlation results
        """
        results = []
        politicians = list(politician_data.keys())

        for i in range(len(politicians)):
            for j in range(i + 1, len(politicians)):
                pol1_id = politicians[i]
                pol2_id = politicians[j]

                result = self._calculate_correlation(
                    politician_data[pol1_id],
                    politician_data[pol2_id],
                    pol1_id,
                    pol2_id
                )

                if result:
                    results.append(result)

        return results

    def _calculate_correlation(
        self,
        series1: pd.Series,
        series2: pd.Series,
        id1: str,
        id2: str,
        max_lag: int = 30
    ) -> Optional[CorrelationResult]:
        """Calculate correlation between two time series with lag optimization"""

        # Align series to common date range
        common_index = series1.index.intersection(series2.index)

        if len(common_index) < 30:
            # Not enough overlap
            return None

        s1_aligned = series1.reindex(common_index, fill_value=0)
        s2_aligned = series2.reindex(common_index, fill_value=0)

        # Try different lags to find optimal correlation
        best_corr = 0
        best_lag = 0
        best_pval = 1.0

        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                # series2 leads series1
                s1_lagged = s1_aligned.iloc[-lag:]
                s2_lagged = s2_aligned.iloc[:lag]
            elif lag > 0:
                # series1 leads series2
                s1_lagged = s1_aligned.iloc[:-lag]
                s2_lagged = s2_aligned.iloc[lag:]
            else:
                s1_lagged = s1_aligned
                s2_lagged = s2_aligned

            if len(s1_lagged) < 20:
                continue

            # Pearson correlation
            corr, pval = stats.pearsonr(s1_lagged, s2_lagged)

            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag
                best_pval = pval

        # Interpret correlation
        interpretation = self._interpret_correlation(best_corr, best_pval, best_lag)

        return CorrelationResult(
            politician1_id=id1,
            politician2_id=id2,
            correlation=float(best_corr),
            p_value=float(best_pval),
            shared_days=len(common_index),
            lag=int(best_lag),
            interpretation=interpretation
        )

    def _interpret_correlation(self, corr: float, pval: float, lag: int) -> str:
        """Generate human-readable interpretation"""

        if pval > self.significance_threshold:
            return "No significant correlation"

        strength = ""
        if abs(corr) > 0.7:
            strength = "Strong"
        elif abs(corr) > 0.4:
            strength = "Moderate"
        else:
            strength = "Weak"

        direction = "positive" if corr > 0 else "negative"

        if lag == 0:
            lag_desc = "synchronized"
        elif lag > 0:
            lag_desc = f"politician 1 leads by {lag} days"
        else:
            lag_desc = f"politician 2 leads by {-lag} days"

        return f"{strength} {direction} correlation ({lag_desc})"

    def build_correlation_matrix(
        self,
        politician_data: Dict[str, pd.Series]
    ) -> pd.DataFrame:
        """
        Build correlation matrix for all politicians.

        Args:
            politician_data: Dict mapping politician_id to trade frequency

        Returns:
            DataFrame with pairwise correlations
        """
        politicians = list(politician_data.keys())
        n = len(politicians)

        matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i, j] = 1.0
                elif i < j:
                    result = self._calculate_correlation(
                        politician_data[politicians[i]],
                        politician_data[politicians[j]],
                        politicians[i],
                        politicians[j]
                    )
                    if result:
                        matrix[i, j] = result.correlation
                        matrix[j, i] = result.correlation

        return pd.DataFrame(
            matrix,
            index=politicians,
            columns=politicians
        )

    def detect_clusters(
        self,
        correlation_matrix: pd.DataFrame,
        min_correlation: float = 0.5,
        method: str = 'ward'
    ) -> List[ClusterInfo]:
        """
        Detect clusters of correlated politicians using hierarchical clustering.

        Args:
            correlation_matrix: Pairwise correlation matrix
            min_correlation: Minimum correlation to form clusters
            method: Clustering linkage method

        Returns:
            List of identified clusters
        """
        # Convert correlation to distance
        distance_matrix = 1 - correlation_matrix.abs()

        # Hierarchical clustering
        condensed_dist = squareform(distance_matrix.values, checks=False)
        linkage_matrix = hierarchy.linkage(condensed_dist, method=method)

        # Cut tree at threshold
        threshold = 1 - min_correlation
        cluster_labels = hierarchy.fcluster(linkage_matrix, threshold, criterion='distance')

        # Build cluster info
        clusters = []
        unique_labels = set(cluster_labels)

        for label in unique_labels:
            indices = np.where(cluster_labels == label)[0]

            if len(indices) < 2:
                # Single-member "cluster", skip
                continue

            politicians = [correlation_matrix.index[i] for i in indices]

            # Calculate average pairwise correlation within cluster
            cluster_corrs = []
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    idx1, idx2 = indices[i], indices[j]
                    cluster_corrs.append(correlation_matrix.iloc[idx1, idx2])

            avg_correlation = np.mean(cluster_corrs) if cluster_corrs else 0

            clusters.append(ClusterInfo(
                cluster_id=int(label),
                politicians=politicians,
                avg_correlation=float(avg_correlation),
                common_characteristics={}  # To be filled by caller
            ))

        return clusters

    def build_network_graph(
        self,
        correlation_matrix: pd.DataFrame,
        min_correlation: float = 0.5
    ) -> nx.Graph:
        """
        Build network graph of politician trading relationships.

        Args:
            correlation_matrix: Pairwise correlation matrix
            min_correlation: Minimum correlation to create edge

        Returns:
            NetworkX graph
        """
        G = nx.Graph()

        # Add nodes
        for politician in correlation_matrix.index:
            G.add_node(politician)

        # Add edges for significant correlations
        n = len(correlation_matrix)
        for i in range(n):
            for j in range(i + 1, n):
                corr = correlation_matrix.iloc[i, j]

                if abs(corr) >= min_correlation:
                    G.add_edge(
                        correlation_matrix.index[i],
                        correlation_matrix.index[j],
                        weight=abs(corr),
                        correlation=corr
                    )

        return G

    def calculate_network_metrics(self, G: nx.Graph) -> NetworkMetrics:
        """Calculate network analysis metrics"""

        if len(G.nodes()) == 0:
            return NetworkMetrics(
                density=0,
                clustering_coefficient=0,
                average_path_length=0,
                central_politicians=[]
            )

        # Density: how connected the network is
        density = nx.density(G)

        # Clustering coefficient: tendency to form tight groups
        clustering_coef = nx.average_clustering(G) if len(G.nodes()) > 0 else 0

        # Average path length (if connected)
        if nx.is_connected(G):
            avg_path_length = nx.average_shortest_path_length(G)
        else:
            # For disconnected graphs, calculate per component
            lengths = []
            for component in nx.connected_components(G):
                subgraph = G.subgraph(component)
                if len(subgraph) > 1:
                    lengths.append(nx.average_shortest_path_length(subgraph))
            avg_path_length = np.mean(lengths) if lengths else 0

        # Centrality: most influential politicians
        centrality = nx.eigenvector_centrality(G, max_iter=1000, weight='weight')
        central_politicians = sorted(
            centrality.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]  # Top 5

        return NetworkMetrics(
            density=float(density),
            clustering_coefficient=float(clustering_coef),
            average_path_length=float(avg_path_length),
            central_politicians=[(str(name), float(score)) for name, score in central_politicians]
        )

    def detect_coordinated_trading(
        self,
        politician_data: Dict[str, pd.Series],
        metadata: Dict[str, Dict],  # politician_id -> {party, state, etc}
        correlation_threshold: float = 0.6
    ) -> Dict[str, List[str]]:
        """
        Detect potential coordinated trading groups.

        Args:
            politician_data: Trade frequency data
            metadata: Politician metadata (party, family, etc)
            correlation_threshold: Minimum correlation

        Returns:
            Dict of group types to list of politician groups
        """
        correlations = self.analyze_cycle_correlation(politician_data)

        # Filter for significant high correlations
        significant = [
            c for c in correlations
            if abs(c.correlation) >= correlation_threshold
            and c.p_value < self.significance_threshold
        ]

        groups = {
            'family': [],
            'party': [],
            'state': [],
            'unexplained': []
        }

        for corr in significant:
            id1, id2 = corr.politician1_id, corr.politician2_id
            meta1 = metadata.get(id1, {})
            meta2 = metadata.get(id2, {})

            # Check for family relationship (same last name)
            name1 = meta1.get('name', '')
            name2 = meta2.get('name', '')

            if name1 and name2:
                lastname1 = name1.split()[-1]
                lastname2 = name2.split()[-1]

                if lastname1 == lastname2:
                    groups['family'].append((id1, id2, corr.correlation))
                    continue

            # Check for same party
            if meta1.get('party') == meta2.get('party') and meta1.get('party'):
                groups['party'].append((id1, id2, corr.correlation))
                continue

            # Check for same state
            if meta1.get('state') == meta2.get('state') and meta1.get('state'):
                groups['state'].append((id1, id2, corr.correlation))
                continue

            # No obvious explanation
            groups['unexplained'].append((id1, id2, corr.correlation))

        return groups

    def analyze_regime_synchronization(
        self,
        regime_data: Dict[str, List[int]]  # politician_id -> regime sequence
    ) -> Dict[str, float]:
        """
        Analyze how often politicians are in the same regime simultaneously.

        Args:
            regime_data: Dict mapping politician_id to list of regime labels over time

        Returns:
            Dict with synchronization metrics
        """
        if len(regime_data) < 2:
            return {'synchronization': 0.0}

        politicians = list(regime_data.keys())

        # Find common time points (all must have data)
        min_length = min(len(regimes) for regimes in regime_data.values())

        # Truncate all to same length
        aligned_regimes = {
            pol_id: regimes[:min_length]
            for pol_id, regimes in regime_data.items()
        }

        # Count simultaneous regime matches
        sync_scores = []

        for i in range(min_length):
            # Get all regimes at time i
            regimes_at_i = [aligned_regimes[pol][i] for pol in politicians]

            # Most common regime
            unique, counts = np.unique(regimes_at_i, return_counts=True)
            max_count = np.max(counts)

            # Synchronization = fraction in most common regime
            sync = max_count / len(politicians)
            sync_scores.append(sync)

        return {
            'avg_synchronization': float(np.mean(sync_scores)),
            'max_synchronization': float(np.max(sync_scores)),
            'min_synchronization': float(np.min(sync_scores)),
            'time_points': min_length
        }


class SectorAnalyzer:
    """
    Analyze sector-based trading patterns.
    """

    def __init__(self):
        self.sector_map = {
            'NVDA': 'Technology',
            'MSFT': 'Technology',
            'AAPL': 'Technology',
            'GOOGL': 'Technology',
            'META': 'Technology',
            'TSLA': 'Automotive',
            'SPY': 'ETF',
        }

    def analyze_sector_preference(
        self,
        trades_df: pd.DataFrame  # Must have 'ticker' and 'transaction_date' columns
    ) -> Dict[str, float]:
        """
        Analyze sector preferences in trading.

        Args:
            trades_df: DataFrame with trade data

        Returns:
            Dict mapping sector to frequency (0-1)
        """
        # Add sector column
        trades_df = trades_df.copy()
        trades_df['sector'] = trades_df['ticker'].map(self.sector_map)

        # Count by sector
        sector_counts = trades_df['sector'].value_counts()
        total = len(trades_df)

        return {
            sector: float(count / total)
            for sector, count in sector_counts.items()
        }

    def detect_sector_rotation(
        self,
        trades_df: pd.DataFrame,
        window_size: int = 90
    ) -> List[Dict]:
        """
        Detect sector rotation patterns over time.

        Args:
            trades_df: DataFrame with trade data
            window_size: Rolling window in days

        Returns:
            List of rotation events
        """
        trades_df = trades_df.copy()
        trades_df['sector'] = trades_df['ticker'].map(self.sector_map)

        # Sort by date
        trades_df = trades_df.sort_values('transaction_date')

        rotations = []

        for i in range(0, len(trades_df) - window_size, window_size // 2):
            window = trades_df.iloc[i:i + window_size]

            if len(window) < 5:
                continue

            sectors = window['sector'].value_counts()
            dominant = sectors.index[0] if len(sectors) > 0 else None

            if dominant:
                rotations.append({
                    'start_date': window['transaction_date'].min(),
                    'end_date': window['transaction_date'].max(),
                    'dominant_sector': dominant,
                    'concentration': float(sectors.iloc[0] / len(window))
                })

        return rotations
