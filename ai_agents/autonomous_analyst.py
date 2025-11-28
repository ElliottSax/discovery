"""
Autonomous Pattern Discovery Agent
Uses cheap LLMs + advanced ML to discover novel patterns 24/7
This is the "ULTRATHINK" component
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ai_agents.llm_router import get_llm_router, generate_with_retry
from ml_models.advanced_models import EnsemblePatternDetector
from ml_models.quant_patterns import QuantitativePatternDetector
from ai_agents.deepseek_ultra import DeepSeekUltra
from ai_agents.adaptive_learning import AdaptiveLearning, PatternScorer
from data_pipeline.db_to_pipeline import PipelineGenerator
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class AutonomousAnalyst:
    """Autonomous agent that continuously discovers patterns"""

    def __init__(self):
        self.llm_router = get_llm_router()
        self.ml_detector = EnsemblePatternDetector()
        self.quant_detector = QuantitativePatternDetector()
        self.deepseek_ultra = DeepSeekUltra()
        self.adaptive_learning = AdaptiveLearning()
        self.pattern_scorer = PatternScorer()
        self.pipeline_gen = PipelineGenerator()

        self.db_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'quant_db'),
            'user': os.getenv('DB_USER', 'quant_user'),
            'password': os.getenv('DB_PASSWORD', 'REDACTED_PASSWORD')
        }

        self.discoveries_file = Path("./data/patterns/discoveries.jsonl")
        self.discoveries_file.parent.mkdir(parents=True, exist_ok=True)

        self.analysis_count = 0
        self.discoveries_count = 0

    async def analyze_once(self) -> Dict[str, Any]:
        """Run one complete analysis cycle"""

        logger.info(f"=== Starting Analysis Cycle #{self.analysis_count + 1} ===")

        try:
            # Step 0: Learn from past discoveries and optimize parameters
            learning_result = self.adaptive_learning.learn_from_discoveries()
            suggested_params = self.adaptive_learning.suggest_parameters()
            logger.info(f"Adaptive learning: {learning_result.get('patterns_analyzed', 0)} patterns analyzed")

            # Step 1: Load fresh data from database
            trades = self._load_trades_from_db()
            logger.info(f"Loaded {len(trades)} trades from database")

            # Step 2: Run ML pattern detection
            ml_patterns = self.ml_detector.detect_all_patterns(trades)
            logger.info(f"ML detected {len(ml_patterns.get('novel_discoveries', []))} novel patterns")

            # Step 2b: Run quantitative pattern detection (NEW!)
            quant_patterns = self.quant_detector.detect_all_quant_patterns(trades)
            logger.info(f"Quant detected {len(quant_patterns.get('statistical_patterns', []))} statistical patterns")

            # Step 3: Prepare data summary
            data_summary = self._prepare_data_summary(trades, ml_patterns)
            data_summary['quant_patterns'] = quant_patterns

            # Step 4: Generate hypotheses using DeepSeek Ultra (NEW!)
            hypotheses = await self.deepseek_ultra.generate_hypotheses(data_summary, ml_patterns)
            logger.info(f"DeepSeek generated {len(hypotheses)} hypotheses")

            # Step 5: Use AI to discover novel patterns (NEW!)
            known_patterns = ml_patterns.get('novel_discoveries', [])
            ai_novel_patterns = await self.deepseek_ultra.discover_novel_patterns(trades, known_patterns)
            logger.info(f"AI discovered {len(ai_novel_patterns)} novel patterns")

            # Step 6: Use LLM to analyze and interpret patterns
            llm_analysis = await self._llm_deep_analysis(trades, ml_patterns)
            logger.info(f"LLM analysis complete")

            # Step 7: Find unusual/novel patterns that need attention
            novel_findings = self._extract_novel_findings(
                ml_patterns, quant_patterns, llm_analysis, hypotheses, ai_novel_patterns
            )
            logger.info(f"Found {len(novel_findings)} novel findings")

            # Step 8: Score and rank all findings (NEW!)
            scored_findings = self.pattern_scorer.rank_patterns(novel_findings)
            high_priority = [f for f in scored_findings if f['scoring']['priority'] in ['critical', 'high']]
            logger.info(f"Scored findings: {len(high_priority)} high priority")

            # Step 9: Deep analysis of top patterns using DeepSeek (NEW!)
            deep_analyses = []
            for finding in high_priority[:3]:  # Analyze top 3
                if self.adaptive_learning.should_investigate_deeper(finding):
                    analysis = await self.deepseek_ultra.deep_pattern_analysis(finding)
                    deep_analyses.append(analysis)
            logger.info(f"Deep analysis completed on {len(deep_analyses)} patterns")

            # Step 10: Store discoveries
            if scored_findings:
                self._store_discoveries(scored_findings)

            # Step 11: Generate pipeline data for API
            self.pipeline_gen.generate_all()

            result = {
                "cycle": self.analysis_count + 1,
                "timestamp": datetime.now().isoformat(),
                "trades_analyzed": len(trades),
                "learning_stats": learning_result,
                "suggested_params": suggested_params,
                "ml_patterns": ml_patterns,
                "quant_patterns": quant_patterns,
                "llm_analysis": llm_analysis,
                "hypotheses": hypotheses,
                "ai_novel_patterns": ai_novel_patterns,
                "novel_findings": scored_findings,  # Return full list for orchestrator
                "high_priority_findings": high_priority,
                "deep_analyses": deep_analyses,
                "total_discoveries": self.discoveries_count
            }

            self.analysis_count += 1

            return result

        except Exception as e:
            logger.error(f"Error in analysis cycle: {e}", exc_info=True)
            return {
                "cycle": self.analysis_count + 1,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _load_trades_from_db(self) -> List[Dict]:
        """Load all trades from database"""

        conn = psycopg2.connect(**self.db_params)
        trades = []

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        t.*,
                        p.name as politician_name,
                        p.chamber,
                        p.state,
                        p.party
                    FROM trades t
                    LEFT JOIN politicians p ON t.politician_id = p.id
                    ORDER BY t.transaction_date DESC
                """)

                rows = cur.fetchall()

                for row in rows:
                    trade = dict(row)
                    # Convert dates to strings
                    if trade.get('transaction_date'):
                        trade['transaction_date'] = trade['transaction_date'].isoformat()
                    if trade.get('disclosure_date'):
                        trade['disclosure_date'] = trade['disclosure_date'].isoformat()

                    # Convert Decimal to float for ML processing
                    if trade.get('amount_min'):
                        trade['amount_min'] = float(trade['amount_min'])
                    if trade.get('amount_max'):
                        trade['amount_max'] = float(trade['amount_max'])

                    trades.append(trade)

            conn.close()
            return trades

        except Exception as e:
            logger.error(f"Error loading trades: {e}")
            if conn:
                conn.close()
            return []

    async def _llm_deep_analysis(self, trades: List[Dict], ml_patterns: Dict) -> Dict[str, Any]:
        """Use LLM to deeply analyze the patterns"""

        # Prepare summary of data for LLM
        summary = self._prepare_data_summary(trades, ml_patterns)

        prompt = f"""You are an expert financial analyst specializing in political trading patterns.

DATA SUMMARY:
{json.dumps(summary, indent=2)}

TASK: Analyze this data and provide insights on:

1. What are the most significant patterns you observe?
2. Are there any unusual or suspicious trading behaviors?
3. Which patterns suggest possible insider knowledge or market manipulation?
4. What correlations exist between politicians, timing, and specific stocks?
5. What novel patterns exist that traditional analysis might miss?

Be specific, cite data, and rank findings by significance.

RESPOND IN JSON FORMAT:
{{
    "top_insights": [
        {{"insight": "...", "significance": "high|medium|low", "evidence": "..."}}
    ],
    "suspicious_patterns": [
        {{"pattern": "...", "politicians": [...], "risk_level": "high|medium|low"}}
    ],
    "correlations": [
        {{"correlation": "...", "strength": 0-1, "details": "..."}}
    ],
    "novel_discoveries": [
        {{"discovery": "...", "novelty_score": 0-1, "implications": "..."}}
    ]
}}
"""

        try:
            response = await generate_with_retry(
                prompt=prompt,
                system_prompt="You are an expert financial analyst. Always respond with valid JSON.",
                max_tokens=3000,
                temperature=0.7
            )

            # Try to parse JSON response
            try:
                # Extract JSON from response (handle markdown code blocks)
                json_str = response
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0].strip()

                analysis = json.loads(json_str)
                return analysis

            except json.JSONDecodeError:
                logger.warning("LLM response was not valid JSON, using raw text")
                return {
                    "raw_analysis": response,
                    "parsed": False
                }

        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return {"error": str(e)}

    async def _generate_hypotheses(self, ml_patterns: Dict, llm_analysis: Dict) -> List[Dict]:
        """Generate hypotheses about why patterns exist"""

        # Extract key findings
        novel_ml = ml_patterns.get('novel_discoveries', [])
        novel_llm = llm_analysis.get('novel_discoveries', [])

        if not novel_ml and not novel_llm:
            return []

        prompt = f"""You are a financial research scientist. Generate testable hypotheses to explain these patterns.

ML PATTERNS DETECTED:
{json.dumps(novel_ml[:5], indent=2)}

LLM INSIGHTS:
{json.dumps(novel_llm[:5], indent=2)}

TASK: Generate 3-5 testable hypotheses that could explain these patterns.

For each hypothesis:
1. State the hypothesis clearly
2. Explain the reasoning
3. Suggest how to test it
4. Rate the likelihood (0-1)

RESPOND IN JSON:
{{
    "hypotheses": [
        {{
            "hypothesis": "...",
            "reasoning": "...",
            "test_method": "...",
            "likelihood": 0.0-1.0,
            "implications": "..."
        }}
    ]
}}
"""

        try:
            response = await generate_with_retry(
                prompt=prompt,
                system_prompt="You are a financial research scientist. Respond with valid JSON.",
                max_tokens=2000,
                temperature=0.8  # Higher temperature for creativity
            )

            # Parse JSON
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()

            result = json.loads(json_str)
            return result.get("hypotheses", [])

        except Exception as e:
            logger.error(f"Error generating hypotheses: {e}")
            return []

    def _prepare_data_summary(self, trades: List[Dict], ml_patterns: Dict) -> Dict:
        """Prepare concise summary for LLM"""

        # Get top politicians by trade count
        pol_trades = {}
        for trade in trades:
            pol = trade.get('politician_name')
            if pol:
                pol_trades[pol] = pol_trades.get(pol, 0) + 1

        top_pols = sorted(pol_trades.items(), key=lambda x: x[1], reverse=True)[:10]

        # Get top stocks
        stock_trades = {}
        for trade in trades:
            ticker = trade.get('ticker')
            if ticker:
                stock_trades[ticker] = stock_trades.get(ticker, 0) + 1

        top_stocks = sorted(stock_trades.items(), key=lambda x: x[1], reverse=True)[:10]

        # Recent trades (last 30 days)
        recent_date = (datetime.now() - timedelta(days=30)).isoformat()
        recent_trades = [t for t in trades if t.get('transaction_date', '') >= recent_date]

        return {
            "total_trades": len(trades),
            "total_politicians": len(pol_trades),
            "total_stocks": len(stock_trades),
            "top_politicians": [{"name": p, "trades": c} for p, c in top_pols],
            "top_stocks": [{"ticker": s, "trades": c} for s, c in top_stocks],
            "recent_trades_30d": len(recent_trades),
            "ml_novel_patterns": len(ml_patterns.get('novel_discoveries', [])),
            "synchronized_trading_events": len(ml_patterns.get('cross_patterns', {}).get('synchronized_trading', [])),
            "mimicry_pairs": len(ml_patterns.get('cross_patterns', {}).get('mimicry_patterns', []))
        }

    def _extract_novel_findings(self, ml_patterns: Dict, quant_patterns: Dict,
                                 llm_analysis: Dict, hypotheses: List[Dict],
                                 ai_novel_patterns: List[Dict]) -> List[Dict]:
        """Extract truly novel and significant findings"""

        findings = []

        # High significance LLM insights
        for insight in llm_analysis.get('top_insights', []):
            if insight.get('significance') == 'high':
                findings.append({
                    "type": "llm_insight",
                    "finding": insight,
                    "timestamp": datetime.now().isoformat()
                })

        # Suspicious patterns
        for pattern in llm_analysis.get('suspicious_patterns', []):
            if pattern.get('risk_level') in ['high', 'medium']:
                findings.append({
                    "type": "suspicious_pattern",
                    "finding": pattern,
                    "timestamp": datetime.now().isoformat()
                })

        # Strong correlations
        for corr in llm_analysis.get('correlations', []):
            if corr.get('strength', 0) > 0.6:
                findings.append({
                    "type": "correlation",
                    "finding": corr,
                    "timestamp": datetime.now().isoformat()
                })

        # ML novel discoveries
        for discovery in ml_patterns.get('novel_discoveries', []):
            if discovery.get('significance') in ['high', 'very_high']:
                findings.append({
                    "type": "ml_discovery",
                    "finding": discovery,
                    "timestamp": datetime.now().isoformat()
                })

        # Quantitative statistical patterns (NEW!)
        for stat_pattern in quant_patterns.get('statistical_patterns', []):
            if stat_pattern.get('significant'):
                findings.append({
                    "type": "quant_statistical",
                    "finding": stat_pattern,
                    "timestamp": datetime.now().isoformat()
                })

        # Quantitative anomalies (NEW!)
        for anomaly in quant_patterns.get('anomalies', []):
            findings.append({
                "type": "quant_anomaly",
                "finding": anomaly,
                "timestamp": datetime.now().isoformat()
            })

        # AI-discovered novel patterns (NEW!)
        for ai_pattern in ai_novel_patterns:
            if ai_pattern.get('significance') in ['high', 'medium']:
                findings.append({
                    "type": "ai_novel_pattern",
                    "finding": ai_pattern,
                    "timestamp": datetime.now().isoformat()
                })

        # High likelihood hypotheses
        for hypothesis in hypotheses:
            if hypothesis.get('likelihood', 0) > 0.7:
                findings.append({
                    "type": "hypothesis",
                    "finding": hypothesis,
                    "timestamp": datetime.now().isoformat()
                })

        return findings

    def _store_discoveries(self, findings: List[Dict]):
        """Store discoveries to JSONL file"""

        try:
            with open(self.discoveries_file, 'a') as f:
                for finding in findings:
                    f.write(json.dumps(finding) + '\n')
                    self.discoveries_count += 1

            logger.info(f"Stored {len(findings)} discoveries to {self.discoveries_file}")

        except Exception as e:
            logger.error(f"Error storing discoveries: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get analyst statistics"""

        return {
            "analysis_cycles_completed": self.analysis_count,
            "total_discoveries": self.discoveries_count,
            "llm_stats": self.llm_router.get_stats(),
            "deepseek_stats": self.deepseek_ultra.get_stats(),
            "learning_stats": self.adaptive_learning.get_learning_stats(),
            "discoveries_file": str(self.discoveries_file),
            "uptime": "24/7"
        }


# CLI interface
async def main():
    """Run one analysis cycle (for testing)"""

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    analyst = AutonomousAnalyst()

    logger.info("Starting autonomous analysis...")
    result = await analyst.analyze_once()

    print("\n" + "="*80)
    print("ANALYSIS RESULTS")
    print("="*80)
    print(json.dumps(result, indent=2))
    print("\n" + "="*80)
    print("ANALYST STATS")
    print("="*80)
    print(json.dumps(analyst.get_stats(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
