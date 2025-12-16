"""
Multi-Scale Pattern Mining for Politician Trading Analysis

Integrates multiple time scales (daily, weekly, monthly) to discover
hierarchical patterns and scale-invariant trading behaviors.

Key Features:
- Simultaneous analysis at multiple resolutions
- Scale-invariant pattern matching
- Hierarchical pattern relationships
- Cross-scale pattern propagation
- Temporal abstraction layers

Use Cases:
- Detect patterns that span multiple time scales
- Find scale-invariant trading strategies
- Identify cascading effects (daily → weekly → monthly)
- Distinguish local noise from global trends

Author: Claude
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from analysis.advanced.wavelet import MultiResolutionWaveletAnalyzer
from analysis.patterns.matrix_profile import MatrixProfileAnalyzer

logger = logging.getLogger(__name__)


class ScaleInvariantPattern:
    """
    Represents a pattern that exists across multiple time scales.

    A scale-invariant pattern maintains its structure when viewed at
    different resolutions (e.g., same pattern in daily and weekly data).
    """

    def __init__(
        self,
        pattern_id: str,
        scales: List[int],
        patterns: Dict[int, np.ndarray],
        similarity: float,
        metadata: Dict = None
    ):
        """
        Initialize scale-invariant pattern.

        Args:
            pattern_id: Unique identifier
            scales: List of scales where pattern appears (in days)
            patterns: Dict mapping scale to pattern array
            similarity: Cross-scale similarity score (0-1)
            metadata: Additional pattern information
        """
        self.pattern_id = pattern_id
        self.scales = scales
        self.patterns = patterns
        self.similarity = similarity
        self.metadata = metadata or {}

    def get_scale_ratio(self) -> float:
        """Get ratio between largest and smallest scale."""
        if len(self.scales) < 2:
            return 1.0
        return max(self.scales) / min(self.scales)

    def is_fractal(self, threshold: float = 0.8) -> bool:
        """Check if pattern exhibits fractal-like self-similarity."""
        return self.similarity >= threshold and len(self.scales) >= 3


class HierarchicalPatternLibrary:
    """
    Maintains library of patterns organized by scale hierarchy.

    Organizes patterns into:
    - Level 1 (Micro): Intraday to daily (1-7 days)
    - Level 2 (Meso): Weekly to monthly (7-30 days)
    - Level 3 (Macro): Monthly to quarterly (30-90 days)
    - Level 4 (Strategic): Quarterly to annual (90-365 days)
    """

    def __init__(self):
        self.patterns_by_scale = {
            'micro': [],    # 1-7 days
            'meso': [],     # 7-30 days
            'macro': [],    # 30-90 days
            'strategic': [] # 90+ days
        }
        self.scale_invariant_patterns = []
        self.hierarchical_relationships = []

    def add_pattern(
        self,
        pattern: np.ndarray,
        scale: int,
        metadata: Dict = None
    ):
        """Add pattern to appropriate scale category."""
        category = self._categorize_scale(scale)

        entry = {
            'pattern': pattern,
            'scale': scale,
            'metadata': metadata or {},
            'added_at': datetime.now().isoformat()
        }

        self.patterns_by_scale[category].append(entry)

    def _categorize_scale(self, scale: int) -> str:
        """Categorize scale into hierarchy level."""
        if scale <= 7:
            return 'micro'
        elif scale <= 30:
            return 'meso'
        elif scale <= 90:
            return 'macro'
        else:
            return 'strategic'

    def find_scale_invariant_patterns(
        self,
        similarity_threshold: float = 0.7
    ) -> List[ScaleInvariantPattern]:
        """
        Find patterns that appear across multiple scales.

        Returns patterns that maintain their structure across different
        time resolutions, indicating fundamental trading behavior.
        """
        scale_invariant = []
        pattern_id = 0

        # Compare patterns across different scale categories
        all_scales = ['micro', 'meso', 'macro', 'strategic']

        for i in range(len(all_scales)):
            for j in range(i + 1, len(all_scales)):
                scale_i = all_scales[i]
                scale_j = all_scales[j]

                # Compare patterns between scales
                for pattern_i in self.patterns_by_scale[scale_i]:
                    for pattern_j in self.patterns_by_scale[scale_j]:
                        similarity = self._compute_scale_invariant_similarity(
                            pattern_i['pattern'],
                            pattern_j['pattern']
                        )

                        if similarity >= similarity_threshold:
                            # Found scale-invariant pattern
                            scales = [pattern_i['scale'], pattern_j['scale']]
                            patterns = {
                                pattern_i['scale']: pattern_i['pattern'],
                                pattern_j['scale']: pattern_j['pattern']
                            }

                            scale_inv = ScaleInvariantPattern(
                                pattern_id=f"SIP_{pattern_id:04d}",
                                scales=scales,
                                patterns=patterns,
                                similarity=similarity,
                                metadata={
                                    'scale_categories': [scale_i, scale_j],
                                    'pattern_i_meta': pattern_i['metadata'],
                                    'pattern_j_meta': pattern_j['metadata']
                                }
                            )

                            scale_invariant.append(scale_inv)
                            pattern_id += 1

        self.scale_invariant_patterns = scale_invariant
        return scale_invariant

    def _compute_scale_invariant_similarity(
        self,
        pattern1: np.ndarray,
        pattern2: np.ndarray
    ) -> float:
        """
        Compute similarity between patterns at different scales.

        Uses dynamic time warping distance and normalization to handle
        different lengths and scales.
        """
        # Normalize patterns
        p1 = (pattern1 - np.mean(pattern1)) / (np.std(pattern1) + 1e-8)
        p2 = (pattern2 - np.mean(pattern2)) / (np.std(pattern2) + 1e-8)

        # Resample to same length
        from scipy.interpolate import interp1d

        if len(p1) != len(p2):
            # Interpolate to match lengths
            target_len = min(len(p1), len(p2))

            if len(p1) > target_len:
                x = np.linspace(0, 1, len(p1))
                f = interp1d(x, p1, kind='linear')
                p1 = f(np.linspace(0, 1, target_len))

            if len(p2) > target_len:
                x = np.linspace(0, 1, len(p2))
                f = interp1d(x, p2, kind='linear')
                p2 = f(np.linspace(0, 1, target_len))

        # Pearson correlation (scale-invariant)
        if len(p1) > 1 and len(p2) > 1:
            correlation = np.corrcoef(p1, p2)[0, 1]
            # Convert to similarity (0-1)
            similarity = (correlation + 1) / 2
        else:
            similarity = 0.0

        return similarity

    def build_hierarchy(self) -> Dict:
        """
        Build hierarchical relationships between patterns.

        Returns:
            {
                'hierarchy_levels': 4,
                'relationships': [...],
                'cross_scale_influences': [...]
            }
        """
        relationships = []

        # Find patterns that influence patterns at coarser scales
        scale_order = ['micro', 'meso', 'macro', 'strategic']

        for i in range(len(scale_order) - 1):
            finer_scale = scale_order[i]
            coarser_scale = scale_order[i + 1]

            # Check if finer patterns aggregate to coarser patterns
            for fine_pattern in self.patterns_by_scale[finer_scale]:
                for coarse_pattern in self.patterns_by_scale[coarser_scale]:
                    # Check if fine pattern is a component of coarse pattern
                    influence = self._measure_cross_scale_influence(
                        fine_pattern['pattern'],
                        coarse_pattern['pattern']
                    )

                    if influence > 0.5:
                        relationships.append({
                            'fine_scale': finer_scale,
                            'coarse_scale': coarser_scale,
                            'influence_score': influence,
                            'type': 'aggregation'
                        })

        self.hierarchical_relationships = relationships

        return {
            'hierarchy_levels': len(scale_order),
            'relationships': relationships,
            'n_relationships': len(relationships)
        }

    def _measure_cross_scale_influence(
        self,
        fine_pattern: np.ndarray,
        coarse_pattern: np.ndarray
    ) -> float:
        """Measure how much a fine-scale pattern influences coarse-scale."""
        # Simple approach: check if fine pattern appears as subsequence
        # in aggregated version of coarse pattern

        # Resample coarse to finer resolution
        from scipy.interpolate import interp1d

        if len(coarse_pattern) < 2:
            return 0.0

        x_coarse = np.linspace(0, 1, len(coarse_pattern))
        f = interp1d(x_coarse, coarse_pattern, kind='linear')
        coarse_resampled = f(np.linspace(0, 1, len(fine_pattern)))

        # Normalize both
        fine_norm = (fine_pattern - np.mean(fine_pattern)) / (np.std(fine_pattern) + 1e-8)
        coarse_norm = (coarse_resampled - np.mean(coarse_resampled)) / (np.std(coarse_resampled) + 1e-8)

        # Correlation
        if len(fine_norm) > 1:
            corr = np.corrcoef(fine_norm, coarse_norm)[0, 1]
            return abs(corr)
        return 0.0


class MultiScalePatternMiner:
    """
    Discovers patterns across multiple time scales simultaneously.

    Combines:
    - Multi-resolution wavelet decomposition
    - Matrix profile at different window sizes
    - Hierarchical pattern library
    - Scale-invariant pattern detection
    """

    def __init__(
        self,
        scales: List[int] = [7, 14, 30, 60, 90],
        wavelet: str = 'db4'
    ):
        """
        Initialize multi-scale pattern miner.

        Args:
            scales: Time scales to analyze (in days)
            wavelet: Wavelet for multi-resolution analysis
        """
        self.scales = scales
        self.wavelet = wavelet
        self.pattern_library = HierarchicalPatternLibrary()

    def discover_multiscale_patterns(
        self,
        time_series: Union[pd.Series, np.ndarray],
        use_wavelet: bool = True,
        use_matrix_profile: bool = True
    ) -> Dict:
        """
        Comprehensive multi-scale pattern discovery.

        Args:
            time_series: Time series data
            use_wavelet: Use wavelet decomposition
            use_matrix_profile: Use matrix profile at multiple scales

        Returns:
            {
                'wavelet_patterns': Patterns from wavelet analysis,
                'matrix_profile_patterns': Patterns from matrix profile,
                'scale_invariant_patterns': Patterns across scales,
                'hierarchical_structure': Pattern hierarchy,
                'cross_scale_correlations': Scale dependencies
            }
        """
        results = {}

        # 1. Wavelet-based multi-resolution analysis
        if use_wavelet:
            logger.info("Performing multi-resolution wavelet analysis...")
            results['wavelet_analysis'] = self._wavelet_multiscale(time_series)

        # 2. Matrix Profile at multiple scales
        if use_matrix_profile:
            logger.info("Performing multi-scale matrix profile analysis...")
            results['matrix_profile_analysis'] = self._matrix_profile_multiscale(time_series)

        # 3. Find scale-invariant patterns
        logger.info("Detecting scale-invariant patterns...")
        scale_invariant = self.pattern_library.find_scale_invariant_patterns()
        results['scale_invariant_patterns'] = [
            {
                'pattern_id': p.pattern_id,
                'scales': p.scales,
                'similarity': p.similarity,
                'scale_ratio': p.get_scale_ratio(),
                'is_fractal': p.is_fractal(),
                'metadata': p.metadata
            }
            for p in scale_invariant
        ]

        # 4. Build hierarchical structure
        logger.info("Building pattern hierarchy...")
        results['hierarchy'] = self.pattern_library.build_hierarchy()

        # 5. Summary statistics
        results['summary'] = {
            'scales_analyzed': self.scales,
            'n_wavelet_patterns': len(results.get('wavelet_analysis', {}).get('patterns_by_scale', {})),
            'n_matrix_profile_patterns': sum(
                len(p.get('motifs', []))
                for p in results.get('matrix_profile_analysis', {}).values()
            ),
            'n_scale_invariant': len(scale_invariant),
            'n_hierarchical_relations': results['hierarchy']['n_relationships']
        }

        return results

    def _wavelet_multiscale(
        self,
        time_series: Union[pd.Series, np.ndarray]
    ) -> Dict:
        """Perform wavelet analysis across scales."""
        analyzer = MultiResolutionWaveletAnalyzer(wavelet=self.wavelet)

        # Decompose
        decomposition = analyzer.decompose(time_series)

        # Extract patterns from each scale
        patterns_by_scale = {}

        for level in range(1, decomposition['max_level'] + 1):
            scale_patterns = analyzer.extract_scale_specific_patterns(
                decomposition,
                level
            )

            # Add to pattern library
            if len(scale_patterns['peaks']) > 0:
                detail_signal = np.array(scale_patterns['detail_signal'])
                scale_days = 2 ** level

                self.pattern_library.add_pattern(
                    detail_signal,
                    scale_days,
                    metadata={
                        'source': 'wavelet',
                        'level': level,
                        'level_name': scale_patterns['level_name'],
                        'energy': scale_patterns['energy']
                    }
                )

            patterns_by_scale[f"scale_{level}"] = scale_patterns

        # Cross-scale correlations
        correlations = analyzer.detect_cross_scale_correlations(decomposition)

        # Multi-scale anomalies
        anomalies = analyzer.detect_multiscale_anomalies(decomposition)

        return {
            'decomposition': {
                'max_level': decomposition['max_level'],
                'energy_distribution': decomposition['energy_distribution'],
                'reconstruction_error': decomposition['reconstruction_error']
            },
            'patterns_by_scale': patterns_by_scale,
            'cross_scale_correlations': correlations,
            'multiscale_anomalies': anomalies
        }

    def _matrix_profile_multiscale(
        self,
        time_series: Union[pd.Series, np.ndarray]
    ) -> Dict:
        """Perform matrix profile analysis at multiple scales."""
        results = {}

        for scale in self.scales:
            logger.info(f"Computing matrix profile at {scale}-day window...")

            try:
                analyzer = MatrixProfileAnalyzer(window_size=scale)

                # Discover motifs
                motif_result = analyzer.discover_motifs(time_series, k_motifs=3)

                # Add motifs to pattern library
                for motif in motif_result['motifs']:
                    pattern = np.array(motif['pattern_1'])

                    self.pattern_library.add_pattern(
                        pattern,
                        scale,
                        metadata={
                            'source': 'matrix_profile',
                            'motif_id': motif['motif_id'],
                            'similarity': motif['similarity']
                        }
                    )

                # Discover discords (anomalies)
                discord_result = analyzer.find_discords(time_series, k_discords=3)

                results[f"scale_{scale}"] = {
                    'window_size': scale,
                    'motifs': motif_result['motifs'],
                    'discords': discord_result['discords'],
                    'n_motifs': len(motif_result['motifs']),
                    'n_discords': len(discord_result['discords'])
                }

            except Exception as e:
                logger.warning(f"Error at scale {scale}: {e}")
                continue

        return results

    def detect_temporal_cascades(
        self,
        multiscale_results: Dict
    ) -> List[Dict]:
        """
        Detect cascading patterns across time scales.

        A cascade occurs when a pattern at fine scale triggers or
        propagates to coarser scales (e.g., daily spike → weekly trend).

        Returns:
            List of detected cascades with propagation paths
        """
        cascades = []

        # Look for patterns that appear sequentially across scales
        matrix_results = multiscale_results.get('matrix_profile_analysis', {})

        if not matrix_results:
            return []

        # Order scales
        ordered_scales = sorted(self.scales)

        for i in range(len(ordered_scales) - 1):
            fine_scale = ordered_scales[i]
            coarse_scale = ordered_scales[i + 1]

            fine_key = f"scale_{fine_scale}"
            coarse_key = f"scale_{coarse_scale}"

            if fine_key not in matrix_results or coarse_key not in matrix_results:
                continue

            fine_motifs = matrix_results[fine_key].get('motifs', [])
            coarse_motifs = matrix_results[coarse_key].get('motifs', [])

            # Check for temporal alignment
            for fine_motif in fine_motifs:
                for coarse_motif in coarse_motifs:
                    # Check if fine pattern location aligns with coarse pattern
                    # (allowing for scale difference)
                    fine_loc = fine_motif.get('location_1', 0)
                    coarse_loc = coarse_motif.get('location_1', 0)

                    # Scale ratio
                    scale_ratio = coarse_scale / fine_scale

                    # Expected alignment (fine location should be within coarse window)
                    if isinstance(coarse_loc, (int, float)) and isinstance(fine_loc, (int, float)):
                        if abs(fine_loc - coarse_loc * scale_ratio) < coarse_scale:
                            # Potential cascade
                            cascades.append({
                                'fine_scale': fine_scale,
                                'coarse_scale': coarse_scale,
                                'fine_location': fine_loc,
                                'coarse_location': coarse_loc,
                                'cascade_strength': fine_motif.get('similarity', 0) * coarse_motif.get('similarity', 0),
                                'interpretation': f"Pattern cascades from {fine_scale}-day to {coarse_scale}-day scale"
                            })

        return cascades


def analyze_politician_multiscale(
    trades: List[Dict],
    scales: List[int] = [7, 14, 30, 60, 90]
) -> Dict:
    """
    Convenience function for multi-scale analysis of politician trades.

    Example:
        >>> trades = [...]  # Politician trade data
        >>> result = analyze_politician_multiscale(trades)
        >>> print(f"Found {result['summary']['n_scale_invariant']} scale-invariant patterns")
    """
    # Convert trades to time series
    from analysis.patterns.motif_discovery import MotifDiscoveryEngine

    engine = MotifDiscoveryEngine()
    time_series = engine._trades_to_time_series(trades, group_by_date=False)

    if time_series is None or len(time_series) < 30:
        return {
            'status': 'insufficient_data',
            'n_trades': len(trades)
        }

    # Multi-scale analysis
    miner = MultiScalePatternMiner(scales=scales)
    results = miner.discover_multiscale_patterns(time_series)

    # Detect cascades
    cascades = miner.detect_temporal_cascades(results)
    results['temporal_cascades'] = cascades
    results['summary']['n_cascades'] = len(cascades)

    return results


__all__ = [
    'ScaleInvariantPattern',
    'HierarchicalPatternLibrary',
    'MultiScalePatternMiner',
    'analyze_politician_multiscale'
]
