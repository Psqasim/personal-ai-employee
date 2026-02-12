"""Shared pytest fixtures for Personal AI Employee tests."""

import pytest


@pytest.fixture
def vault_path(tmp_path):
    """Create a minimal vault structure for testing."""
    for folder in ["Inbox", "Needs_Action", "Done", "Plans", "Logs", "Approved", "Pending_Approval"]:
        (tmp_path / folder).mkdir()
    (tmp_path / "Logs" / "API_Cache").mkdir()
    (tmp_path / "Logs" / "API_Usage").mkdir()
    (tmp_path / "Pending_Approval" / "Email").mkdir()
    (tmp_path / "Pending_Approval" / "LinkedIn").mkdir()
    (tmp_path / "Pending_Approval" / "MCP").mkdir()

    # Create minimal Dashboard.md
    dashboard = tmp_path / "Dashboard.md"
    dashboard.write_text(
        "# Personal AI Employee Dashboard\n\n"
        "## Task Overview\n"
        "| Filename | Date Added | Status | Priority |\n"
        "|----------|-----------|--------|----------|\n"
        "\n## Statistics\n"
        "- **Total Tasks**: 0\n\n"
        "---\n"
        "*Last Updated: 2026-01-01 00:00:00*\n",
        encoding="utf-8",
    )

    # Create minimal Company_Handbook.md
    handbook = tmp_path / "Company_Handbook.md"
    handbook.write_text(
        "# Company Handbook\n\n"
        "## Business Goals\n"
        "- Grow revenue by 20% this year\n"
        "- Improve customer satisfaction\n\n"
        "## AI Employee Settings\n"
        "- Polling Interval: 30\n",
        encoding="utf-8",
    )

    return tmp_path
