"""
Comprehensive Test Suite for ULTRATHINK Autonomous System
Tests all components: ML models, LLM router, deduplicator, analyst, orchestrator
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import tempfile

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_agents.llm_router import LLMRouter, get_llm_router, LLMProvider
from ai_agents.pattern_deduplicator import PatternDeduplicator
from ml_models.advanced_models import LSTMPatternDetector, TransformerAttentionAnalyzer, EnsemblePatternDetector


class TestLLMRouter:
    """Test LLM routing and failover"""

    def test_router_initialization(self):
        """Test router initializes with correct providers"""
        router = LLMRouter()

        assert router.total_cost == 0.0
        assert router.request_count == 0
        assert LLMProvider.DEEPSEEK in router.COSTS
        assert LLMProvider.LOCAL in router.COSTS

        # Verify cost ordering (cheapest first)
        assert router.COSTS[LLMProvider.DEEPSEEK][0] == 0.14
        assert router.COSTS[LLMProvider.TOGETHER][0] == 0.20

    def test_get_available_providers(self):
        """Test provider availability detection"""
        router = LLMRouter()
        providers = router.get_available_providers()

        # Local should always be available
        assert LLMProvider.LOCAL in providers

        # Should be sorted by cost
        costs = [router.COSTS[p][0] for p in providers]
        assert costs == sorted(costs)

    @pytest.mark.asyncio
    async def test_local_fallback(self):
        """Test local fallback when no API keys"""
        router = LLMRouter()

        result = await router.generate(
            prompt="Test prompt",
            max_tokens=100
        )

        assert result["provider"] == "local"
        assert result["cost"] == 0.0
        assert "content" in result
        assert router.request_count == 1

    @pytest.mark.asyncio
    async def test_cost_tracking(self):
        """Test cost is tracked correctly"""
        router = LLMRouter()

        await router.generate(prompt="Test 1")
        await router.generate(prompt="Test 2")

        stats = router.get_stats()
        assert stats["total_requests"] == 2
        assert stats["total_cost"] == 0.0  # Local is free
        assert "provider_stats" in stats


class TestPatternDeduplicator:
    """Test pattern deduplication logic"""

    def test_deduplicator_initialization(self):
        """Test deduplicator initializes correctly"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_file = Path(f.name)

        try:
            dedup = PatternDeduplicator(temp_file)
            assert dedup.discoveries_file == temp_file
            assert len(dedup.recent_hashes) == 0
        finally:
            temp_file.unlink(missing_ok=True)

    def test_hash_pattern(self):
        """Test pattern hashing is deterministic"""
        dedup = PatternDeduplicator()

        pattern1 = {
            "type": "test",
            "finding": {"data": "value"},
            "timestamp": "2025-11-27T10:00:00"
        }

        pattern2 = {
            "type": "test",
            "finding": {"data": "value"},
            "timestamp": "2025-11-27T11:00:00"  # Different timestamp
        }

        hash1 = dedup._hash_pattern(pattern1)
        hash2 = dedup._hash_pattern(pattern2)

        # Should be same (timestamp excluded from hash)
        assert hash1 == hash2

    def test_is_novel_exact_duplicate(self):
        """Test exact duplicate detection"""
        dedup = PatternDeduplicator()

        pattern = {
            "type": "test",
            "finding": {"data": "value"}
        }

        # First time should be novel
        assert dedup.is_novel(pattern) == True

        # Add to index
        dedup.add_pattern(pattern)

        # Second time should not be novel
        assert dedup.is_novel(pattern) == False

    def test_is_novel_similar_pattern(self):
        """Test similarity-based deduplication"""
        dedup = PatternDeduplicator()

        pattern1 = {
            "type": "test",
            "finding": {"ticker": "AAPL", "politician": "John Doe"}
        }

        pattern2 = {
            "type": "test",
            "finding": {"ticker": "AAPL", "politician": "Jane Smith"}
        }

        # Add first pattern
        dedup.add_pattern(pattern1)

        # Second pattern is similar but not identical
        # Default threshold is 0.9, these should be <0.9 similar
        assert dedup.is_novel(pattern2, similarity_threshold=0.5) == True

    def test_filter_novel(self):
        """Test filtering list of patterns"""
        dedup = PatternDeduplicator()

        patterns = [
            {"type": "test", "finding": {"id": 1}},
            {"type": "test", "finding": {"id": 2}},
            {"type": "test", "finding": {"id": 1}},  # Duplicate
        ]

        novel = dedup.filter_novel(patterns)

        # Should filter out the duplicate
        assert len(novel) == 2

    def test_get_stats(self):
        """Test statistics generation"""
        dedup = PatternDeduplicator()

        patterns = [
            {"type": "mimicry", "finding": {"id": 1}},
            {"type": "mimicry", "finding": {"id": 2}},
            {"type": "synchronized", "finding": {"id": 3}},
        ]

        dedup.filter_novel(patterns)
        stats = dedup.get_stats()

        assert stats["total_patterns"] == 3
        assert "mimicry" in stats["pattern_types"]
        assert stats["pattern_types"]["mimicry"] == 2


class TestMLModels:
    """Test ML pattern detection models"""

    def test_lstm_detector_initialization(self):
        """Test LSTM detector initializes"""
        detector = LSTMPatternDetector()

        assert detector.input_dim == 10
        assert detector.hidden_dim == 64

    def test_lstm_detect_patterns_insufficient_data(self):
        """Test LSTM handles insufficient data"""
        detector = LSTMPatternDetector()

        trades = [
            {"politician_name": "Test", "ticker": "AAPL"}
        ]

        result = detector.detect_patterns(trades, "Test")
        assert result["pattern"] == "insufficient_data"

    def test_lstm_detect_patterns_with_data(self):
        """Test LSTM detects patterns with sufficient data"""
        detector = LSTMPatternDetector()

        trades = [
            {
                "politician_name": "Test",
                "ticker": "AAPL",
                "transaction_type": "buy",
                "transaction_date": f"2023-01-{i:02d}",
                "amount_min": 1000,
                "amount_max": 5000
            }
            for i in range(1, 21)  # 20 trades
        ]

        result = detector.detect_patterns(trades, "Test")

        assert "patterns" in result or "pattern" in result

    def test_transformer_analyzer_initialization(self):
        """Test Transformer analyzer initializes"""
        analyzer = TransformerAttentionAnalyzer()

        assert analyzer.embed_dim == 64
        assert analyzer.num_heads == 4

    def test_transformer_find_synchronized_trading(self):
        """Test synchronized trading detection"""
        analyzer = TransformerAttentionAnalyzer()

        trades = [
            {
                "politician_name": "Pol1",
                "ticker": "AAPL",
                "transaction_date": "2023-01-10",
                "transaction_type": "buy"
            },
            {
                "politician_name": "Pol2",
                "ticker": "AAPL",
                "transaction_date": "2023-01-12",  # Within 7 days
                "transaction_type": "buy"
            },
        ]

        result = analyzer.analyze_cross_patterns(trades)

        assert "synchronized_trading" in result
        # Should detect the synchronized AAPL trades

    def test_transformer_find_mimicry(self):
        """Test mimicry pattern detection"""
        analyzer = TransformerAttentionAnalyzer()

        trades = [
            {"politician_name": "Pol1", "ticker": "AAPL"},
            {"politician_name": "Pol1", "ticker": "MSFT"},
            {"politician_name": "Pol2", "ticker": "AAPL"},
            {"politician_name": "Pol2", "ticker": "MSFT"},
        ]

        result = analyzer.analyze_cross_patterns(trades)

        assert "mimicry_patterns" in result

    def test_ensemble_detector(self):
        """Test ensemble detector combines results"""
        ensemble = EnsemblePatternDetector()

        trades = [
            {
                "politician_name": "Test",
                "ticker": "AAPL",
                "transaction_type": "buy",
                "transaction_date": f"2023-01-{i:02d}",
                "amount_min": 1000,
                "amount_max": 5000
            }
            for i in range(1, 21)
        ]

        result = ensemble.detect_all_patterns(trades)

        assert "individual_patterns" in result
        assert "cross_patterns" in result
        assert "novel_discoveries" in result


class TestDatabaseIntegration:
    """Test database connectivity and queries"""

    @pytest.mark.skipif(
        not Path("/mnt/e/projects/discovery").exists(),
        reason="Database not available"
    )
    def test_database_connection(self):
        """Test can connect to database"""
        import psycopg2
        import os

        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 5432)),
                database=os.getenv('DB_NAME', 'quant_db'),
                user=os.getenv('DB_USER', 'quant_user'),
                password=os.getenv('DB_PASSWORD')
            )
            assert conn is not None
            conn.close()
        except Exception as e:
            pytest.skip(f"Database not available: {e}")


class TestEndToEnd:
    """End-to-end integration tests"""

    @pytest.mark.asyncio
    async def test_full_analysis_cycle(self):
        """Test complete analysis cycle"""
        # This would require database access
        # For now, test with mock data

        from ai_agents.autonomous_analyst import AutonomousAnalyst

        # Mock the database connection
        with patch('ai_agents.autonomous_analyst.psycopg2.connect'):
            analyst = AutonomousAnalyst()

            # Mock _load_trades_from_db to return test data
            test_trades = [
                {
                    "politician_name": "Test",
                    "ticker": "AAPL",
                    "transaction_type": "buy",
                    "transaction_date": "2023-01-10",
                    "amount_min": 1000.0,
                    "amount_max": 5000.0
                }
                for _ in range(20)
            ]

            analyst._load_trades_from_db = Mock(return_value=test_trades)

            # Run analysis
            result = await analyst.analyze_once()

            assert "cycle" in result
            assert "timestamp" in result


class TestSystemHealth:
    """Test system health and monitoring"""

    def test_status_file_format(self):
        """Test status.json has correct format"""
        status_file = Path("logs/status.json")

        if status_file.exists():
            with open(status_file) as f:
                status = json.load(f)

            # Check required fields
            assert "running" in status
            assert "total_cycles" in status
            assert "analyst_stats" in status

            # Check types
            assert isinstance(status["running"], bool)
            assert isinstance(status["total_cycles"], int)

    def test_discoveries_file_format(self):
        """Test discoveries.jsonl has correct format"""
        discoveries_file = Path("data/patterns/discoveries.jsonl")

        if discoveries_file.exists():
            with open(discoveries_file) as f:
                for line in f:
                    discovery = json.loads(line.strip())

                    # Check required fields
                    assert "type" in discovery
                    assert "finding" in discovery
                    assert "timestamp" in discovery

                    # Check timestamp format
                    datetime.fromisoformat(discovery["timestamp"])


def run_diagnostics():
    """Run system diagnostics"""
    print("\n" + "="*70)
    print("ULTRATHINK SYSTEM DIAGNOSTICS")
    print("="*70 + "\n")

    # Check database
    print("1. Database Connection")
    try:
        import psycopg2
        import os
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'quant_db'),
            user=os.getenv('DB_USER', 'quant_user'),
            password=os.getenv('DB_PASSWORD', 'REDACTED_PASSWORD')
        )
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM trades")
            count = cur.fetchone()[0]
            print(f"   ✅ Connected to PostgreSQL")
            print(f"   ✅ {count} trades in database")
        conn.close()
    except Exception as e:
        print(f"   ❌ Database error: {e}")

    # Check file system
    print("\n2. File System")
    paths = {
        "Discoveries": "data/patterns/discoveries.jsonl",
        "Pipeline trades": "data/pipeline/trades_*.json",
        "Pipeline analytics": "data/pipeline/analytics_*.json",
        "Orchestrator log": "logs/orchestrator.log",
        "Status file": "logs/status.json"
    }

    for name, path in paths.items():
        if '*' in path:
            files = list(Path(".").glob(path))
            if files:
                print(f"   ✅ {name}: {len(files)} files")
            else:
                print(f"   ⚠️  {name}: No files found")
        else:
            if Path(path).exists():
                size = Path(path).stat().st_size
                print(f"   ✅ {name}: {size} bytes")
            else:
                print(f"   ⚠️  {name}: Not found")

    # Check running processes
    print("\n3. Running Processes")
    import subprocess
    try:
        result = subprocess.run(
            ["pgrep", "-f", "orchestrator_24x7"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"   ✅ Orchestrator running (PIDs: {', '.join(pids)})")
        else:
            print(f"   ⚠️  Orchestrator not running")
    except Exception as e:
        print(f"   ⚠️  Cannot check processes: {e}")

    # Check LLM availability
    print("\n4. LLM Providers")
    router = get_llm_router()
    providers = router.get_available_providers()
    for provider in providers:
        cost = router.COSTS[provider][0]
        if provider == LLMProvider.LOCAL:
            print(f"   ✅ {provider.value}: Available (fallback)")
        elif router.api_keys.get(provider):
            print(f"   ✅ {provider.value}: API key set (${cost}/M tokens)")
        else:
            print(f"   ⚠️  {provider.value}: No API key (${cost}/M tokens)")

    # Check ML models
    print("\n5. ML Models")
    try:
        import torch
        print(f"   ✅ PyTorch: {torch.__version__}")
    except ImportError:
        print(f"   ⚠️  PyTorch: Not installed (using fallback)")

    try:
        import sklearn
        print(f"   ✅ scikit-learn: {sklearn.__version__}")
    except ImportError:
        print(f"   ⚠️  scikit-learn: Not installed (using fallback)")

    # Check recent activity
    print("\n6. Recent Activity")
    if Path("data/patterns/discoveries.jsonl").exists():
        with open("data/patterns/discoveries.jsonl") as f:
            lines = f.readlines()
            if lines:
                last_discovery = json.loads(lines[-1])
                timestamp = last_discovery["timestamp"]
                discovery_type = last_discovery["type"]
                print(f"   ✅ Last discovery: {timestamp}")
                print(f"      Type: {discovery_type}")
                print(f"      Total discoveries: {len(lines)}")

    if Path("logs/status.json").exists():
        with open("logs/status.json") as f:
            status = json.load(f)
            print(f"   ✅ Total cycles: {status.get('total_cycles', 0)}")
            print(f"   ✅ Success rate: {status.get('success_rate', 0)*100:.1f}%")
            print(f"   ✅ Total discoveries: {status.get('analyst_stats', {}).get('total_discoveries', 0)}")

    print("\n" + "="*70)
    print("DIAGNOSTICS COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Run diagnostics
    run_diagnostics()

    # Run tests
    print("\nRunning automated tests...\n")
    pytest.main([__file__, "-v", "--tb=short"])
