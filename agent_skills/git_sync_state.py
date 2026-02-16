"""
Git Sync State Persistence
Stores sync status in vault/.git_sync_state.md
"""
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import yaml
import logging

from agent_skills.entities import GitSyncState, SyncStatus

logger = logging.getLogger(__name__)


class GitSyncStateManager:
    """
    Manage GitSyncState persistence to vault/.git_sync_state.md
    """

    def __init__(self, vault_path: str):
        """
        Initialize Git sync state manager

        Args:
            vault_path: Absolute path to vault directory
        """
        self.vault_path = Path(vault_path)
        self.state_file = self.vault_path / ".git_sync_state.md"

    def load_state(self) -> GitSyncState:
        """
        Load Git sync state from file

        Returns:
            GitSyncState object (creates new if file doesn't exist)
        """
        if not self.state_file.exists():
            return self._create_default_state()

        try:
            with open(self.state_file, "r") as f:
                content = f.read()

            # Parse YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])

                    return GitSyncState(
                        sync_id=frontmatter.get("sync_id", "default"),
                        last_pull_timestamp=self._parse_datetime(frontmatter.get("last_pull_timestamp")),
                        last_push_timestamp=self._parse_datetime(frontmatter.get("last_push_timestamp")),
                        commit_hash_cloud=frontmatter.get("commit_hash_cloud", ""),
                        commit_hash_local=frontmatter.get("commit_hash_local", ""),
                        pending_conflicts=frontmatter.get("pending_conflicts", []),
                        sync_status=SyncStatus(frontmatter.get("sync_status", "synced"))
                    )

            return self._create_default_state()

        except Exception as e:
            logger.error(f"Failed to load sync state: {e}")
            return self._create_default_state()

    def save_state(self, state: GitSyncState):
        """
        Save Git sync state to file

        Args:
            state: GitSyncState object to persist
        """
        try:
            frontmatter = {
                "sync_id": state.sync_id,
                "last_pull_timestamp": state.last_pull_timestamp.isoformat() if state.last_pull_timestamp else None,
                "last_push_timestamp": state.last_push_timestamp.isoformat() if state.last_push_timestamp else None,
                "commit_hash_cloud": state.commit_hash_cloud,
                "commit_hash_local": state.commit_hash_local,
                "pending_conflicts": state.pending_conflicts,
                "sync_status": state.sync_status.value
            }

            content = "---\n"
            content += yaml.dump(frontmatter, default_flow_style=False)
            content += "---\n\n"
            content += "# Git Sync State\n\n"
            content += f"**Last Updated**: {datetime.now().isoformat()}\n\n"
            content += f"**Status**: {state.sync_status.value}\n"
            content += f"**In Sync**: {'Yes' if state.is_synced() else 'No'}\n"
            content += f"**Has Conflicts**: {'Yes' if state.has_conflicts() else 'No'}\n\n"

            if state.pending_conflicts:
                content += "## Pending Conflicts\n\n"
                for conflict in state.pending_conflicts:
                    content += f"- {conflict}\n"

            with open(self.state_file, "w") as f:
                f.write(content)

            logger.debug(f"Saved sync state: {state.sync_status.value}")

        except Exception as e:
            logger.error(f"Failed to save sync state: {e}")

    def update_cloud_push(self, commit_hash: str):
        """
        Update state after Cloud push

        Args:
            commit_hash: Commit hash that was pushed
        """
        state = self.load_state()
        state.last_push_timestamp = datetime.now()
        state.commit_hash_cloud = commit_hash
        state.sync_status = SyncStatus.DIVERGED if state.commit_hash_cloud != state.commit_hash_local else SyncStatus.SYNCED
        self.save_state(state)

    def update_local_pull(self, commit_hash: str, conflicts: List[str] = None):
        """
        Update state after Local pull

        Args:
            commit_hash: Commit hash that was pulled
            conflicts: List of conflicted files (if any)
        """
        state = self.load_state()
        state.last_pull_timestamp = datetime.now()
        state.commit_hash_local = commit_hash
        state.pending_conflicts = conflicts or []

        if conflicts:
            state.sync_status = SyncStatus.CONFLICT
        elif state.commit_hash_cloud == state.commit_hash_local:
            state.sync_status = SyncStatus.SYNCED
        else:
            state.sync_status = SyncStatus.DIVERGED

        self.save_state(state)

    def mark_offline(self):
        """Mark sync as offline (remote unreachable)"""
        state = self.load_state()
        state.sync_status = SyncStatus.OFFLINE
        self.save_state(state)

    def _create_default_state(self) -> GitSyncState:
        """Create default GitSyncState"""
        return GitSyncState(
            sync_id=f"sync_{datetime.now().strftime('%Y%m%d')}",
            sync_status=SyncStatus.SYNCED
        )

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO format datetime string"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str)
        except Exception:
            return None
