"""
Cloud Agent Orchestrator
Main loop: Email triage → Social drafts → Git push → WhatsApp notifications
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
from agent_skills.git_sync_state import GitSyncStateManager
from agent_skills.api_usage_tracker import APIUsageTracker

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

        for email_file in email_files:
            try:
                # Parse email
                email_data = parse_email_from_vault(str(email_file))

                if not email_data:
                    logger.warning(f"Failed to parse: {email_file.name}")
                    continue

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

            except Exception as e:
                logger.error(f"Failed to process {email_file.name}: {e}")

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
        Send WhatsApp notifications for urgent events
        """
        logger.debug("Checking notifications...")

        # TODO: Implement WhatsApp notifications
        # 1. Check for urgent emails (priority="High")
        # 2. Check for critical errors (Git sync failing >5 min)
        # 3. Send WhatsApp notification via MCP
        # 4. Log notification sent

        pass

    def poll_gmail(self):
        """
        Poll Gmail for new emails and write to vault/Inbox/.
        Called every orchestration cycle (default: 5 min for orchestrator,
        but gmail_watcher.py can also run as a separate PM2 process at 60s).
        """
        try:
            count = self.gmail_watcher.poll_once()
            if count:
                logger.info(f"📬 Gmail poll: {count} new email(s) added to inbox")
        except Exception as e:
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
