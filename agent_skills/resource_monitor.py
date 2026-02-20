"""
FR-P048: Resource Monitor — CPU / Memory alerting

Checks CPU and Memory every 5 minutes.
Sends WhatsApp alert if:
  - CPU  > CPU_ALERT_THRESHOLD  (default 80%)
  - Memory > MEM_ALERT_THRESHOLD (default 90%)

Logs to vault/Logs/System/resource-YYYY-MM-DD.md

Usage (integrate into orchestrator):
    from agent_skills.resource_monitor import ResourceMonitor
    monitor = ResourceMonitor(vault_path)
    monitor.check()   # call in your orchestration loop
"""

import os
import time
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Thresholds from env (override in .env) ─────────────────────────────────────
_CPU_THRESHOLD = float(os.getenv("CPU_ALERT_THRESHOLD", "80"))
_MEM_THRESHOLD = float(os.getenv("MEM_ALERT_THRESHOLD", "90"))
_CHECK_INTERVAL = int(os.getenv("RESOURCE_CHECK_INTERVAL_SEC", "300"))  # 5 min


class ResourceMonitor:
    """
    Monitors CPU and Memory usage and sends WhatsApp alerts on threshold breach.
    Designed to be called once per orchestrator cycle (it self-throttles).
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.log_dir = self.vault_path / "Logs" / "System"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._last_check: float = 0.0
        self._last_alert_cpu: float = 0.0    # suppress repeated alerts (15 min)
        self._last_alert_mem: float = 0.0

    def check(self) -> None:
        """
        Run resource check if enough time has passed since last check.
        Safe to call every 30 seconds — throttles itself to _CHECK_INTERVAL.
        """
        now = time.time()
        if now - self._last_check < _CHECK_INTERVAL:
            return
        self._last_check = now

        try:
            import psutil
        except ImportError:
            logger.debug("psutil not installed — resource monitoring skipped")
            return

        try:
            cpu_pct = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            mem_pct = mem.percent

            timestamp = datetime.now()
            self._log(timestamp, cpu_pct, mem_pct)

            alerts = []
            if cpu_pct > _CPU_THRESHOLD and now - self._last_alert_cpu > 900:
                alerts.append(f"⚠️ *High CPU*: {cpu_pct:.0f}% (threshold {_CPU_THRESHOLD:.0f}%)")
                self._last_alert_cpu = now

            if mem_pct > _MEM_THRESHOLD and now - self._last_alert_mem > 900:
                used_gb = mem.used / 1e9
                total_gb = mem.total / 1e9
                alerts.append(
                    f"⚠️ *High Memory*: {mem_pct:.0f}% "
                    f"({used_gb:.1f} / {total_gb:.1f} GB, threshold {_MEM_THRESHOLD:.0f}%)"
                )
                self._last_alert_mem = now

            if alerts:
                msg = "\n".join(alerts) + f"\n🕐 {timestamp.strftime('%H:%M')}"
                self._send_alert(msg)

        except Exception as e:
            logger.warning(f"Resource check error: {e}")

    def _log(self, ts: datetime, cpu: float, mem: float) -> None:
        """Append a one-line entry to today's resource log."""
        log_file = self.log_dir / f"resource-{ts.strftime('%Y-%m-%d')}.md"
        if not log_file.exists():
            log_file.write_text(
                "# Resource Monitor Log\n\n"
                "| Time | CPU% | Mem% |\n"
                "|------|------|------|\n"
            )
        with open(log_file, "a", encoding="utf-8") as f:
            flag = " ⚠️" if cpu > _CPU_THRESHOLD or mem > _MEM_THRESHOLD else ""
            f.write(f"| {ts.strftime('%H:%M:%S')} | {cpu:.0f} | {mem:.0f}{flag} |\n")

    def _send_alert(self, message: str) -> None:
        """Send WhatsApp alert (non-fatal if unavailable)."""
        try:
            from cloud_agent.src.notifications.whatsapp_notifier import notify_critical_error
            notify_critical_error(message)
            logger.warning(f"Resource alert sent: {message[:80]}")
        except Exception as e:
            logger.debug(f"Resource alert WhatsApp failed: {e}")
