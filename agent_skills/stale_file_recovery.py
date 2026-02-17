"""
Stale File Recovery - FR-P016

Checks vault/In_Progress/ every hour for files older than 24 hours.
Moves them back to vault/Needs_Action/ and logs the recovery action.

Author: Personal AI Employee (Platinum Tier)
Created: 2026-02-17
"""

import logging
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

STALE_THRESHOLD_HOURS = 24


def recover_stale_files(vault_path: str) -> int:
    """
    Check vault/In_Progress/ for files older than 24h and move back to Needs_Action/.

    Args:
        vault_path: Absolute path to the vault directory

    Returns:
        Number of files recovered
    """
    vault = Path(vault_path)
    in_progress = vault / "In_Progress"
    needs_action = vault / "Needs_Action"
    log_path = vault / "Logs" / "Local" / "stale_recovery.md"

    if not in_progress.exists():
        return 0

    needs_action.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=STALE_THRESHOLD_HOURS)
    recovered = 0

    for stale_file in in_progress.rglob("*.md"):
        try:
            mtime = datetime.fromtimestamp(stale_file.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                dest = needs_action / stale_file.name
                # Avoid overwriting — suffix with timestamp if name collision
                if dest.exists():
                    stem = stale_file.stem
                    suffix = stale_file.suffix
                    dest = needs_action / f"{stem}_recovered_{now.strftime('%Y%m%d%H%M%S')}{suffix}"

                shutil.move(str(stale_file), str(dest))
                recovered += 1

                age_hours = (now - mtime).total_seconds() / 3600
                logger.info(
                    f"[stale_recovery] Recovered stale file: {stale_file.name} "
                    f"(age={age_hours:.1f}h) → Needs_Action/"
                )
                _log_recovery(log_path, stale_file.name, age_hours, str(dest))

        except Exception as e:
            logger.error(f"[stale_recovery] Failed to recover {stale_file.name}: {e}")

    if recovered:
        logger.info(f"[stale_recovery] ✅ Recovered {recovered} stale file(s) from In_Progress/")

    return recovered


def _log_recovery(log_path: Path, filename: str, age_hours: float, dest: str) -> None:
    """Append recovery log entry."""
    timestamp = datetime.now().isoformat()
    entry = f"| {timestamp} | {filename} | {age_hours:.1f}h | {dest} |\n"

    try:
        if not log_path.exists():
            log_path.write_text(
                "# Stale File Recovery Log\n\n"
                "| Timestamp | File | Age | Moved To |\n"
                "|-----------|------|-----|----------|\n"
            )
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        logger.warning(f"[stale_recovery] Could not write log: {e}")
