#!/usr/bin/env python3
"""
Check health of all configured workers across platforms
"""
import os
import sys
import requests
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# ANSI color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
BOLD = '\033[1m'
NC = '\033[0m'


def check_worker(url: str, timeout: int = 5) -> Dict:
    """Check if a worker is healthy"""
    try:
        # Ensure URL has protocol
        if not url.startswith('http'):
            url = f'http://{url}'

        # Try health endpoint
        response = requests.get(f'{url}/health', timeout=timeout)

        if response.ok:
            data = response.json()
            return {
                'status': 'healthy',
                'url': url,
                'platform': data.get('compute_platform', 'unknown'),
                'worker_type': data.get('worker_type', 'general'),
                'gpu': data.get('gpu_available', False),
                'response_time': response.elapsed.total_seconds()
            }
        else:
            return {
                'status': 'unhealthy',
                'url': url,
                'error': f'HTTP {response.status_code}'
            }
    except requests.Timeout:
        return {
            'status': 'timeout',
            'url': url,
            'error': 'Request timeout'
        }
    except requests.ConnectionError:
        return {
            'status': 'offline',
            'url': url,
            'error': 'Connection failed'
        }
    except Exception as e:
        return {
            'status': 'error',
            'url': url,
            'error': str(e)
        }


def get_configured_workers() -> Dict[str, List[str]]:
    """Get all configured workers from environment and files"""
    workers = {
        'oracle': [],
        'huggingface': [],
        'gpu': []
    }

    # Load .env file
    env_file = Path(__file__).parent.parent.parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith('ORACLE_WORKER'):
                    url = line.split('=')[1].strip()
                    if url:
                        workers['oracle'].append(url)
                elif line.startswith('HUGGINGFACE_WORKER'):
                    url = line.split('=')[1].strip()
                    if url:
                        workers['huggingface'].append(url)
                elif 'GPU_WORKER' in line:
                    url = line.split('=')[1].strip()
                    if url:
                        workers['gpu'].append(url)

    # Load workers.txt
    workers_file = Path(__file__).parent.parent / 'deploy' / 'workers.txt'
    if workers_file.exists():
        with open(workers_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Check if it's an IP:port format
                    if ':' in line and not line.startswith('http'):
                        workers['oracle'].append(f'http://{line}')

    return workers


def print_status_table(results: List[Dict]):
    """Print formatted status table"""
    print(f"\n{BOLD}╔════════════════════════════════════════════════════════════════════╗{NC}")
    print(f"{BOLD}║                     Worker Status Report                          ║{NC}")
    print(f"{BOLD}╚════════════════════════════════════════════════════════════════════╝{NC}\n")

    # Group by platform
    platforms = {}
    for result in results:
        platform = result.get('platform', 'unknown')
        if platform not in platforms:
            platforms[platform] = []
        platforms[platform].append(result)

    # Print each platform
    total_healthy = 0
    total_workers = len(results)

    for platform, workers in platforms.items():
        print(f"{BOLD}{platform.upper()}{NC}")
        print("─" * 70)

        for worker in workers:
            status = worker['status']
            url = worker['url']

            if status == 'healthy':
                icon = f"{GREEN}✅{NC}"
                total_healthy += 1
                worker_type = worker.get('worker_type', 'general')
                gpu_status = f"{BLUE}🎮 GPU{NC}" if worker.get('gpu') else ""
                response_time = worker.get('response_time', 0)
                print(f"{icon} {url}")
                print(f"   Type: {worker_type} {gpu_status} | Response: {response_time:.3f}s")
            elif status == 'timeout':
                icon = f"{YELLOW}⏱️{NC}"
                print(f"{icon} {url}")
                print(f"   {YELLOW}Timeout - may be starting up or overloaded{NC}")
            else:
                icon = f"{RED}❌{NC}"
                error = worker.get('error', 'Unknown error')
                print(f"{icon} {url}")
                print(f"   {RED}{error}{NC}")

        print()

    # Summary
    print("═" * 70)
    print(f"\n{BOLD}Summary{NC}")
    print(f"Total Workers: {total_workers}")
    print(f"Healthy: {GREEN}{total_healthy}{NC}")
    print(f"Unhealthy: {RED}{total_workers - total_healthy}{NC}")
    print(f"Availability: {GREEN}{(total_healthy/total_workers*100):.1f}%{NC}" if total_workers > 0 else "N/A")

    # Resource summary
    total_cores = 0
    total_ram = 0
    gpu_count = sum(1 for r in results if r.get('gpu'))

    # Estimate resources based on platform
    for result in results:
        if result['status'] == 'healthy':
            platform = result.get('platform', 'unknown')
            if platform in ['oracle', 'oracle_cloud']:
                total_cores += 1  # Per Oracle instance
                total_ram += 6    # GB per instance
            elif platform in ['huggingface', 'huggingface_spaces']:
                total_cores += 2
                total_ram += 16
            elif platform in ['colab', 'kaggle']:
                total_cores += 2
                total_ram += 13

    if total_cores > 0:
        print(f"\n{BOLD}Available Resources{NC}")
        print(f"CPU Cores: ~{total_cores}")
        print(f"RAM: ~{total_ram} GB")
        print(f"GPUs: {gpu_count}")

    print()


def main():
    """Main function"""
    print(f"\n{BLUE}Checking all configured workers...{NC}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Get workers
    workers_by_platform = get_configured_workers()

    # Flatten to single list
    all_workers = []
    for platform_workers in workers_by_platform.values():
        all_workers.extend(platform_workers)

    # Remove duplicates
    all_workers = list(set(all_workers))

    if not all_workers:
        print(f"{YELLOW}⚠️  No workers configured{NC}")
        print(f"\nAdd workers to:")
        print(f"  • .env file (ORACLE_WORKER_1, HUGGINGFACE_WORKER_1, etc.)")
        print(f"  • cloud/deploy/workers.txt")
        return

    print(f"Found {len(all_workers)} configured workers\n")

    # Check each worker
    results = []
    for i, url in enumerate(all_workers, 1):
        print(f"Checking {i}/{len(all_workers)}: {url}... ", end='', flush=True)
        result = check_worker(url)
        results.append(result)

        if result['status'] == 'healthy':
            print(f"{GREEN}✓{NC}")
        elif result['status'] == 'timeout':
            print(f"{YELLOW}⏱{NC}")
        else:
            print(f"{RED}✗{NC}")

    # Print results table
    print_status_table(results)

    # Exit code based on health
    healthy_count = sum(1 for r in results if r['status'] == 'healthy')
    if healthy_count == 0:
        sys.exit(1)  # No healthy workers
    elif healthy_count < len(results):
        sys.exit(2)  # Some workers unhealthy
    else:
        sys.exit(0)  # All healthy


if __name__ == '__main__':
    main()
