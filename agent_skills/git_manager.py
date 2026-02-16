"""
Git Manager - GitPython wrapper for vault synchronization
Handles commit, push, pull, conflict detection, and retry logic
"""
import git
import time
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GitConflictError(Exception):
    """Raised when Git merge conflicts occur"""
    pass


class GitManager:
    """
    GitPython wrapper for Cloud/Local vault sync
    Provides atomic Git operations with retry and conflict handling
    """

    def __init__(self, vault_path: str, remote_url: str, branch: str = "main"):
        """
        Initialize Git manager

        Args:
            vault_path: Absolute path to vault directory
            remote_url: Git SSH URL (git@github.com:user/repo.git)
            branch: Git branch name (default: main)
        """
        self.vault_path = Path(vault_path)
        self.remote_url = remote_url
        self.branch = branch

        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")

        try:
            self.repo = git.Repo(self.vault_path)
        except git.exc.InvalidGitRepositoryError:
            logger.info(f"Initializing Git repository at {vault_path}")
            self.repo = git.Repo.init(self.vault_path)
            self._add_remote()

    def _add_remote(self):
        """Add origin remote if not exists"""
        try:
            self.repo.create_remote("origin", self.remote_url)
        except git.exc.GitCommandError:
            # Remote already exists
            pass

    def get_current_commit_hash(self) -> str:
        """Get current HEAD commit hash"""
        try:
            return self.repo.head.commit.hexsha
        except ValueError:
            # No commits yet
            return ""

    def commit(self, message: str, agent_id: str = "agent") -> Optional[str]:
        """
        Create Git commit with all changes

        Args:
            message: Commit message summary
            agent_id: "cloud" or "local" (prefixed to message)

        Returns:
            Commit hash if changes committed, None if no changes
        """
        try:
            # Stage all changes
            self.repo.git.add(".")

            # Check if there are changes
            try:
                if not self.repo.index.diff("HEAD"):
                    logger.debug("No changes to commit")
                    return None
            except git.exc.BadName:
                # No commits yet (HEAD doesn't exist), proceed with first commit
                pass

            # Create commit
            full_message = f"{agent_id.capitalize()}: {message}"
            commit = self.repo.index.commit(full_message)
            logger.info(f"Created commit: {commit.hexsha[:8]} - {full_message}")
            return commit.hexsha

        except git.exc.GitCommandError as e:
            logger.error(f"Git commit failed: {e}")
            raise

    def push(self, retries: int = 3) -> bool:
        """
        Push commits to remote with retry logic

        Args:
            retries: Number of retry attempts (default: 3)

        Returns:
            True if push succeeded, False otherwise
        """
        delays = [10, 30, 90]  # Exponential backoff (seconds)

        for attempt in range(retries):
            try:
                logger.info(f"Pushing to {self.remote_url} (attempt {attempt + 1}/{retries})")
                self.repo.remote("origin").push(refspec=f"{self.branch}:{self.branch}")
                logger.info("Push succeeded")
                return True

            except git.exc.GitCommandError as e:
                logger.warning(f"Push failed (attempt {attempt + 1}): {e}")

                if attempt < retries - 1:
                    delay = delays[attempt]
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)

        logger.error(f"Push failed after {retries} attempts")
        return False

    def pull(self, retries: int = 3) -> Tuple[bool, List[str]]:
        """
        Pull commits from remote with conflict detection

        Args:
            retries: Number of retry attempts

        Returns:
            Tuple of (success: bool, conflicts: List[str])
        """
        delays = [10, 30, 90]

        for attempt in range(retries):
            try:
                logger.info(f"Pulling from {self.remote_url} (attempt {attempt + 1}/{retries})")

                # Pull with rebase to avoid merge commits
                self.repo.git.pull("origin", self.branch, rebase=True)

                logger.info("Pull succeeded")
                return True, []

            except git.exc.GitCommandError as e:
                error_msg = str(e)

                # Check if merge conflict
                if "CONFLICT" in error_msg or "conflict" in error_msg.lower():
                    conflicts = self.detect_conflicts()
                    logger.warning(f"Merge conflicts detected: {conflicts}")
                    return False, conflicts

                # Network or other error
                logger.warning(f"Pull failed (attempt {attempt + 1}): {e}")

                if attempt < retries - 1:
                    delay = delays[attempt]
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)

        logger.error(f"Pull failed after {retries} attempts")
        return False, []

    def detect_conflicts(self) -> List[str]:
        """
        Detect conflicted files after failed pull

        Returns:
            List of file paths with conflicts
        """
        try:
            # Get unmerged paths (files with conflicts)
            unmerged = self.repo.index.unmerged_blobs()
            conflicts = list(unmerged.keys())
            return conflicts
        except Exception as e:
            logger.error(f"Error detecting conflicts: {e}")
            return []

    def resolve_dashboard_conflict(self) -> bool:
        """
        Auto-resolve Dashboard.md conflict (Platinum tier strategy)

        Strategy:
        - Cloud owns /## Updates/ section (timestamped status messages)
        - Local owns main content (task table, statistics)
        - Accept Cloud's /## Updates/, keep Local's main content

        Returns:
            True if conflict resolved, False otherwise
        """
        dashboard_path = self.vault_path / "Dashboard.md"

        if not dashboard_path.exists():
            return False

        try:
            # Get conflicted content
            with open(dashboard_path, "r") as f:
                content = f.read()

            if "<<<<<<< HEAD" not in content:
                return False  # No conflict markers

            # Parse conflict markers
            sections = content.split("<<<<<<< HEAD")
            if len(sections) < 2:
                return False

            # Extract Local (HEAD) and Cloud (incoming) versions
            local_section = sections[1].split("=======")[0].strip()
            cloud_section = sections[1].split("=======")[1].split(">>>>>>>")[0].strip()

            # Strategy: Keep Local main content + Cloud Updates section
            # Simple implementation: accept Cloud version (theirs)
            # TODO: Implement smart merge (extract ## Updates from Cloud, keep rest from Local)

            self.repo.git.checkout("--theirs", "Dashboard.md")
            self.repo.git.add("Dashboard.md")

            # Log conflict resolution
            conflict_log = self.vault_path / "Logs" / "Local" / "git_conflicts.md"
            conflict_log.parent.mkdir(parents=True, exist_ok=True)

            with open(conflict_log, "a") as f:
                f.write(f"\n## {datetime.now().isoformat()}\n")
                f.write(f"- **File**: Dashboard.md\n")
                f.write(f"- **Strategy**: Accepted Cloud version (theirs)\n")
                f.write(f"- **Status**: Auto-resolved\n\n")

            logger.info("Dashboard.md conflict auto-resolved")
            return True

        except Exception as e:
            logger.error(f"Failed to resolve Dashboard.md conflict: {e}")
            return False

    def abort_rebase(self):
        """Abort Git rebase if stuck in conflict state"""
        try:
            self.repo.git.rebase("--abort")
            logger.info("Git rebase aborted")
        except git.exc.GitCommandError as e:
            logger.warning(f"Failed to abort rebase: {e}")

    def get_sync_status(self) -> str:
        """
        Get current sync status

        Returns:
            "synced", "diverged", "conflict", or "offline"
        """
        try:
            # Fetch remote without merging
            self.repo.remote("origin").fetch()

            # Compare local and remote
            local_commit = self.repo.head.commit.hexsha
            remote_commit = self.repo.commit(f"origin/{self.branch}").hexsha

            if local_commit == remote_commit:
                return "synced"
            else:
                return "diverged"

        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return "offline"
