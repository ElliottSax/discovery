#!/usr/bin/env python3
"""
Distributed Quantitative Analysis Runner
Distributes advanced quant analysis across HuggingFace workers
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment
load_dotenv()


class DistributedQuantAnalyzer:
    """Runs quantitative analysis distributed across workers"""

    def __init__(self):
        self.workers = self._load_workers()
        print(f"✅ Loaded {len(self.workers)} workers")

    def _load_workers(self) -> List[str]:
        """Load all available workers from environment"""
        workers = []
        i = 1
        while True:
            worker = os.getenv(f'HUGGINGFACE_WORKER_{i}')
            if not worker:
                break
            workers.append(worker)
            i += 1
        return workers

    def health_check(self) -> Dict[str, bool]:
        """Check health of all workers"""
        print("\n🔍 Checking worker health...")
        health_status = {}

        for i, worker in enumerate(self.workers, 1):
            try:
                response = requests.get(f"{worker}/health", timeout=10)
                healthy = response.status_code == 200
                health_status[f"Worker {i}"] = healthy
                status = "✅" if healthy else "❌"
                print(f"  {status} Worker {i}: {worker}")
            except Exception as e:
                health_status[f"Worker {i}"] = False
                print(f"  ❌ Worker {i}: Failed - {str(e)}")

        return health_status

    def _generate_mock_trades(self, count: int = 500) -> List[Dict]:
        """Generate mock trade data for analysis"""
        import random

        tickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN', 'META',
                   'NFLX', 'AMD', 'CRM', 'ORCL', 'INTC', 'CSCO', 'ADBE', 'QCOM']

        politicians = [
            {'name': 'Nancy Pelosi', 'party': 'D', 'chamber': 'House'},
            {'name': 'Dan Crenshaw', 'party': 'R', 'chamber': 'House'},
            {'name': 'Tommy Tuberville', 'party': 'R', 'chamber': 'Senate'},
            {'name': 'Josh Gottheimer', 'party': 'D', 'chamber': 'House'},
            {'name': 'Austin Scott', 'party': 'R', 'chamber': 'House'},
        ]

        trades = []
        base_date = datetime.now() - timedelta(days=365)

        for i in range(count):
            trade_date = base_date + timedelta(days=i % 365)
            disclosure_date = trade_date + timedelta(days=15 + (i % 30))
            pol = random.choice(politicians)

            trades.append({
                'id': i + 1,
                'ticker': random.choice(tickers),
                'transaction_date': trade_date.isoformat(),
                'disclosure_date': disclosure_date.isoformat(),
                'transaction_type': 'purchase' if i % 3 != 0 else 'sale',
                'amount_min': 15000 + (i * 1000),
                'amount_max': 50000 + (i * 2000),
                'politician': pol['name'],
                'party': pol['party'],
                'chamber': pol['chamber'],
                'price_at_disclosure': 100 + random.uniform(-20, 50),
                'price_change_7d': random.uniform(-10, 15),
                'price_change_30d': random.uniform(-20, 30),
            })

        return trades

    def analyze_chunk_on_worker(self, worker_url: str, trades: List[Dict],
                                analysis_types: List[str], chunk_id: int) -> Dict[str, Any]:
        """Run quant analysis on a single worker"""
        try:
            print(f"  📊 Worker processing chunk {chunk_id} ({len(trades)} trades)...")

            response = requests.post(
                f"{worker_url}/analyze",
                json={
                    "trades": trades,
                    "analysis_types": analysis_types,
                    "metadata": {
                        "chunk_id": chunk_id,
                        "timestamp": datetime.now().isoformat()
                    }
                },
                timeout=120  # 2 minute timeout for complex analysis
            )
            response.raise_for_status()
            result = response.json()
            result['chunk_id'] = chunk_id
            result['worker'] = worker_url
            return result

        except Exception as e:
            return {
                "error": str(e),
                "worker": worker_url,
                "chunk_id": chunk_id,
                "trades_count": len(trades)
            }

    def run_distributed_analysis(self, trades: List[Dict],
                                 analysis_types: List[str]) -> Dict[str, Any]:
        """
        Distribute quant analysis across all workers

        Args:
            trades: List of trade data
            analysis_types: Types of analysis to run

        Returns:
            Aggregated results from all workers
        """
        if not self.workers:
            raise Exception("No workers available")

        # Split trades among workers
        chunk_size = len(trades) // len(self.workers)
        if chunk_size == 0:
            chunk_size = 1

        chunks = [
            trades[i:i + chunk_size]
            for i in range(0, len(trades), chunk_size)
        ]

        print(f"\n🚀 DISTRIBUTED QUANT ANALYSIS")
        print(f"   Total trades: {len(trades)}")
        print(f"   Workers: {len(self.workers)}")
        print(f"   Chunks: {len(chunks)}")
        print(f"   Chunk size: ~{chunk_size} trades")
        print(f"   Analysis types: {', '.join(analysis_types)}")
        print()

        results = []
        start_time = time.time()

        # Execute in parallel across all workers
        with ThreadPoolExecutor(max_workers=len(self.workers)) as executor:
            futures = {
                executor.submit(
                    self.analyze_chunk_on_worker,
                    self.workers[i % len(self.workers)],
                    chunk,
                    analysis_types,
                    i + 1
                ): i
                for i, chunk in enumerate(chunks)
            }

            for future in as_completed(futures):
                chunk_idx = futures[future]
                try:
                    result = future.result()
                    if "error" not in result:
                        results.append(result)
                        print(f"  ✅ Chunk {result['chunk_id']} completed successfully")
                    else:
                        print(f"  ❌ Chunk {result['chunk_id']} failed: {result['error']}")
                        results.append(result)
                except Exception as e:
                    print(f"  ❌ Chunk {chunk_idx + 1} exception: {e}")

        elapsed = time.time() - start_time

        # Aggregate results
        successful = [r for r in results if "error" not in r]
        failed = [r for r in results if "error" in r]

        print(f"\n⏱️  Analysis completed in {elapsed:.2f} seconds")
        print(f"   Successful chunks: {len(successful)}/{len(chunks)}")
        print(f"   Failed chunks: {len(failed)}/{len(chunks)}")
        print(f"   Throughput: {len(trades)/elapsed:.2f} trades/second")

        return {
            "summary": {
                "total_trades": len(trades),
                "total_chunks": len(chunks),
                "successful_chunks": len(successful),
                "failed_chunks": len(failed),
                "elapsed_seconds": elapsed,
                "throughput": len(trades)/elapsed if elapsed > 0 else 0,
                "workers_used": len(self.workers)
            },
            "results": successful,
            "errors": failed,
            "timestamp": datetime.now().isoformat()
        }

    def save_results(self, results: Dict, output_file: str = None):
        """Save analysis results to file"""
        if output_file is None:
            output_file = f"data/analysis/distributed_quant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Results saved to: {output_path}")
        return output_path


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("DISTRIBUTED QUANTITATIVE ANALYSIS")
    print("="*80)

    # Initialize analyzer
    analyzer = DistributedQuantAnalyzer()

    if not analyzer.workers:
        print("\n❌ No workers found!")
        print("   Make sure HUGGINGFACE_WORKER_* variables are set in .env")
        return 1

    # Run health check
    health = analyzer.health_check()
    healthy_count = sum(1 for status in health.values() if status)

    if healthy_count == 0:
        print("\n❌ No healthy workers available!")
        return 1

    print(f"\n✅ {healthy_count}/{len(analyzer.workers)} workers healthy")

    # Generate mock trades
    print("\n📝 Generating mock trade data...")
    trades = analyzer._generate_mock_trades(count=500)
    print(f"   Generated {len(trades)} trades")

    # Define analysis types to run
    analysis_types = [
        "sentiment",           # Sentiment analysis
        "volume_analysis",     # Volume patterns
        "price_patterns",      # Price pattern detection
        "correlation",         # Cross-asset correlation
        "timing_analysis",     # Timing patterns
        "cluster_analysis",    # Trade clustering
    ]

    # Run distributed analysis
    results = analyzer.run_distributed_analysis(trades, analysis_types)

    # Save results
    output_file = analyzer.save_results(results)

    # Print summary
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"📊 Summary:")
    for key, value in results['summary'].items():
        print(f"   {key}: {value}")

    print("\n✅ Distributed quant analysis complete!")
    print(f"📄 Full results: {output_file}")
    print("="*80 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
