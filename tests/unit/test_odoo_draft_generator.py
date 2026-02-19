"""
Unit tests for cloud_agent/src/generators/odoo_draft.py

Tests cover:
- Invoice keyword detection
- Claude extraction result parsing
- Fallback regex extraction
- Draft file content format
- Idempotency (skip if draft exists)
"""
import os
import sys
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cloud_agent.src.generators.odoo_draft import (
    _contains_invoice_keywords,
    _fallback_extraction,
    OdooDraftGenerator,
)


# ─── keyword detection ────────────────────────────────────────────────────────

class TestInvoiceKeywordDetection:
    def test_detects_invoice_in_subject(self):
        assert _contains_invoice_keywords("Invoice #1234 attached", "") is True

    def test_detects_bill_in_body(self):
        assert _contains_invoice_keywords("Hi", "Please find your bill attached.") is True

    def test_detects_payment_due(self):
        assert _contains_invoice_keywords("Payment due", "Amount due: $500") is True

    def test_detects_quote(self):
        assert _contains_invoice_keywords("Quotation for services", "") is True

    def test_ignores_unrelated_email(self):
        assert _contains_invoice_keywords("Team lunch Friday", "See you at noon!") is False

    def test_case_insensitive(self):
        assert _contains_invoice_keywords("INVOICE ENCLOSED", "") is True


# ─── fallback extraction ─────────────────────────────────────────────────────

class TestFallbackExtraction:
    def test_extracts_dollar_amount(self):
        result = _fallback_extraction("Invoice $1,500", "Please pay $1,500", "john@example.com")
        assert result["amount"] == 1500.0

    def test_extracts_plain_amount(self):
        result = _fallback_extraction("Bill", "Total: 250.00", "client@example.com")
        assert result["amount"] == 250.0

    def test_extracts_customer_from_display_name(self):
        result = _fallback_extraction("Hi", "Body", "John Smith <john@example.com>")
        assert result["customer"] == "John Smith"

    def test_extracts_customer_from_email(self):
        result = _fallback_extraction("Hi", "Body", "john.doe@example.com")
        assert "John" in result["customer"] or "john" in result["customer"].lower()

    def test_default_currency_usd(self):
        result = _fallback_extraction("Invoice", "Pay now", "a@b.com")
        assert result["currency"] == "USD"

    def test_action_always_create_draft_invoice(self):
        result = _fallback_extraction("Invoice", "Pay now", "a@b.com")
        assert result["action"] == "create_draft_invoice"

    def test_zero_amount_when_none_found(self):
        result = _fallback_extraction("No money here", "Nothing to pay", "x@y.com")
        assert result["amount"] == 0.0


# ─── OdooDraftGenerator ───────────────────────────────────────────────────────

class TestOdooDraftGenerator:
    @pytest.fixture
    def vault_dir(self, tmp_path):
        """Temporary vault directory."""
        vault = tmp_path / "vault"
        vault.mkdir()
        return vault

    @pytest.fixture
    def generator(self, vault_dir):
        return OdooDraftGenerator(str(vault_dir))

    @pytest.fixture
    def invoice_email(self):
        return {
            "email_id": "EMAIL_TEST_001",
            "from": "acme@example.com",
            "subject": "Invoice #5001 for consulting services",
            "body": "Please find attached invoice for USD 2,500 for consulting services rendered.",
            "priority": "Normal",
        }

    def test_should_not_generate_when_odoo_disabled(self, generator, invoice_email):
        with patch.dict(os.environ, {"ENABLE_ODOO": "false"}):
            assert generator.should_generate(invoice_email) is False

    def test_should_generate_when_odoo_enabled(self, generator, invoice_email):
        with patch.dict(os.environ, {"ENABLE_ODOO": "true"}):
            assert generator.should_generate(invoice_email) is True

    def test_should_not_generate_for_non_invoice_email(self, generator):
        with patch.dict(os.environ, {"ENABLE_ODOO": "true"}):
            email = {"subject": "Team lunch Friday", "body": "See you at noon!"}
            assert generator.should_generate(email) is False

    def test_generate_creates_file(self, generator, vault_dir, invoice_email):
        with patch.dict(os.environ, {"ENABLE_ODOO": "true", "CLAUDE_API_KEY": ""}):
            path = generator.generate_and_save(invoice_email)

        assert path is not None
        assert path.exists()
        assert path.suffix == ".md"

    def test_generated_file_has_correct_frontmatter(self, generator, vault_dir, invoice_email):
        with patch.dict(os.environ, {"ENABLE_ODOO": "true", "CLAUDE_API_KEY": ""}):
            path = generator.generate_and_save(invoice_email)

        content = path.read_text(encoding="utf-8")
        assert "type: odoo_invoice" in content
        assert "action: create_draft_invoice" in content
        assert "status: pending" in content
        assert "mcp_server: odoo-mcp" in content

    def test_idempotent_does_not_overwrite(self, generator, vault_dir, invoice_email):
        with patch.dict(os.environ, {"ENABLE_ODOO": "true", "CLAUDE_API_KEY": ""}):
            path1 = generator.generate_and_save(invoice_email)
            path1.write_text("ORIGINAL", encoding="utf-8")
            path2 = generator.generate_and_save(invoice_email)

        # Should return same path, not overwrite
        assert path1 == path2
        assert path2.read_text(encoding="utf-8") == "ORIGINAL"

    def test_generate_skips_when_disabled(self, generator, invoice_email):
        with patch.dict(os.environ, {"ENABLE_ODOO": "false"}):
            path = generator.generate_and_save(invoice_email)
        assert path is None

    def test_file_stored_in_pending_approval_odoo(self, generator, vault_dir, invoice_email):
        with patch.dict(os.environ, {"ENABLE_ODOO": "true", "CLAUDE_API_KEY": ""}):
            path = generator.generate_and_save(invoice_email)

        assert "Pending_Approval" in str(path)
        assert "Odoo" in str(path)

    def test_filename_contains_invoice_draft(self, generator, vault_dir, invoice_email):
        with patch.dict(os.environ, {"ENABLE_ODOO": "true", "CLAUDE_API_KEY": ""}):
            path = generator.generate_and_save(invoice_email)

        assert "INVOICE_DRAFT" in path.name

    def test_claude_extraction_used_when_key_present(self, generator, invoice_email):
        mock_extraction = {
            "customer": "Acme Corp",
            "amount": 2500.0,
            "currency": "USD",
            "description": "Consulting services",
            "action": "create_draft_invoice",
        }
        with patch.dict(os.environ, {"ENABLE_ODOO": "true", "CLAUDE_API_KEY": "test-key"}):
            with patch(
                "cloud_agent.src.generators.odoo_draft._extract_odoo_data_with_claude",
                return_value=mock_extraction
            ):
                path = generator.generate_and_save(invoice_email)

        content = path.read_text(encoding="utf-8")
        assert "Acme Corp" in content
        assert "2500.00" in content
