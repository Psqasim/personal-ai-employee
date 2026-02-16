"""
Cloud Agent - Git Sync Service
60s cycle: add all changes → commit → push to remote
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

from agent_skills.git_manager import GitManager
from agent_skills.env_validator import EnvValidator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [CLOUD-GIT] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CloudGitSync:
    """
    Cloud Agent Git synchronization service
    Batched commits every 60s: draft files → commit → push
    """

    def __init__(self):
        """Initialize Cloud Git sync"""
        # Validate environment
        try:
            EnvValidator.validate_cloud_agent()
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            sys.exit(1)

        # Load config
        self.vault_path = os.getenv("VAULT_PATH")
        self.git_remote_url = os.getenv("GIT_REMOTE_URL")
        self.git_branch = os.getenv("GIT_BRANCH", "main")
        self.sync_interval = int(os.getenv("GIT_SYNC_INTERVAL", "60"))

        # Initialize Git manager
        try:
            self.git_manager = GitManager(
                vault_path=self.vault_path,
                remote_url=self.git_remote_url,
                branch=self.git_branch
            )
            logger.info(f"Git manager initialized: {self.git_remote_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Git manager: {e}")
            sys.exit(1)

    def sync_cycle(self) -> bool:
        """
        Single sync cycle: commit all changes + push to remote

        Returns:
            True if sync succeeded, False otherwise
        """
        try:
            # Summarize changes for commit message
            summary = self._summarize_changes()

            if not summary:
                logger.debug("No changes to sync")
                return True

            # Create commit
            commit_hash = self.git_manager.commit(
                message=summary,
                agent_id="cloud"
            )

            if not commit_hash:
                logger.debug("No commit created (no changes)")
                return True

            # Push to remote
            push_success = self.git_manager.push(retries=3)

            if push_success:
                logger.info(f"✅ Sync complete: {commit_hash[:8]} - {summary}")
                return True
            else:
                logger.error(f"❌ Push failed after retries")
                self._log_sync_failure("push_failed", summary)
                return False

        except Exception as e:
            logger.error(f"Sync cycle error: {e}")
            self._log_sync_failure("exception", str(e))
            return False

    def _summarize_changes(self) -> str:
        """
        Summarize pending changes for commit message

        Returns:
            Human-readable summary (e.g., "3 email drafts, 1 LinkedIn post")
        """
        try:
            repo = self.git_manager.repo

            # Get changed files
            changed_files = [item.a_path for item in repo.index.diff(None)]  # Unstaged
            changed_files += [item.a_path for item in repo.index.diff("HEAD")]  # Staged

            if not changed_files:
                return ""

            # Count by category
            email_drafts = sum(1 for f in changed_files if "Email" in f and "Pending_Approval" in f)
            linkedin_posts = sum(1 for f in changed_files if "LinkedIn" in f and "Pending_Approval" in f)
            whatsapp_drafts = sum(1 for f in changed_files if "WhatsApp" in f and "Pending_Approval" in f)
            social_posts = sum(1 for f in changed_files if any(s in f for s in ["Facebook", "Instagram", "Twitter"]))
            dashboard_updates = sum(1 for f in changed_files if "Dashboard.md" in f)

            parts = []
            if email_drafts:
                parts.append(f"{email_drafts} email draft{'s' if email_drafts > 1 else ''}")
            if linkedin_posts:
                parts.append(f"{linkedin_posts} LinkedIn post{'s' if linkedin_posts > 1 else ''}")
            if whatsapp_drafts:
                parts.append(f"{whatsapp_drafts} WhatsApp draft{'s' if whatsapp_drafts > 1 else ''}")
            if social_posts:
                parts.append(f"{social_posts} social post{'s' if social_posts > 1 else ''}")
            if dashboard_updates:
                parts.append("Dashboard update")

            if not parts:
                parts.append(f"{len(changed_files)} file{'s' if len(changed_files) > 1 else ''} updated")

            return ", ".join(parts)

        except Exception as e:
            logger.warning(f"Failed to summarize changes: {e}")
            return "files updated"

    def _log_sync_failure(self, error_type: str, details: str):
        """Log sync failure to vault/Logs/Cloud/git_sync_errors.md"""
        try:
            error_log = Path(self.vault_path) / "Logs" / "Cloud" / "git_sync_errors.md"
            error_log.parent.mkdir(parents=True, exist_ok=True)

            with open(error_log, "a") as f:
                f.write(f"\n## {datetime.now().isoformat()}\n")
                f.write(f"- **Error Type**: {error_type}\n")
                f.write(f"- **Details**: {details}\n\n")

        except Exception as e:
            logger.error(f"Failed to log sync failure: {e}")

    def run(self):
        """Main loop: sync every {sync_interval} seconds"""
        logger.info(f"🚀 Cloud Git Sync started (interval: {self.sync_interval}s)")

        cycle_count = 0
        while True:
            try:
                cycle_count += 1
                logger.debug(f"Sync cycle #{cycle_count}")

                # Run sync
                self.sync_cycle()

                # Wait for next cycle
                time.sleep(self.sync_interval)

            except KeyboardInterrupt:
                logger.info("Shutting down Cloud Git Sync...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(self.sync_interval)


if __name__ == "__main__":
    sync = CloudGitSync()
    sync.run()
