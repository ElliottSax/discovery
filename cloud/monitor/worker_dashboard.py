#!/usr/bin/env python3
"""
Oracle Cloud Worker Monitoring Dashboard
Real-time monitoring of distributed worker infrastructure
"""

import os
import sys
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Terminal colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


class WorkerMonitor:
    """Monitors Oracle Cloud worker nodes"""

    def __init__(self, worker_urls: List[str] = None):
        self.worker_urls = worker_urls or self.load_worker_urls()
        self.stats = {}
        self.start_time = time.time()

    def load_worker_urls(self) -> List[str]:
        """Load worker URLs from environment or workers.txt"""
        # Try environment variable first
        env_workers = os.getenv('ORACLE_WORKERS')
        if env_workers:
            return env_workers.split(',')

        # Try workers.txt file
        workers_file = Path(__file__).parent.parent / 'deploy' / 'workers.txt'
        if workers_file.exists():
            workers = []
            with open(workers_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        workers.append(f'http://{line}:8000')
            return workers

        return []

    async def check_worker_health(self, session: aiohttp.ClientSession, worker_url: str) -> Dict:
        """Check health of a single worker"""
        try:
            async with session.get(f'{worker_url}/health', timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'url': worker_url,
                        'status': 'online',
                        'uptime_hours': data.get('uptime_hours', 0),
                        'tasks_completed': data.get('tasks_completed', 0),
                        'response_time': 0
                    }
                else:
                    return {
                        'url': worker_url,
                        'status': 'error',
                        'error': f'HTTP {response.status}'
                    }
        except asyncio.TimeoutError:
            return {'url': worker_url, 'status': 'timeout'}
        except aiohttp.ClientError as e:
            return {'url': worker_url, 'status': 'offline', 'error': str(e)}
        except Exception as e:
            return {'url': worker_url, 'status': 'error', 'error': str(e)}

    async def get_worker_stats(self, session: aiohttp.ClientSession, worker_url: str) -> Dict:
        """Get detailed statistics from a worker"""
        try:
            async with session.get(f'{worker_url}/stats', timeout=5) as response:
                if response.status == 200:
                    return await response.json()
                return {}
        except:
            return {}

    async def monitor_all_workers(self) -> Dict[str, Dict]:
        """Check all workers simultaneously"""
        async with aiohttp.ClientSession() as session:
            health_tasks = [
                self.check_worker_health(session, url)
                for url in self.worker_urls
            ]
            health_results = await asyncio.gather(*health_tasks)

            stats_tasks = [
                self.get_worker_stats(session, url)
                for url in self.worker_urls
            ]
            stats_results = await asyncio.gather(*stats_tasks)

            # Combine health and stats
            results = {}
            for health, stats in zip(health_results, stats_results):
                worker_url = health['url']
                results[worker_url] = {**health, **stats}

            return results

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def format_uptime(self, hours: float) -> str:
        """Format uptime in human-readable format"""
        if hours < 1:
            return f"{int(hours * 60)}m"
        elif hours < 24:
            return f"{hours:.1f}h"
        else:
            days = int(hours / 24)
            remaining_hours = hours % 24
            return f"{days}d {int(remaining_hours)}h"

    def format_number(self, num: int) -> str:
        """Format large numbers with K/M suffix"""
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        return str(num)

    def print_dashboard(self, worker_stats: Dict[str, Dict]):
        """Print formatted dashboard"""
        self.clear_screen()

        # Header
        print(f"{Colors.BOLD}{Colors.CYAN}")
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 20 + "ULTRATHINK WORKER DASHBOARD" + " " * 31 + "║")
        print("╚" + "═" * 78 + "╝")
        print(Colors.END)

        # Timestamp
        now = datetime.now()
        runtime = time.time() - self.start_time
        print(f"Time: {now.strftime('%Y-%m-%d %H:%M:%S')} | Runtime: {self.format_uptime(runtime/3600)}")
        print("-" * 80)

        # Worker summary
        total_workers = len(self.worker_urls)
        online_workers = sum(1 for w in worker_stats.values() if w.get('status') == 'online')
        total_tasks = sum(w.get('tasks_completed', 0) for w in worker_stats.values())

        print(f"\n{Colors.BOLD}Summary:{Colors.END}")
        print(f"  Workers: {Colors.GREEN if online_workers == total_workers else Colors.YELLOW}"
              f"{online_workers}/{total_workers} online{Colors.END}")
        print(f"  Total Tasks: {self.format_number(total_tasks)}")

        # Calculate aggregate metrics
        if online_workers > 0:
            avg_uptime = sum(w.get('uptime_hours', 0) for w in worker_stats.values()
                           if w.get('status') == 'online') / online_workers
            print(f"  Avg Uptime: {self.format_uptime(avg_uptime)}")

        print("\n" + "-" * 80)

        # Individual worker status
        print(f"\n{Colors.BOLD}Workers:{Colors.END}\n")

        for i, (url, stats) in enumerate(worker_stats.items(), 1):
            # Extract IP/hostname
            worker_id = url.replace('http://', '').replace(':8000', '')

            # Status indicator
            if stats.get('status') == 'online':
                status_color = Colors.GREEN
                status_icon = "●"
                status_text = "ONLINE"
            elif stats.get('status') == 'offline':
                status_color = Colors.RED
                status_icon = "○"
                status_text = "OFFLINE"
            elif stats.get('status') == 'timeout':
                status_color = Colors.YELLOW
                status_icon = "◐"
                status_text = "TIMEOUT"
            else:
                status_color = Colors.RED
                status_icon = "✗"
                status_text = "ERROR"

            # Worker line
            print(f"  {status_color}{status_icon}{Colors.END} Worker {i}: {worker_id}")
            print(f"     Status: {status_color}{status_text}{Colors.END}")

            if stats.get('status') == 'online':
                uptime = stats.get('uptime_hours', 0)
                tasks = stats.get('tasks_completed', 0)

                print(f"     Uptime: {self.format_uptime(uptime)}")
                print(f"     Tasks: {self.format_number(tasks)}")

                # Additional metrics if available
                if 'current_batch' in stats:
                    print(f"     Current: Batch {stats['current_batch']}")
                if 'avg_processing_time' in stats:
                    print(f"     Avg Time: {stats['avg_processing_time']:.2f}s")
                if 'success_rate' in stats and tasks > 0:
                    success_rate = stats.get('success_rate', 0) * 100
                    color = Colors.GREEN if success_rate > 95 else Colors.YELLOW
                    print(f"     Success: {color}{success_rate:.1f}%{Colors.END}")

            elif stats.get('error'):
                error_msg = str(stats['error'])[:50]
                print(f"     Error: {error_msg}")

            print()

        # Performance metrics
        if online_workers > 0 and total_tasks > 0:
            print("-" * 80)
            print(f"\n{Colors.BOLD}Performance:{Colors.END}\n")

            # Calculate throughput
            if runtime > 0:
                throughput = total_tasks / (runtime / 3600)  # tasks per hour
                print(f"  Throughput: {self.format_number(int(throughput))} tasks/hour")

            # Show estimated capacity
            if online_workers == 4:
                print(f"  Capacity: ~20-50x speedup vs single machine")
                print(f"  Est. Time for 200K trades: 2-4 hours")

        # Footer
        print("\n" + "-" * 80)
        print(f"{Colors.CYAN}Press Ctrl+C to exit | Refreshing every 5 seconds{Colors.END}")

    async def run_dashboard(self, refresh_interval: int = 5):
        """Run the dashboard with auto-refresh"""
        print(f"{Colors.BOLD}Starting monitor...{Colors.END}")

        if not self.worker_urls:
            print(f"{Colors.RED}No worker URLs found!{Colors.END}")
            print("Configure workers in:")
            print("  1. ORACLE_WORKERS environment variable")
            print("  2. cloud/deploy/workers.txt file")
            return

        try:
            while True:
                # Get current stats
                worker_stats = await self.monitor_all_workers()

                # Print dashboard
                self.print_dashboard(worker_stats)

                # Wait for refresh
                await asyncio.sleep(refresh_interval)

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Dashboard stopped by user{Colors.END}")

    def print_summary(self):
        """Print final summary on exit"""
        runtime = time.time() - self.start_time
        print(f"\n{Colors.BOLD}Session Summary:{Colors.END}")
        print(f"  Total Runtime: {self.format_uptime(runtime/3600)}")
        print(f"  Workers Monitored: {len(self.worker_urls)}")


async def test_mode():
    """Test mode with mock data for development"""
    print("Running in test mode with mock data...")

    # Mock worker URLs
    mock_workers = [
        'http://192.168.1.10:8000',
        'http://192.168.1.11:8000',
        'http://192.168.1.12:8000',
        'http://192.168.1.13:8000'
    ]

    monitor = WorkerMonitor(mock_workers)

    # Mock stats
    mock_stats = {
        mock_workers[0]: {
            'url': mock_workers[0],
            'status': 'online',
            'uptime_hours': 24.5,
            'tasks_completed': 1250,
            'success_rate': 0.98
        },
        mock_workers[1]: {
            'url': mock_workers[1],
            'status': 'online',
            'uptime_hours': 12.3,
            'tasks_completed': 650,
            'success_rate': 0.95
        },
        mock_workers[2]: {
            'url': mock_workers[2],
            'status': 'offline',
            'error': 'Connection refused'
        },
        mock_workers[3]: {
            'url': mock_workers[3],
            'status': 'online',
            'uptime_hours': 48.7,
            'tasks_completed': 2340,
            'success_rate': 0.99
        }
    }

    monitor.print_dashboard(mock_stats)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Oracle Cloud Worker Dashboard')
    parser.add_argument('--test', action='store_true', help='Run in test mode with mock data')
    parser.add_argument('--interval', type=int, default=5, help='Refresh interval in seconds')
    parser.add_argument('--workers', nargs='+', help='Worker URLs to monitor')

    args = parser.parse_args()

    if args.test:
        asyncio.run(test_mode())
    else:
        # Create monitor with specified workers or auto-detect
        monitor = WorkerMonitor(args.workers)

        try:
            asyncio.run(monitor.run_dashboard(args.interval))
        finally:
            monitor.print_summary()


if __name__ == "__main__":
    main()