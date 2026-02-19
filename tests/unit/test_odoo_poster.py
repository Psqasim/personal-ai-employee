"""
Unit tests for local_agent/src/executors/odoo_poster.py

Tests cover:
- ENABLE_ODOO guard
- Parse error handling
- Successful flow (mocked XML-RPC)
- Failed file moved to vault/Failed/Odoo/
- Done file moved to vault/Done/Odoo/
"""
import os
import sys
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from local_agent.src.executors.odoo_poster import OdooPoster


# ─── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_DRAFT_MD = """\
---
type: odoo_invoice
draft_id: TEST_DRAFT_001
action: create_draft_invoice
status: pending
customer: Test Client A
amount: 500.00
currency: USD
description: Consulting services Q1 2026
source_email_id: EMAIL_TEST_001
source_email_from: client@example.com
created: 2026-02-19T10:00:00
mcp_server: odoo-mcp
---

## Odoo Invoice Draft

**Customer:** Test Client A
**Amount:** USD 500.00
**Description:** Consulting services Q1 2026
"""


@pytest.fixture
def vault_dir(tmp_path):
    vault = tmp_path / "vault"
    for d in ["Approved/Odoo", "Done/Odoo", "Failed/Odoo", "Logs/Odoo"]:
        (vault / d).mkdir(parents=True)
    return vault


@pytest.fixture
def poster(vault_dir):
    return OdooPoster(str(vault_dir))


@pytest.fixture
def draft_file(vault_dir):
    approved = vault_dir / "Approved" / "Odoo"
    approved.mkdir(parents=True, exist_ok=True)
    f = approved / "INVOICE_DRAFT_TEST_001.md"
    f.write_text(SAMPLE_DRAFT_MD, encoding="utf-8")
    return f


# ─── ENABLE_ODOO guard ────────────────────────────────────────────────────────

class TestOdooPosterGuard:
    def test_returns_error_when_odoo_disabled(self, poster, draft_file):
        with patch.dict(os.environ, {"ENABLE_ODOO": "false"}):
            result = poster.post_from_file(str(draft_file))
        assert result["success"] is False
        assert "disabled" in result["error"].lower()

    def test_returns_error_on_parse_failure(self, poster, tmp_path):
        bad_file = tmp_path / "bad.md"
        bad_file.write_text("not valid frontmatter", encoding="utf-8")
        with patch.dict(os.environ, {"ENABLE_ODOO": "true"}):
            result = poster.post_from_file(str(bad_file))
        # Should fail gracefully (parse error or credentials error)
        assert result["success"] is False


# ─── Successful flow (mocked XML-RPC) ────────────────────────────────────────

class TestOdooPosterSuccess:
    def _mock_xmlrpc(self):
        mock_common = MagicMock()
        mock_common.authenticate.return_value = 42

        mock_models = MagicMock()
        # search returns empty (partner not found) → create returns partner_id=99
        mock_models.execute_kw.side_effect = [
            [],        # res.partner search → not found
            99,        # res.partner create → partner_id
            123,       # account.move create → record_id
            [{"name": "INV/2026/0001", "state": "draft", "create_date": "2026-02-19 10:00:00"}],  # read back
        ]
        return mock_common, mock_models

    def test_success_returns_odoo_record_id(self, poster, draft_file):
        mock_common, mock_models = self._mock_xmlrpc()

        env = {
            "ENABLE_ODOO": "true",
            "ODOO_URL": "https://demo.odoo.com",
            "ODOO_DB": "testdb",
            "ODOO_USER": "admin",
            "ODOO_API_KEY": "test-api-key",
        }
        with patch.dict(os.environ, env):
            with patch("xmlrpc.client.ServerProxy") as mock_proxy:
                mock_proxy.side_effect = [mock_common, mock_models]
                result = poster.post_from_file(str(draft_file))

        assert result["success"] is True
        assert result["odoo_record_id"] == 123
        assert result["invoice_number"] == "INV/2026/0001"
        assert result["error"] is None

    def test_success_moves_file_to_done(self, poster, vault_dir, draft_file):
        mock_common, mock_models = self._mock_xmlrpc()
        env = {
            "ENABLE_ODOO": "true",
            "ODOO_URL": "https://demo.odoo.com",
            "ODOO_DB": "testdb",
            "ODOO_USER": "admin",
            "ODOO_API_KEY": "test-api-key",
        }
        with patch.dict(os.environ, env):
            with patch("xmlrpc.client.ServerProxy") as mock_proxy:
                mock_proxy.side_effect = [mock_common, mock_models]
                poster.post_from_file(str(draft_file))

        done_dir = vault_dir / "Done" / "Odoo"
        done_files = list(done_dir.glob("*.md"))
        assert len(done_files) == 1
        assert done_files[0].name == "INVOICE_DRAFT_TEST_001.md"


# ─── Failure handling ─────────────────────────────────────────────────────────

class TestOdooPosterFailure:
    def test_api_error_moves_file_to_failed(self, poster, vault_dir, draft_file):
        env = {
            "ENABLE_ODOO": "true",
            "ODOO_URL": "https://demo.odoo.com",
            "ODOO_DB": "testdb",
            "ODOO_USER": "admin",
            "ODOO_API_KEY": "bad-key",
        }
        with patch.dict(os.environ, env):
            with patch("xmlrpc.client.ServerProxy") as mock_proxy:
                mock_common = MagicMock()
                mock_common.authenticate.return_value = None  # auth failure
                mock_proxy.return_value = mock_common
                result = poster.post_from_file(str(draft_file))

        assert result["success"] is False
        # File should be in Failed dir
        failed_dir = vault_dir / "Failed" / "Odoo"
        failed_files = list(failed_dir.glob("*.md"))
        assert len(failed_files) == 1

    def test_failed_file_has_error_appended(self, poster, vault_dir, draft_file):
        env = {
            "ENABLE_ODOO": "true",
            "ODOO_URL": "https://demo.odoo.com",
            "ODOO_DB": "testdb",
            "ODOO_USER": "admin",
            "ODOO_API_KEY": "bad-key",
        }
        with patch.dict(os.environ, env):
            with patch("xmlrpc.client.ServerProxy") as mock_proxy:
                mock_common = MagicMock()
                mock_common.authenticate.return_value = None
                mock_proxy.return_value = mock_common
                poster.post_from_file(str(draft_file))

        failed_file = next((vault_dir / "Failed" / "Odoo").glob("*.md"))
        content = failed_file.read_text(encoding="utf-8")
        assert "FAILED" in content
