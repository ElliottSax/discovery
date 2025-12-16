"""
Network Analysis Service for ULTRATHINK

Generates network graphs showing politician coordination and trading relationships.
Analyzes:
- Synchronized trading networks
- Mimicry patterns between politicians
- Stock correlation networks
- Suspicious activity clusters
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class NetworkAnalyzer:
    """
    Service for generating network graph data from trading patterns
    """

    def __init__(self):
        """Initialize network analyzer"""
        self.discoveries_file = Path("data/patterns/discoveries.jsonl")

    def load_discoveries(self) -> List[Dict[str, Any]]:
        """
        Load pattern discoveries from file

        Returns:
            List of discovery records
        """
        discoveries = []

        if not self.discoveries_file.exists():
            logger.warning(f"Discoveries file not found: {self.discoveries_file}")
            return []

        try:
            with open(self.discoveries_file, 'r') as f:
                for line in f:
                    if line.strip():
                        discoveries.append(json.loads(line))
        except Exception as e:
            logger.error(f"Error loading discoveries: {e}")
            return []

        logger.info(f"Loaded {len(discoveries)} discoveries")
        return discoveries

    def extract_politician_nodes(
        self,
        discoveries: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract politician nodes from discoveries

        Args:
            discoveries: List of all discoveries

        Returns:
            Dictionary of politician stats for node creation
        """
        politician_stats = defaultdict(lambda: {
            'trade_count': 0,
            'suspicious_flags': 0,
            'benford_violations': 0,
            'synchronized_events': 0,
            'mimicry_events': 0,
            'stocks': set()
        })

        for disc in discoveries:
            disc_type = disc.get('type', '')
            finding = disc.get('finding', {})

            # Extract from Benford violations
            if disc_type == 'benford_violation':
                pol = finding.get('politician', 'Unknown')
                politician_stats[pol]['benford_violations'] += 1
                politician_stats[pol]['suspicious_flags'] += 1

            # Extract from ML discoveries
            elif disc_type == 'ml_discovery':
                data = finding.get('data', {})
                pattern_type = finding.get('type', '')

                if pattern_type == 'synchronized':
                    politicians = data.get('politicians', [])
                    ticker = data.get('ticker', '')
                    for pol in politicians:
                        politician_stats[pol]['synchronized_events'] += 1
                        politician_stats[pol]['suspicious_flags'] += 1
                        if ticker:
                            politician_stats[pol]['stocks'].add(ticker)

                elif pattern_type == 'mimicry':
                    pol1 = data.get('politician_1', '')
                    pol2 = data.get('politician_2', '')
                    if pol1:
                        politician_stats[pol1]['mimicry_events'] += 1
                        politician_stats[pol1]['suspicious_flags'] += 1
                    if pol2:
                        politician_stats[pol2]['mimicry_events'] += 1
                        politician_stats[pol2]['suspicious_flags'] += 1

        return politician_stats

    def build_nodes(
        self,
        politician_stats: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build node list from politician stats

        Args:
            politician_stats: Statistics for each politician

        Returns:
            List of node objects
        """
        nodes = []

        for name, stats in politician_stats.items():
            if name == 'Unknown':
                continue

            # Determine node size based on activity
            total_activity = (
                stats['synchronized_events'] +
                stats['mimicry_events'] +
                stats['benford_violations']
            )

            # Determine color based on suspicion level
            if stats['benford_violations'] > 0:
                color = '#ef4444'  # Red - CRITICAL
                risk_level = 'CRITICAL'
            elif stats['suspicious_flags'] >= 10:
                color = '#f97316'  # Orange - HIGH
                risk_level = 'HIGH'
            elif stats['suspicious_flags'] >= 5:
                color = '#eab308'  # Yellow - MEDIUM
                risk_level = 'MEDIUM'
            else:
                color = '#22c55e'  # Green - LOW
                risk_level = 'LOW'

            nodes.append({
                'id': name,
                'label': name,
                'size': min(10 + total_activity * 2, 50),  # Cap at size 50
                'color': color,
                'risk_level': risk_level,
                'stats': {
                    'synchronized_events': stats['synchronized_events'],
                    'mimicry_events': stats['mimicry_events'],
                    'benford_violations': stats['benford_violations'],
                    'suspicious_flags': stats['suspicious_flags'],
                    'unique_stocks': len(stats['stocks'])
                }
            })

        return nodes

    def extract_edges(
        self,
        discoveries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract edge relationships from discoveries

        Args:
            discoveries: List of all discoveries

        Returns:
            List of edge objects
        """
        # Track edge weights
        edge_weights = defaultdict(lambda: {
            'synchronized': 0,
            'mimicry': 0,
            'granger': 0
        })

        for disc in discoveries:
            disc_type = disc.get('type', '')
            finding = disc.get('finding', {})

            if disc_type == 'ml_discovery':
                data = finding.get('data', {})
                pattern_type = finding.get('type', '')

                if pattern_type == 'synchronized':
                    # Create edges between all politicians in sync event
                    politicians = data.get('politicians', [])
                    for i, pol1 in enumerate(politicians):
                        for pol2 in politicians[i+1:]:
                            edge_key = tuple(sorted([pol1, pol2]))
                            edge_weights[edge_key]['synchronized'] += 1

                elif pattern_type == 'mimicry':
                    pol1 = data.get('politician_1', '')
                    pol2 = data.get('politician_2', '')
                    if pol1 and pol2:
                        edge_key = tuple(sorted([pol1, pol2]))
                        edge_weights[edge_key]['mimicry'] += 1

            elif disc_type == 'granger_causality':
                direction = finding.get('direction', '')
                if ' -> ' in direction:
                    pol1, pol2 = direction.split(' -> ')
                    edge_key = tuple(sorted([pol1.strip(), pol2.strip()]))
                    edge_weights[edge_key]['granger'] += 1

        # Convert to edge list
        edges = []
        for (source, target), weights in edge_weights.items():
            if source == 'Unknown' or target == 'Unknown':
                continue

            total_weight = sum(weights.values())

            # Determine edge type (primary relationship)
            if weights['synchronized'] > 0:
                edge_type = 'synchronized'
                color = '#3b82f6'  # Blue
            elif weights['mimicry'] > 0:
                edge_type = 'mimicry'
                color = '#8b5cf6'  # Purple
            else:
                edge_type = 'granger'
                color = '#64748b'  # Gray

            edges.append({
                'source': source,
                'target': target,
                'weight': total_weight,
                'type': edge_type,
                'color': color,
                'details': {
                    'synchronized_events': weights['synchronized'],
                    'mimicry_patterns': weights['mimicry'],
                    'granger_relationships': weights['granger']
                }
            })

        return edges

    def generate_network_graph(
        self,
        discoveries: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete network graph from discoveries

        Args:
            discoveries: Optional list of discoveries (will load if not provided)

        Returns:
            Network graph data with nodes and edges
        """
        # Load discoveries if not provided
        if discoveries is None:
            discoveries = self.load_discoveries()

        if not discoveries:
            return {
                'nodes': [],
                'edges': [],
                'stats': {
                    'total_nodes': 0,
                    'total_edges': 0,
                    'generated': datetime.now().isoformat()
                }
            }

        # Extract nodes
        politician_stats = self.extract_politician_nodes(discoveries)
        nodes = self.build_nodes(politician_stats)

        # Extract edges
        edges = self.extract_edges(discoveries)

        # Calculate network statistics
        stats = {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'generated': datetime.now().isoformat(),
            'risk_distribution': Counter(node['risk_level'] for node in nodes),
            'edge_types': Counter(edge['type'] for edge in edges)
        }

        return {
            'nodes': nodes,
            'edges': edges,
            'stats': stats
        }

    def get_politician_connections(
        self,
        politician_name: str,
        discoveries: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Get connections for a specific politician

        Args:
            politician_name: Name of the politician
            discoveries: Optional list of discoveries

        Returns:
            Politician's connection data
        """
        # Generate full network
        network = self.generate_network_graph(discoveries)

        # Filter for this politician
        politician_node = None
        connected_edges = []

        for node in network['nodes']:
            if node['id'].lower() == politician_name.lower():
                politician_node = node
                break

        if not politician_node:
            return {
                'politician': politician_name,
                'found': False,
                'message': 'Politician not found in network'
            }

        # Find all connected edges
        for edge in network['edges']:
            if edge['source'].lower() == politician_name.lower() or \
               edge['target'].lower() == politician_name.lower():
                connected_edges.append(edge)

        # Extract connected politicians
        connections = []
        for edge in connected_edges:
            other = edge['target'] if edge['source'].lower() == politician_name.lower() else edge['source']

            # Find the other node
            other_node = next((n for n in network['nodes'] if n['id'] == other), None)

            connections.append({
                'politician': other,
                'connection_type': edge['type'],
                'weight': edge['weight'],
                'details': edge['details'],
                'risk_level': other_node['risk_level'] if other_node else 'UNKNOWN'
            })

        # Sort by weight
        connections.sort(key=lambda x: x['weight'], reverse=True)

        return {
            'politician': politician_name,
            'found': True,
            'node_stats': politician_node['stats'],
            'risk_level': politician_node['risk_level'],
            'total_connections': len(connections),
            'connections': connections
        }

    def identify_clusters(
        self,
        network: Dict[str, Any],
        min_cluster_size: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Identify clusters of highly connected politicians

        Args:
            network: Network graph data
            min_cluster_size: Minimum size for a cluster

        Returns:
            List of identified clusters
        """
        # Simple clustering based on edge weights
        # This is a basic implementation - could be enhanced with proper graph algorithms

        # Build adjacency list
        adjacency = defaultdict(set)
        for edge in network['edges']:
            if edge['weight'] >= 3:  # Only strong connections
                adjacency[edge['source']].add(edge['target'])
                adjacency[edge['target']].add(edge['source'])

        # Find connected components
        visited = set()
        clusters = []

        for politician in adjacency:
            if politician in visited:
                continue

            # BFS to find cluster
            cluster = set()
            queue = [politician]

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue

                visited.add(current)
                cluster.add(current)

                for neighbor in adjacency[current]:
                    if neighbor not in visited:
                        queue.append(neighbor)

            if len(cluster) >= min_cluster_size:
                # Get cluster stats
                cluster_edges = [
                    e for e in network['edges']
                    if e['source'] in cluster and e['target'] in cluster
                ]

                clusters.append({
                    'size': len(cluster),
                    'members': sorted(list(cluster)),
                    'internal_edges': len(cluster_edges),
                    'total_weight': sum(e['weight'] for e in cluster_edges)
                })

        # Sort by size
        clusters.sort(key=lambda x: x['size'], reverse=True)

        return clusters


class TemporalNetworkAnalyzer:
    """
    Analyzes network evolution over time.

    Tracks:
    - Network topology changes
    - Centrality evolution
    - Community dynamics
    - Emerging/dissolving relationships
    - Anomalous network events
    """

    def __init__(self):
        """Initialize temporal network analyzer"""
        self.snapshots = []  # List of (timestamp, network) tuples
        self.evolution_metrics = []

    def create_temporal_snapshots(
        self,
        discoveries: List[Dict[str, Any]],
        time_window_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Create network snapshots at different time windows.

        Args:
            discoveries: All pattern discoveries
            time_window_days: Size of time window for each snapshot

        Returns:
            List of network snapshots with timestamps
        """
        # Group discoveries by time window
        from datetime import datetime, timedelta

        # Find time range
        timestamps = []
        for disc in discoveries:
            ts_str = disc.get('timestamp', disc.get('discovered_at'))
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    timestamps.append(ts)
                except:
                    continue

        if not timestamps:
            logger.warning("No valid timestamps found in discoveries")
            return []

        min_time = min(timestamps)
        max_time = max(timestamps)

        # Create time windows
        snapshots = []
        current_time = min_time

        while current_time <= max_time:
            window_end = current_time + timedelta(days=time_window_days)

            # Filter discoveries in this window
            window_discoveries = []
            for disc in discoveries:
                ts_str = disc.get('timestamp', disc.get('discovered_at'))
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                        if current_time <= ts < window_end:
                            window_discoveries.append(disc)
                    except:
                        continue

            # Generate network for this window
            if window_discoveries:
                analyzer = NetworkAnalyzer()
                network = analyzer.generate_network_graph(window_discoveries)

                snapshot = {
                    'timestamp': current_time.isoformat(),
                    'window_start': current_time.isoformat(),
                    'window_end': window_end.isoformat(),
                    'network': network,
                    'n_discoveries': len(window_discoveries)
                }

                snapshots.append(snapshot)

            current_time = window_end

        self.snapshots = snapshots
        logger.info(f"Created {len(snapshots)} temporal snapshots")
        return snapshots

    def compute_centrality_evolution(
        self,
        snapshots: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Track how politician centrality changes over time.

        Computes degree centrality for each politician at each snapshot.

        Args:
            snapshots: Network snapshots (uses self.snapshots if None)

        Returns:
            {
                politician_name: [
                    {'timestamp': ..., 'centrality': ..., 'degree': ...},
                    ...
                ]
            }
        """
        if snapshots is None:
            snapshots = self.snapshots

        if not snapshots:
            return {}

        centrality_evolution = defaultdict(list)

        for snapshot in snapshots:
            timestamp = snapshot['timestamp']
            network = snapshot['network']

            # Calculate degree for each node
            degree_count = defaultdict(int)

            for edge in network['edges']:
                degree_count[edge['source']] += 1
                degree_count[edge['target']] += 1

            # Normalize to centrality (0-1)
            max_degree = max(degree_count.values()) if degree_count else 1

            for node in network['nodes']:
                politician = node['id']
                degree = degree_count.get(politician, 0)
                centrality = degree / max_degree if max_degree > 0 else 0.0

                centrality_evolution[politician].append({
                    'timestamp': timestamp,
                    'centrality': centrality,
                    'degree': degree,
                    'risk_level': node.get('risk_level', 'UNKNOWN')
                })

        return dict(centrality_evolution)

    def detect_network_anomalies(
        self,
        snapshots: Optional[List[Dict[str, Any]]] = None,
        threshold_std: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalous changes in network structure.

        Anomalies include:
        - Sudden connectivity spikes
        - Emergence of new clusters
        - Rapid centrality changes

        Args:
            snapshots: Network snapshots
            threshold_std: Standard deviations for anomaly detection

        Returns:
            List of detected anomalies
        """
        if snapshots is None:
            snapshots = self.snapshots

        if len(snapshots) < 3:
            logger.warning("Need at least 3 snapshots for anomaly detection")
            return []

        anomalies = []

        # Track metrics over time
        edge_counts = []
        node_counts = []
        avg_degrees = []

        for snapshot in snapshots:
            network = snapshot['network']
            stats = network.get('stats', {})

            edge_counts.append(stats.get('total_edges', 0))
            node_counts.append(stats.get('total_nodes', 0))

            # Average degree
            if stats.get('total_nodes', 0) > 0:
                avg_degree = (2 * stats.get('total_edges', 0)) / stats.get('total_nodes', 1)
            else:
                avg_degree = 0
            avg_degrees.append(avg_degree)

        # Detect anomalies in each metric
        metrics = {
            'edge_count': edge_counts,
            'node_count': node_counts,
            'avg_degree': avg_degrees
        }

        for metric_name, values in metrics.items():
            if len(values) < 3:
                continue

            mean = np.mean(values)
            std = np.std(values)

            if std == 0:
                continue

            for i, value in enumerate(values):
                z_score = abs(value - mean) / std

                if z_score > threshold_std:
                    anomalies.append({
                        'snapshot_idx': i,
                        'timestamp': snapshots[i]['timestamp'],
                        'metric': metric_name,
                        'value': value,
                        'expected': mean,
                        'z_score': float(z_score),
                        'interpretation': self._interpret_anomaly(metric_name, value, mean)
                    })

        return anomalies

    def _interpret_anomaly(
        self,
        metric_name: str,
        value: float,
        expected: float
    ) -> str:
        """Interpret what an anomaly means."""
        diff_pct = ((value - expected) / expected * 100) if expected > 0 else 0

        if value > expected:
            direction = "increased"
        else:
            direction = "decreased"

        metric_display = metric_name.replace('_', ' ')

        return f"{metric_display.title()} {direction} by {abs(diff_pct):.1f}% (unusual activity)"

    def track_community_evolution(
        self,
        snapshots: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Track how communities (clusters) form and dissolve over time.

        Args:
            snapshots: Network snapshots

        Returns:
            List of community events (formation, growth, dissolution)
        """
        if snapshots is None:
            snapshots = self.snapshots

        if len(snapshots) < 2:
            return []

        community_events = []

        # Track communities at each snapshot
        prev_clusters = None

        for i, snapshot in enumerate(snapshots):
            network = snapshot['network']
            analyzer = NetworkAnalyzer()
            current_clusters = analyzer.identify_clusters(network, min_cluster_size=2)

            if prev_clusters is not None:
                # Compare with previous snapshot
                events = self._compare_clusters(
                    prev_clusters,
                    current_clusters,
                    snapshot['timestamp']
                )
                community_events.extend(events)

            prev_clusters = current_clusters

        return community_events

    def _compare_clusters(
        self,
        prev_clusters: List[Dict[str, Any]],
        current_clusters: List[Dict[str, Any]],
        timestamp: str
    ) -> List[Dict[str, Any]]:
        """Compare two snapshots of clusters to detect changes."""
        events = []

        # Convert to sets for comparison
        prev_sets = [set(c['members']) for c in prev_clusters]
        current_sets = [set(c['members']) for c in current_clusters]

        # Detect new clusters
        for curr_cluster in current_clusters:
            curr_members = set(curr_cluster['members'])

            # Check if this is a new cluster (no overlap with previous)
            is_new = True
            for prev_members in prev_sets:
                overlap = len(curr_members & prev_members)
                if overlap >= len(curr_members) * 0.5:  # 50% overlap
                    is_new = False
                    break

            if is_new:
                events.append({
                    'timestamp': timestamp,
                    'event_type': 'cluster_formation',
                    'members': curr_cluster['members'],
                    'size': curr_cluster['size'],
                    'interpretation': f"New cluster formed: {curr_cluster['size']} members"
                })

        # Detect dissolved clusters
        for prev_cluster in prev_clusters:
            prev_members = set(prev_cluster['members'])

            # Check if this cluster still exists
            still_exists = False
            for curr_members in current_sets:
                overlap = len(prev_members & curr_members)
                if overlap >= len(prev_members) * 0.5:
                    still_exists = True
                    break

            if not still_exists:
                events.append({
                    'timestamp': timestamp,
                    'event_type': 'cluster_dissolution',
                    'members': prev_cluster['members'],
                    'size': prev_cluster['size'],
                    'interpretation': f"Cluster dissolved: {prev_cluster['size']} members"
                })

        return events

    def get_evolution_summary(self) -> Dict[str, Any]:
        """
        Get summary of network evolution.

        Returns:
            Summary statistics and insights
        """
        if not self.snapshots:
            return {'status': 'no_data'}

        # Overall trends
        edge_counts = [s['network']['stats']['total_edges'] for s in self.snapshots]
        node_counts = [s['network']['stats']['total_nodes'] for s in self.snapshots]

        # Centrality evolution
        centrality = self.compute_centrality_evolution()

        # Most central politicians (final snapshot)
        if centrality:
            final_centralities = []
            for pol, history in centrality.items():
                if history:
                    final_centralities.append({
                        'politician': pol,
                        'centrality': history[-1]['centrality'],
                        'degree': history[-1]['degree']
                    })

            final_centralities.sort(key=lambda x: x['centrality'], reverse=True)
            top_politicians = final_centralities[:10]
        else:
            top_politicians = []

        return {
            'n_snapshots': len(self.snapshots),
            'time_span': {
                'start': self.snapshots[0]['timestamp'],
                'end': self.snapshots[-1]['timestamp']
            },
            'network_growth': {
                'initial_edges': edge_counts[0],
                'final_edges': edge_counts[-1],
                'growth': edge_counts[-1] - edge_counts[0],
                'initial_nodes': node_counts[0],
                'final_nodes': node_counts[-1]
            },
            'top_central_politicians': top_politicians,
            'anomalies_detected': len(self.detect_network_anomalies()),
            'community_events': len(self.track_community_evolution())
        }


# Global instances
network_analyzer = NetworkAnalyzer()
temporal_analyzer = TemporalNetworkAnalyzer()
