"""
API Usage Tracker - Log Claude API calls for cost tracking
Writes to vault/Logs/API_Usage/YYYY-MM-DD.md
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

# FR-P053: Daily cost alert threshold (override via .env)
_COST_ALERT_THRESHOLD = float(os.getenv("COST_ALERT_THRESHOLD", "1.00"))

logger = logging.getLogger(__name__)


class APIUsageTracker:
    """
    Track Claude API usage and calculate costs
    Logs to daily markdown files for CEO Briefing and Dashboard
    """

    # Pricing (USD per 1M tokens)
    PRICING = {
        "claude-opus-4": {"prompt": 15.0, "completion": 75.0},
        "claude-opus-4-6": {"prompt": 15.0, "completion": 75.0},
        "claude-sonnet-4": {"prompt": 3.0, "completion": 15.0},
        "claude-sonnet-4-5-20250929": {"prompt": 3.0, "completion": 15.0},
        "claude-haiku-3-5": {"prompt": 0.8, "completion": 4.0},
        "claude-haiku-4-5-20251001": {"prompt": 0.8, "completion": 4.0},
    }

    def __init__(self, vault_path: str, agent_id: str):
        """
        Initialize API usage tracker

        Args:
            vault_path: Absolute path to vault directory
            agent_id: "cloud" or "local"
        """
        self.vault_path = Path(vault_path)
        self.agent_id = agent_id
        self.log_dir = self.vault_path / "Logs" / "API_Usage"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # FR-P053: Track last alert date to send once per day
        self._cost_alert_sent_date: str = ""

    def log_api_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        task_type: str,
        timestamp: Optional[datetime] = None,
    ) -> float:
        """
        Log a Claude API call and calculate cost

        Args:
            model: Claude model name (e.g., "claude-sonnet-4-5-20250929")
            prompt_tokens: Input token count
            completion_tokens: Output token count
            task_type: Task that triggered call (email_draft, linkedin_draft, etc.)
            timestamp: Call timestamp (default: now)

        Returns:
            Cost in USD
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Calculate cost
        cost_usd = self.calculate_cost(model, prompt_tokens, completion_tokens)

        # Get today's log file
        log_file = self.log_dir / f"{timestamp.strftime('%Y-%m-%d')}.md"

        # Create or append to log
        if not log_file.exists():
            self._create_log_file(log_file, timestamp.strftime("%Y-%m-%d"))

        # Append call record
        with open(log_file, "a") as f:
            f.write(
                f"| {timestamp.strftime('%H:%M:%S')} | {self.agent_id} | {model} | "
                f"{prompt_tokens} | {completion_tokens} | ${cost_usd:.4f} | {task_type} |\n"
            )

        logger.info(
            f"API call logged: {model} - {prompt_tokens + completion_tokens} tokens - ${cost_usd:.4f}"
        )

        # FR-P053: Check daily cost threshold after each call
        self._check_cost_alert(timestamp)

        return cost_usd

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate API call cost

        Args:
            model: Claude model name
            prompt_tokens: Input tokens
            completion_tokens: Output tokens

        Returns:
            Cost in USD
        """
        # Get pricing (fallback to Sonnet if model not found)
        pricing = self.PRICING.get(model, self.PRICING["claude-sonnet-4-5-20250929"])

        prompt_cost = (prompt_tokens * pricing["prompt"]) / 1_000_000
        completion_cost = (completion_tokens * pricing["completion"]) / 1_000_000

        return prompt_cost + completion_cost

    def _create_log_file(self, log_file: Path, date: str):
        """Create new daily log file with header"""
        with open(log_file, "w") as f:
            f.write(f"# Claude API Usage - {date}\n\n")
            f.write("| Time | Agent | Model | Prompt Tokens | Completion Tokens | Cost (USD) | Task Type |\n")
            f.write("|------|-------|-------|---------------|-------------------|------------|----------|\n")

    def _check_cost_alert(self, timestamp: datetime) -> None:
        """FR-P053: Send WhatsApp alert if daily cost exceeds threshold (once per day)."""
        today = timestamp.strftime("%Y-%m-%d")
        if self._cost_alert_sent_date == today:
            return  # already alerted today

        daily_total = self.get_daily_total(today)
        if daily_total <= _COST_ALERT_THRESHOLD:
            return

        self._cost_alert_sent_date = today
        msg = (
            f"⚠️ *API Cost Alert* — {today}\n"
            f"Daily spend: *${daily_total:.4f}* exceeds threshold ${_COST_ALERT_THRESHOLD:.2f}\n"
            f"Review: vault/Logs/API_Usage/{today}.md"
        )
        logger.warning(f"Cost alert triggered: ${daily_total:.4f} > ${_COST_ALERT_THRESHOLD:.2f}")
        try:
            from cloud_agent.src.notifications.whatsapp_notifier import notify_critical_error
            notify_critical_error(msg)
        except Exception as e:
            logger.debug(f"Cost alert WhatsApp failed: {e}")

    def get_daily_total(self, date: Optional[str] = None) -> float:
        """
        Get total cost for a specific day

        Args:
            date: Date string (YYYY-MM-DD), default: today

        Returns:
            Total cost in USD
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        log_file = self.log_dir / f"{date}.md"
        if not log_file.exists():
            return 0.0

        total = 0.0
        try:
            with open(log_file, "r") as f:
                for line in f:
                    if line.startswith("|") and "$" in line:
                        # Extract cost column
                        parts = line.split("|")
                        if len(parts) >= 7:
                            cost_str = parts[6].strip().replace("$", "")
                            try:
                                total += float(cost_str)
                            except ValueError:
                                pass
        except Exception as e:
            logger.error(f"Failed to calculate daily total: {e}")

        return total

    def get_weekly_total(self) -> float:
        """
        Get total cost for current week (last 7 days)

        Returns:
            Total cost in USD
        """
        total = 0.0
        today = datetime.now()

        for i in range(7):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            total += self.get_daily_total(date)

        return total

    def check_cost_alert(self, threshold: float) -> bool:
        """
        Check if weekly cost exceeds threshold

        Args:
            threshold: Cost threshold in USD

        Returns:
            True if cost exceeds threshold
        """
        weekly_cost = self.get_weekly_total()
        return weekly_cost > threshold


# Import for timedelta
from datetime import timedelta
