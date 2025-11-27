"""
Pattern Deduplication System
Prevents storing duplicate patterns and identifies truly novel discoveries
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import logging

logger = logging.getLogger(__name__)


class PatternDeduplicator:
    """Deduplicates patterns and identifies novel ones"""

    def __init__(self, discoveries_file: Optional[Path] = None):
        """
        Initialize deduplicator

        Args:
            discoveries_file: Path to discoveries JSONL file
        """
        self.discoveries_file = discoveries_file or Path("./data/patterns/discoveries.jsonl")
        self.discoveries_file.parent.mkdir(parents=True, exist_ok=True)

        # Cache of recent pattern hashes
        self.recent_hashes: Set[str] = set()
        self.pattern_index: Dict[str, List[Dict]] = {}

        # Load existing patterns
        self._build_index()

    def _build_index(self):
        """Build index of existing patterns"""

        if not self.discoveries_file.exists():
            logger.info("No existing discoveries file, starting fresh")
            return

        logger.info(f"Building pattern index from {self.discoveries_file}")

        try:
            with open(self.discoveries_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        pattern = json.loads(line.strip())
                        pattern_hash = self._hash_pattern(pattern)

                        self.recent_hashes.add(pattern_hash)

                        # Index by type
                        pattern_type = pattern.get('type', 'unknown')
                        if pattern_type not in self.pattern_index:
                            self.pattern_index[pattern_type] = []

                        self.pattern_index[pattern_type].append(pattern)

                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON on line {line_num}")

            total_patterns = sum(len(patterns) for patterns in self.pattern_index.values())
            logger.info(f"Indexed {total_patterns} existing patterns")
            logger.info(f"Pattern types: {list(self.pattern_index.keys())}")

        except Exception as e:
            logger.error(f"Error building index: {e}")

    def _hash_pattern(self, pattern: Dict) -> str:
        """Create hash of pattern for deduplication"""

        # Extract key fields for hashing
        key_fields = {
            'type': pattern.get('type'),
            'finding': self._normalize_finding(pattern.get('finding', {}))
        }

        # Create deterministic JSON string
        json_str = json.dumps(key_fields, sort_keys=True)

        # Hash it
        return hashlib.md5(json_str.encode()).hexdigest()

    def _normalize_finding(self, finding: Any) -> Any:
        """Normalize finding data for comparison"""

        if isinstance(finding, dict):
            # Remove timestamp and other variable fields
            normalized = {
                k: v for k, v in finding.items()
                if k not in ['timestamp', 'date', 'generated_at', 'updated_at']
            }

            # Recursively normalize
            return {k: self._normalize_finding(v) for k, v in normalized.items()}

        elif isinstance(finding, list):
            return [self._normalize_finding(item) for item in finding]

        elif isinstance(finding, str):
            # Normalize strings (lowercase, strip)
            return finding.lower().strip()

        else:
            return finding

    def is_novel(self, pattern: Dict, similarity_threshold: float = 0.9) -> bool:
        """
        Check if pattern is novel

        Args:
            pattern: Pattern to check
            similarity_threshold: Similarity threshold (0-1)

        Returns:
            True if novel, False if duplicate/similar
        """

        pattern_hash = self._hash_pattern(pattern)

        # Exact duplicate check
        if pattern_hash in self.recent_hashes:
            logger.debug(f"Exact duplicate found for pattern {pattern.get('type')}")
            return False

        # Similarity check within same type
        pattern_type = pattern.get('type', 'unknown')
        similar_patterns = self.pattern_index.get(pattern_type, [])

        for existing in similar_patterns:
            similarity = self._calculate_similarity(pattern, existing)

            if similarity >= similarity_threshold:
                logger.debug(
                    f"Similar pattern found (similarity: {similarity:.2f}) "
                    f"for type {pattern_type}"
                )
                return False

        # Novel pattern!
        return True

    def _calculate_similarity(self, pattern1: Dict, pattern2: Dict) -> float:
        """Calculate similarity between two patterns (0-1)"""

        # Simple similarity based on field overlap
        # In production, use more sophisticated methods

        finding1 = pattern1.get('finding', {})
        finding2 = pattern2.get('finding', {})

        # Convert to comparable strings
        str1 = json.dumps(self._normalize_finding(finding1), sort_keys=True)
        str2 = json.dumps(self._normalize_finding(finding2), sort_keys=True)

        # Calculate Jaccard similarity on words
        words1 = set(str1.split())
        words2 = set(str2.split())

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union

    def add_pattern(self, pattern: Dict):
        """Add pattern to index"""

        pattern_hash = self._hash_pattern(pattern)
        self.recent_hashes.add(pattern_hash)

        pattern_type = pattern.get('type', 'unknown')
        if pattern_type not in self.pattern_index:
            self.pattern_index[pattern_type] = []

        self.pattern_index[pattern_type].append(pattern)

    def filter_novel(self, patterns: List[Dict]) -> List[Dict]:
        """
        Filter list to only novel patterns

        Args:
            patterns: List of patterns to filter

        Returns:
            List of novel patterns
        """

        novel = []

        for pattern in patterns:
            if self.is_novel(pattern):
                novel.append(pattern)
                self.add_pattern(pattern)  # Add to index
            else:
                logger.debug(f"Filtered out duplicate/similar pattern: {pattern.get('type')}")

        logger.info(f"Filtered {len(patterns)} patterns -> {len(novel)} novel")

        return novel

    def cleanup_old_patterns(self, days_to_keep: int = 30):
        """Remove patterns older than specified days"""

        if not self.discoveries_file.exists():
            return

        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

        temp_file = self.discoveries_file.with_suffix('.tmp')
        kept_count = 0
        removed_count = 0

        try:
            with open(self.discoveries_file, 'r') as infile, \
                 open(temp_file, 'w') as outfile:

                for line in infile:
                    try:
                        pattern = json.loads(line.strip())
                        timestamp = pattern.get('timestamp', '')

                        if timestamp >= cutoff_date:
                            outfile.write(line)
                            kept_count += 1
                        else:
                            removed_count += 1

                    except json.JSONDecodeError:
                        continue

            # Replace original with cleaned version
            temp_file.replace(self.discoveries_file)

            logger.info(f"Cleanup: kept {kept_count}, removed {removed_count} old patterns")

            # Rebuild index
            self._build_index()

        except Exception as e:
            logger.error(f"Error cleaning up old patterns: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def get_stats(self) -> Dict[str, Any]:
        """Get deduplicator statistics"""

        total_patterns = sum(len(patterns) for patterns in self.pattern_index.values())

        return {
            "total_patterns": total_patterns,
            "unique_hashes": len(self.recent_hashes),
            "pattern_types": {
                ptype: len(patterns)
                for ptype, patterns in self.pattern_index.items()
            },
            "discoveries_file": str(self.discoveries_file)
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    dedup = PatternDeduplicator()
    print("Pattern Deduplicator Stats:")
    print(json.dumps(dedup.get_stats(), indent=2))
