"""
SAX (Symbolic Aggregate Approximation) Pattern Mining

Converts time series into symbolic strings for fast pattern discovery.
Enables pattern matching using string algorithms instead of numeric computation.

Key Advantages:
- Dimensionality reduction (1000 points → 10 symbols)
- Fast pattern matching (string algorithms)
- Discretization reduces noise
- Easily interpretable patterns (e.g., "AABBCC")
- Distance lower bounding (SAX distance ≤ Euclidean distance)

References:
- Lin et al. (2003) - "A Symbolic Representation of Time Series"
- Lin et al. (2007) - "Experiencing SAX: A Novel Symbolic Representation"
- Senin & Malinchik (2013) - "SAX-VSM: Interpretable Time Series Classification"

Use Cases:
- Discover recurring symbolic patterns (e.g., "Buy-Wait-Sell")
- Fast similarity search in large databases
- Pattern classification and labeling
- Anomaly detection (rare symbolic sequences)

Author: Claude
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


class SAXTransformer:
    """
    Transform time series into symbolic representation.

    Process:
    1. Normalize time series (z-normalization)
    2. PAA: Reduce dimensionality by averaging segments
    3. Discretize: Map PAA values to symbols using Gaussian breakpoints

    Example:
        [1.2, 1.5, 0.8, -0.3, -1.1, -0.9] →
        PAA: [1.17, -0.77] →
        SAX: "BA" (using alphabet_size=3)
    """

    def __init__(
        self,
        word_size: int = 8,
        alphabet_size: int = 5,
        normalize: bool = True
    ):
        """
        Initialize SAX transformer.

        Args:
            word_size: Number of symbols in SAX representation (n)
            alphabet_size: Size of alphabet (a) - typically 3-10
            normalize: Whether to z-normalize before transformation

        Example:
            >>> transformer = SAXTransformer(word_size=8, alphabet_size=5)
            >>> sax_string = transformer.transform(time_series)
            >>> print(sax_string)  # "ABCDDCBA"
        """
        self.word_size = word_size
        self.alphabet_size = alphabet_size
        self.normalize = normalize

        # Precompute Gaussian breakpoints
        self.breakpoints = self._compute_breakpoints()

        # Create alphabet (letters)
        self.alphabet = [chr(65 + i) for i in range(alphabet_size)]  # A, B, C, ...

        logger.info(f"Initialized SAX with word_size={word_size}, alphabet_size={alphabet_size}")

    def _compute_breakpoints(self) -> np.ndarray:
        """
        Compute Gaussian breakpoints for discretization.

        For alphabet size a, we need (a-1) breakpoints that divide
        the standard normal distribution into equal probability regions.
        """
        from scipy.stats import norm

        if self.alphabet_size <= 1:
            return np.array([])

        # Compute quantiles
        breakpoints = []
        for i in range(1, self.alphabet_size):
            quantile = i / self.alphabet_size
            breakpoint = norm.ppf(quantile)
            breakpoints.append(breakpoint)

        return np.array(breakpoints)

    def transform(
        self,
        time_series: Union[pd.Series, np.ndarray]
    ) -> str:
        """
        Transform time series to SAX representation.

        Args:
            time_series: Input time series

        Returns:
            SAX string (e.g., "ABCDCBA")
        """
        # Convert to numpy array
        if isinstance(time_series, pd.Series):
            data = time_series.values
        else:
            data = np.array(time_series)

        # Normalize
        if self.normalize:
            data = self._normalize(data)

        # PAA (Piecewise Aggregate Approximation)
        paa = self._paa(data, self.word_size)

        # Discretize to symbols
        sax_string = self._discretize(paa)

        return sax_string

    def _normalize(self, data: np.ndarray) -> np.ndarray:
        """Z-normalize time series (zero mean, unit variance)."""
        mean = np.mean(data)
        std = np.std(data)

        if std < 1e-8:
            return data - mean  # Constant series

        return (data - mean) / std

    def _paa(self, data: np.ndarray, segments: int) -> np.ndarray:
        """
        Piecewise Aggregate Approximation.

        Reduces n-length time series to w-length by averaging segments.
        """
        n = len(data)

        if n < segments:
            raise ValueError(f"Time series length {n} < word_size {segments}")

        # Calculate segment size
        segment_size = n / segments

        paa_values = []

        for i in range(segments):
            start = int(i * segment_size)
            end = int((i + 1) * segment_size)

            # Average this segment
            segment_mean = np.mean(data[start:end])
            paa_values.append(segment_mean)

        return np.array(paa_values)

    def _discretize(self, paa_values: np.ndarray) -> str:
        """
        Discretize PAA values into symbols.

        Maps each PAA value to a symbol based on which region it falls into
        relative to the Gaussian breakpoints.
        """
        sax_string = ""

        for value in paa_values:
            # Find which region this value belongs to
            symbol_idx = 0

            for breakpoint in self.breakpoints:
                if value >= breakpoint:
                    symbol_idx += 1
                else:
                    break

            # Ensure within alphabet bounds
            symbol_idx = min(symbol_idx, self.alphabet_size - 1)

            sax_string += self.alphabet[symbol_idx]

        return sax_string

    def distance(self, sax1: str, sax2: str) -> float:
        """
        Compute MINDIST - lower bound on Euclidean distance.

        This distance measure guarantees:
        MINDIST(SAX1, SAX2) ≤ Euclidean_Distance(TS1, TS2)

        Allows fast pruning in similarity search.

        Args:
            sax1: First SAX string
            sax2: Second SAX string

        Returns:
            Lower bound distance
        """
        if len(sax1) != len(sax2):
            raise ValueError("SAX strings must have same length")

        # Precompute distance matrix between symbols
        dist_matrix = self._build_distance_matrix()

        total_dist = 0.0

        for c1, c2 in zip(sax1, sax2):
            # Index in alphabet
            idx1 = ord(c1) - 65
            idx2 = ord(c2) - 65

            total_dist += dist_matrix[idx1, idx2] ** 2

        # Scaling factor
        n = len(sax1)  # Should use original time series length, but approximation
        mindist = np.sqrt(total_dist) * np.sqrt(n / self.word_size)

        return mindist

    def _build_distance_matrix(self) -> np.ndarray:
        """Build distance matrix between alphabet symbols."""
        a = self.alphabet_size
        dist_matrix = np.zeros((a, a))

        # Distance between symbols based on breakpoint regions
        for i in range(a):
            for j in range(a):
                if abs(i - j) <= 1:
                    # Adjacent regions have 0 distance
                    dist_matrix[i, j] = 0
                else:
                    # Non-adjacent regions
                    # Distance is the gap between regions
                    if i > j:
                        dist_matrix[i, j] = self.breakpoints[i - 1] - self.breakpoints[j]
                    else:
                        dist_matrix[i, j] = self.breakpoints[j - 1] - self.breakpoints[i]

        return dist_matrix


class SAXPatternMiner:
    """
    Mine frequent patterns in SAX representation.

    Discovers:
    - Frequent subsequence patterns (e.g., "ABC" appears 10 times)
    - Rare patterns (anomalies)
    - Pattern associations (if "AB" then "CD")
    - Pattern evolution over time
    """

    def __init__(
        self,
        word_size: int = 8,
        alphabet_size: int = 5,
        min_pattern_length: int = 2,
        max_pattern_length: int = 4
    ):
        """
        Initialize SAX pattern miner.

        Args:
            word_size: SAX word size
            alphabet_size: Alphabet size
            min_pattern_length: Minimum pattern length to mine
            max_pattern_length: Maximum pattern length to mine
        """
        self.transformer = SAXTransformer(word_size, alphabet_size)
        self.min_pattern_length = min_pattern_length
        self.max_pattern_length = max_pattern_length

        self.pattern_counts = defaultdict(int)
        self.pattern_locations = defaultdict(list)

    def mine_patterns(
        self,
        sax_strings: List[str],
        min_support: int = 2
    ) -> Dict:
        """
        Mine frequent patterns from SAX strings.

        Args:
            sax_strings: List of SAX representations
            min_support: Minimum number of occurrences

        Returns:
            {
                'frequent_patterns': [...],
                'rare_patterns': [...],
                'pattern_statistics': {...}
            }
        """
        # Reset counters
        self.pattern_counts.clear()
        self.pattern_locations.clear()

        # Extract all subsequences
        for idx, sax_string in enumerate(sax_strings):
            for pattern_len in range(self.min_pattern_length, self.max_pattern_length + 1):
                # Sliding window
                for i in range(len(sax_string) - pattern_len + 1):
                    pattern = sax_string[i:i + pattern_len]

                    self.pattern_counts[pattern] += 1
                    self.pattern_locations[pattern].append({
                        'string_idx': idx,
                        'position': i
                    })

        # Filter by support
        frequent = []
        rare = []

        for pattern, count in self.pattern_counts.items():
            pattern_info = {
                'pattern': pattern,
                'count': count,
                'support': count / len(sax_strings),
                'length': len(pattern),
                'locations': self.pattern_locations[pattern]
            }

            if count >= min_support:
                frequent.append(pattern_info)
            elif count == 1:
                rare.append(pattern_info)

        # Sort by frequency
        frequent.sort(key=lambda x: x['count'], reverse=True)
        rare.sort(key=lambda x: x['length'], reverse=True)

        # Statistics
        stats = {
            'n_unique_patterns': len(self.pattern_counts),
            'n_frequent': len(frequent),
            'n_rare': len(rare),
            'most_common': frequent[0] if frequent else None,
            'longest_rare': rare[0] if rare else None
        }

        return {
            'frequent_patterns': frequent,
            'rare_patterns': rare,
            'pattern_statistics': stats
        }

    def find_pattern_associations(
        self,
        sax_strings: List[str],
        min_confidence: float = 0.7
    ) -> List[Dict]:
        """
        Find pattern associations (if A then B).

        Args:
            sax_strings: SAX representations
            min_confidence: Minimum confidence for association rule

        Returns:
            List of association rules
        """
        # Get frequent patterns
        patterns = self.mine_patterns(sax_strings)['frequent_patterns']

        associations = []

        # Look for sequential patterns
        for i, pattern1 in enumerate(patterns):
            for pattern2 in patterns[i + 1:]:
                # Check if pattern2 frequently follows pattern1
                p1_str = pattern1['pattern']
                p2_str = pattern2['pattern']

                # Count co-occurrences
                cooccur = 0
                p1_total = pattern1['count']

                for sax_string in sax_strings:
                    # Find all occurrences of p1
                    start = 0
                    while True:
                        idx = sax_string.find(p1_str, start)
                        if idx == -1:
                            break

                        # Check if p2 follows
                        next_pos = idx + len(p1_str)
                        if next_pos <= len(sax_string) - len(p2_str):
                            if sax_string[next_pos:next_pos + len(p2_str)] == p2_str:
                                cooccur += 1

                        start = idx + 1

                # Calculate confidence: P(p2 | p1)
                if p1_total > 0:
                    confidence = cooccur / p1_total

                    if confidence >= min_confidence:
                        associations.append({
                            'antecedent': p1_str,
                            'consequent': p2_str,
                            'confidence': confidence,
                            'support': cooccur / len(sax_strings),
                            'interpretation': f"Pattern '{p1_str}' → '{p2_str}' ({confidence:.1%} confidence)"
                        })

        # Sort by confidence
        associations.sort(key=lambda x: x['confidence'], reverse=True)

        return associations


class SAXPatternClassifier:
    """
    Classify time series based on SAX patterns.

    Uses bag-of-words approach with SAX patterns as features.
    """

    def __init__(
        self,
        word_size: int = 8,
        alphabet_size: int = 5,
        pattern_length: int = 3
    ):
        """Initialize SAX pattern classifier."""
        self.transformer = SAXTransformer(word_size, alphabet_size)
        self.pattern_length = pattern_length
        self.vocabulary = set()
        self.class_profiles = {}

    def fit(
        self,
        time_series_list: List[np.ndarray],
        labels: List[str]
    ):
        """
        Build pattern vocabulary and class profiles.

        Args:
            time_series_list: List of time series
            labels: Corresponding class labels
        """
        # Transform all series to SAX
        sax_strings = [self.transformer.transform(ts) for ts in time_series_list]

        # Build vocabulary
        for sax_string in sax_strings:
            patterns = self._extract_patterns(sax_string)
            self.vocabulary.update(patterns)

        # Build class profiles (pattern frequency per class)
        class_patterns = defaultdict(lambda: defaultdict(int))

        for sax_string, label in zip(sax_strings, labels):
            patterns = self._extract_patterns(sax_string)

            for pattern in patterns:
                class_patterns[label][pattern] += 1

        # Normalize to probabilities
        for label in class_patterns:
            total = sum(class_patterns[label].values())
            for pattern in class_patterns[label]:
                class_patterns[label][pattern] /= total

        self.class_profiles = dict(class_patterns)

    def predict(self, time_series: np.ndarray) -> Dict:
        """
        Classify time series based on pattern similarity.

        Args:
            time_series: Time series to classify

        Returns:
            {
                'predicted_class': str,
                'confidence': float,
                'class_scores': Dict[str, float]
            }
        """
        # Transform to SAX
        sax_string = self.transformer.transform(time_series)

        # Extract patterns
        patterns = self._extract_patterns(sax_string)
        pattern_freq = Counter(patterns)

        # Normalize
        total = sum(pattern_freq.values())
        for p in pattern_freq:
            pattern_freq[p] /= total

        # Compute similarity to each class profile
        class_scores = {}

        for label, profile in self.class_profiles.items():
            # Cosine similarity
            score = 0.0
            norm1 = 0.0
            norm2 = 0.0

            for pattern in self.vocabulary:
                f1 = pattern_freq.get(pattern, 0)
                f2 = profile.get(pattern, 0)

                score += f1 * f2
                norm1 += f1 ** 2
                norm2 += f2 ** 2

            if norm1 > 0 and norm2 > 0:
                similarity = score / (np.sqrt(norm1) * np.sqrt(norm2))
            else:
                similarity = 0.0

            class_scores[label] = similarity

        # Predict class with highest score
        if class_scores:
            predicted_class = max(class_scores, key=class_scores.get)
            confidence = class_scores[predicted_class]
        else:
            predicted_class = None
            confidence = 0.0

        return {
            'predicted_class': predicted_class,
            'confidence': confidence,
            'class_scores': class_scores
        }

    def _extract_patterns(self, sax_string: str) -> List[str]:
        """Extract all patterns of specified length."""
        patterns = []

        for i in range(len(sax_string) - self.pattern_length + 1):
            pattern = sax_string[i:i + self.pattern_length]
            patterns.append(pattern)

        return patterns


def quick_sax_analysis(
    time_series: Union[pd.Series, np.ndarray],
    word_size: int = 10,
    alphabet_size: int = 5
) -> Dict:
    """
    Convenience function for quick SAX analysis.

    Example:
        >>> result = quick_sax_analysis(stock_prices)
        >>> print(f"SAX: {result['sax_string']}")
        >>> print(f"Found {len(result['patterns'])} frequent patterns")
    """
    # Transform to SAX
    transformer = SAXTransformer(word_size, alphabet_size)
    sax_string = transformer.transform(time_series)

    # Mine patterns
    miner = SAXPatternMiner(word_size, alphabet_size)
    pattern_results = miner.mine_patterns([sax_string], min_support=1)

    return {
        'sax_string': sax_string,
        'word_size': word_size,
        'alphabet_size': alphabet_size,
        'patterns': pattern_results['frequent_patterns'],
        'statistics': pattern_results['pattern_statistics']
    }


__all__ = ['SAXTransformer', 'SAXPatternMiner', 'SAXPatternClassifier', 'quick_sax_analysis']
