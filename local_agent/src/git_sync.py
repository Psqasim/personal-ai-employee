"""
Local Agent - Git Sync Service
60s cycle: pull from remote → auto-resolve Dashboard.md conflicts → log
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
    format='%(asctime)s - [LOCAL-GIT] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalGitSync:
    """
    Local Agent Git synchronization service
    Pull every 60s: fetch remote → rebase → auto-resolve conflicts
    """

    def __init__(self):
        """Initialize Local Git sync"""
        # Validate environment
        try:
            EnvValidator.validate_local_agent()
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
        Single sync cycle: pull from remote + auto-resolve conflicts

        Returns:
            True if sync succeeded, False otherwise
        """
        try:
            # Pull from remote (with rebase)
            pull_success, conflicts = self.git_manager.pull(retries=3)

            if pull_success:
                logger.info("✅ Pull complete - vault synchronized")
                return True

            # Handle conflicts
            if conflicts:
                logger.warning(f"⚠️  Merge conflicts detected: {conflicts}")

                # Auto-resolve Dashboard.md
                if "Dashboard.md" in conflicts:
                    if self.git_manager.resolve_dashboard_conflict():
                        logger.info("✅ Dashboard.md conflict auto-resolved")

                        # Try to complete rebase
                        try:
                            self.git_manager.repo.git.rebase("--continue")
                            logger.info("✅ Rebase completed after conflict resolution")
                            return True
                        except Exception as e:
                            logger.error(f"Failed to continue rebase: {e}")
                            self.git_manager.abort_rebase()
                            self._log_conflict_failure(conflicts)
                            return False
                    else:
                        logger.error("❌ Failed to auto-resolve Dashboard.md")
                        self.git_manager.abort_rebase()
                        self._log_conflict_failure(conflicts)
                        return False

                # Other conflicts require manual intervention
                logger.error(f"❌ Manual conflict resolution required: {conflicts}")
                self.git_manager.abort_rebase()
                self._log_conflict_failure(conflicts)
                return False

            # Pull failed without conflicts (network/other error)
            logger.error("❌ Pull failed (no conflicts)")
            self._log_sync_failure("pull_failed", "Network or Git error")
            return False

        except Exception as e:
            logger.error(f"Sync cycle error: {e}")
            self._log_sync_failure("exception", str(e))
            return False

    def _log_conflict_failure(self, conflicts: list):
        """Log unresolved conflicts to vault/Logs/Local/git_conflicts.md"""
        try:
            conflict_log = Path(self.vault_path) / "Logs" / "Local" / "git_conflicts.md"
            conflict_log.parent.mkdir(parents=True, exist_ok=True)

            with open(conflict_log, "a") as f:
                f.write(f"\n## {datetime.now().isoformat()}\n")
                f.write(f"- **Status**: Unresolved (manual intervention required)\n")
                f.write(f"- **Conflicted Files**:\n")
                for file in conflicts:
                    f.write(f"  - {file}\n")
                f.write("\n")

        except Exception as e:
            logger.error(f"Failed to log conflicts: {e}")

    def _log_sync_failure(self, error_type: str, details: str):
        """Log sync failure to vault/Logs/Local/git_sync_errors.md"""
        try:
            error_log = Path(self.vault_path) / "Logs" / "Local" / "git_sync_errors.md"
            error_log.parent.mkdir(parents=True, exist_ok=True)

            with open(error_log, "a") as f:
                f.write(f"\n## {datetime.now().isoformat()}\n")
                f.write(f"- **Error Type**: {error_type}\n")
                f.write(f"- **Details**: {details}\n\n")

        except Exception as e:
            logger.error(f"Failed to log sync failure: {e}")

    def run(self):
        """Main loop: pull every {sync_interval} seconds"""
        logger.info(f"🚀 Local Git Sync started (interval: {self.sync_interval}s)")

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
                logger.info("Shutting down Local Git Sync...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(self.sync_interval)


if __name__ == "__main__":
    sync = LocalGitSync()
    sync.run()
