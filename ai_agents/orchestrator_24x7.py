"""
24/7 Orchestrator for Autonomous Pattern Discovery
Runs continuously, managing the autonomous analyst and monitoring health
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import json
import traceback

sys.path.append(str(Path(__file__).parent.parent))

from ai_agents.autonomous_analyst import AutonomousAnalyst

logger = logging.getLogger(__name__)


class Orchestrator24x7:
    """24/7 orchestrator that manages continuous pattern discovery"""

    def __init__(
        self,
        analysis_interval_minutes: int = 30,
        max_consecutive_failures: int = 5
    ):
        """
        Initialize orchestrator

        Args:
            analysis_interval_minutes: Minutes between analysis cycles
            max_consecutive_failures: Max failures before alerting
        """
        self.analysis_interval = timedelta(minutes=analysis_interval_minutes)
        self.max_consecutive_failures = max_consecutive_failures

        self.analyst = AutonomousAnalyst()
        self.running = False
        self.consecutive_failures = 0
        self.last_success = None
        self.last_failure = None

        # Stats
        self.start_time = None
        self.total_cycles = 0
        self.successful_cycles = 0
        self.failed_cycles = 0

        # Logging
        self.log_file = Path("./logs/orchestrator.log")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.status_file = Path("./logs/status.json")

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
        logger.info("STARTING 24/7 AUTONOMOUS PATTERN DISCOVERY SYSTEM")
        logger.info("="*80)
        logger.info(f"Analysis interval: {self.analysis_interval.total_seconds() / 60} minutes")
        logger.info(f"Max consecutive failures: {self.max_consecutive_failures}")
        logger.info("="*80)

        self.running = True
        self.start_time = datetime.now()

        while self.running:
            cycle_start = datetime.now()

            try:
                logger.info(f"\n{'='*80}")
                logger.info(f"CYCLE #{self.total_cycles + 1} - {cycle_start.isoformat()}")
                logger.info(f"{'='*80}")

                # Run analysis
                result = await self.analyst.analyze_once()

                # Check for errors
                if "error" in result:
                    self._handle_failure(result)
                else:
                    self._handle_success(result)

                # Update status file
                self._update_status()

            except Exception as e:
                logger.error(f"Unexpected error in cycle: {e}", exc_info=True)
                self._handle_failure({"error": str(e), "traceback": traceback.format_exc()})

            # Check if we should continue
            if self.consecutive_failures >= self.max_consecutive_failures:
                logger.critical(
                    f"CRITICAL: {self.consecutive_failures} consecutive failures. "
                    f"Pausing for investigation."
                )
                self._send_alert("critical_failure")

                # Wait longer before retrying
                await asyncio.sleep(300)  # 5 minutes
                self.consecutive_failures = 0  # Reset after long wait

            # Calculate sleep time
            cycle_duration = datetime.now() - cycle_start
            sleep_time = self.analysis_interval - cycle_duration

            if sleep_time.total_seconds() > 0:
                logger.info(f"Sleeping for {sleep_time.total_seconds() / 60:.1f} minutes...")
                await asyncio.sleep(sleep_time.total_seconds())
            else:
                logger.warning(f"Cycle took longer than interval! Duration: {cycle_duration}")

        logger.info("Orchestrator stopped.")

    def _handle_success(self, result: dict):
        """Handle successful analysis cycle"""

        self.total_cycles += 1
        self.successful_cycles += 1
        self.consecutive_failures = 0
        self.last_success = datetime.now()

        novel_count = len(result.get('novel_findings', []))

        logger.info(f"✅ Cycle #{self.total_cycles} SUCCESSFUL")
        logger.info(f"   - Trades analyzed: {result.get('trades_analyzed', 0)}")
        logger.info(f"   - Novel findings: {novel_count}")
        logger.info(f"   - Total discoveries: {result.get('total_discoveries', 0)}")

        # Alert if significant discoveries
        if novel_count >= 5:
            logger.info(f"🔥 SIGNIFICANT DISCOVERIES: {novel_count} novel findings!")
            self._send_alert("significant_discoveries", result)

    def _handle_failure(self, result: dict):
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
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "analyst_stats": self.analyst.get_stats(),
            "updated_at": datetime.now().isoformat()
        }

        try:
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            logger.error(f"Error updating status file: {e}")

    def _send_alert(self, alert_type: str, data: Optional[dict] = None):
        """Send alert (implement with email, Slack, etc.)"""

        logger.warning(f"🚨 ALERT: {alert_type}")

        # For now, just log
        # In production, integrate with alerting service

        alert_file = Path("./logs/alerts.jsonl")
        alert_file.parent.mkdir(parents=True, exist_ok=True)

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
        """Stop the orchestrator gracefully"""
        logger.info("Stopping orchestrator...")
        self.running = False
        self._update_status()

    def get_status(self) -> dict:
        """Get current status"""

        try:
            with open(self.status_file) as f:
                return json.load(f)
        except:
            return {"error": "Status file not available"}


async def main():
    """Main entry point"""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('./logs/orchestrator.log'),
            logging.StreamHandler()
        ]
    )

    # Create and run orchestrator
    orchestrator = Orchestrator24x7(
        analysis_interval_minutes=30,  # Run every 30 minutes
        max_consecutive_failures=5
    )

    try:
        await orchestrator.run_forever()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        orchestrator.stop()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
