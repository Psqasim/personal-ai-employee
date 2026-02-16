"""
Git Sync Failure Alerts
Creates vault/Needs_Action/git_sync_failed.md when offline >5 min
"""
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SyncAlertManager:
    """
    Manage alerts for Git sync failures
    """

    OFFLINE_THRESHOLD_MINUTES = 5

    def __init__(self, vault_path: str, agent_id: str):
        """
        Initialize sync alert manager

        Args:
            vault_path: Absolute path to vault directory
            agent_id: "cloud" or "local"
        """
        self.vault_path = Path(vault_path)
        self.agent_id = agent_id
        self.last_successful_sync: Optional[datetime] = datetime.now()
        self.alert_created = False

    def record_success(self):
        """Record successful Git sync"""
        self.last_successful_sync = datetime.now()
        self.alert_created = False

        # Remove alert if exists
        alert_file = self.vault_path / "Needs_Action" / "git_sync_failed.md"
        if alert_file.exists():
            try:
                alert_file.unlink()
                logger.info("Removed git_sync_failed.md (sync recovered)")
            except Exception as e:
                logger.warning(f"Failed to remove alert file: {e}")

    def record_failure(self):
        """Record Git sync failure"""
        if not self.last_successful_sync:
            self.last_successful_sync = datetime.now()
            return

        time_offline = datetime.now() - self.last_successful_sync

        # Check if offline > threshold
        if time_offline > timedelta(minutes=self.OFFLINE_THRESHOLD_MINUTES):
            if not self.alert_created:
                self._create_alert(time_offline)
                self.alert_created = True

    def _create_alert(self, time_offline: timedelta):
        """
        Create git_sync_failed.md alert in vault/Needs_Action/

        Args:
            time_offline: How long sync has been failing
        """
        try:
            needs_action_dir = self.vault_path / "Needs_Action"
            needs_action_dir.mkdir(parents=True, exist_ok=True)

            alert_file = needs_action_dir / "git_sync_failed.md"

            minutes_offline = int(time_offline.total_seconds() / 60)

            content = f"""---
title: Git Sync Failed - {self.agent_id.capitalize()} Agent
type: system_alert
priority: high
created: {datetime.now().isoformat()}
agent: {self.agent_id}
---

# 🚨 Git Sync Failure Alert

## Issue
Git synchronization has been failing for **{minutes_offline} minutes** on the **{self.agent_id.capitalize()} Agent**.

## Impact
- Cloud and Local agents are out of sync
- Changes may not be propagating between agents
- Risk of duplicate processing or data loss

## Troubleshooting Steps

### 1. Check Network Connectivity
```bash
# Test Git remote connection
ssh -T git@github.com

# Check internet connectivity
ping -c 3 google.com
```

### 2. Verify Git Remote
```bash
# Check remote URL
git remote -v

# Test pull manually
git pull origin main
```

### 3. Check Logs
- **Cloud Agent**: `vault/Logs/Cloud/git_sync_errors.md`
- **Local Agent**: `vault/Logs/Local/git_sync_errors.md`

### 4. Common Fixes

**SSH Key Issues**:
```bash
# Re-add SSH key
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

**Merge Conflicts**:
```bash
# Abort rebase and retry
git rebase --abort
git pull origin main
```

**Network Issues**:
- Check firewall/VPN settings
- Verify GitHub status: https://www.githubstatus.com/

## Next Steps
1. Review troubleshooting steps above
2. Check error logs for details
3. Fix underlying issue
4. Restart Git sync process:
   - Cloud: `pm2 restart git_sync_cloud`
   - Local: `pm2 restart git_sync_local`
5. Verify sync working: Check git log for new commits

## Auto-Recovery
This alert will automatically disappear once Git sync succeeds.
"""

            with open(alert_file, "w") as f:
                f.write(content)

            logger.warning(f"🚨 Created git_sync_failed.md alert ({minutes_offline} min offline)")

        except Exception as e:
            logger.error(f"Failed to create sync failure alert: {e}")


# Import for type hint
from typing import Optional
