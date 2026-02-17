"""
Local Agent Orchestrator
Main loop: Approval processing → MCP execution → Git pull
"""
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent_skills.env_validator import EnvValidator
from agent_skills.claim_manager import ClaimManager
from agent_skills.api_usage_tracker import APIUsageTracker
from agent_skills.stale_file_recovery import recover_stale_files

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [LOCAL-ORCH] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalOrchestrator:
    """
    Local Agent main orchestration loop
    Coordinates approval processing, MCP execution
    """

    def __init__(self):
        """Initialize Local Orchestrator"""
        # Validate environment
        try:
            EnvValidator.validate_local_agent()
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            sys.exit(1)

        # Load config
        self.vault_path = os.getenv("VAULT_PATH")
        self.agent_id = "local"

        # Initialize components
        self.claim_mgr = ClaimManager(self.vault_path, self.agent_id)
        self.api_tracker = APIUsageTracker(self.vault_path, self.agent_id)

        # Track last stale recovery check (run hourly)
        self._last_stale_check: float = 0.0

        logger.info("Local Orchestrator initialized")

    def process_approvals(self):
        """
        Process vault/Approved/ for user-approved drafts.
        Routes to correct executor based on subfolder type.
        """
        logger.debug("Processing approvals...")

        from local_agent.src.approval_handler import ApprovalHandler
        handler = ApprovalHandler(self.vault_path, self.agent_id)
        count = handler.run_once()
        if count:
            logger.info(f"✅ Processed {count} approval(s)")

    def monitor_needs_action(self):
        """
        Monitor vault/Needs_Action/ for tasks
        Claim and process tasks
        """
        logger.debug("Monitoring /Needs_Action/...")

        # Scan for tasks
        tasks = self.claim_mgr.scan_needs_action()

        for task in tasks:
            # Try to claim
            if self.claim_mgr.claim_task(task):
                logger.info(f"Claimed task: {task.name}")

                # TODO: Process claimed task
                # 1. Read task file
                # 2. Determine task type
                # 3. Execute appropriate action
                # 4. Release to /Done/

                pass

    def recover_stale(self):
        """
        FR-P016: Check vault/In_Progress/ every hour for stale files (>24h).
        Move them back to Needs_Action/ and log recovery.
        """
        now = time.time()
        if now - self._last_stale_check < 3600:  # Run at most once per hour
            return
        self._last_stale_check = now

        count = recover_stale_files(self.vault_path)
        if count:
            logger.info(f"🔄 Stale recovery: moved {count} file(s) back to Needs_Action/")

    def orchestration_cycle(self):
        """
        Single orchestration cycle
        Run all Local Agent tasks
        """
        try:
            # Process approvals (highest priority)
            self.process_approvals()

            # Monitor and claim tasks
            self.monitor_needs_action()

            # FR-P016: Stale file recovery (runs hourly)
            self.recover_stale()

            logger.debug("Orchestration cycle complete")

        except Exception as e:
            logger.error(f"Orchestration cycle error: {e}")

    def run(self):
        """
        Main loop: Run orchestration every 30 seconds
        (Git sync runs separately via git_sync.py)
        """
        logger.info("🚀 Local Orchestrator started")

        cycle_interval = 30  # 30 seconds

        while True:
            try:
                self.orchestration_cycle()
                time.sleep(cycle_interval)

            except KeyboardInterrupt:
                logger.info("Shutting down Local Orchestrator...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(cycle_interval)


if __name__ == "__main__":
    orchestrator = LocalOrchestrator()
    orchestrator.run()
