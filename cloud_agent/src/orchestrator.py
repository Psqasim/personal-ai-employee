"""
Cloud Agent Orchestrator
Main loop: Email triage → Social drafts → Git push → WhatsApp notifications
"""
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env.cloud (or ENV_FILE override)
try:
    from dotenv import load_dotenv
    _env_file = os.getenv("ENV_FILE", str(project_root / ".env"))
    load_dotenv(_env_file)
    load_dotenv(project_root / ".env.cloud", override=True)  # no-op if missing
except ImportError:
    pass  # env vars must be set manually

from agent_skills.env_validator import EnvValidator
from agent_skills.git_sync_state import GitSyncStateManager
from agent_skills.api_usage_tracker import APIUsageTracker
from cloud_agent.src.notifications.whatsapp_notifier import (
    notify_urgent_email,
    notify_pending_approvals,
    notify_critical_error,
    notify_morning_summary,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [CLOUD-ORCH] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CloudOrchestrator:
    """
    Cloud Agent main orchestration loop
    Coordinates email triage, social drafting, Git sync
    """

    def __init__(self):
        """Initialize Cloud Orchestrator"""
        # Validate environment
        try:
            EnvValidator.validate_cloud_agent()
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            sys.exit(1)

        # Load config
        self.vault_path = os.getenv("VAULT_PATH")
        self.agent_id = "cloud"

        # Initialize components
        self.sync_state_mgr = GitSyncStateManager(self.vault_path)
        self.api_tracker = APIUsageTracker(self.vault_path, self.agent_id)

        # Track last morning summary sent (avoid duplicates)
        self._morning_summary_sent_date: str = ""

        # Pending approval alert cooldown — only send once per hour (not every 5-min cycle)
        self._last_pending_alert_time: float = 0.0
        self._pending_alert_interval: float = 3600.0  # 1 hour

        # Gmail auth failure cooldown — disable polling after repeated auth errors
        self._gmail_auth_failures: int = 0
        self._gmail_disabled_until: float = 0.0  # epoch; 0 = not disabled

        # Gmail watcher (polls on each orchestration cycle)
        from cloud_agent.src.watchers.gmail_watcher import CloudGmailWatcher
        self.gmail_watcher = CloudGmailWatcher(self.vault_path)

        logger.info("Cloud Orchestrator initialized")

    def process_inbox(self):
        """
        Process vault/Inbox/ for new emails
        Draft replies for high-priority emails
        """
        logger.debug("Processing inbox...")

        inbox_path = Path(self.vault_path) / "Inbox"
        if not inbox_path.exists():
            logger.debug("Inbox directory not found")
            return

        # Scan for EMAIL_*.md files
        email_files = list(inbox_path.glob("EMAIL_*.md"))
        if not email_files:
            logger.debug("No email files in inbox")
            return

        logger.info(f"📧 Found {len(email_files)} email(s) in inbox")

        # Process each email
        from agent_skills.vault_parser import parse_email_from_vault
        from agent_skills.draft_generator import generate_email_draft
        from agent_skills.dashboard_updater import update_dashboard

        # Odoo draft generator (only instantiate if enabled)
        odoo_gen = None
        if os.getenv("ENABLE_ODOO", "false").lower() == "true":
            try:
                from cloud_agent.src.generators.odoo_draft import OdooDraftGenerator
                odoo_gen = OdooDraftGenerator(self.vault_path)
            except Exception as e:
                logger.debug(f"Odoo draft generator unavailable: {e}")

        for email_file in email_files:
            try:
                # Parse email
                email_data = parse_email_from_vault(str(email_file))

                if not email_data:
                    logger.warning(f"Failed to parse (skipping): {email_file.name}")
                    # Move unparseable file to quarantine to avoid infinite retry
                    quarantine = Path(self.vault_path) / "Logs" / "Cloud" / "unparseable"
                    quarantine.mkdir(parents=True, exist_ok=True)
                    try:
                        import shutil
                        shutil.move(str(email_file), str(quarantine / email_file.name))
                        logger.info(f"Quarantined unparseable file: {email_file.name}")
                    except Exception as qe:
                        logger.warning(f"Could not quarantine {email_file.name}: {qe}")
                    continue

                # Generate Odoo invoice draft if invoice keywords detected
                if odoo_gen:
                    try:
                        odoo_path = odoo_gen.generate_and_save(email_data)
                        if odoo_path:
                            logger.info(f"🧾 Odoo draft queued: {odoo_path.name}")
                    except Exception as e:
                        logger.debug(f"Odoo draft skipped for {email_file.name}: {e}")

                # Check if already drafted
                draft_id = email_data.get("email_id", email_file.stem)
                draft_path = Path(self.vault_path) / "Pending_Approval" / "Email" / f"EMAIL_DRAFT_{draft_id}.md"

                if draft_path.exists():
                    logger.debug(f"Draft already exists for {draft_id}")
                    continue

                # Generate draft
                logger.info(f"Generating draft for: {email_data.get('subject', 'Unknown')}")

                company_handbook = Path(self.vault_path) / "Company_Handbook.md"
                draft = generate_email_draft(
                    original_email=email_data,
                    company_handbook_path=str(company_handbook) if company_handbook.exists() else None
                )

                # Save draft
                draft_path.parent.mkdir(parents=True, exist_ok=True)
                with open(draft_path, 'w', encoding='utf-8') as f:
                    f.write(f"---\n")
                    f.write(f"draft_id: {draft['draft_id']}\n")
                    f.write(f"to: {draft['to']}\n")
                    f.write(f"subject: {draft['subject']}\n")
                    f.write(f"status: pending\n")
                    f.write(f"created: {draft.get('created', datetime.now().isoformat())}\n")
                    f.write(f"---\n\n")
                    f.write(draft['draft_body'])

                # Update Dashboard
                update_dashboard(
                    vault_path=self.vault_path,
                    agent_id="cloud",
                    update_type="email_draft_created",
                    details=f"Email draft: {email_data.get('subject', 'Unknown')[:50]}"
                )

                # Track API usage
                self.api_tracker.log_api_call(
                    model="claude-sonnet-4-5-20250929",
                    prompt_tokens=500,  # Estimate
                    completion_tokens=300,  # Estimate
                    task_type="email_draft"
                )

                logger.info(f"✅ Draft created: {draft_path.name}")

                # Notify admin via WhatsApp if urgent email
                priority = email_data.get("priority", "").lower()
                if priority in ("high", "urgent"):
                    notify_urgent_email(
                        sender=email_data.get("from", "Unknown"),
                        subject=email_data.get("subject", "No Subject")
                    )

            except Exception as e:
                logger.error(f"Failed to process {email_file.name}: {e}")
                notify_critical_error(f"Email processing failed: {e}")

    def generate_social_drafts(self):
        """
        Generate social media drafts (LinkedIn, Facebook, Instagram, Twitter)
        Based on Company_Handbook.md business goals
        """
        logger.debug("Generating social drafts...")

        # TODO: Implement social draft generation
        # 1. Read Company_Handbook.md business goals
        # 2. Check posting schedule (daily/weekly)
        # 3. Generate LinkedIn post
        # 4. Save to vault/Pending_Approval/LinkedIn/
        # 5. Log API usage

        pass

    def send_notifications(self):
        """
        Send WhatsApp notifications for pending approvals and morning summary.
        Urgent email notifications are sent inline in process_inbox().
        """
        logger.debug("Checking notifications...")

        vault = Path(self.vault_path)

        # Check pending approvals — alert if 5+
        pending_count = 0
        oldest_item = ""
        oldest_mtime = float("inf")
        pending_approval_path = vault / "Pending_Approval"
        if pending_approval_path.exists():
            for f in pending_approval_path.rglob("*.md"):
                pending_count += 1
                mtime = f.stat().st_mtime
                if mtime < oldest_mtime:
                    oldest_mtime = mtime
                    oldest_item = f.name

        if pending_count >= 5:
            now = time.time()
            if now - self._last_pending_alert_time >= self._pending_alert_interval:
                logger.info(f"⏳ {pending_count} items pending approval — sending WhatsApp alert")
                notify_pending_approvals(count=pending_count, oldest_item=oldest_item)
                self._last_pending_alert_time = now
            else:
                mins_left = int((self._pending_alert_interval - (now - self._last_pending_alert_time)) / 60)
                logger.debug(f"⏳ {pending_count} pending — alert suppressed (next in ~{mins_left}m)")

        # Morning summary at 8 AM UTC (send once per day)
        now_utc = datetime.now(timezone.utc)
        today_str = now_utc.strftime("%Y-%m-%d")
        if now_utc.hour == 8 and self._morning_summary_sent_date != today_str:
            self._morning_summary_sent_date = today_str

            # Count inbox + pending emails
            inbox_count = len(list((vault / "Inbox").glob("EMAIL_*.md"))) if (vault / "Inbox").exists() else 0
            pending_email_count = len(list((vault / "Pending_Approval" / "Email").glob("*.md"))) if (vault / "Pending_Approval" / "Email").exists() else 0
            emails_pending = inbox_count + pending_email_count

            # Count done files from yesterday
            done_path = vault / "Done"
            yesterday_str = (now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
                             .strftime("%Y-%m-%d"))
            processed_yesterday = 0
            if done_path.exists():
                for f in done_path.rglob("*.md"):
                    mtime_str = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
                    if mtime_str == yesterday_str:
                        processed_yesterday += 1

            # Get today's API cost
            api_cost_today = self.api_tracker.get_daily_cost() if hasattr(self.api_tracker, "get_daily_cost") else 0.0

            logger.info("☀️ Sending morning summary WhatsApp notification")
            notify_morning_summary(
                emails_pending=emails_pending,
                processed_yesterday=processed_yesterday,
                api_cost_today=api_cost_today
            )

    def poll_gmail(self):
        """
        Poll Gmail for new emails and write to vault/Inbox/.
        Set ENABLE_GMAIL_WATCHER=false to disable entirely.
        Auto-disables for 6 hours after 3 consecutive auth failures to avoid
        spamming logs with invalid_grant / SSL errors.
        """
        # Respect ENABLE_GMAIL_WATCHER env var (default true for backwards compat)
        if os.getenv("ENABLE_GMAIL_WATCHER", "true").lower() == "false":
            return

        now = time.time()

        # Check if Gmail is temporarily disabled due to repeated auth errors
        if self._gmail_disabled_until > now:
            mins_left = int((self._gmail_disabled_until - now) / 60)
            logger.debug(f"Gmail polling disabled (auth errors) — resumes in ~{mins_left}m")
            return

        try:
            count = self.gmail_watcher.poll_once()
            if count:
                logger.info(f"📬 Gmail poll: {count} new email(s) added to inbox")
            # Reset failure counter on success
            self._gmail_auth_failures = 0
        except Exception as e:
            err_str = str(e).lower()
            # Detect auth errors: invalid_grant, token expired, SSL OAuth failures
            if any(kw in err_str for kw in ("invalid_grant", "token has been expired", "revoked", "ssleoferror")):
                self._gmail_auth_failures += 1
                if self._gmail_auth_failures >= 3:
                    disable_hours = 6
                    self._gmail_disabled_until = now + (disable_hours * 3600)
                    logger.warning(
                        f"Gmail auth error #{self._gmail_auth_failures} — "
                        f"disabling Gmail polling for {disable_hours}h. "
                        f"Re-run scripts/setup_gmail_auth.py to fix."
                    )
                else:
                    logger.warning(f"Gmail auth error #{self._gmail_auth_failures}/3: {e}")
            else:
                logger.error(f"Gmail poll error: {e}")

    def orchestration_cycle(self):
        """
        Single orchestration cycle
        Run all Cloud Agent tasks
        """
        try:
            # 1. Poll Gmail for new emails
            self.poll_gmail()

            # 2. Process inbox → generate drafts
            self.process_inbox()

            # 3. Social media draft generation
            self.generate_social_drafts()

            # 4. WhatsApp notifications
            self.send_notifications()

            logger.debug("Orchestration cycle complete")

        except Exception as e:
            logger.error(f"Orchestration cycle error: {e}")

    def run(self):
        """
        Main loop: Run orchestration every 5 minutes
        (Git sync runs separately via git_sync.py)
        """
        logger.info("🚀 Cloud Orchestrator started")

        cycle_interval = 300  # 5 minutes

        while True:
            try:
                self.orchestration_cycle()
                time.sleep(cycle_interval)

            except KeyboardInterrupt:
                logger.info("Shutting down Cloud Orchestrator...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(cycle_interval)


if __name__ == "__main__":
    orchestrator = CloudOrchestrator()
    orchestrator.run()
