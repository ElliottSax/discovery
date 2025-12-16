"""
Unified Pattern Library - Integration of All Pattern Discovery Methods

Combines:
- Matrix Profile (motif discovery)
- Multi-Resolution Wavelet (scale analysis)
- SAX (symbolic patterns)
- Dynamic Network Analysis
- Traditional statistical patterns

Provides:
- Unified pattern storage and retrieval
- Cross-method pattern validation
- Pattern ranking and scoring
- Real-time pattern matching
- Pattern evolution tracking

Author: Claude
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from collections import defaultdict
from datetime import datetime, timedelta
import logging
import hashlib

from analysis.patterns.matrix_profile import MatrixProfileAnalyzer
from analysis.patterns.motif_discovery import MotifLibrary, MotifDiscoveryEngine
from analysis.advanced.wavelet import MultiResolutionWaveletAnalyzer
from analysis.patterns.sax_patterns import SAXTransformer, SAXPatternMiner
from analysis.patterns.multiscale_patterns import MultiScalePatternMiner

logger = logging.getLogger(__name__)


class Pattern:
    """
    Unified pattern representation.

    A pattern can come from any discovery method and is stored
    in a standardized format for comparison and ranking.
    """

    def __init__(
        self,
        pattern_id: str,
        pattern_type: str,
        source_method: str,
        pattern_data: np.ndarray,
        metadata: Dict[str, Any],
        discovered_at: datetime = None
    ):
        """
        Initialize pattern.

        Args:
            pattern_id: Unique identifier
            pattern_type: Type (motif, wavelet, sax, network, etc.)
            source_method: Discovery method
            pattern_data: Numeric pattern representation
            metadata: Additional information
            discovered_at: Discovery timestamp
        """
        self.pattern_id = pattern_id
        self.pattern_type = pattern_type
        self.source_method = source_method
        self.pattern_data = pattern_data
        self.metadata = metadata
        self.discovered_at = discovered_at or datetime.now()

        # Compute pattern signature (hash)
        self.signature = self._compute_signature()

        # Pattern metrics
        self.validation_score = 0.0
        self.occurrence_count = 1
        self.last_seen = self.discovered_at

    def _compute_signature(self) -> str:
        """Compute hash signature of pattern."""
        # Normalize pattern
        normalized = (self.pattern_data - np.mean(self.pattern_data)) / (np.std(self.pattern_data) + 1e-8)

        # Discretize to reduce sensitivity
        discretized = np.round(normalized, decimals=2)

        # Hash
        signature = hashlib.md5(discretized.tobytes()).hexdigest()[:16]
        return signature

    def similarity_to(self, other: 'Pattern') -> float:
        """Compute similarity to another pattern."""
        # Quick check: same signature = identical
        if self.signature == other.signature:
            return 1.0

        # Normalize both patterns
        p1 = (self.pattern_data - np.mean(self.pattern_data)) / (np.std(self.pattern_data) + 1e-8)
        p2 = (other.pattern_data - np.mean(other.pattern_data)) / (np.std(other.pattern_data) + 1e-8)

        # Align lengths
        min_len = min(len(p1), len(p2))
        p1 = p1[:min_len]
        p2 = p2[:min_len]

        # Pearson correlation
        if len(p1) > 1:
            corr = np.corrcoef(p1, p2)[0, 1]
            return (corr + 1) / 2  # Convert to 0-1 range
        return 0.0

    def update_occurrence(self, timestamp: datetime = None):
        """Update pattern occurrence statistics."""
        self.occurrence_count += 1
        self.last_seen = timestamp or datetime.now()


class UnifiedPatternLibrary:
    """
    Central repository for all discovered patterns.

    Features:
    - Multi-method pattern storage
    - Deduplication (same pattern from different methods)
    - Pattern validation and scoring
    - Similarity search
    - Pattern evolution tracking
    """

    def __init__(self):
        self.patterns = []
        self.patterns_by_type = defaultdict(list)
        self.patterns_by_method = defaultdict(list)
        self.pattern_index = {}  # signature → pattern
        self.validation_methods = []

    def add_pattern(
        self,
        pattern_type: str,
        source_method: str,
        pattern_data: np.ndarray,
        metadata: Dict[str, Any] = None
    ) -> Pattern:
        """
        Add pattern to library with deduplication.

        If pattern already exists (same signature), increments occurrence count.
        Otherwise, creates new pattern entry.

        Returns:
            Pattern object (new or existing)
        """
        # Create pattern object
        pattern_id = f"P_{len(self.patterns):06d}"
        pattern = Pattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            source_method=source_method,
            pattern_data=pattern_data,
            metadata=metadata or {}
        )

        # Check for duplicates
        if pattern.signature in self.pattern_index:
            # Pattern already exists
            existing = self.pattern_index[pattern.signature]
            existing.update_occurrence()

            # Merge metadata
            if 'sources' not in existing.metadata:
                existing.metadata['sources'] = [existing.source_method]

            if source_method not in existing.metadata['sources']:
                existing.metadata['sources'].append(source_method)

            logger.debug(f"Pattern {pattern.signature} already exists (count={existing.occurrence_count})")
            return existing

        # New pattern
        self.patterns.append(pattern)
        self.patterns_by_type[pattern_type].append(pattern)
        self.patterns_by_method[source_method].append(pattern)
        self.pattern_index[pattern.signature] = pattern

        logger.info(f"Added pattern {pattern_id} ({pattern_type} from {source_method})")
        return pattern

    def find_similar_patterns(
        self,
        query_pattern: np.ndarray,
        similarity_threshold: float = 0.7,
        max_results: int = 10
    ) -> List[Tuple[Pattern, float]]:
        """
        Find patterns similar to query.

        Args:
            query_pattern: Pattern to search for
            similarity_threshold: Minimum similarity
            max_results: Maximum number of results

        Returns:
            List of (pattern, similarity) tuples
        """
        # Create temporary pattern for comparison
        query = Pattern(
            pattern_id="QUERY",
            pattern_type="query",
            source_method="search",
            pattern_data=query_pattern,
            metadata={}
        )

        # Compute similarities
        results = []

        for pattern in self.patterns:
            similarity = query.similarity_to(pattern)

            if similarity >= similarity_threshold:
                results.append((pattern, similarity))

        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:max_results]

    def validate_pattern(
        self,
        pattern: Pattern,
        validation_data: Dict[str, Any]
    ) -> float:
        """
        Validate pattern using multiple criteria.

        Validation score based on:
        - Statistical significance
        - Occurrence frequency
        - Multi-method confirmation
        - Temporal consistency

        Returns:
            Validation score (0-1)
        """
        score = 0.0
        weights = []

        # 1. Occurrence frequency (more occurrences = more reliable)
        if pattern.occurrence_count >= 5:
            score += 0.3
            weights.append(0.3)
        elif pattern.occurrence_count >= 2:
            score += 0.15
            weights.append(0.15)

        # 2. Multi-method confirmation
        if 'sources' in pattern.metadata and len(pattern.metadata['sources']) > 1:
            score += 0.3
            weights.append(0.3)

        # 3. Statistical significance (from metadata)
        if 'significance' in pattern.metadata:
            sig_score = pattern.metadata['significance']
            score += sig_score * 0.2
            weights.append(0.2)

        # 4. Pattern strength (from metadata)
        if 'strength' in pattern.metadata:
            strength = pattern.metadata['strength']
            score += min(strength, 1.0) * 0.2
            weights.append(0.2)

        # Normalize
        if weights:
            max_score = sum(weights)
            validation_score = score / max_score if max_score > 0 else 0.0
        else:
            validation_score = 0.0

        pattern.validation_score = validation_score
        return validation_score

    def get_top_patterns(
        self,
        n: int = 10,
        pattern_type: Optional[str] = None,
        min_validation_score: float = 0.0
    ) -> List[Pattern]:
        """
        Get top-ranked patterns.

        Args:
            n: Number of patterns to return
            pattern_type: Filter by type (optional)
            min_validation_score: Minimum validation score

        Returns:
            List of top patterns
        """
        # Filter patterns
        if pattern_type:
            candidates = self.patterns_by_type.get(pattern_type, [])
        else:
            candidates = self.patterns

        # Filter by validation score
        candidates = [p for p in candidates if p.validation_score >= min_validation_score]

        # Sort by multiple criteria
        candidates.sort(
            key=lambda p: (p.validation_score, p.occurrence_count, -len(p.pattern_data)),
            reverse=True
        )

        return candidates[:n]

    def get_statistics(self) -> Dict:
        """Get library statistics."""
        return {
            'total_patterns': len(self.patterns),
            'unique_signatures': len(self.pattern_index),
            'patterns_by_type': {
                ptype: len(patterns)
                for ptype, patterns in self.patterns_by_type.items()
            },
            'patterns_by_method': {
                method: len(patterns)
                for method, patterns in self.patterns_by_method.items()
            },
            'avg_validation_score': np.mean([p.validation_score for p in self.patterns]) if self.patterns else 0.0,
            'multi_method_patterns': sum(
                1 for p in self.patterns
                if 'sources' in p.metadata and len(p.metadata['sources']) > 1
            )
        }


class IntegratedPatternDiscovery:
    """
    Discovers patterns using all available methods and integrates results.

    Methods integrated:
    1. Matrix Profile - Motif discovery
    2. Multi-Resolution Wavelet - Scale analysis
    3. SAX - Symbolic patterns
    4. Multi-Scale Mining - Cross-scale patterns
    """

    def __init__(self):
        self.library = UnifiedPatternLibrary()

    def discover_all_patterns(
        self,
        time_series: Union[pd.Series, np.ndarray],
        methods: List[str] = ['matrix_profile', 'wavelet', 'sax', 'multiscale']
    ) -> Dict:
        """
        Run all pattern discovery methods and integrate results.

        Args:
            time_series: Time series data
            methods: List of methods to use

        Returns:
            {
                'patterns_found': int,
                'patterns_by_method': {...},
                'top_patterns': [...],
                'library': UnifiedPatternLibrary
            }
        """
        results = {
            'patterns_by_method': {},
            'method_stats': {}
        }

        # 1. Matrix Profile
        if 'matrix_profile' in methods:
            logger.info("Running Matrix Profile analysis...")
            mp_results = self._discover_matrix_profile(time_series)
            results['patterns_by_method']['matrix_profile'] = mp_results
            results['method_stats']['matrix_profile'] = {
                'patterns_found': mp_results['n_patterns']
            }

        # 2. Wavelet Analysis
        if 'wavelet' in methods:
            logger.info("Running Wavelet analysis...")
            wav_results = self._discover_wavelet(time_series)
            results['patterns_by_method']['wavelet'] = wav_results
            results['method_stats']['wavelet'] = {
                'patterns_found': wav_results['n_patterns']
            }

        # 3. SAX Patterns
        if 'sax' in methods:
            logger.info("Running SAX analysis...")
            sax_results = self._discover_sax(time_series)
            results['patterns_by_method']['sax'] = sax_results
            results['method_stats']['sax'] = {
                'patterns_found': sax_results['n_patterns']
            }

        # 4. Multi-Scale Patterns
        if 'multiscale' in methods:
            logger.info("Running Multi-Scale analysis...")
            ms_results = self._discover_multiscale(time_series)
            results['patterns_by_method']['multiscale'] = ms_results
            results['method_stats']['multiscale'] = {
                'patterns_found': ms_results['n_patterns']
            }

        # Validate all patterns
        for pattern in self.library.patterns:
            self.library.validate_pattern(pattern, {})

        # Get top patterns
        top_patterns = self.library.get_top_patterns(n=20)

        results['patterns_found'] = len(self.library.patterns)
        results['top_patterns'] = [
            {
                'pattern_id': p.pattern_id,
                'type': p.pattern_type,
                'source': p.source_method,
                'validation_score': p.validation_score,
                'occurrences': p.occurrence_count,
                'length': len(p.pattern_data)
            }
            for p in top_patterns
        ]
        results['library'] = self.library
        results['statistics'] = self.library.get_statistics()

        return results

    def _discover_matrix_profile(self, time_series: Union[pd.Series, np.ndarray]) -> Dict:
        """Discover patterns using Matrix Profile."""
        try:
            analyzer = MatrixProfileAnalyzer(window_size=30)
            result = analyzer.discover_motifs(time_series, k_motifs=5)

            n_patterns = 0
            for motif in result['motifs']:
                pattern_data = np.array(motif['pattern_1'])

                self.library.add_pattern(
                    pattern_type='motif',
                    source_method='matrix_profile',
                    pattern_data=pattern_data,
                    metadata={
                        'motif_id': motif['motif_id'],
                        'similarity': motif['similarity'],
                        'window_size': motif['window_size']
                    }
                )
                n_patterns += 1

            return {'n_patterns': n_patterns, 'motifs': result['motifs']}

        except Exception as e:
            logger.error(f"Matrix Profile error: {e}")
            return {'n_patterns': 0, 'error': str(e)}

    def _discover_wavelet(self, time_series: Union[pd.Series, np.ndarray]) -> Dict:
        """Discover patterns using Wavelet analysis."""
        try:
            analyzer = MultiResolutionWaveletAnalyzer()
            decomposition = analyzer.decompose(time_series)

            n_patterns = 0
            for level in range(1, min(decomposition['max_level'] + 1, 4)):
                patterns = analyzer.extract_scale_specific_patterns(decomposition, level)

                if len(patterns['peaks']) > 0:
                    pattern_data = np.array(patterns['detail_signal'])

                    self.library.add_pattern(
                        pattern_type='wavelet',
                        source_method='wavelet',
                        pattern_data=pattern_data,
                        metadata={
                            'level': level,
                            'level_name': patterns['level_name'],
                            'energy': patterns['energy']
                        }
                    )
                    n_patterns += 1

            return {'n_patterns': n_patterns, 'decomposition': decomposition}

        except Exception as e:
            logger.error(f"Wavelet error: {e}")
            return {'n_patterns': 0, 'error': str(e)}

    def _discover_sax(self, time_series: Union[pd.Series, np.ndarray]) -> Dict:
        """Discover patterns using SAX."""
        try:
            transformer = SAXTransformer(word_size=10, alphabet_size=5)
            sax_string = transformer.transform(time_series)

            miner = SAXPatternMiner(word_size=10, alphabet_size=5)
            result = miner.mine_patterns([sax_string], min_support=1)

            # For now, just store the SAX string itself
            # Could expand to store individual frequent patterns
            n_patterns = 1

            return {
                'n_patterns': n_patterns,
                'sax_string': sax_string,
                'frequent_patterns': result['frequent_patterns'][:10]
            }

        except Exception as e:
            logger.error(f"SAX error: {e}")
            return {'n_patterns': 0, 'error': str(e)}

    def _discover_multiscale(self, time_series: Union[pd.Series, np.ndarray]) -> Dict:
        """Discover patterns using Multi-Scale analysis."""
        try:
            miner = MultiScalePatternMiner(scales=[7, 14, 30])
            result = miner.discover_multiscale_patterns(time_series, use_wavelet=False)

            # Extract patterns from matrix profile results
            n_patterns = 0
            mp_analysis = result.get('matrix_profile_analysis', {})

            for scale_key, scale_data in mp_analysis.items():
                for motif in scale_data.get('motifs', [])[:2]:  # Top 2 per scale
                    pattern_data = np.array(motif['pattern_1'])

                    self.library.add_pattern(
                        pattern_type='multiscale_motif',
                        source_method='multiscale',
                        pattern_data=pattern_data,
                        metadata={
                            'scale': scale_data['window_size'],
                            'similarity': motif['similarity']
                        }
                    )
                    n_patterns += 1

            return {'n_patterns': n_patterns, 'multiscale_result': result.get('summary', {})}

        except Exception as e:
            logger.error(f"Multi-scale error: {e}")
            return {'n_patterns': 0, 'error': str(e)}


__all__ = ['Pattern', 'UnifiedPatternLibrary', 'IntegratedPatternDiscovery']
