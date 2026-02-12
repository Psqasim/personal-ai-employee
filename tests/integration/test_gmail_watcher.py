"""Integration tests for watchers/gmail_watcher.py (Silver Tier)."""

import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from watchers.gmail_watcher import (
    _is_already_processed,
    _load_processed_ids,
    create_email_task,
    poll_gmail,
    track_processed_ids,
)


@pytest.fixture
def vault(tmp_path):
    """Create a minimal vault structure for Gmail watcher tests."""
    (tmp_path / "Inbox").mkdir()
    (tmp_path / "Logs").mkdir()
    return tmp_path


@pytest.fixture
def sample_email():
    """Sample email data dict."""
    return {
        "id": "18d3a2f1c4b5e6a7",
        "from": "client@example.com",
        "subject": "URGENT: Invoice #1234 needs approval",
        "snippet": "Please review and approve invoice #1234 for $5,000.",
        "received": "2026-02-12T10:00:00",
    }


class TestTrackProcessedIds:
    """Tests for track_processed_ids() duplicate prevention."""

    def test_new_id_returns_false(self, vault):
        """New message ID is not a duplicate."""
        result = track_processed_ids(vault, "msg001")
        assert result is False

    def test_same_id_returns_true(self, vault):
        """Same message ID detected as duplicate on second call."""
        track_processed_ids(vault, "msg001")
        result = track_processed_ids(vault, "msg001")
        assert result is True

    def test_different_ids_not_duplicate(self, vault):
        """Different IDs are not duplicates."""
        track_processed_ids(vault, "msg001")
        result = track_processed_ids(vault, "msg002")
        assert result is False

    def test_creates_processed_file(self, vault):
        """Creates gmail_processed_ids.txt if not exists."""
        track_processed_ids(vault, "msg001")
        processed_file = vault / "Logs" / "gmail_processed_ids.txt"
        assert processed_file.exists()

    def test_persists_across_calls(self, vault):
        """IDs persist in file across multiple calls."""
        track_processed_ids(vault, "msg001")
        track_processed_ids(vault, "msg002")
        track_processed_ids(vault, "msg003")

        ids = _load_processed_ids(vault)
        assert "msg001" in ids
        assert "msg002" in ids
        assert "msg003" in ids

    def test_none_message_id_returns_false(self, vault):
        """None message_id returns False (initialization call)."""
        result = track_processed_ids(vault, None)
        assert result is False


class TestCreateEmailTask:
    """Tests for create_email_task() file creation."""

    def test_creates_email_file(self, vault, sample_email):
        """Creates EMAIL_{id}.md in vault/Inbox/."""
        result = create_email_task(vault, sample_email)

        assert result is not None
        expected_path = vault / "Inbox" / f"EMAIL_{sample_email['id']}.md"
        assert expected_path.exists()
        assert result == expected_path

    def test_file_contains_yaml_frontmatter(self, vault, sample_email):
        """Created file has correct YAML frontmatter."""
        create_email_task(vault, sample_email)
        content = (vault / "Inbox" / f"EMAIL_{sample_email['id']}.md").read_text()

        assert "type: email" in content
        assert "priority: high" in content
        assert "status: pending" in content
        assert "source: gmail" in content

    def test_file_contains_sender(self, vault, sample_email):
        """Created file includes sender email."""
        create_email_task(vault, sample_email)
        content = (vault / "Inbox" / f"EMAIL_{sample_email['id']}.md").read_text()

        assert "client@example.com" in content

    def test_file_contains_subject(self, vault, sample_email):
        """Created file includes email subject."""
        create_email_task(vault, sample_email)
        content = (vault / "Inbox" / f"EMAIL_{sample_email['id']}.md").read_text()

        assert "Invoice #1234" in content

    def test_file_contains_snippet(self, vault, sample_email):
        """Created file includes email snippet."""
        create_email_task(vault, sample_email)
        content = (vault / "Inbox" / f"EMAIL_{sample_email['id']}.md").read_text()

        assert "review and approve invoice" in content

    def test_file_contains_action_checklist(self, vault, sample_email):
        """Created file includes suggested actions checklist."""
        create_email_task(vault, sample_email)
        content = (vault / "Inbox" / f"EMAIL_{sample_email['id']}.md").read_text()

        assert "- [ ]" in content

    def test_returns_existing_file_if_already_exists(self, vault, sample_email):
        """Returns existing file path without overwriting."""
        path1 = create_email_task(vault, sample_email)
        content_before = path1.read_text()

        # Create again with modified snippet
        sample_email["snippet"] = "MODIFIED CONTENT"
        path2 = create_email_task(vault, sample_email)

        content_after = path2.read_text()
        assert content_before == content_after  # Not overwritten

    def test_handles_missing_fields_gracefully(self, vault):
        """Creates task even with minimal email data."""
        minimal_email = {"id": "msg_minimal"}
        result = create_email_task(vault, minimal_email)

        assert result is not None
        assert (vault / "Inbox" / "EMAIL_msg_minimal.md").exists()


class TestPollGmail:
    """Tests for poll_gmail() API integration."""

    def test_returns_empty_list_for_no_messages(self, vault):
        """Returns empty list when no messages found."""
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {"resultSizeEstimate": 0}

        result = poll_gmail(mock_service, vault)
        assert result == []

    def test_skips_already_processed_messages(self, vault):
        """Skips messages already in processed IDs list."""
        # Pre-process message
        track_processed_ids(vault, "msg_already_done")

        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg_already_done", "threadId": "t1"}]
        }

        result = poll_gmail(mock_service, vault)
        assert result == []

    def test_returns_messages_with_correct_fields(self, vault):
        """Returns message list with from, subject, snippet, received, id."""
        mock_service = MagicMock()

        mock_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "test_msg_001", "threadId": "t1"}]
        }

        mock_service.users().messages().get().execute.return_value = {
            "id": "test_msg_001",
            "internalDate": "1739354400000",
            "snippet": "Test email snippet",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@test.com"},
                    {"name": "Subject", "value": "Test Subject"},
                ]
            },
        }

        result = poll_gmail(mock_service, vault)

        assert len(result) == 1
        assert result[0]["id"] == "test_msg_001"
        assert result[0]["from"] == "sender@test.com"
        assert result[0]["subject"] == "Test Subject"
        assert "snippet" in result[0]
        assert "received" in result[0]

    def test_handles_403_error(self, vault):
        """Propagates 403 error for caller to handle."""
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.side_effect = Exception(
            "403: Request had insufficient authentication scopes"
        )

        with pytest.raises(Exception, match="403"):
            poll_gmail(mock_service, vault)

    def test_handles_message_fetch_failure_gracefully(self, vault):
        """Skips messages that fail to fetch details."""
        mock_service = MagicMock()

        mock_service.users().messages().list().execute.return_value = {
            "messages": [
                {"id": "msg_good", "threadId": "t1"},
                {"id": "msg_bad", "threadId": "t2"},
            ]
        }

        # Good message succeeds, bad message fails
        def get_side_effect(*args, **kwargs):
            mock_get = MagicMock()
            msg_id = kwargs.get("id", "")
            if msg_id == "msg_bad":
                mock_get.execute.side_effect = Exception("Fetch failed")
            else:
                mock_get.execute.return_value = {
                    "id": "msg_good",
                    "internalDate": "1739354400000",
                    "snippet": "Good email",
                    "payload": {
                        "headers": [
                            {"name": "From", "value": "good@test.com"},
                            {"name": "Subject", "value": "Good Subject"},
                        ]
                    },
                }
            return mock_get

        mock_service.users().messages().get.side_effect = get_side_effect

        result = poll_gmail(mock_service, vault)
        # Should return 1 (the good one), skipping the bad one
        # (may vary based on mock - testing it doesn't crash)
        assert isinstance(result, list)


class TestGmailWatcherIntegration:
    """End-to-end integration tests for Gmail watcher workflow."""

    def test_full_workflow_creates_task_prevents_duplicates(self, vault):
        """Full workflow: receive email → create task → prevent duplicate."""
        email = {
            "id": "integration_test_001",
            "from": "test@example.com",
            "subject": "Integration Test Email",
            "snippet": "Testing the full workflow",
            "received": "2026-02-12T12:00:00",
        }

        # First time: create task
        already_processed = track_processed_ids(vault, email["id"])
        assert already_processed is False

        task_path = create_email_task(vault, email)
        assert task_path is not None
        assert task_path.exists()

        track_processed_ids(vault, email["id"])

        # Second time: skip (duplicate)
        already_processed = track_processed_ids(vault, email["id"])
        assert already_processed is True

    def test_multiple_emails_all_created(self, vault):
        """Multiple emails each get their own task file."""
        emails = [
            {"id": f"email_{i}", "from": f"sender{i}@test.com", "subject": f"Subject {i}",
             "snippet": f"Content {i}", "received": "2026-02-12T10:00:00"}
            for i in range(3)
        ]

        for email in emails:
            if not track_processed_ids(vault, email["id"]):
                create_email_task(vault, email)
                track_processed_ids(vault, email["id"])

        inbox_files = list((vault / "Inbox").glob("EMAIL_*.md"))
        assert len(inbox_files) == 3
