"""
Temporal Network Analysis for Politician Trading Patterns

Advanced temporal network analysis methods including:
- Dynamic community detection
- Temporal motif mining
- Bursty event detection
- Network entropy analysis
- Influence propagation

Author: Claude
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TemporalMotif:
    """
    Represents a recurring temporal pattern in network structure.

    Examples:
    - A → B → C (sequential influence)
    - A ↔ B (reciprocal trading)
    - A, B, C → simultaneous (coordinated action)
    """

    def __init__(
        self,
        motif_type: str,
        participants: List[str],
        timestamps: List[datetime],
        pattern: str
    ):
        self.motif_type = motif_type
        self.participants = participants
        self.timestamps = timestamps
        self.pattern = pattern
        self.frequency = 1

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'motif_type': self.motif_type,
            'participants': self.participants,
            'timestamps': [t.isoformat() for t in self.timestamps],
            'pattern': self.pattern,
            'frequency': self.frequency
        }


class BurstyEventDetector:
    """
    Detects bursty events in temporal networks.

    Bursty events are sudden increases in network activity that
    deviate from normal patterns.
    """

    def __init__(self, baseline_window: int = 30):
        """
        Initialize detector.

        Args:
            baseline_window: Days for baseline calculation
        """
        self.baseline_window = baseline_window

    def detect_bursts(
        self,
        events: List[Tuple[datetime, str, str]],
        min_burst_size: int = 5
    ) -> List[Dict]:
        """
        Detect bursty periods in network events.

        Args:
            events: List of (timestamp, source, target) tuples
            min_burst_size: Minimum events for burst

        Returns:
            List of detected bursts
        """
        if len(events) < 10:
            return []

        # Sort events by time
        sorted_events = sorted(events, key=lambda x: x[0])

        # Count events per day
        daily_counts = defaultdict(int)
        for timestamp, _, _ in sorted_events:
            date = timestamp.date()
            daily_counts[date] += 1

        # Convert to series
        dates = sorted(daily_counts.keys())
        counts = [daily_counts[d] for d in dates]

        # Detect bursts using z-score
        bursts = []
        window = self.baseline_window

        for i in range(window, len(counts)):
            # Baseline (previous window)
            baseline = counts[i - window:i]
            baseline_mean = np.mean(baseline)
            baseline_std = np.std(baseline)

            if baseline_std == 0:
                continue

            # Current value
            current = counts[i]
            z_score = (current - baseline_mean) / baseline_std

            # Burst detected
            if z_score > 2.0 and current >= min_burst_size:
                bursts.append({
                    'date': dates[i].isoformat(),
                    'event_count': current,
                    'baseline_mean': float(baseline_mean),
                    'z_score': float(z_score),
                    'severity': 'HIGH' if z_score > 3.0 else 'MEDIUM'
                })

        return bursts


class NetworkEntropyAnalyzer:
    """
    Analyzes network entropy to detect structural changes.

    Network entropy measures uncertainty in network structure.
    Low entropy = regular structure (potentially coordinated)
    High entropy = random structure
    """

    def compute_degree_entropy(self, degrees: List[int]) -> float:
        """
        Compute entropy of degree distribution.

        Args:
            degrees: List of node degrees

        Returns:
            Entropy value
        """
        if not degrees:
            return 0.0

        # Degree distribution
        degree_counts = Counter(degrees)
        total = sum(degree_counts.values())

        # Compute probabilities
        probabilities = [count / total for count in degree_counts.values()]

        # Shannon entropy
        entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)

        return entropy

    def compute_temporal_entropy(
        self,
        snapshots: List[Dict[str, Any]]
    ) -> List[Dict]:
        """
        Compute entropy for each network snapshot.

        Args:
            snapshots: Network snapshots over time

        Returns:
            Entropy evolution over time
        """
        entropy_evolution = []

        for snapshot in snapshots:
            network = snapshot['network']

            # Extract degrees
            degree_count = defaultdict(int)
            for edge in network['edges']:
                degree_count[edge['source']] += 1
                degree_count[edge['target']] += 1

            degrees = list(degree_count.values())

            # Compute entropy
            entropy = self.compute_degree_entropy(degrees)

            entropy_evolution.append({
                'timestamp': snapshot['timestamp'],
                'entropy': entropy,
                'n_nodes': len(network['nodes']),
                'n_edges': len(network['edges'])
            })

        return entropy_evolution

    def detect_entropy_anomalies(
        self,
        entropy_evolution: List[Dict],
        threshold_std: float = 2.0
    ) -> List[Dict]:
        """
        Detect sudden changes in network entropy.

        Args:
            entropy_evolution: Entropy over time
            threshold_std: Threshold for anomaly

        Returns:
            List of entropy anomalies
        """
        if len(entropy_evolution) < 3:
            return []

        entropies = [e['entropy'] for e in entropy_evolution]
        mean_entropy = np.mean(entropies)
        std_entropy = np.std(entropies)

        anomalies = []

        if std_entropy == 0:
            return []

        for i, ent_data in enumerate(entropy_evolution):
            entropy = ent_data['entropy']
            z_score = abs(entropy - mean_entropy) / std_entropy

            if z_score > threshold_std:
                if entropy < mean_entropy:
                    interpretation = "Unusually low entropy - highly regular structure (potential coordination)"
                else:
                    interpretation = "Unusually high entropy - chaotic structure"

                anomalies.append({
                    'timestamp': ent_data['timestamp'],
                    'entropy': entropy,
                    'expected_entropy': mean_entropy,
                    'z_score': float(z_score),
                    'interpretation': interpretation
                })

        return anomalies


class InfluencePropagationAnalyzer:
    """
    Analyzes how trading behavior propagates through network.

    Identifies:
    - Influence leaders (who others follow)
    - Influence cascades (chain reactions)
    - Propagation speed
    """

    def detect_influence_cascades(
        self,
        trades: List[Dict[str, Any]],
        network_edges: List[Tuple[str, str]],
        time_window_days: int = 7
    ) -> List[Dict]:
        """
        Detect influence cascades in trading behavior.

        A cascade occurs when one politician trades, followed by
        connected politicians trading the same stock shortly after.

        Args:
            trades: All trades
            network_edges: Network connections
            time_window_days: Window for cascade detection

        Returns:
            List of detected cascades
        """
        # Build adjacency list
        adjacency = defaultdict(set)
        for source, target in network_edges:
            adjacency[source].add(target)
            adjacency[target].add(source)

        # Group trades by stock
        trades_by_stock = defaultdict(list)
        for trade in trades:
            ticker = trade.get('ticker', '').upper()
            if ticker:
                trades_by_stock[ticker].append(trade)

        cascades = []

        # For each stock, look for cascade patterns
        for ticker, stock_trades in trades_by_stock.items():
            if len(stock_trades) < 2:
                continue

            # Sort by date
            sorted_trades = sorted(
                stock_trades,
                key=lambda x: x.get('transaction_date', x.get('date', ''))
            )

            # Look for cascade patterns
            for i, seed_trade in enumerate(sorted_trades[:-1]):
                seed_pol = seed_trade.get('politician_name', seed_trade.get('politician', ''))
                seed_date = pd.to_datetime(seed_trade.get('transaction_date', seed_trade.get('date')))

                if not seed_pol or pd.isna(seed_date):
                    continue

                # Find connected politicians who traded shortly after
                cascade_members = [seed_pol]
                cascade_dates = [seed_date]

                for follow_trade in sorted_trades[i + 1:]:
                    follow_pol = follow_trade.get('politician_name', follow_trade.get('politician', ''))
                    follow_date = pd.to_datetime(follow_trade.get('transaction_date', follow_trade.get('date')))

                    if pd.isna(follow_date):
                        continue

                    # Check if within time window
                    days_diff = (follow_date - seed_date).days

                    if days_diff > time_window_days:
                        break  # Too far in future

                    # Check if connected
                    if follow_pol in adjacency[seed_pol]:
                        cascade_members.append(follow_pol)
                        cascade_dates.append(follow_date)

                # If cascade found
                if len(cascade_members) >= 2:
                    cascades.append({
                        'ticker': ticker,
                        'seed_politician': seed_pol,
                        'seed_date': seed_date.isoformat(),
                        'cascade_size': len(cascade_members),
                        'participants': cascade_members,
                        'propagation_days': (cascade_dates[-1] - cascade_dates[0]).days,
                        'interpretation': f"{seed_pol} → {len(cascade_members)-1} followers on {ticker}"
                    })

        # Sort by cascade size
        cascades.sort(key=lambda x: x['cascade_size'], reverse=True)

        return cascades

    def compute_influence_scores(
        self,
        cascades: List[Dict]
    ) -> Dict[str, float]:
        """
        Compute influence score for each politician.

        Politicians who frequently initiate cascades have high scores.

        Args:
            cascades: Detected cascades

        Returns:
            {politician: influence_score}
        """
        influence_scores = defaultdict(float)

        for cascade in cascades:
            seed = cascade['seed_politician']
            cascade_size = cascade['cascade_size']

            # Score = sum of cascade sizes they initiated
            influence_scores[seed] += cascade_size

        # Normalize
        if influence_scores:
            max_score = max(influence_scores.values())
            for pol in influence_scores:
                influence_scores[pol] /= max_score

        return dict(influence_scores)


class DynamicCommunityDetector:
    """
    Detects evolving communities in temporal networks.

    Uses incremental community detection to track how communities
    form, grow, merge, split, and dissolve over time.
    """

    def __init__(self):
        self.communities_over_time = []

    def detect_communities_incremental(
        self,
        snapshots: List[Dict[str, Any]]
    ) -> List[Dict]:
        """
        Incrementally detect communities across snapshots.

        Args:
            snapshots: Network snapshots

        Returns:
            Community evolution timeline
        """
        community_timeline = []

        for snapshot in snapshots:
            timestamp = snapshot['timestamp']
            network = snapshot['network']

            # Simple community detection based on edge weights
            communities = self._label_propagation(network)

            community_timeline.append({
                'timestamp': timestamp,
                'communities': communities,
                'n_communities': len(communities)
            })

        self.communities_over_time = community_timeline
        return community_timeline

    def _label_propagation(
        self,
        network: Dict[str, Any],
        max_iterations: int = 10
    ) -> List[Dict]:
        """
        Simple label propagation for community detection.

        Args:
            network: Network data
            max_iterations: Maximum iterations

        Returns:
            List of detected communities
        """
        # Build adjacency with weights
        adjacency = defaultdict(lambda: defaultdict(float))

        for edge in network['edges']:
            source = edge['source']
            target = edge['target']
            weight = edge.get('weight', 1.0)

            adjacency[source][target] = weight
            adjacency[target][source] = weight

        if not adjacency:
            return []

        # Initialize: each node has unique label
        labels = {node: i for i, node in enumerate(adjacency.keys())}

        # Iterate
        for _ in range(max_iterations):
            # Random order
            nodes = list(adjacency.keys())
            np.random.shuffle(nodes)

            changed = False

            for node in nodes:
                # Count neighbor labels weighted by edge weight
                neighbor_labels = defaultdict(float)

                for neighbor, weight in adjacency[node].items():
                    neighbor_labels[labels[neighbor]] += weight

                if neighbor_labels:
                    # Adopt most common neighbor label
                    best_label = max(neighbor_labels, key=neighbor_labels.get)

                    if labels[node] != best_label:
                        labels[node] = best_label
                        changed = True

            if not changed:
                break

        # Group nodes by label
        communities = defaultdict(list)
        for node, label in labels.items():
            communities[label].append(node)

        # Convert to list of community dicts
        community_list = [
            {
                'id': f"community_{cid}",
                'members': members,
                'size': len(members)
            }
            for cid, members in communities.items()
        ]

        return community_list


def analyze_temporal_network(
    trades: List[Dict],
    discoveries: List[Dict],
    time_window_days: int = 30
) -> Dict:
    """
    Comprehensive temporal network analysis.

    Args:
        trades: Politician trades
        discoveries: Pattern discoveries
        time_window_days: Time window for snapshots

    Returns:
        Complete temporal network analysis
    """
    from services.network_analyzer import TemporalNetworkAnalyzer

    # Create temporal analyzer
    analyzer = TemporalNetworkAnalyzer()

    # Create snapshots
    snapshots = analyzer.create_temporal_snapshots(discoveries, time_window_days)

    if not snapshots:
        return {'status': 'insufficient_data'}

    # Bursty event detection
    burst_detector = BurstyEventDetector()

    # Extract events
    events = []
    for disc in discoveries:
        timestamp = disc.get('timestamp', disc.get('discovered_at'))
        if timestamp:
            try:
                ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

                finding = disc.get('finding', {})
                data = finding.get('data', {})

                source = data.get('politician_1', data.get('politician', ''))
                target = data.get('politician_2', '')

                if source:
                    events.append((ts, source, target if target else source))
            except:
                continue

    bursts = burst_detector.detect_bursts(events)

    # Entropy analysis
    entropy_analyzer = NetworkEntropyAnalyzer()
    entropy_evolution = entropy_analyzer.compute_temporal_entropy(snapshots)
    entropy_anomalies = entropy_analyzer.detect_entropy_anomalies(entropy_evolution)

    # Influence propagation
    influence_analyzer = InfluencePropagationAnalyzer()

    # Build network edges from discoveries
    network_edges = []
    for disc in discoveries:
        finding = disc.get('finding', {})
        data = finding.get('data', {})

        pol1 = data.get('politician_1', '')
        pol2 = data.get('politician_2', '')

        if pol1 and pol2:
            network_edges.append((pol1, pol2))

    cascades = influence_analyzer.detect_influence_cascades(trades, network_edges)
    influence_scores = influence_analyzer.compute_influence_scores(cascades)

    # Community detection
    community_detector = DynamicCommunityDetector()
    community_timeline = community_detector.detect_communities_incremental(snapshots)

    # Summary
    return {
        'n_snapshots': len(snapshots),
        'time_span': {
            'start': snapshots[0]['timestamp'],
            'end': snapshots[-1]['timestamp']
        },
        'bursty_events': {
            'n_bursts': len(bursts),
            'bursts': bursts[:10]  # Top 10
        },
        'entropy_analysis': {
            'evolution': entropy_evolution,
            'anomalies': entropy_anomalies,
            'n_anomalies': len(entropy_anomalies)
        },
        'influence_propagation': {
            'n_cascades': len(cascades),
            'cascades': cascades[:10],  # Top 10
            'top_influencers': sorted(
                [{'politician': p, 'score': s} for p, s in influence_scores.items()],
                key=lambda x: x['score'],
                reverse=True
            )[:10]
        },
        'community_evolution': {
            'timeline': community_timeline,
            'n_final_communities': community_timeline[-1]['n_communities'] if community_timeline else 0
        },
        'network_evolution_summary': analyzer.get_evolution_summary()
    }


__all__ = [
    'TemporalMotif',
    'BurstyEventDetector',
    'NetworkEntropyAnalyzer',
    'InfluencePropagationAnalyzer',
    'DynamicCommunityDetector',
    'analyze_temporal_network'
]
