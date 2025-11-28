"""
DeepSeek Ultra-Intelligence Layer
Advanced AI-powered pattern discovery and hypothesis generation
Uses DeepSeek and multiple AI models in parallel for deep analysis
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from ai_agents.llm_router import get_llm_router, LLMProvider

logger = logging.getLogger(__name__)


class DeepSeekUltra:
    """Ultra-advanced AI analysis using DeepSeek and ensemble AI"""

    def __init__(self):
        self.router = get_llm_router()
        self.analysis_history = []
        self.pattern_library = {}

    async def generate_hypotheses(self, data_summary: Dict, ml_patterns: Dict) -> List[Dict]:
        """Generate deep hypotheses using AI"""

        prompt = f"""You are a world-class quantitative analyst and financial detective.

TRADING DATA SUMMARY:
{json.dumps(data_summary, indent=2)}

MACHINE LEARNING PATTERNS DETECTED:
{json.dumps(ml_patterns, indent=2)}

YOUR TASK: Generate 10 testable hypotheses that explain these patterns. Think like a quant:

1. Consider market microstructure, information asymmetry, regulatory loopholes
2. Look for alpha-generating strategies being employed
3. Identify risk arbitrage opportunities
4. Detect possible insider information flows
5. Find systematic trading strategies
6. Analyze timing relative to market events
7. Consider portfolio theory and hedging strategies
8. Look for coordinated behavior across parties
9. Identify statistical arbitrage patterns
10. Find anomalies that violate efficient market hypothesis

For each hypothesis, provide:
- Clear statement of the pattern
- Statistical evidence from the data
- Testable prediction
- Profit/information mechanism
- Risk level (low/medium/high)
- Likelihood score (0-1)
- Specific stocks/politicians involved

RESPOND IN VALID JSON:
{{
    "hypotheses": [
        {{
            "id": "H001",
            "hypothesis": "...",
            "evidence": "...",
            "test_method": "...",
            "mechanism": "...",
            "risk_level": "high|medium|low",
            "likelihood": 0.0-1.0,
            "entities": {{"politicians": [...], "stocks": [...]}},
            "expected_alpha": "...",
            "statistical_significance": 0.0-1.0
        }}
    ]
}}
"""

        try:
            response = await self.router.generate(
                prompt=prompt,
                system_prompt="You are a quantitative finance expert specializing in market microstructure, information asymmetry, and statistical arbitrage. Always respond with valid JSON.",
                max_tokens=4000,
                temperature=0.8,  # Higher for creativity
                preferred_provider=LLMProvider.DEEPSEEK  # Prefer DeepSeek
            )

            content = response["content"]

            # Parse JSON
            json_str = self._extract_json(content)
            result = json.loads(json_str)

            hypotheses = result.get("hypotheses", [])

            # Rank by likelihood and statistical significance
            hypotheses.sort(key=lambda x: x.get("likelihood", 0) * x.get("statistical_significance", 0), reverse=True)

            return hypotheses

        except Exception as e:
            logger.error(f"Error generating hypotheses: {e}")
            return []

    async def deep_pattern_analysis(self, pattern: Dict) -> Dict[str, Any]:
        """Deep dive analysis of a specific pattern using AI"""

        prompt = f"""You are analyzing a suspicious trading pattern. Conduct a DEEP investigation.

PATTERN DETAILS:
{json.dumps(pattern, indent=2)}

INVESTIGATION CHECKLIST:
1. What market information could explain this pattern?
2. Timeline: What happened before/during/after these trades?
3. Is this pattern consistent with legal trading or possible violations?
4. What is the statistical probability of this occurring by chance?
5. Are there similar historical precedents?
6. What regulatory filings or news events correlate?
7. How much alpha could this strategy generate?
8. What risks does the trader face?
9. Is this front-running, insider trading, or legitimate market-making?
10. What would SEC/investigators look for?

Provide a detailed forensic analysis.

RESPOND IN VALID JSON:
{{
    "pattern_id": "...",
    "investigation_findings": {{
        "likely_explanation": "...",
        "legal_analysis": "...",
        "statistical_probability": 0.0-1.0,
        "comparable_cases": [...],
        "correlated_events": [...],
        "estimated_alpha": "...",
        "risk_assessment": "...",
        "regulatory_concerns": [...],
        "recommendation": "..."
    }},
    "evidence_strength": "strong|moderate|weak",
    "confidence": 0.0-1.0
}}
"""

        try:
            response = await self.router.generate(
                prompt=prompt,
                system_prompt="You are a forensic financial analyst and regulatory expert.",
                max_tokens=3000,
                temperature=0.7,
                preferred_provider=LLMProvider.DEEPSEEK
            )

            content = response["content"]
            json_str = self._extract_json(content)
            result = json.loads(json_str)

            return result

        except Exception as e:
            logger.error(f"Error in deep analysis: {e}")
            return {"error": str(e)}

    async def multi_ai_consensus(self, question: str, context: Dict) -> Dict[str, Any]:
        """Get consensus from multiple AI models for robust analysis"""

        # Prepare same prompt for all models
        prompt = f"""Question: {question}

Context:
{json.dumps(context, indent=2)}

Provide your expert analysis with confidence score (0-1).

RESPOND IN JSON:
{{
    "analysis": "...",
    "confidence": 0.0-1.0,
    "key_factors": [...],
    "recommendation": "..."
}}
"""

        # Query multiple providers in parallel
        providers = [
            LLMProvider.DEEPSEEK,
            LLMProvider.TOGETHER,
            LLMProvider.OPENROUTER_QWEN,
        ]

        tasks = []
        for provider in providers:
            if self.router.api_keys.get(provider):
                task = self.router.generate(
                    prompt=prompt,
                    max_tokens=2000,
                    temperature=0.6,
                    preferred_provider=provider
                )
                tasks.append(task)

        # If no API keys, use local
        if not tasks:
            tasks.append(self.router.generate(prompt=prompt, max_tokens=2000))

        # Execute in parallel
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Parse and aggregate responses
        analyses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.warning(f"Provider {i} failed: {response}")
                continue

            try:
                content = response["content"]
                json_str = self._extract_json(content)
                analysis = json.loads(json_str)
                analysis["provider"] = response.get("provider", "unknown")
                analyses.append(analysis)
            except Exception as e:
                logger.warning(f"Failed to parse response {i}: {e}")

        # Calculate consensus
        if analyses:
            avg_confidence = sum(a.get("confidence", 0) for a in analyses) / len(analyses)

            # Extract common key factors
            all_factors = []
            for a in analyses:
                all_factors.extend(a.get("key_factors", []))

            # Count frequency
            factor_counts = {}
            for factor in all_factors:
                factor_counts[factor] = factor_counts.get(factor, 0) + 1

            # Get consensus factors (mentioned by >50% of models)
            consensus_threshold = len(analyses) / 2
            consensus_factors = [f for f, count in factor_counts.items() if count > consensus_threshold]

            return {
                "question": question,
                "consensus_analysis": " ".join(a.get("analysis", "") for a in analyses),
                "consensus_confidence": avg_confidence,
                "consensus_factors": consensus_factors,
                "individual_analyses": analyses,
                "num_models": len(analyses),
                "agreement_score": len(consensus_factors) / max(len(all_factors), 1) if all_factors else 0
            }
        else:
            return {"error": "All AI providers failed"}

    async def discover_novel_patterns(self, trades: List[Dict], known_patterns: List[Dict]) -> List[Dict]:
        """Use AI to discover patterns that ML might miss"""

        # Sample trades for AI analysis
        sample_size = min(100, len(trades))
        trade_sample = trades[:sample_size]

        # Prepare trade sample (keep only essential fields to reduce token usage)
        simplified_sample = []
        for trade in trade_sample[:20]:
            simplified = {
                'politician': trade.get('politician_name'),
                'ticker': trade.get('ticker'),
                'type': trade.get('type'),
                'transaction_date': str(trade.get('transaction_date')),
                'amount': trade.get('amount_min'),
                'party': trade.get('party'),
                'chamber': trade.get('chamber')
            }
            simplified_sample.append(simplified)

        prompt = f"""You are discovering NOVEL trading patterns that traditional algorithms miss.

TRADE SAMPLE:
{json.dumps(simplified_sample, indent=2)}
... (total {len(trade_sample)} trades)

KNOWN PATTERNS (already discovered):
{json.dumps([p.get("type") for p in known_patterns], indent=2)}

YOUR TASK: Find NEW patterns not in the known list. Think creatively:

1. Unusual correlations (e.g., trades on specific days before earnings)
2. Hidden sequences (A trades, then B trades, then C)
3. Ratio patterns (buy/sell ratios at specific times)
4. Sector rotation patterns
5. Pairs trading strategies
6. Options-related hedging patterns
7. Tax-loss harvesting patterns
8. Window dressing patterns
9. Momentum/reversal strategies
10. Any other novel patterns

RESPOND IN JSON:
{{
    "novel_patterns": [
        {{
            "pattern_name": "...",
            "description": "...",
            "evidence": "...",
            "frequency": 0-100,
            "significance": "high|medium|low",
            "involves": {{"politicians": [...], "stocks": [...]}},
            "profit_potential": "..."
        }}
    ]
}}
"""

        try:
            response = await self.router.generate(
                prompt=prompt,
                system_prompt="You are a pattern recognition expert specializing in finding hidden structures in financial data.",
                max_tokens=3000,
                temperature=0.9,  # Very high for creativity
                preferred_provider=LLMProvider.DEEPSEEK
            )

            content = response["content"]
            json_str = self._extract_json(content)
            result = json.loads(json_str)

            return result.get("novel_patterns", [])

        except Exception as e:
            logger.error(f"Error discovering novel patterns: {e}")
            return []

    async def explain_pattern(self, pattern: Dict) -> str:
        """Generate natural language explanation of a pattern"""

        prompt = f"""Explain this trading pattern in simple terms to a non-expert:

PATTERN:
{json.dumps(pattern, indent=2)}

Provide a clear, concise explanation that answers:
1. What is this pattern?
2. Why is it significant?
3. What does it suggest about the traders' behavior?
4. Is this concerning or normal?

Write 2-3 paragraphs maximum. Be direct and avoid jargon.
"""

        try:
            response = await self.router.generate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.5
            )

            return response["content"]

        except Exception as e:
            logger.error(f"Error explaining pattern: {e}")
            return f"Error generating explanation: {e}"

    def _extract_json(self, text: str) -> str:
        """Extract JSON from markdown code blocks or raw text"""

        # Try to find JSON in markdown code blocks
        if "```json" in text:
            parts = text.split("```json")
            if len(parts) > 1:
                json_part = parts[1].split("```")[0].strip()
                return json_part

        elif "```" in text:
            parts = text.split("```")
            if len(parts) > 1:
                json_part = parts[1].strip()
                return json_part

        # Try to find JSON by looking for { }
        start = text.find('{')
        if start != -1:
            # Find matching closing brace
            count = 0
            for i in range(start, len(text)):
                if text[i] == '{':
                    count += 1
                elif text[i] == '}':
                    count -= 1
                    if count == 0:
                        return text[start:i+1]

        # Return as-is if no JSON found
        return text

    def get_stats(self) -> Dict:
        """Get usage statistics"""

        return {
            "total_analyses": len(self.analysis_history),
            "pattern_library_size": len(self.pattern_library),
            "llm_stats": self.router.get_stats()
        }


__all__ = ['DeepSeekUltra']


# Example usage
if __name__ == "__main__":
    async def test():
        ultra = DeepSeekUltra()

        # Test hypothesis generation
        data_summary = {
            "total_trades": 564,
            "top_stocks": [{"ticker": "NVDA", "trades": 50}],
            "synchronized_events": 10
        }

        ml_patterns = {
            "mimicry_patterns": [{"pol1": "A", "pol2": "B", "overlap": 1.0}]
        }

        hypotheses = await ultra.generate_hypotheses(data_summary, ml_patterns)

        print("Generated Hypotheses:")
        print(json.dumps(hypotheses[:3], indent=2))

    asyncio.run(test())
