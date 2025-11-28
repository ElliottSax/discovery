"""
Adaptive Learning System for ULTRATHINK
Learns from past discoveries to improve future pattern detection
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class AdaptiveLearning:
    """System that learns and adapts from discovered patterns"""

    def __init__(self, discoveries_file: Path = None):
        self.discoveries_file = discoveries_file or Path("data/patterns/discoveries.jsonl")
        self.knowledge_base = Path("data/patterns/knowledge_base.json")

        self.pattern_weights = {}  # Learned weights for different pattern types
        self.successful_strategies = []  # Strategies that found good patterns
        self.failed_strategies = []  # Strategies that didn't work
        self.pattern_evolution = defaultdict(list)  # How patterns change over time

        # Load existing knowledge
        self._load_knowledge()

    def _load_knowledge(self):
        """Load accumulated knowledge from disk"""

        if self.knowledge_base.exists():
            try:
                with open(self.knowledge_base) as f:
                    data = json.load(f)

                self.pattern_weights = data.get("pattern_weights", {})
                self.successful_strategies = data.get("successful_strategies", [])
                self.failed_strategies = data.get("failed_strategies", [])

                logger.info(f"Loaded knowledge: {len(self.pattern_weights)} pattern types")
            except Exception as e:
                logger.error(f"Error loading knowledge base: {e}")

    def _save_knowledge(self):
        """Save accumulated knowledge to disk"""

        self.knowledge_base.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "pattern_weights": self.pattern_weights,
            "successful_strategies": self.successful_strategies,
            "failed_strategies": self.failed_strategies,
            "last_updated": datetime.now().isoformat(),
            "total_patterns_learned": sum(w.get("count", 0) for w in self.pattern_weights.values())
        }

        with open(self.knowledge_base, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info("Knowledge base saved")

    def learn_from_discoveries(self) -> Dict[str, Any]:
        """Analyze past discoveries and update knowledge"""

        if not self.discoveries_file.exists():
            return {"error": "No discoveries file found"}

        # Load all discoveries
        discoveries = []
        with open(self.discoveries_file) as f:
            for line in f:
                try:
                    discoveries.append(json.loads(line.strip()))
                except:
                    continue

        if not discoveries:
            return {"error": "No discoveries to learn from"}

        # Learn pattern frequencies
        pattern_counts = defaultdict(int)
        pattern_significances = defaultdict(list)

        for discovery in discoveries:
            dtype = discovery.get("type")
            finding = discovery.get("finding", {})

            # Count pattern types
            if isinstance(finding, dict):
                pattern_type = finding.get("type", dtype)
                pattern_counts[pattern_type] += 1

                # Track significance
                sig = finding.get("significance")
                if sig:
                    pattern_significances[pattern_type].append(sig)

        # Update weights based on frequency and significance
        for pattern_type, count in pattern_counts.items():
            # Calculate average significance score
            sigs = pattern_significances.get(pattern_type, [])
            sig_score = self._significance_to_score(sigs)

            # Update weight
            self.pattern_weights[pattern_type] = {
                "count": count,
                "significance_score": sig_score,
                "weight": count * sig_score,  # Combined score
                "last_seen": datetime.now().isoformat()
            }

        # Identify successful strategies
        self._identify_successful_strategies(discoveries)

        # Learn temporal patterns
        self._learn_temporal_patterns(discoveries)

        # Save updated knowledge
        self._save_knowledge()

        return {
            "patterns_analyzed": len(discoveries),
            "unique_pattern_types": len(self.pattern_weights),
            "top_patterns": sorted(
                self.pattern_weights.items(),
                key=lambda x: x[1]["weight"],
                reverse=True
            )[:5],
            "successful_strategies": len(self.successful_strategies)
        }

    def _significance_to_score(self, significances: List[str]) -> float:
        """Convert significance levels to numeric scores"""

        score_map = {
            "very_high": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.2
        }

        if not significances:
            return 0.5

        scores = [score_map.get(s, 0.5) for s in significances]
        return np.mean(scores)

    def _identify_successful_strategies(self, discoveries: List[Dict]):
        """Identify which detection strategies work best"""

        # Group by time windows
        time_windows = defaultdict(list)

        for discovery in discoveries:
            timestamp = discovery.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    window = dt.strftime("%Y-%m-%d %H")  # Hourly windows
                    time_windows[window].append(discovery)
                except:
                    continue

        # Find windows with many high-quality discoveries
        for window, window_discoveries in time_windows.items():
            if len(window_discoveries) >= 5:  # At least 5 discoveries
                high_sig = sum(1 for d in window_discoveries
                              if d.get("finding", {}).get("significance") in ["high", "very_high"])

                if high_sig / len(window_discoveries) > 0.6:  # >60% high significance
                    self.successful_strategies.append({
                        "window": window,
                        "discoveries": len(window_discoveries),
                        "high_significance_ratio": high_sig / len(window_discoveries),
                        "pattern_types": list(set(d.get("type") for d in window_discoveries))
                    })

    def _learn_temporal_patterns(self, discoveries: List[Dict]):
        """Learn how patterns evolve over time"""

        # Group by pattern type
        by_type = defaultdict(list)

        for discovery in discoveries:
            finding = discovery.get("finding", {})
            if isinstance(finding, dict):
                pattern_type = finding.get("type", discovery.get("type"))
                timestamp = discovery.get("timestamp")

                if timestamp:
                    by_type[pattern_type].append({
                        "timestamp": timestamp,
                        "data": finding.get("data", {})
                    })

        # Analyze evolution
        for pattern_type, instances in by_type.items():
            if len(instances) < 3:
                continue

            # Sort by time
            instances.sort(key=lambda x: x["timestamp"])

            # Track changes
            self.pattern_evolution[pattern_type] = {
                "first_seen": instances[0]["timestamp"],
                "last_seen": instances[-1]["timestamp"],
                "frequency": len(instances),
                "trend": "increasing" if len(instances[-5:]) > len(instances[:5]) else "stable"
            }

    def suggest_parameters(self) -> Dict[str, Any]:
        """Suggest optimal parameters based on learning"""

        suggestions = {
            "analysis_interval_minutes": 30,
            "pattern_thresholds": {},
            "focus_areas": []
        }

        # If certain patterns are found frequently, suggest focusing on them
        if self.pattern_weights:
            top_patterns = sorted(
                self.pattern_weights.items(),
                key=lambda x: x[1]["weight"],
                reverse=True
            )[:3]

            suggestions["focus_areas"] = [p[0] for p in top_patterns]

            # Suggest thresholds
            for pattern_type, weights in self.pattern_weights.items():
                if weights["weight"] > 10:  # High weight
                    suggestions["pattern_thresholds"][pattern_type] = 0.7  # Lower threshold
                else:
                    suggestions["pattern_thresholds"][pattern_type] = 0.9  # Higher threshold

        # If we're finding lots of patterns quickly, increase frequency
        if self.successful_strategies:
            avg_discoveries = np.mean([s["discoveries"] for s in self.successful_strategies])
            if avg_discoveries > 10:
                suggestions["analysis_interval_minutes"] = 15  # More frequent

        return suggestions

    def get_pattern_priority(self, pattern_type: str) -> float:
        """Get priority score for a pattern type (0-1)"""

        if pattern_type in self.pattern_weights:
            weight = self.pattern_weights[pattern_type]["weight"]
            max_weight = max(w["weight"] for w in self.pattern_weights.values())
            return weight / max_weight if max_weight > 0 else 0.5

        return 0.5  # Default priority

    def should_investigate_deeper(self, pattern: Dict) -> bool:
        """Decide if a pattern warrants deeper investigation"""

        finding = pattern.get("finding", {})

        # High significance always gets investigated
        if finding.get("significance") in ["very_high", "high"]:
            return True

        # Pattern types we've learned are important
        pattern_type = finding.get("type", pattern.get("type"))
        priority = self.get_pattern_priority(pattern_type)

        return priority > 0.7

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""

        return {
            "knowledge_base_size": len(self.pattern_weights),
            "total_patterns_learned": sum(w.get("count", 0) for w in self.pattern_weights.values()),
            "successful_strategies": len(self.successful_strategies),
            "pattern_evolution_tracked": len(self.pattern_evolution),
            "top_priority_patterns": sorted(
                [(k, v["weight"]) for k, v in self.pattern_weights.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }


class PatternScorer:
    """Advanced pattern scoring and ranking system"""

    def __init__(self):
        self.adaptive = AdaptiveLearning()

    def score_pattern(self, pattern: Dict) -> Dict[str, Any]:
        """Comprehensive pattern scoring"""

        finding = pattern.get("finding", {})
        pattern_type = finding.get("type", pattern.get("type"))

        scores = {
            "novelty": 0.0,
            "significance": 0.0,
            "confidence": 0.0,
            "actionability": 0.0,
            "risk": 0.0
        }

        # Novelty score (from adaptive learning)
        priority = self.adaptive.get_pattern_priority(pattern_type)
        scores["novelty"] = 1.0 - priority  # Lower priority = more novel

        # Significance score
        sig = finding.get("significance", "medium")
        sig_map = {"very_high": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
        scores["significance"] = sig_map.get(sig, 0.5)

        # Confidence score
        if "confidence" in finding:
            scores["confidence"] = finding["confidence"]
        elif "p_value" in finding.get("data", {}):
            # Convert p-value to confidence
            p_val = finding["data"]["p_value"]
            scores["confidence"] = 1.0 - p_val
        else:
            scores["confidence"] = 0.5

        # Actionability score (can we act on this?)
        if pattern_type in ["synchronized", "mimicry"]:
            scores["actionability"] = 0.9  # Highly actionable
        elif pattern_type in ["timing_pattern", "burst_trading"]:
            scores["actionability"] = 0.7
        else:
            scores["actionability"] = 0.5

        # Risk score (regulatory/legal risk)
        if finding.get("significance") == "very_high":
            scores["risk"] = 0.8  # High significance = high risk
        elif "anomaly" in pattern_type or "outlier" in pattern_type:
            scores["risk"] = 0.7
        else:
            scores["risk"] = 0.3

        # Overall score (weighted combination)
        overall = (
            scores["novelty"] * 0.25 +
            scores["significance"] * 0.30 +
            scores["confidence"] * 0.25 +
            scores["actionability"] * 0.15 +
            (1 - scores["risk"]) * 0.05  # Lower risk is better
        )

        return {
            "overall_score": overall,
            "scores": scores,
            "rank": self._score_to_rank(overall),
            "priority": "critical" if overall > 0.85 else "high" if overall > 0.7 else "medium" if overall > 0.5 else "low"
        }

    def _score_to_rank(self, score: float) -> str:
        """Convert score to letter rank"""

        if score >= 0.9:
            return "S"  # S-tier
        elif score >= 0.8:
            return "A+"
        elif score >= 0.7:
            return "A"
        elif score >= 0.6:
            return "B"
        elif score >= 0.5:
            return "C"
        else:
            return "D"

    def rank_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """Rank patterns by score"""

        scored = []

        for pattern in patterns:
            scoring = self.score_pattern(pattern)
            pattern_with_score = pattern.copy()
            pattern_with_score["scoring"] = scoring
            scored.append(pattern_with_score)

        # Sort by overall score
        scored.sort(key=lambda x: x["scoring"]["overall_score"], reverse=True)

        return scored


__all__ = ['AdaptiveLearning', 'PatternScorer']


if __name__ == "__main__":
    # Test adaptive learning
    logging.basicConfig(level=logging.INFO)

    adaptive = AdaptiveLearning()
    result = adaptive.learn_from_discoveries()

    print("Learning Results:")
    print(json.dumps(result, indent=2))

    print("\nSuggested Parameters:")
    print(json.dumps(adaptive.suggest_parameters(), indent=2))

    print("\nLearning Stats:")
    print(json.dumps(adaptive.get_learning_stats(), indent=2))
