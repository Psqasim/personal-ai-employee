"""
Odoo Poster Executor (Local Agent)

Reads an approved Odoo draft from vault/Approved/Odoo/,
calls the Odoo MCP server to create a DRAFT invoice in Odoo (never auto-posts),
moves the file to vault/Done/Odoo/, and sends a WhatsApp confirmation.

Flow:
  vault/Approved/Odoo/INVOICE_DRAFT_*.md
      → Odoo XML-RPC (create draft invoice)
      → vault/Done/Odoo/
      → WhatsApp confirmation
"""
import os
import sys
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from agent_skills.vault_parser import parse_draft_file, OdooDraft

logger = logging.getLogger(__name__)


class OdooPoster:
    """
    Executes approved Odoo invoice/expense drafts via XML-RPC.

    Does NOT use the MCP JSON-RPC server subprocess — calls Odoo directly
    via xmlrpc.client for reliability in the local agent context.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.done_dir = self.vault_path / "Done" / "Odoo"
        self.failed_dir = self.vault_path / "Failed" / "Odoo"
        self.log_dir = self.vault_path / "Logs" / "Odoo"
        for d in [self.done_dir, self.failed_dir, self.log_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def post_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process an approved Odoo draft file.

        Args:
            file_path: Absolute path to approved draft .md file

        Returns:
            {"success": bool, "odoo_record_id": int|None, "error": str|None}
        """
        file_path = Path(file_path)

        # Parse the draft
        try:
            draft: OdooDraft = parse_draft_file(str(file_path), draft_type="odoo")
        except Exception as e:
            return {"success": False, "odoo_record_id": None, "error": f"Parse error: {e}"}

        # Check Odoo is enabled
        if os.getenv("ENABLE_ODOO", "false").lower() != "true":
            return {"success": False, "odoo_record_id": None, "error": "Odoo disabled (ENABLE_ODOO=false)"}

        # Create in Odoo
        try:
            result = self._create_in_odoo(draft)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Odoo API error: {error_msg}")
            self._move_to_failed(file_path, error_msg)
            self._log(f"FAILED {file_path.name}: {error_msg}")
            return {"success": False, "odoo_record_id": None, "error": error_msg}

        # Move to Done
        done_path = self.done_dir / file_path.name
        try:
            shutil.move(str(file_path), str(done_path))
        except Exception as e:
            logger.warning(f"Could not move to Done: {e}")

        # Log success
        log_msg = (
            f"DONE {file_path.name} | "
            f"Odoo ID: {result.get('odoo_record_id')} | "
            f"Invoice#: {result.get('invoice_number', 'N/A')} | "
            f"Customer: {draft.customer} | "
            f"Amount: {draft.currency} {draft.amount:.2f}"
        )
        self._log(log_msg)
        logger.info(f"✅ Odoo invoice created: {result.get('invoice_number')} (ID {result.get('odoo_record_id')})")

        # WhatsApp confirmation
        self._send_whatsapp_confirmation(draft, result)

        return {
            "success": True,
            "odoo_record_id": result.get("odoo_record_id"),
            "invoice_number": result.get("invoice_number"),
            "error": None,
        }

    def _create_in_odoo(self, draft: OdooDraft) -> Dict[str, Any]:
        """Call Odoo XML-RPC directly to create draft invoice."""
        import xmlrpc.client

        url = os.getenv("ODOO_URL", "").rstrip("/")
        db = os.getenv("ODOO_DB", "")
        user = os.getenv("ODOO_USER", "")
        # API key takes priority over password
        password = os.getenv("ODOO_API_KEY") or os.getenv("ODOO_PASSWORD", "")

        if not all([url, db, user, password]):
            raise ValueError("Missing Odoo credentials in .env (ODOO_URL, ODOO_DB, ODOO_USER, ODOO_API_KEY)")

        # Authenticate
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
        uid = common.authenticate(db, user, password, {})
        if not uid:
            raise ValueError("Odoo authentication failed — check ODOO_API_KEY / ODOO_PASSWORD")

        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

        def execute(model, method, args, kwargs=None):
            return models.execute_kw(db, uid, password, model, method, args, kwargs or {})

        # Find or create partner
        partner_ids = execute("res.partner", "search", [[["name", "=", draft.customer]]], {"limit": 1})
        if partner_ids:
            partner_id = partner_ids[0]
        else:
            # Pass single dict (not a list) → Odoo returns one integer ID
            raw = execute("res.partner", "create", [{"name": draft.customer}])
            partner_id = raw[0] if isinstance(raw, list) else raw
            logger.info(f"Created Odoo partner: {draft.customer} (ID {partner_id})")

        # Build invoice data
        invoice_date = draft.odoo_data.get("invoice_date") or datetime.now().strftime("%Y-%m-%d")
        move_type = "out_invoice" if draft.action == "create_draft_invoice" else "in_invoice"

        invoice_vals = {
            "move_type": move_type,
            "partner_id": int(partner_id),  # ensure plain int, not list
            "invoice_date": invoice_date,
            "ref": draft.description,
            "state": "draft",  # ALWAYS draft — never auto-post
            "invoice_line_ids": [(0, 0, {
                "name": draft.description,
                "quantity": 1.0,
                "price_unit": float(draft.amount),
            })]
        }

        # Pass single dict → Odoo returns one integer ID
        raw_id = execute("account.move", "create", [invoice_vals])
        record_id = raw_id[0] if isinstance(raw_id, list) else raw_id

        # Read back for invoice number
        invoice = execute(
            "account.move", "read", [[int(record_id)]],
            {"fields": ["name", "state", "create_date"]}
        )[0]

        return {
            "odoo_record_id": record_id,
            "invoice_number": invoice.get("name") or f"INV/{record_id}",
            "status": invoice.get("state") or "draft",
        }

    def _send_whatsapp_confirmation(self, draft: OdooDraft, result: Dict[str, Any]):
        """Send WhatsApp notification on successful Odoo creation."""
        try:
            from cloud_agent.src.notifications.whatsapp_notifier import notify_task_completed
            invoice_num = result.get("invoice_number", "N/A")
            notify_task_completed(
                task_type="odoo_invoice",
                details=f"Invoice {invoice_num} created in Odoo | {draft.customer} | {draft.currency} {draft.amount:.2f}"
            )
        except Exception as e:
            logger.debug(f"WhatsApp notification skipped: {e}")

    def _move_to_failed(self, file_path: Path, error: str):
        """Move failed draft to vault/Failed/Odoo/ with error note appended."""
        try:
            dest = self.failed_dir / file_path.name
            shutil.copy2(str(file_path), str(dest))
            with open(dest, "a", encoding="utf-8") as f:
                f.write(f"\n\n---\n**FAILED**: {error}\n**At**: {datetime.now().isoformat()}\n")
            file_path.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Could not move to Failed: {e}")

    def _log(self, message: str):
        """Append to daily Odoo log."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"odoo-{today}.md"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"- {datetime.now().strftime('%H:%M:%S')} [local] {message}\n")
        except Exception:
            pass
