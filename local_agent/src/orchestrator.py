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
from agent_skills.resource_monitor import ResourceMonitor

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
        self.resource_monitor = ResourceMonitor(self.vault_path)

        # Track last stale recovery check (run hourly)
        self._last_stale_check: float = 0.0
        # Track last CEO briefing check (run hourly on Sunday 23:xx)
        self._last_briefing_check: float = 0.0
        self._briefing_sent_this_sunday: str = ""  # "YYYY-WW" to avoid double-send

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
        A2A: Monitor vault/Needs_Action/ for tasks written by the cloud agent.
        Claim each task atomically, detect its type from the `action` frontmatter
        field, route to the appropriate executor, then release to Done/ or Failed/.
        """
        logger.debug("Monitoring /Needs_Action/...")

        tasks = self.claim_mgr.scan_needs_action()
        if not tasks:
            return

        from agent_skills.vault_parser import parse_frontmatter

        for task_file in tasks:
            if not self.claim_mgr.claim_task(task_file):
                continue  # another agent claimed it first

            # task was moved to In_Progress/local/
            claimed_path = (
                Path(self.vault_path) / "In_Progress" / self.agent_id / task_file.name
            )

            try:
                frontmatter, body = parse_frontmatter(str(claimed_path))
                action = frontmatter.get("action", "")
                logger.info(f"🔧 A2A task: {task_file.name} | action={action}")

                success, result_info = self._execute_needs_action_task(
                    claimed_path, action, frontmatter, body
                )

                target = "Done" if success else "Failed"
                self.claim_mgr.release_task(claimed_path, target)
                logger.info(f"{'✅' if success else '❌'} {task_file.name} → {target}/ | {result_info}")

            except Exception as e:
                logger.error(f"❌ Error processing {task_file.name}: {e}")
                try:
                    self.claim_mgr.release_task(claimed_path, "Failed")
                except Exception:
                    pass

    def _execute_needs_action_task(
        self,
        task_path: "Path",
        action: str,
        frontmatter: dict,
        body: str,
    ) -> tuple:
        """
        Route a claimed Needs_Action task to the correct executor.

        Returns: (success: bool, info: str)
        """
        from pathlib import Path as _Path

        # ── Odoo: Invoice / Expense ──────────────────────────────────────────
        if action in ("create_draft_invoice", "create_draft_expense"):
            from local_agent.src.executors.odoo_poster import OdooPoster
            poster = OdooPoster(self.vault_path)
            result = poster.post_from_file(str(task_path))
            ok = result.get("success", False)
            info = (
                f"Invoice {result.get('invoice_number')} (ID {result.get('odoo_record_id')})"
                if ok else result.get("error", "unknown")
            )
            return ok, info

        # ── Odoo: Contact ────────────────────────────────────────────────────
        elif action == "create_contact":
            from local_agent.src.executors.odoo_poster import OdooPoster
            poster = OdooPoster(self.vault_path)
            result = poster.create_contact(
                name=frontmatter.get("name", frontmatter.get("customer", "")),
                email=frontmatter.get("email", ""),
                phone=frontmatter.get("phone", ""),
            )
            ok = result.get("success", False)
            return ok, result.get("partner_id", result.get("error", ""))

        # ── Odoo: Payment ────────────────────────────────────────────────────
        elif action == "register_payment":
            from local_agent.src.executors.odoo_poster import OdooPoster
            poster = OdooPoster(self.vault_path)
            result = poster.register_payment(
                invoice_number=frontmatter.get("invoice_number", ""),
                amount=frontmatter.get("amount", 0),
            )
            ok = result.get("success", False)
            return ok, result.get("payment_id", result.get("error", ""))

        # ── Odoo: Purchase Bill ──────────────────────────────────────────────
        elif action == "create_purchase_bill":
            from local_agent.src.executors.odoo_poster import OdooPoster
            poster = OdooPoster(self.vault_path)
            result = poster.create_purchase_bill(
                vendor=frontmatter.get("vendor", frontmatter.get("customer", "")),
                amount=float(frontmatter.get("amount", 0)),
                description=frontmatter.get("description", ""),
                currency=frontmatter.get("currency", "PKR"),
            )
            ok = result.get("success", False)
            return ok, result.get("bill_number", result.get("error", ""))

        # ── Email ────────────────────────────────────────────────────────────
        elif action == "send_email":
            from agent_skills.approval_watcher import process_approval
            ok = process_approval(str(task_path), "email")
            return ok, "sent" if ok else "failed"

        # ── WhatsApp ─────────────────────────────────────────────────────────
        elif action == "send_message":
            from agent_skills.approval_watcher import process_approval
            ok = process_approval(str(task_path), "whatsapp")
            return ok, "sent" if ok else "failed"

        # ── LinkedIn ─────────────────────────────────────────────────────────
        elif action == "create_post":
            from agent_skills.approval_watcher import process_approval
            ok = process_approval(str(task_path), "linkedin")
            return ok, "posted" if ok else "failed"

        else:
            logger.warning(f"Unknown action '{action}' in {task_path.name} — skipping")
            return False, f"unknown action: {action}"

    def check_ceo_briefing(self):
        """
        FR-P054: Check every hour if it's Sunday 23:xx — if so, generate CEO briefing.
        Uses week ID to avoid double-sending.
        """
        now = time.time()
        if now - self._last_briefing_check < 3600:
            return
        self._last_briefing_check = now

        dt = datetime.now()
        # Sunday = weekday() 6, hour 23
        if dt.weekday() != 6 or dt.hour != 23:
            return

        week_id = dt.strftime("%Y-%W")  # e.g. "2026-08"
        if self._briefing_sent_this_sunday == week_id:
            return  # already sent this week

        logger.info("📊 Sunday 23:00 — generating CEO briefing…")
        try:
            from scripts.ceo_briefing import generate_briefing
            generate_briefing(self.vault_path, send_wa=True)
            self._briefing_sent_this_sunday = week_id
            logger.info("✅ CEO briefing generated")
        except Exception as e:
            logger.error(f"CEO briefing failed: {e}")

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

            # FR-P054: CEO briefing (Sunday 23:00)
            self.check_ceo_briefing()

            # FR-P048: Resource monitoring (CPU/Memory alerts every 5 min)
            self.resource_monitor.check()

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
