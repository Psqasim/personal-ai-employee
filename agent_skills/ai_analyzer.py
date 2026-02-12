"""AI Analyzer module for Silver Tier Personal AI Employee.

Provides Claude API integration for intelligent task analysis:
- analyze_priority(): Assign High/Medium/Low priority with category
- _call_claude_api(): Internal Claude API call with timeout/retry
- _sanitize_input(): Remove PII before sending to API
- _cache_response(): 24-hour file-based response caching

All functions gracefully fall back to Bronze defaults on API failure.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Fallback response when AI analysis is unavailable
BRONZE_FALLBACK = {
    "priority": "Medium",
    "category": "Uncategorized",
    "reasoning": "Bronze mode - AI analysis unavailable",
    "cost": 0.0,
    "cached": False,
    "fallback": True,
}

# Valid priority and category values
VALID_PRIORITIES = {"High", "Medium", "Low"}
VALID_CATEGORIES = {"Work", "Personal", "Urgent", "Uncategorized"}


def _get_vault_path() -> Path:
    """Get vault path from environment or use default."""
    vault_path = os.getenv("VAULT_PATH", "vault")
    return Path(vault_path).resolve()


def _sanitize_input(text: str) -> str:
    """Remove PII from text before sending to Claude API.

    Removes:
    - Email addresses
    - US phone numbers
    - Account numbers (6+ consecutive digits)
    Truncates to 200 characters.

    Args:
        text: Raw text that may contain PII

    Returns:
        Sanitized text, max 200 characters
    """
    if not text:
        return ""

    # Remove email addresses
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "[EMAIL]",
        text
    )
    # Remove phone numbers (US format: 10 digits with optional separators)
    text = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]", text)
    # Remove account numbers (6+ consecutive digits not already matched)
    text = re.sub(r"\b\d{6,}\b", "[ACCOUNT]", text)

    return text[:200]


def _cache_response(
    task_title: str,
    response: Optional[Dict[str, Any]],
    vault_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Check or store a cached API response for a task title.

    Uses SHA256 hash of task_title as cache key.
    Cache TTL is controlled by API_CACHE_DURATION env var (default: 86400s = 24h).

    Args:
        task_title: Task title used as cache key
        response: If provided, save this response to cache. If None, attempt to read.
        vault_path: Optional vault path override (for testing)

    Returns:
        Cached response dict if valid cache hit when reading, else None.
        Returns None when writing (response saved to disk).
    """
    if vault_path is None:
        vault_path = _get_vault_path()

    cache_dir = vault_path / "Logs" / "API_Cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_key = hashlib.sha256(task_title.encode("utf-8")).hexdigest()
    cache_file = cache_dir / f"{cache_key}.json"

    cache_duration = int(os.getenv("API_CACHE_DURATION", "86400"))

    if response is not None:
        # Write mode: save response with timestamp
        cache_entry = {
            "task_title": task_title,
            "timestamp": datetime.now().isoformat(),
            "response": response,
        }
        try:
            cache_file.write_text(json.dumps(cache_entry, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to write cache: {e}")
        return None

    # Read mode: check for valid cache entry
    if not cache_file.exists():
        return None

    try:
        cache_entry = json.loads(cache_file.read_text(encoding="utf-8"))
        cached_time = datetime.fromisoformat(cache_entry["timestamp"])
        expiry_time = cached_time + timedelta(seconds=cache_duration)

        if datetime.now() < expiry_time:
            cached_response = cache_entry["response"].copy()
            cached_response["cached"] = True
            cached_response["fallback"] = False
            return cached_response
        else:
            # Cache expired, remove stale entry
            cache_file.unlink(missing_ok=True)
            return None
    except Exception as e:
        logger.warning(f"Failed to read cache: {e}")
        return None


async def _call_claude_api(
    task_title: str,
    task_snippet: str,
    vault_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Call Claude API to analyze task priority and category.

    Uses AsyncAnthropic client with 5-second timeout.
    Logs API usage via api_usage_tracker if available.

    Args:
        task_title: Sanitized task title (max 100 chars)
        task_snippet: Sanitized task content snippet (max 200 chars)
        vault_path: Optional vault path for usage tracking

    Returns:
        Dict with priority, category, reasoning, cost keys

    Raises:
        asyncio.TimeoutError: If API call exceeds 5 seconds
        Exception: Re-raises unexpected errors for caller to handle
    """
    try:
        import anthropic
    except ImportError:
        logger.error("anthropic package not installed. Run: pip install anthropic>=0.18.0")
        return BRONZE_FALLBACK.copy()

    api_key = os.getenv("CLAUDE_API_KEY", "")
    if not api_key:
        logger.warning("CLAUDE_API_KEY not set. Using Bronze fallback.")
        return BRONZE_FALLBACK.copy()

    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

    system_prompt = (
        "You are a task priority analyzer. Analyze the given task and respond with ONLY a JSON object "
        "(no markdown, no explanation) in this exact format:\n"
        '{"priority": "High|Medium|Low", "category": "Work|Personal|Urgent|Uncategorized", '
        '"reasoning": "Brief explanation under 100 chars"}\n\n'
        "Priority rules:\n"
        "- High: Client-facing, invoices, deadlines, URGENT/ASAP keywords, emergencies\n"
        "- Medium: Regular work tasks, meetings, projects without immediate deadline\n"
        "- Low: Personal notes, future planning, non-urgent items\n\n"
        "Category rules:\n"
        "- Urgent: Contains URGENT/ASAP/emergency keywords\n"
        "- Work: Business, client, invoice, proposal, meeting, project keywords\n"
        "- Personal: Family, health, vacation, personal life keywords\n"
        "- Uncategorized: Cannot clearly classify"
    )

    user_message = f"Task title: {task_title}\nTask content: {task_snippet}"

    client = anthropic.AsyncAnthropic(api_key=api_key)

    # Apply 5-second timeout
    response = await asyncio.wait_for(
        client.messages.create(
            model=model,
            max_tokens=100,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        ),
        timeout=5.0,
    )

    # Parse structured JSON response (strip markdown code fences if present)
    response_text = response.content[0].text.strip()
    if response_text.startswith("```"):
        # Remove ```json ... ``` wrapping
        lines = response_text.splitlines()
        response_text = "\n".join(lines[1:-1]).strip()
    result = json.loads(response_text)

    # Validate and normalize fields
    priority = result.get("priority", "Medium")
    if priority not in VALID_PRIORITIES:
        priority = "Medium"

    category = result.get("category", "Uncategorized")
    if category not in VALID_CATEGORIES:
        category = "Uncategorized"

    # Calculate cost (claude-3-5-sonnet: $3/M input, $15/M output)
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost = (input_tokens * 3.0 + output_tokens * 15.0) / 1_000_000

    # Log API usage (non-blocking)
    try:
        from agent_skills.api_usage_tracker import log_api_call
        log_api_call("priority_analysis", input_tokens, output_tokens, cost)
    except Exception:
        pass  # Usage tracking is optional

    return {
        "priority": priority,
        "category": category,
        "reasoning": result.get("reasoning", ""),
        "cost": cost,
        "cached": False,
        "fallback": False,
    }


async def categorize_task(
    task_title: str,
    task_snippet: str = "",
    vault_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Categorize a task as Work/Personal/Urgent/Uncategorized.

    Delegates to analyze_priority() which returns both priority and category
    in a single API call for cost efficiency.

    Args:
        task_title: Task title
        task_snippet: Task content snippet
        vault_path: Optional vault path override

    Returns:
        Same dict as analyze_priority() with priority, category, cost, cached, fallback
    """
    return await analyze_priority(task_title, task_snippet, vault_path)


async def analyze_priority(
    task_title: str,
    task_snippet: str = "",
    vault_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Analyze task priority using Claude API with graceful fallback.

    Checks ENABLE_AI_ANALYSIS flag before calling API.
    Uses 24-hour cache to avoid duplicate API calls.
    Falls back to Bronze defaults on any error.

    Args:
        task_title: Task title (max 100 chars used)
        task_snippet: First part of task content (max 200 chars)
        vault_path: Optional vault path override (for testing)

    Returns:
        Dict with keys:
        - priority: "High" | "Medium" | "Low"
        - category: "Work" | "Personal" | "Urgent" | "Uncategorized"
        - reasoning: str (brief explanation)
        - cost: float (USD, 0.0 for cached/fallback)
        - cached: bool (True if from cache)
        - fallback: bool (True if Bronze defaults used)

    Raises:
        ValueError: If task_title is empty
    """
    if not task_title or not task_title.strip():
        raise ValueError("task_title cannot be empty")

    # Check if AI analysis is enabled
    if not os.getenv("ENABLE_AI_ANALYSIS", "false").lower() == "true":
        return BRONZE_FALLBACK.copy()

    # Sanitize inputs
    clean_title = _sanitize_input(task_title[:100])
    clean_snippet = _sanitize_input(task_snippet) if task_snippet else ""

    # Check cache first
    cached = _cache_response(clean_title, None, vault_path)
    if cached is not None:
        logger.debug(f"Cache hit for task: {clean_title[:50]}")
        return cached

    # Call Claude API
    try:
        result = await _call_claude_api(clean_title, clean_snippet, vault_path)

        # Save to cache
        _cache_response(clean_title, result, vault_path)

        return result

    except asyncio.TimeoutError:
        logger.warning(f"Claude API timeout (>5s) for task: {clean_title[:50]}. Using Bronze fallback.")
        return BRONZE_FALLBACK.copy()

    except json.JSONDecodeError as e:
        logger.warning(f"Claude API returned invalid JSON: {e}. Using Bronze fallback.")
        return BRONZE_FALLBACK.copy()

    except Exception as e:
        error_msg = str(e).lower()
        if "api key" in error_msg or "authentication" in error_msg or "unauthorized" in error_msg:
            logger.error(
                f"Claude API authentication error: {e}. "
                "Check CLAUDE_API_KEY in .env. Get key at: https://console.anthropic.com/"
            )
        elif "rate limit" in error_msg or "429" in error_msg:
            logger.warning(f"Claude API rate limit exceeded: {e}. Using Bronze fallback.")
        else:
            logger.warning(f"Claude API error: {e}. Using Bronze fallback.")

        return BRONZE_FALLBACK.copy()
