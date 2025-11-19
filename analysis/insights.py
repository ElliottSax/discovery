"""
Automated Insight Generation Engine

Generates human-readable insights from pattern analysis results.
Uses rule-based logic, statistical significance testing, and anomaly scoring.

Key Features:
- Multi-model insight synthesis
- Significance testing
- Anomaly detection and scoring
- Natural language generation
- Prioritization and ranking

Author: Claude
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class InsightType(str, Enum):
    """Category of insight"""
    PATTERN = "pattern"
    ANOMALY = "anomaly"
    PREDICTION = "prediction"
    CORRELATION = "correlation"
    REGIME = "regime"
    SECTOR = "sector"
    RISK = "risk"


class InsightSeverity(str, Enum):
    """Severity/importance level"""
    CRITICAL = "critical"  # Requires immediate attention
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Insight:
    """A generated insight"""
    type: InsightType
    severity: InsightSeverity
    title: str
    description: str
    confidence: float  # 0-1
    evidence: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime


class InsightGenerator:
    """
    Generate automated insights from analysis results.
    """

    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize insight generator.

        Args:
            confidence_threshold: Minimum confidence for insights
        """
        self.confidence_threshold = confidence_threshold

    def generate_comprehensive_insights(
        self,
        fourier_result: Dict,
        hmm_result: Dict,
        dtw_result: Dict,
        ensemble_prediction: Optional[Any] = None,
        correlation_results: Optional[List] = None,
        sector_analysis: Optional[Dict] = None,
        politician_metadata: Optional[Dict] = None
    ) -> List[Insight]:
        """
        Generate all insights from complete analysis.

        Args:
            fourier_result: Fourier analysis results
            hmm_result: HMM regime detection results
            dtw_result: DTW pattern matching results
            ensemble_prediction: Ensemble model prediction
            correlation_results: Cross-politician correlations
            sector_analysis: Sector-based analysis
            politician_metadata: Politician information

        Returns:
            List of prioritized insights
        """
        insights = []

        # Generate insights from each source
        insights.extend(self._insights_from_fourier(fourier_result))
        insights.extend(self._insights_from_hmm(hmm_result))
        insights.extend(self._insights_from_dtw(dtw_result))

        if ensemble_prediction:
            insights.extend(self._insights_from_ensemble(ensemble_prediction))

        if correlation_results:
            insights.extend(self._insights_from_correlation(correlation_results, politician_metadata))

        if sector_analysis:
            insights.extend(self._insights_from_sector(sector_analysis))

        # Filter by confidence
        insights = [i for i in insights if i.confidence >= self.confidence_threshold]

        # Sort by severity and confidence
        severity_order = {
            InsightSeverity.CRITICAL: 0,
            InsightSeverity.HIGH: 1,
            InsightSeverity.MEDIUM: 2,
            InsightSeverity.LOW: 3,
            InsightSeverity.INFO: 4
        }

        insights.sort(key=lambda x: (severity_order[x.severity], -x.confidence))

        return insights

    def _insights_from_fourier(self, result: Dict) -> List[Insight]:
        """Generate insights from Fourier analysis"""
        insights = []

        if not result.get('dominant_cycles'):
            return insights

        top_cycle = result['dominant_cycles'][0]

        # Strong cycle detected
        if top_cycle['confidence'] > 0.85 and top_cycle['strength'] > 0.8:
            insights.append(Insight(
                type=InsightType.PATTERN,
                severity=InsightSeverity.HIGH,
                title=f"Highly Regular {top_cycle['category'].title()} Trading Cycle",
                description=(
                    f"Detected a strong {top_cycle['period_days']:.1f}-day trading cycle "
                    f"with {top_cycle['confidence']:.0%} confidence and {top_cycle['strength']:.2f} strength. "
                    f"This suggests systematic, planned trading behavior rather than opportunistic trades."
                ),
                confidence=top_cycle['confidence'],
                evidence={
                    'period_days': top_cycle['period_days'],
                    'strength': top_cycle['strength'],
                    'category': top_cycle['category']
                },
                recommendations=[
                    f"Monitor trading activity every {top_cycle['period_days']:.0f} days",
                    "Investigate if cycle aligns with earnings seasons or market events",
                    "Compare cycle timing with policy-making schedule"
                ],
                timestamp=datetime.utcnow()
            ))

        # Multiple strong cycles (complex pattern)
        strong_cycles = [c for c in result['dominant_cycles'] if c['confidence'] > 0.75]
        if len(strong_cycles) >= 3:
            cycle_periods = ', '.join([f"{c['period_days']:.0f}d" for c in strong_cycles[:3]])
            insights.append(Insight(
                type=InsightType.PATTERN,
                severity=InsightSeverity.MEDIUM,
                title="Complex Multi-Cycle Trading Pattern",
                description=(
                    f"Detected {len(strong_cycles)} distinct trading cycles "
                    f"({cycle_periods}). "
                    f"This indicates a sophisticated trading strategy with multiple time horizons."
                ),
                confidence=np.mean([c['confidence'] for c in strong_cycles]),
                evidence={
                    'num_cycles': len(strong_cycles),
                    'periods': [c['period_days'] for c in strong_cycles]
                },
                recommendations=[
                    "Analyze each cycle independently",
                    "Look for interactions between cycles",
                    "Check if cycles align with different types of information"
                ],
                timestamp=datetime.utcnow()
            ))

        # Election cycle detected
        election_cycles = [c for c in result['dominant_cycles'] if c['category'] == 'election_cycle']
        if election_cycles:
            cycle = election_cycles[0]
            insights.append(Insight(
                type=InsightType.PATTERN,
                severity=InsightSeverity.HIGH,
                title="Election Cycle Trading Pattern Detected",
                description=(
                    f"Detected {cycle['period_days']:.0f}-day cycle aligned with election cycles. "
                    f"Trading frequency may be correlated with political calendar and fundraising needs."
                ),
                confidence=cycle['confidence'],
                evidence=cycle,
                recommendations=[
                    "Compare with election dates",
                    "Investigate campaign finance correlation",
                    "Monitor leading up to elections"
                ],
                timestamp=datetime.utcnow()
            ))

        return insights

    def _insights_from_hmm(self, result: Dict) -> List[Insight]:
        """Generate insights from HMM regime detection"""
        insights = []

        if not result.get('regime_characteristics'):
            return insights

        current_regime_id = result.get('current_regime')
        if current_regime_id is None:
            return insights

        current_regime = result['regime_characteristics'].get(current_regime_id, {})
        regime_name = result.get('current_regime_name', 'Unknown')

        # Regime change imminent
        expected_duration = result.get('expected_duration', [float('inf')])[current_regime_id]
        if expected_duration < 7:
            insights.append(Insight(
                type=InsightType.REGIME,
                severity=InsightSeverity.HIGH,
                title=f"Regime Change Imminent: Exiting '{regime_name}'",
                description=(
                    f"Current trading regime ('{regime_name}') is expected to change within "
                    f"{expected_duration:.1f} days. Transition to different trading behavior is likely."
                ),
                confidence=0.85,
                evidence={
                    'current_regime': regime_name,
                    'expected_duration': expected_duration,
                    'transition_probabilities': result.get('transition_probabilities', {})
                },
                recommendations=[
                    "Monitor for regime transition",
                    "Identify trigger events for transition",
                    "Prepare for different trading pattern"
                ],
                timestamp=datetime.utcnow()
            ))

        # Unusual regime (rare occurrence)
        if current_regime.get('frequency', 0) < 0.15:
            insights.append(Insight(
                type=InsightType.ANOMALY,
                severity=InsightSeverity.MEDIUM,
                title=f"Rare Trading Regime: '{regime_name}'",
                description=(
                    f"Currently in a rare regime that occurs only {current_regime['frequency']:.1%} "
                    f"of the time. This may indicate unusual market conditions or behavior change."
                ),
                confidence=0.80,
                evidence=current_regime,
                recommendations=[
                    "Investigate what triggered this regime",
                    "Compare with historical periods in same regime",
                    "Monitor for return to typical behavior"
                ],
                timestamp=datetime.utcnow()
            ))

        # High volatility regime
        if current_regime.get('volatility', 0) > 0.03:
            insights.append(Insight(
                type=InsightType.RISK,
                severity=InsightSeverity.MEDIUM,
                title="High Volatility Trading Regime",
                description=(
                    f"Current regime shows high trading volatility "
                    f"(σ = {current_regime['volatility']:.3f}). "
                    f"Trading behavior is unpredictable and may indicate uncertainty or rapid strategy changes."
                ),
                confidence=0.75,
                evidence=current_regime,
                recommendations=[
                    "Increased monitoring recommended",
                    "Look for market events causing uncertainty",
                    "Compare with market volatility indices"
                ],
                timestamp=datetime.utcnow()
            ))

        return insights

    def _insights_from_dtw(self, result: Dict) -> List[Insight]:
        """Generate insights from DTW pattern matching"""
        insights = []

        matches_found = result.get('matches_found', 0)

        # No historical precedent (anomaly)
        if matches_found == 0:
            insights.append(Insight(
                type=InsightType.ANOMALY,
                severity=InsightSeverity.CRITICAL,
                title="⚠️ Unprecedented Trading Pattern",
                description=(
                    "No similar historical patterns found. Current trading behavior is unprecedented "
                    "in the politician's history. This could indicate:\n"
                    "• Response to unique market conditions\n"
                    "• Change in trading strategy\n"
                    "• Potential anomalous behavior requiring investigation"
                ),
                confidence=0.90,
                evidence={'matches_found': 0},
                recommendations=[
                    "IMMEDIATE: Detailed investigation required",
                    "Compare with major market events",
                    "Check for unusual information access",
                    "Review recent policy involvement"
                ],
                timestamp=datetime.utcnow()
            ))
            return insights

        # Strong historical precedent
        if matches_found > 0:
            top_match = result.get('top_matches', [{}])[0]
            similarity = top_match.get('similarity_score', 0)

            if similarity > 0.85:
                outcome_30d = top_match.get('outcome_30d_trades', 0)

                insights.append(Insight(
                    type=InsightType.PREDICTION,
                    severity=InsightSeverity.MEDIUM,
                    title=f"Strong Historical Precedent ({similarity:.0%} Match)",
                    description=(
                        f"Current pattern closely matches {top_match.get('match_date', 'past period')} "
                        f"({similarity:.0%} similarity). After that similar period, "
                        f"{'there were ' + str(int(abs(outcome_30d))) + ' ' + ('more' if outcome_30d > 0 else 'fewer') + ' trades' if outcome_30d else 'similar activity continued'} "
                        f"in the next 30 days."
                    ),
                    confidence=similarity,
                    evidence=top_match,
                    recommendations=[
                        "Review what happened after historical match",
                        "Compare market conditions then vs now",
                        f"Expect similar outcome: {outcome_30d:+.1f} trades" if outcome_30d else "Continue monitoring"
                    ],
                    timestamp=datetime.utcnow()
                ))

        return insights

    def _insights_from_ensemble(self, prediction: Any) -> List[Insight]:
        """Generate insights from ensemble prediction"""
        insights = []

        # Low model agreement (uncertainty)
        if prediction.model_agreement < 0.5:
            insights.append(Insight(
                type=InsightType.RISK,
                severity=InsightSeverity.MEDIUM,
                title="High Prediction Uncertainty",
                description=(
                    f"Models disagree significantly (agreement: {prediction.model_agreement:.1%}). "
                    f"This indicates high uncertainty and unpredictable trading behavior."
                ),
                confidence=1.0 - prediction.model_agreement,
                evidence={
                    'model_agreement': prediction.model_agreement,
                    'predictions': [
                        {'model': p.model_name, 'value': p.prediction, 'confidence': p.confidence}
                        for p in prediction.predictions
                    ]
                },
                recommendations=[
                    "Treat predictions with caution",
                    "Wait for more data before drawing conclusions",
                    "Monitor closely for clarifying signals"
                ],
                timestamp=datetime.utcnow()
            ))

        # High anomaly score
        if prediction.anomaly_score > 0.7:
            insights.append(Insight(
                type=InsightType.ANOMALY,
                severity=InsightSeverity.HIGH,
                title=f"Anomalous Behavior Detected (Score: {prediction.anomaly_score:.0%})",
                description=(
                    f"Ensemble model detected highly anomalous trading pattern "
                    f"(anomaly score: {prediction.anomaly_score:.0%}). "
                    f"Behavior significantly deviates from historical norms."
                ),
                confidence=prediction.anomaly_score,
                evidence={'anomaly_score': prediction.anomaly_score},
                recommendations=[
                    "PRIORITY: Detailed investigation recommended",
                    "Check for market events or policy changes",
                    "Review information access and timing",
                    "Compare with other politicians"
                ],
                timestamp=datetime.utcnow()
            ))

        # Large predicted change
        if abs(prediction.value) > 10:
            direction = "increase" if prediction.value > 0 else "decrease"
            insights.append(Insight(
                type=InsightType.PREDICTION,
                severity=InsightSeverity.HIGH,
                title=f"Large Trading {direction.title()} Predicted",
                description=(
                    f"Ensemble model predicts {abs(prediction.value):.1f} trade {direction} "
                    f"in the next 30 days ({prediction.confidence:.0%} confidence). "
                    f"This represents a significant change from typical activity."
                ),
                confidence=prediction.confidence,
                evidence={'predicted_change': prediction.value},
                recommendations=[
                    f"Prepare for {direction}d trading activity",
                    "Identify potential catalysts",
                    "Monitor actual vs predicted closely"
                ],
                timestamp=datetime.utcnow()
            ))

        return insights

    def _insights_from_correlation(
        self,
        correlations: List,
        metadata: Optional[Dict]
    ) -> List[Insight]:
        """Generate insights from correlation analysis"""
        insights = []

        # Find high correlations
        high_corrs = [c for c in correlations if abs(c.correlation) > 0.7 and c.p_value < 0.05]

        if not high_corrs:
            return insights

        # Coordinated trading detected
        for corr in high_corrs[:3]:  # Top 3
            pol1 = metadata.get(corr.politician1_id, {}).get('name', 'Politician 1') if metadata else 'Politician 1'
            pol2 = metadata.get(corr.politician2_id, {}).get('name', 'Politician 2') if metadata else 'Politician 2'

            insights.append(Insight(
                type=InsightType.CORRELATION,
                severity=InsightSeverity.HIGH if abs(corr.correlation) > 0.8 else InsightSeverity.MEDIUM,
                title=f"Highly Correlated Trading: {pol1} ↔ {pol2}",
                description=(
                    f"Strong correlation detected (r = {corr.correlation:.2f}, p < {corr.p_value:.3f}). "
                    f"{'Trading is synchronized' if corr.lag == 0 else f'{pol1} typically trades {abs(corr.lag)} days ' + ('before' if corr.lag > 0 else 'after') + f' {pol2}'}. "
                    f"This may indicate:\n"
                    f"• Shared portfolio management\n"
                    f"• Similar information access\n"
                    f"• Coordinated strategy\n"
                    f"• Common response to market signals"
                ),
                confidence=1.0 - corr.p_value,
                evidence={
                    'correlation': corr.correlation,
                    'p_value': corr.p_value,
                    'lag': corr.lag
                },
                recommendations=[
                    "Investigate relationship between politicians",
                    "Check for family or business connections",
                    "Compare committee assignments",
                    "Monitor for continued correlation"
                ],
                timestamp=datetime.utcnow()
            ))

        return insights

    def _insights_from_sector(self, analysis: Dict) -> List[Insight]:
        """Generate insights from sector analysis"""
        insights = []

        if not analysis:
            return insights

        # Strong sector concentration
        if 'sector_preference' in analysis:
            prefs = analysis['sector_preference']
            if prefs:
                top_sector = max(prefs.items(), key=lambda x: x[1])

                if top_sector[1] > 0.7:  # > 70% in one sector
                    insights.append(Insight(
                        type=InsightType.SECTOR,
                        severity=InsightSeverity.MEDIUM,
                        title=f"Heavy Concentration in {top_sector[0]} Sector",
                        description=(
                            f"{top_sector[1]:.0%} of trades are in {top_sector[0]} sector. "
                            f"This extreme concentration suggests:\n"
                            f"• Specialized knowledge or access\n"
                            f"• Committee/policy focus alignment\n"
                            f"• Potential conflict of interest risk"
                        ),
                        confidence=0.85,
                        evidence={'sector_distribution': prefs},
                        recommendations=[
                            f"Review {top_sector[0]} sector policy involvement",
                            "Check for committee assignments related to sector",
                            "Monitor for sector-specific information access",
                            "Assess diversification vs concentration risk"
                        ],
                        timestamp=datetime.utcnow()
                    ))

        return insights


def generate_executive_summary(insights: List[Insight]) -> str:
    """
    Generate executive summary from insights.

    Returns:
        Human-readable summary suitable for reports
    """
    if not insights:
        return "No significant insights found. Trading patterns appear normal."

    critical = [i for i in insights if i.severity == InsightSeverity.CRITICAL]
    high = [i for i in insights if i.severity == InsightSeverity.HIGH]

    summary = "# Executive Summary\n\n"

    if critical:
        summary += "## 🚨 Critical Issues\n\n"
        for insight in critical:
            summary += f"**{insight.title}**\n"
            summary += f"{insight.description}\n\n"

    if high:
        summary += "## ⚠️ High Priority Findings\n\n"
        for insight in high[:3]:  # Top 3
            summary += f"**{insight.title}**\n"
            summary += f"- Confidence: {insight.confidence:.0%}\n"
            summary += f"- Type: {insight.type.value}\n\n"

    # Overall assessment
    summary += "## Overall Assessment\n\n"

    if critical:
        summary += "**Status**: Requires immediate investigation\n"
    elif len(high) > 2:
        summary += "**Status**: Multiple concerns identified\n"
    else:
        summary += "**Status**: Normal with minor notes\n"

    summary += f"**Total Insights**: {len(insights)}\n"
    summary += f"**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"

    return summary
