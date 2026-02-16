"""
Claim Manager - Claim-by-move file coordination
Prevents race conditions when Cloud and Local process same task
"""
import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ClaimConflictError(Exception):
    """Raised when file is already claimed by another agent"""
    pass


class ClaimManager:
    """
    Atomic file-based claim system for dual-agent coordination
    Uses filesystem move operations (atomic on most systems)
    """

    def __init__(self, vault_path: str, agent_id: str):
        """
        Initialize claim manager

        Args:
            vault_path: Absolute path to vault directory
            agent_id: "cloud" or "local"
        """
        self.vault_path = Path(vault_path)
        self.agent_id = agent_id

        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")

    def claim_task(self, task_file: Path) -> bool:
        """
        Attempt to claim a task by moving from /Needs_Action/ to /In_Progress/{agent}/

        Atomic operation: Only first agent to move succeeds

        Args:
            task_file: Path to task file in /Needs_Action/

        Returns:
            True if claim succeeded, False if already claimed
        """
        # Destination: /In_Progress/{agent_id}/
        in_progress_dir = self.vault_path / "In_Progress" / self.agent_id
        in_progress_dir.mkdir(parents=True, exist_ok=True)

        destination = in_progress_dir / task_file.name

        try:
            # Atomic move (fails if another agent moved it first)
            # On Linux/macOS, os.rename is atomic within same filesystem
            # On Windows, this may not be perfectly atomic, but close enough
            task_file.rename(destination)

            logger.info(f"Claimed task: {task_file.name} → {self.agent_id}")
            return True

        except FileNotFoundError:
            # File doesn't exist or already moved by another agent
            logger.debug(f"Task already claimed by another agent: {task_file.name}")
            return False

        except Exception as e:
            logger.error(f"Failed to claim task {task_file.name}: {e}")
            return False

    def release_task(self, task_file: Path, target_folder: str = "Done") -> bool:
        """
        Release a task by moving from /In_Progress/{agent}/ to target folder

        Args:
            task_file: Path to task file in /In_Progress/{agent}/
            target_folder: Destination folder (Done, Rejected, etc.)

        Returns:
            True if release succeeded, False otherwise
        """
        if not task_file.exists():
            logger.warning(f"Task file not found for release: {task_file}")
            return False

        # Destination: /Done/ or /Rejected/
        dest_dir = self.vault_path / target_folder
        dest_dir.mkdir(parents=True, exist_ok=True)

        destination = dest_dir / task_file.name

        try:
            task_file.rename(destination)
            logger.info(f"Released task: {task_file.name} → {target_folder}")
            return True

        except Exception as e:
            logger.error(f"Failed to release task {task_file.name}: {e}")
            return False

    def check_ownership(self, task_name: str) -> Optional[str]:
        """
        Check which agent owns a task (if any)

        Args:
            task_name: Task filename (e.g., "EMAIL_DRAFT_12345.md")

        Returns:
            Agent ID ("cloud" or "local") if claimed, None if unclaimed
        """
        # Check /In_Progress/cloud/
        cloud_path = self.vault_path / "In_Progress" / "cloud" / task_name
        if cloud_path.exists():
            return "cloud"

        # Check /In_Progress/local/
        local_path = self.vault_path / "In_Progress" / "local" / task_name
        if local_path.exists():
            return "local"

        return None

    def safe_move(self, src: Path, dest: Path, overwrite: bool = False) -> bool:
        """
        Safe file move with error handling

        Args:
            src: Source file path
            dest: Destination file path
            overwrite: Allow overwriting existing file

        Returns:
            True if move succeeded, False otherwise
        """
        if not src.exists():
            logger.error(f"Source file not found: {src}")
            return False

        if dest.exists() and not overwrite:
            logger.warning(f"Destination already exists (overwrite=False): {dest}")
            return False

        try:
            # Ensure destination directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(str(src), str(dest))
            logger.debug(f"Moved: {src.name} → {dest.parent.name}/")
            return True

        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            return False

    def atomic_replace(self, target: Path, new_content: str) -> bool:
        """
        Atomic file content replacement (write to temp, then rename)

        Args:
            target: Target file path
            new_content: New file content

        Returns:
            True if replacement succeeded, False otherwise
        """
        try:
            # Write to temporary file
            temp_file = target.parent / f".{target.name}.tmp"
            with open(temp_file, "w") as f:
                f.write(new_content)

            # Atomic rename (replaces target)
            temp_file.rename(target)
            return True

        except Exception as e:
            logger.error(f"Atomic replace failed for {target}: {e}")
            return False

    def scan_needs_action(self) -> list[Path]:
        """
        Scan /Needs_Action/ for unclaimed tasks

        Returns:
            List of task file paths ready to claim
        """
        needs_action_dir = self.vault_path / "Needs_Action"
        if not needs_action_dir.exists():
            return []

        try:
            # Get all .md files in /Needs_Action/
            tasks = list(needs_action_dir.glob("*.md"))
            # Filter out .gitkeep and hidden files
            tasks = [t for t in tasks if not t.name.startswith(".")]
            return sorted(tasks)

        except Exception as e:
            logger.error(f"Failed to scan /Needs_Action/: {e}")
            return []

    def scan_in_progress(self) -> list[Path]:
        """
        Scan /In_Progress/{agent}/ for tasks owned by this agent

        Returns:
            List of task file paths currently owned
        """
        in_progress_dir = self.vault_path / "In_Progress" / self.agent_id
        if not in_progress_dir.exists():
            return []

        try:
            tasks = list(in_progress_dir.glob("*.md"))
            tasks = [t for t in tasks if not t.name.startswith(".")]
            return sorted(tasks)

        except Exception as e:
            logger.error(f"Failed to scan /In_Progress/{self.agent_id}/: {e}")
            return []
