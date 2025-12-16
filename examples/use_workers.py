#!/usr/bin/env python3
"""
Example: Using Discovery Workers for Distributed Analysis

This script demonstrates how to use the deployed HuggingFace workers
for distributed trade analysis.
"""

import os
import requests
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class WorkerPool:
    """Manages a pool of worker nodes for distributed processing"""

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

    def analyze_single(self, worker_url: str, trades: List[Dict],
                      analysis_types: List[str]) -> Dict[str, Any]:
        """Run analysis on a single worker"""
        try:
            response = requests.post(
                f"{worker_url}/analyze",
                json={
                    "trades": trades,
                    "analysis_types": analysis_types
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "worker": worker_url}

    def analyze_distributed(self, trades: List[Dict],
                          analysis_types: List[str]) -> List[Dict]:
        """
        Distribute analysis across all workers

        Splits the trades among workers for parallel processing
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

        print(f"\n🚀 Distributing {len(trades)} trades across {len(self.workers)} workers...")
        print(f"   Chunk size: ~{chunk_size} trades per worker")

        results = []
        start_time = time.time()

        # Execute in parallel
        with ThreadPoolExecutor(max_workers=len(self.workers)) as executor:
            futures = {
                executor.submit(
                    self.analyze_single,
                    self.workers[i % len(self.workers)],
                    chunk,
                    analysis_types
                ): i
                for i, chunk in enumerate(chunks)
            }

            for future in as_completed(futures):
                chunk_idx = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"  ✅ Chunk {chunk_idx + 1} completed")
                except Exception as e:
                    print(f"  ❌ Chunk {chunk_idx + 1} failed: {e}")

        elapsed = time.time() - start_time
        print(f"\n⏱️  Completed in {elapsed:.2f} seconds")

        return results


def example_basic_usage():
    """Example 1: Basic worker usage"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Worker Usage")
    print("="*60)

    pool = WorkerPool()

    # Simple trade data
    trades = [
        {"price": 100, "volume": 1000, "price_change": 2.5},
        {"price": 102, "volume": 1200, "price_change": 2.0},
        {"price": 101, "volume": 900, "price_change": -1.0},
        {"price": 103, "volume": 1100, "price_change": 2.0},
    ]

    # Analyze on first worker
    result = pool.analyze_single(
        pool.workers[0],
        trades,
        ["sentiment", "volume_analysis", "price_patterns"]
    )

    print(f"\n📊 Analysis Results:")
    print(f"   Status: {result.get('status')}")
    print(f"   Trades Processed: {result.get('trades_processed')}")
    print(f"\n   Sentiment: {result['results']['sentiment']}")
    print(f"   Volume: {result['results']['volume']}")
    print(f"   Pattern: {result['results']['patterns']['pattern']}")


def example_distributed_analysis():
    """Example 2: Distributed analysis across multiple workers"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Distributed Analysis")
    print("="*60)

    pool = WorkerPool()

    # Larger dataset
    trades = [
        {"price": 100 + i, "volume": 1000 + (i * 10), "price_change": (i % 5) - 2}
        for i in range(50)  # 50 trades
    ]

    # Distribute across all workers
    results = pool.analyze_distributed(
        trades,
        ["sentiment", "volume_analysis"]
    )

    # Aggregate results
    total_positive = sum(r['results']['sentiment']['positive'] for r in results if 'results' in r)
    total_negative = sum(r['results']['sentiment']['negative'] for r in results if 'results' in r)

    print(f"\n📊 Aggregated Results:")
    print(f"   Total Positive Trades: {total_positive}")
    print(f"   Total Negative Trades: {total_negative}")
    print(f"   Overall Sentiment: {'Bullish' if total_positive > total_negative else 'Bearish'}")


def example_load_balancing():
    """Example 3: Load balancing across workers"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Load Balancing")
    print("="*60)

    pool = WorkerPool()

    # Multiple analysis requests
    requests_data = [
        [{"price": 100 + i, "volume": 1000, "price_change": 1.0} for i in range(10)]
        for _ in range(len(pool.workers) * 2)  # 2 requests per worker
    ]

    print(f"\n🔄 Processing {len(requests_data)} analysis requests...")

    start = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=len(pool.workers)) as executor:
        futures = [
            executor.submit(
                pool.analyze_single,
                pool.workers[i % len(pool.workers)],
                trades,
                ["sentiment"]
            )
            for i, trades in enumerate(requests_data)
        ]

        for future in as_completed(futures):
            results.append(future.result())

    elapsed = time.time() - start

    print(f"\n📈 Performance:")
    print(f"   Requests: {len(requests_data)}")
    print(f"   Workers: {len(pool.workers)}")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Throughput: {len(requests_data)/elapsed:.2f} requests/second")


if __name__ == "__main__":
    print("\n🤖 Discovery Workers - Usage Examples")
    print("="*60)

    # Initialize pool
    pool = WorkerPool()

    if not pool.workers:
        print("\n❌ No workers found!")
        print("   Make sure HUGGINGFACE_WORKER_* variables are set in .env")
        exit(1)

    # Run health check
    health = pool.health_check()
    healthy_count = sum(1 for status in health.values() if status)

    if healthy_count == 0:
        print("\n❌ No healthy workers available!")
        exit(1)

    print(f"\n✅ {healthy_count}/{len(pool.workers)} workers healthy\n")

    # Run examples
    try:
        example_basic_usage()

        if len(pool.workers) > 1:
            example_distributed_analysis()
            example_load_balancing()

        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
