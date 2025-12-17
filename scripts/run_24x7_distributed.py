#!/usr/bin/env python3
"""
24/7 Distributed Analysis System
Runs continuous quant analysis using distributed workers
"""

import asyncio
import logging
import signal
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import distributed analyzer
from scripts.distributed_quant_analysis import DistributedQuantAnalyzer

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/distributed_24x7.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Distributed24x7System:
    """24/7 system running distributed quant analysis continuously"""

    def __init__(
        self,
        analysis_interval_seconds: int = 5,
        max_consecutive_failures: int = 5,
        trades_per_cycle: int = 500
    ):
        """
        Initialize 24/7 distributed system

        Args:
            analysis_interval_seconds: Seconds between analysis cycles (0 = continuous)
            max_consecutive_failures: Max failures before alerting
            trades_per_cycle: Number of trades to analyze per cycle
        """
        self.analysis_interval = timedelta(seconds=analysis_interval_seconds)
        self.max_consecutive_failures = max_consecutive_failures
        self.trades_per_cycle = trades_per_cycle

        self.analyzer = DistributedQuantAnalyzer()
        self.running = False
        self.consecutive_failures = 0
        self.last_success = None
        self.last_failure = None

        # Stats
        self.start_time = None
        self.total_cycles = 0
        self.successful_cycles = 0
        self.failed_cycles = 0
        self.total_trades_analyzed = 0
        self.total_analysis_time = 0

        # Directories
        self.log_dir = Path("./logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.results_dir = Path("./data/analysis/24x7")
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.status_file = self.log_dir / "24x7_status.json"

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()

    async def run_forever(self):
        """Run analysis cycles continuously"""

        logger.info("="*80)
        logger.info("STARTING 24/7 DISTRIBUTED QUANT ANALYSIS SYSTEM")
        logger.info("="*80)
        interval_sec = self.analysis_interval.total_seconds()
        if interval_sec == 0:
            logger.info(f"Analysis interval: CONTINUOUS (no delay)")
        elif interval_sec < 60:
            logger.info(f"Analysis interval: {interval_sec} seconds")
        else:
            logger.info(f"Analysis interval: {interval_sec / 60} minutes")
        logger.info(f"Max consecutive failures: {self.max_consecutive_failures}")
        logger.info(f"Trades per cycle: {self.trades_per_cycle}")
        logger.info(f"Workers available: {len(self.analyzer.workers)}")
        logger.info("="*80)

        # Initial health check
        health = self.analyzer.health_check()
        healthy_count = sum(1 for status in health.values() if status)

        if healthy_count == 0:
            logger.critical("❌ No healthy workers available! Exiting.")
            return

        logger.info(f"✅ {healthy_count}/{len(self.analyzer.workers)} workers healthy")

        self.running = True
        self.start_time = datetime.now()

        while self.running:
            cycle_start = datetime.now()

            try:
                logger.info(f"\n{'='*80}")
                logger.info(f"CYCLE #{self.total_cycles + 1} - {cycle_start.isoformat()}")
                logger.info(f"{'='*80}")

                # Run distributed analysis
                result = await self._run_analysis_cycle()

                # Check for errors
                if result.get("summary", {}).get("failed_chunks", 0) > 0:
                    self._handle_partial_failure(result)
                else:
                    self._handle_success(result)

                # Update status file
                self._update_status()

            except Exception as e:
                logger.error(f"Unexpected error in cycle: {e}", exc_info=True)
                self._handle_failure({"error": str(e)})

            # Check if we should continue
            if self.consecutive_failures >= self.max_consecutive_failures:
                logger.critical(
                    f"CRITICAL: {self.consecutive_failures} consecutive failures. "
                    f"Pausing for investigation."
                )
                self._send_alert("critical_failure")

                # Wait longer before retrying
                logger.info("Sleeping 5 minutes before retry...")
                await asyncio.sleep(300)  # 5 minutes
                self.consecutive_failures = 0  # Reset after long wait

            # Calculate sleep time
            cycle_duration = datetime.now() - cycle_start
            sleep_time = self.analysis_interval - cycle_duration

            if sleep_time.total_seconds() > 0:
                if sleep_time.total_seconds() < 60:
                    logger.info(f"💤 Sleeping for {sleep_time.total_seconds():.1f} seconds...")
                else:
                    logger.info(f"💤 Sleeping for {sleep_time.total_seconds() / 60:.1f} minutes...")
                await asyncio.sleep(sleep_time.total_seconds())
            elif self.analysis_interval.total_seconds() > 0:
                logger.warning(f"⚠️  Cycle took longer than interval! Duration: {cycle_duration}")
            else:
                logger.info(f"🔄 Starting next cycle immediately (continuous mode)...")

        logger.info("24/7 system stopped.")

    async def _run_analysis_cycle(self) -> Dict[str, Any]:
        """Run a single analysis cycle"""

        # Generate mock trades (in production, load from database)
        logger.info(f"📝 Generating {self.trades_per_cycle} trades...")
        trades = self.analyzer._generate_mock_trades(count=self.trades_per_cycle)

        # Define analysis types
        analysis_types = [
            "sentiment",
            "volume_analysis",
            "price_patterns",
            "correlation",
            "timing_analysis",
            "cluster_analysis",
        ]

        # Run distributed analysis (synchronous, so wrap in executor)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.analyzer.run_distributed_analysis,
            trades,
            analysis_types
        )

        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.results_dir / f"cycle_{self.total_cycles + 1}_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"💾 Results saved to: {output_file}")

        return result

    def _handle_success(self, result: Dict[str, Any]):
        """Handle successful analysis cycle"""

        self.total_cycles += 1
        self.successful_cycles += 1
        self.consecutive_failures = 0
        self.last_success = datetime.now()

        summary = result.get('summary', {})
        trades_analyzed = summary.get('total_trades', 0)
        elapsed = summary.get('elapsed_seconds', 0)
        throughput = summary.get('throughput', 0)

        self.total_trades_analyzed += trades_analyzed
        self.total_analysis_time += elapsed

        logger.info(f"✅ Cycle #{self.total_cycles} SUCCESSFUL")
        logger.info(f"   - Trades analyzed: {trades_analyzed}")
        logger.info(f"   - Analysis time: {elapsed:.2f}s")
        logger.info(f"   - Throughput: {throughput:.2f} trades/sec")
        logger.info(f"   - Workers used: {summary.get('workers_used', 0)}")
        logger.info(f"   - Success rate: {self.successful_cycles}/{self.total_cycles} ({self.successful_cycles/self.total_cycles*100:.1f}%)")

    def _handle_partial_failure(self, result: Dict[str, Any]):
        """Handle partially failed analysis cycle"""

        self.total_cycles += 1
        self.successful_cycles += 1  # Still count as success if some chunks worked

        summary = result.get('summary', {})
        failed_chunks = summary.get('failed_chunks', 0)
        successful_chunks = summary.get('successful_chunks', 0)

        logger.warning(f"⚠️  Cycle #{self.total_cycles} PARTIAL SUCCESS")
        logger.warning(f"   - Successful chunks: {successful_chunks}")
        logger.warning(f"   - Failed chunks: {failed_chunks}")

        self.total_trades_analyzed += summary.get('total_trades', 0)
        self.total_analysis_time += summary.get('elapsed_seconds', 0)

    def _handle_failure(self, result: Dict[str, Any]):
        """Handle failed analysis cycle"""

        self.total_cycles += 1
        self.failed_cycles += 1
        self.consecutive_failures += 1
        self.last_failure = datetime.now()

        logger.error(f"❌ Cycle #{self.total_cycles} FAILED")
        logger.error(f"   - Error: {result.get('error', 'Unknown')}")
        logger.error(f"   - Consecutive failures: {self.consecutive_failures}")

    def _update_status(self):
        """Update status file with current state"""

        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        avg_throughput = 0
        if self.total_analysis_time > 0:
            avg_throughput = self.total_trades_analyzed / self.total_analysis_time

        status = {
            "running": self.running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600 if uptime else None,
            "total_cycles": self.total_cycles,
            "successful_cycles": self.successful_cycles,
            "failed_cycles": self.failed_cycles,
            "consecutive_failures": self.consecutive_failures,
            "success_rate": self.successful_cycles / max(self.total_cycles, 1),
            "total_trades_analyzed": self.total_trades_analyzed,
            "total_analysis_time": self.total_analysis_time,
            "average_throughput": avg_throughput,
            "workers_available": len(self.analyzer.workers),
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "updated_at": datetime.now().isoformat()
        }

        try:
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            logger.error(f"Error updating status file: {e}")

    def _send_alert(self, alert_type: str, data: Optional[Dict] = None):
        """Send alert (implement with email, Slack, etc.)"""

        logger.warning(f"🚨 ALERT: {alert_type}")

        alert_file = self.log_dir / "alerts.jsonl"

        alert = {
            "type": alert_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        try:
            with open(alert_file, 'a') as f:
                f.write(json.dumps(alert) + '\n')
        except Exception as e:
            logger.error(f"Error writing alert: {e}")

    def stop(self):
        """Stop the system gracefully"""
        logger.info("Stopping 24/7 system...")
        self.running = False
        self._update_status()

    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        try:
            with open(self.status_file) as f:
                return json.load(f)
        except:
            return {"error": "Status file not available"}


async def main():
    """Main entry point"""

    logger.info("Initializing 24/7 Distributed Quant Analysis System...")

    # Create and run system
    system = Distributed24x7System(
        analysis_interval_seconds=0,  # 0 = continuous (no delay)
        max_consecutive_failures=5,
        trades_per_cycle=500
    )

    try:
        await system.run_forever()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        system.stop()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        system.stop()


if __name__ == "__main__":
    asyncio.run(main())
