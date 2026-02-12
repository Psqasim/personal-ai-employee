"""Unit tests for agent_skills/ai_analyzer.py (Silver Tier)."""

import asyncio
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_skills.ai_analyzer import (
    BRONZE_FALLBACK,
    _cache_response,
    _sanitize_input,
    analyze_priority,
    categorize_task,
)


class TestSanitizeInput:
    """Tests for _sanitize_input() PII removal."""

    def test_removes_email_address(self):
        result = _sanitize_input("Contact john.doe@example.com for details")
        assert "[EMAIL]" in result
        assert "john.doe@example.com" not in result

    def test_removes_multiple_emails(self):
        result = _sanitize_input("From: a@b.com To: c@d.org")
        assert "a@b.com" not in result
        assert "c@d.org" not in result

    def test_removes_us_phone_dashes(self):
        result = _sanitize_input("Call 555-123-4567 for info")
        assert "[PHONE]" in result
        assert "555-123-4567" not in result

    def test_removes_us_phone_dots(self):
        result = _sanitize_input("Phone: 555.123.4567")
        assert "[PHONE]" in result
        assert "555.123.4567" not in result

    def test_removes_us_phone_no_separators(self):
        result = _sanitize_input("Call 5551234567")
        assert "[PHONE]" in result
        assert "5551234567" not in result

    def test_removes_account_numbers(self):
        result = _sanitize_input("Account 123456789 needs review")
        assert "[ACCOUNT]" in result
        assert "123456789" not in result

    def test_preserves_short_numbers(self):
        result = _sanitize_input("Task has 5 items due in 3 days")
        assert "5" in result
        assert "3" in result

    def test_truncates_to_200_chars(self):
        long_text = "a" * 300
        result = _sanitize_input(long_text)
        assert len(result) == 200

    def test_empty_string(self):
        result = _sanitize_input("")
        assert result == ""

    def test_preserves_normal_text(self):
        result = _sanitize_input("Review Q1 marketing report")
        assert result == "Review Q1 marketing report"

    def test_combined_pii_removal(self):
        text = "Send invoice to john@acme.com, call 555-123-4567, account 9876543"
        result = _sanitize_input(text)
        assert "john@acme.com" not in result
        assert "555-123-4567" not in result
        assert "9876543" not in result
        assert "[EMAIL]" in result
        assert "[PHONE]" in result
        assert "[ACCOUNT]" in result


class TestCacheResponse:
    """Tests for _cache_response() 24-hour TTL caching."""

    def test_write_and_read_cache(self, tmp_path):
        """Cache entry can be written and read back."""
        vault_path = tmp_path
        (vault_path / "Logs" / "API_Cache").mkdir(parents=True)

        response = {"priority": "High", "category": "Work", "cost": 0.001}
        _cache_response("test task", response, vault_path)

        result = _cache_response("test task", None, vault_path)
        assert result is not None
        assert result["priority"] == "High"
        assert result["cached"] is True

    def test_cache_miss_returns_none(self, tmp_path):
        """Missing cache entry returns None."""
        vault_path = tmp_path
        (vault_path / "Logs" / "API_Cache").mkdir(parents=True)

        result = _cache_response("nonexistent task", None, vault_path)
        assert result is None

    def test_expired_cache_returns_none(self, tmp_path):
        """Cache entry older than TTL returns None."""
        vault_path = tmp_path
        (vault_path / "Logs" / "API_Cache").mkdir(parents=True)

        import hashlib

        cache_dir = vault_path / "Logs" / "API_Cache"
        key = hashlib.sha256("old task".encode()).hexdigest()
        cache_file = cache_dir / f"{key}.json"

        # Write expired entry (25 hours ago)
        old_time = (datetime.now() - timedelta(hours=25)).isoformat()
        cache_file.write_text(
            json.dumps({"task_title": "old task", "timestamp": old_time, "response": {"priority": "High"}}),
            encoding="utf-8",
        )

        result = _cache_response("old task", None, vault_path)
        assert result is None

    def test_cache_creates_directory(self, tmp_path):
        """Cache creates API_Cache directory if missing."""
        vault_path = tmp_path
        response = {"priority": "Medium", "category": "Work"}
        _cache_response("task title", response, vault_path)

        cache_dir = vault_path / "Logs" / "API_Cache"
        assert cache_dir.exists()

    def test_different_tasks_have_different_cache_keys(self, tmp_path):
        """Different task titles use different cache files."""
        vault_path = tmp_path
        (vault_path / "Logs" / "API_Cache").mkdir(parents=True)

        _cache_response("task A", {"priority": "High"}, vault_path)
        _cache_response("task B", {"priority": "Low"}, vault_path)

        result_a = _cache_response("task A", None, vault_path)
        result_b = _cache_response("task B", None, vault_path)

        assert result_a["priority"] == "High"
        assert result_b["priority"] == "Low"


class TestAnalyzePriority:
    """Tests for analyze_priority() main function."""

    @pytest.mark.asyncio
    async def test_returns_bronze_fallback_when_disabled(self, tmp_path):
        """Returns Bronze defaults when ENABLE_AI_ANALYSIS=false."""
        with patch.dict(os.environ, {"ENABLE_AI_ANALYSIS": "false"}):
            result = await analyze_priority("Review quarterly report", vault_path=tmp_path)

        assert result["priority"] == "Medium"
        assert result["category"] == "Uncategorized"
        assert result["fallback"] is True

    @pytest.mark.asyncio
    async def test_raises_on_empty_title(self, tmp_path):
        """Raises ValueError for empty task_title."""
        with pytest.raises(ValueError, match="task_title cannot be empty"):
            await analyze_priority("", vault_path=tmp_path)

    @pytest.mark.asyncio
    async def test_raises_on_whitespace_title(self, tmp_path):
        """Raises ValueError for whitespace-only task_title."""
        with pytest.raises(ValueError, match="task_title cannot be empty"):
            await analyze_priority("   ", vault_path=tmp_path)

    @pytest.mark.asyncio
    async def test_uses_cache_on_second_call(self, tmp_path):
        """Second call with same title uses cache, not API."""
        (tmp_path / "Logs" / "API_Cache").mkdir(parents=True)

        mock_response = {
            "priority": "High",
            "category": "Work",
            "reasoning": "Cached",
            "cost": 0.001,
            "cached": False,
            "fallback": False,
        }

        with patch.dict(os.environ, {"ENABLE_AI_ANALYSIS": "true", "CLAUDE_API_KEY": "test-key"}):
            with patch("agent_skills.ai_analyzer._call_claude_api", new_callable=AsyncMock) as mock_api:
                mock_api.return_value = mock_response

                # First call hits API
                result1 = await analyze_priority("urgent client invoice", vault_path=tmp_path)
                assert mock_api.call_count == 1

                # Second call uses cache
                result2 = await analyze_priority("urgent client invoice", vault_path=tmp_path)
                assert mock_api.call_count == 1  # Not called again
                assert result2["cached"] is True

    @pytest.mark.asyncio
    async def test_graceful_fallback_on_timeout(self, tmp_path):
        """Returns Bronze fallback on API timeout."""
        with patch.dict(os.environ, {"ENABLE_AI_ANALYSIS": "true", "CLAUDE_API_KEY": "test-key"}):
            with patch("agent_skills.ai_analyzer._call_claude_api", new_callable=AsyncMock) as mock_api:
                mock_api.side_effect = asyncio.TimeoutError()

                result = await analyze_priority("any task", vault_path=tmp_path)

        assert result["priority"] == "Medium"
        assert result["category"] == "Uncategorized"
        assert result["fallback"] is True

    @pytest.mark.asyncio
    async def test_graceful_fallback_on_api_error(self, tmp_path):
        """Returns Bronze fallback on general API error."""
        with patch.dict(os.environ, {"ENABLE_AI_ANALYSIS": "true", "CLAUDE_API_KEY": "test-key"}):
            with patch("agent_skills.ai_analyzer._call_claude_api", new_callable=AsyncMock) as mock_api:
                mock_api.side_effect = Exception("Connection refused")

                result = await analyze_priority("any task", vault_path=tmp_path)

        assert result["fallback"] is True
        assert result["priority"] == "Medium"

    @pytest.mark.asyncio
    async def test_sanitizes_pii_before_api_call(self, tmp_path):
        """PII is removed from title before sending to API."""
        captured_args = []

        async def capture_call(title, snippet, vault_path=None):
            captured_args.append((title, snippet))
            return {
                "priority": "High",
                "category": "Work",
                "reasoning": "test",
                "cost": 0.001,
                "cached": False,
                "fallback": False,
            }

        with patch.dict(os.environ, {"ENABLE_AI_ANALYSIS": "true", "CLAUDE_API_KEY": "test-key"}):
            with patch("agent_skills.ai_analyzer._call_claude_api", side_effect=capture_call):
                await analyze_priority(
                    "Invoice for john@client.com",
                    "Call 555-123-4567 about account 9876543210",
                    vault_path=tmp_path,
                )

        assert len(captured_args) == 1
        title_sent, snippet_sent = captured_args[0]
        assert "john@client.com" not in title_sent
        assert "555-123-4567" not in snippet_sent
        assert "9876543210" not in snippet_sent

    @pytest.mark.asyncio
    async def test_categorize_task_delegates_to_analyze(self, tmp_path):
        """categorize_task() returns same result as analyze_priority()."""
        mock_response = {
            "priority": "High",
            "category": "Work",
            "reasoning": "Business task",
            "cost": 0.001,
            "cached": False,
            "fallback": False,
        }

        with patch.dict(os.environ, {"ENABLE_AI_ANALYSIS": "true", "CLAUDE_API_KEY": "test-key"}):
            with patch("agent_skills.ai_analyzer._call_claude_api", new_callable=AsyncMock) as mock_api:
                mock_api.return_value = mock_response

                result = await categorize_task("client invoice", vault_path=tmp_path)

        assert result["category"] == "Work"
        assert result["priority"] == "High"

    @pytest.mark.asyncio
    async def test_category_fallback_to_uncategorized_on_api_failure(self, tmp_path):
        """Category falls back to Uncategorized on API failure."""
        with patch.dict(os.environ, {"ENABLE_AI_ANALYSIS": "true", "CLAUDE_API_KEY": "test-key"}):
            with patch("agent_skills.ai_analyzer._call_claude_api", new_callable=AsyncMock) as mock_api:
                mock_api.side_effect = Exception("Network error")

                result = await analyze_priority("any task", vault_path=tmp_path)

        assert result["category"] == "Uncategorized"
        assert result["fallback"] is True

    @pytest.mark.asyncio
    async def test_full_analysis_with_mock_api(self, tmp_path):
        """Full analysis flow with mocked API returns correct result."""
        mock_response = {
            "priority": "High",
            "category": "Work",
            "reasoning": "Urgent client request",
            "cost": 0.001,
            "cached": False,
            "fallback": False,
        }

        with patch.dict(os.environ, {"ENABLE_AI_ANALYSIS": "true", "CLAUDE_API_KEY": "test-key"}):
            with patch("agent_skills.ai_analyzer._call_claude_api", new_callable=AsyncMock) as mock_api:
                mock_api.return_value = mock_response

                result = await analyze_priority("Urgent client proposal", "Need review ASAP", vault_path=tmp_path)

        assert result["priority"] == "High"
        assert result["category"] == "Work"
        assert result["fallback"] is False
        assert result["cached"] is False
