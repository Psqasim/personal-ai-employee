"""
Integration test: full Odoo draft → approve → post flow (mocked XML-RPC)

Simulates the complete pipeline without a real Odoo server:
  Email with invoice keywords
    → OdooDraftGenerator.generate_and_save()  →  vault/Pending_Approval/Odoo/
    → simulate human approve (move file)      →  vault/Approved/Odoo/
    → OdooPoster.post_from_file()             →  vault/Done/Odoo/

Run:
    pytest tests/integration/test_odoo_flow.py -v
"""
import os
import sys
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cloud_agent.src.generators.odoo_draft import OdooDraftGenerator
from local_agent.src.executors.odoo_poster import OdooPoster


@pytest.fixture
def vault(tmp_path):
    """Scratch vault with all required subdirs."""
    v = tmp_path / "vault"
    for d in [
        "Inbox", "Pending_Approval/Odoo", "Approved/Odoo",
        "Done/Odoo", "Failed/Odoo", "Logs/Odoo",
    ]:
        (v / d).mkdir(parents=True)
    return v


INVOICE_EMAIL = {
    "email_id": "EMAIL_INTEG_001",
    "from": "billing@acmecorp.com",
    "subject": "Invoice #2026-001 for consulting services",
    "body": "Dear Team,\n\nPlease find attached invoice for USD 3,500 for consulting services.",
    "priority": "Normal",
}

ODOO_ENV = {
    "ENABLE_ODOO": "true",
    "ODOO_URL": "https://demo.odoo.com",
    "ODOO_DB": "testdb",
    "ODOO_USER": "admin",
    "ODOO_API_KEY": "test-api-key-12345",
}


def make_mock_xmlrpc():
    """Return mocked common + models proxies."""
    mock_common = MagicMock()
    mock_common.authenticate.return_value = 7  # uid

    mock_models = MagicMock()
    mock_models.execute_kw.side_effect = [
        [],    # res.partner search → not found
        55,    # res.partner create → partner_id=55
        200,   # account.move create → record_id=200
        [{"name": "INV/2026/TEST", "state": "draft", "create_date": "2026-02-19"}],
    ]
    return mock_common, mock_models


class TestOdooEndToEndFlow:

    def test_full_pipeline_creates_done_file(self, vault):
        """Complete flow: email → draft → approve → Odoo → Done."""
        # STEP 1: Cloud agent generates draft
        gen = OdooDraftGenerator(str(vault))
        with patch.dict(os.environ, {**ODOO_ENV, "CLAUDE_API_KEY": ""}):
            draft_path = gen.generate_and_save(INVOICE_EMAIL)

        assert draft_path is not None, "Draft should be created"
        assert draft_path.exists(), "Draft file must exist"
        assert "Pending_Approval/Odoo" in str(draft_path).replace("\\", "/")

        # STEP 2: Human approves (simulate file move)
        approved_dir = vault / "Approved" / "Odoo"
        approved_path = approved_dir / draft_path.name
        shutil.move(str(draft_path), str(approved_path))
        assert approved_path.exists()
        assert not draft_path.exists()

        # STEP 3: Local agent posts to Odoo
        poster = OdooPoster(str(vault))
        mock_common, mock_models = make_mock_xmlrpc()

        with patch.dict(os.environ, ODOO_ENV):
            with patch("xmlrpc.client.ServerProxy") as mock_proxy:
                mock_proxy.side_effect = [mock_common, mock_models]
                result = poster.post_from_file(str(approved_path))

        # STEP 4: Verify outcome
        assert result["success"] is True, f"Post failed: {result.get('error')}"
        assert result["odoo_record_id"] == 200
        assert result["invoice_number"] == "INV/2026/TEST"

        # File should be in Done/Odoo
        done_dir = vault / "Done" / "Odoo"
        done_files = list(done_dir.glob("*.md"))
        assert len(done_files) == 1, "Exactly one file should be in Done/Odoo"
        assert done_files[0].name == draft_path.name

    def test_draft_content_has_required_fields(self, vault):
        """Draft file must have all frontmatter fields OdooPoster expects."""
        gen = OdooDraftGenerator(str(vault))
        with patch.dict(os.environ, {**ODOO_ENV, "CLAUDE_API_KEY": ""}):
            draft_path = gen.generate_and_save(INVOICE_EMAIL)

        content = draft_path.read_text(encoding="utf-8")
        for field in ["type:", "draft_id:", "action:", "status:", "customer:", "amount:", "currency:", "description:"]:
            assert field in content, f"Missing frontmatter field: {field}"

    def test_no_draft_created_when_odoo_disabled(self, vault):
        gen = OdooDraftGenerator(str(vault))
        with patch.dict(os.environ, {"ENABLE_ODOO": "false"}):
            draft_path = gen.generate_and_save(INVOICE_EMAIL)
        assert draft_path is None

    def test_no_draft_for_non_invoice_email(self, vault):
        gen = OdooDraftGenerator(str(vault))
        non_invoice = {
            "email_id": "EMAIL_RANDOM",
            "from": "friend@example.com",
            "subject": "Team lunch on Friday",
            "body": "Hi, are you joining us for lunch on Friday at noon?",
        }
        with patch.dict(os.environ, ODOO_ENV):
            draft_path = gen.generate_and_save(non_invoice)
        assert draft_path is None

    def test_odoo_auth_failure_moves_to_failed(self, vault):
        """When Odoo auth fails, file must land in Failed/Odoo."""
        # Create approved draft manually
        approved_dir = vault / "Approved" / "Odoo"
        draft_md = """\
---
type: odoo_invoice
draft_id: FAIL_TEST
action: create_draft_invoice
status: pending
customer: Bad Auth Client
amount: 100.00
currency: USD
description: Test auth failure
created: 2026-02-19T10:00:00
mcp_server: odoo-mcp
---
"""
        draft_file = approved_dir / "INVOICE_DRAFT_FAIL_TEST.md"
        draft_file.write_text(draft_md, encoding="utf-8")

        poster = OdooPoster(str(vault))

        with patch.dict(os.environ, ODOO_ENV):
            with patch("xmlrpc.client.ServerProxy") as mock_proxy:
                mock_common = MagicMock()
                mock_common.authenticate.return_value = None  # auth fail
                mock_proxy.return_value = mock_common
                result = poster.post_from_file(str(draft_file))

        assert result["success"] is False
        failed_files = list((vault / "Failed" / "Odoo").glob("*.md"))
        assert len(failed_files) == 1
        # Error should be appended
        failed_content = failed_files[0].read_text(encoding="utf-8")
        assert "FAILED" in failed_content
