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

        invoice_number = invoice.get("name") or f"INV/{record_id}"

        # ── Optional: update partner email + send invoice PDF via Odoo ──
        if draft.customer_email:
            try:
                # Update partner email so Odoo sends to the right address
                execute("res.partner", "write", [[int(partner_id)], {"email": draft.customer_email}])

                # Find the "Customer Invoice" mail template
                tmpl_ids = execute(
                    "mail.template", "search",
                    [[["model", "=", "account.move"],
                      ["name", "ilike", "Invoice"]]],
                    {"limit": 1}
                )
                if tmpl_ids:
                    execute(
                        "mail.template", "send_mail",
                        [tmpl_ids[0], int(record_id)],
                        {"force_send": True}
                    )
                    logger.info(f"📧 Invoice email sent to {draft.customer_email} via Odoo template")
                else:
                    logger.warning("No 'Invoice' mail template found in Odoo — email NOT sent")
            except Exception as email_err:
                # Non-fatal: invoice was created, just email failed
                logger.warning(f"Odoo email send failed (invoice still created): {email_err}")

        return {
            "odoo_record_id": record_id,
            "invoice_number": invoice_number,
            "status": invoice.get("state") or "draft",
            "email_sent": bool(draft.customer_email),
        }

    # ── New Odoo operations ───────────────────────────────────────────────────

    def create_contact(self, name: str, email: str = "", phone: str = "") -> Dict[str, Any]:
        """
        Create a new res.partner (customer/vendor contact) in Odoo.

        Args:
            name:  Contact full name (required)
            email: Email address (optional)
            phone: Phone number (optional)

        Returns:
            {"success": bool, "partner_id": int|None, "error": str|None}
        """
        if not name:
            return {"success": False, "partner_id": None, "error": "name is required"}

        if os.getenv("ENABLE_ODOO", "false").lower() != "true":
            return {"success": False, "partner_id": None, "error": "Odoo disabled"}

        try:
            import xmlrpc.client
            url      = os.getenv("ODOO_URL", "").rstrip("/")
            db       = os.getenv("ODOO_DB", "")
            user     = os.getenv("ODOO_USER", "")
            password = os.getenv("ODOO_API_KEY") or os.getenv("ODOO_PASSWORD", "")

            common  = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
            uid     = common.authenticate(db, user, password, {})
            if not uid:
                raise ValueError("Odoo auth failed")

            models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

            def execute(model, method, args, kwargs=None):
                return models.execute_kw(db, uid, password, model, method, args, kwargs or {})

            vals = {"name": name}
            if email:
                vals["email"] = email
            if phone:
                vals["phone"] = phone

            raw = execute("res.partner", "create", [vals])
            partner_id = raw[0] if isinstance(raw, list) else raw

            logger.info(f"✅ Odoo contact created: {name} (ID {partner_id})")
            self._log(f"CONTACT_CREATED name={name} id={partner_id}")

            self._notify_whatsapp(
                f"👤 Contact created in Odoo: {name} (ID {partner_id})"
            )

            return {"success": True, "partner_id": partner_id, "error": None}

        except Exception as e:
            logger.error(f"create_contact failed: {e}")
            self._log(f"CONTACT_FAILED name={name} error={e}")
            return {"success": False, "partner_id": None, "error": str(e)}

    def register_payment(self, invoice_number: str, amount: float = 0) -> Dict[str, Any]:
        """
        Register a payment against an existing Odoo invoice.

        Finds the invoice by name (e.g. "INV/2026/00003"), creates a payment
        wizard record and validates it.

        Args:
            invoice_number: Odoo invoice name/reference (e.g. "INV/2026/00003")
            amount:         Payment amount (0 = pay full outstanding amount)

        Returns:
            {"success": bool, "payment_id": int|None, "error": str|None}
        """
        if not invoice_number:
            return {"success": False, "payment_id": None, "error": "invoice_number is required"}

        if os.getenv("ENABLE_ODOO", "false").lower() != "true":
            return {"success": False, "payment_id": None, "error": "Odoo disabled"}

        try:
            import xmlrpc.client
            url      = os.getenv("ODOO_URL", "").rstrip("/")
            db       = os.getenv("ODOO_DB", "")
            user     = os.getenv("ODOO_USER", "")
            password = os.getenv("ODOO_API_KEY") or os.getenv("ODOO_PASSWORD", "")

            common  = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
            uid     = common.authenticate(db, user, password, {})
            if not uid:
                raise ValueError("Odoo auth failed")

            models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

            def execute(model, method, args, kwargs=None):
                return models.execute_kw(db, uid, password, model, method, args, kwargs or {})

            # Find the invoice
            inv_ids = execute(
                "account.move", "search",
                [[["name", "=", invoice_number], ["move_type", "in", ["out_invoice", "in_invoice"]]]],
                {"limit": 1}
            )
            if not inv_ids:
                raise ValueError(f"Invoice not found: {invoice_number}")

            invoice_id = inv_ids[0]

            # Read outstanding amount if no amount specified
            if not amount:
                inv_data = execute(
                    "account.move", "read", [[invoice_id]],
                    {"fields": ["amount_residual", "currency_id"]}
                )[0]
                amount = inv_data["amount_residual"]

            # Create payment using account.payment directly (simpler than wizard)
            inv_data = execute(
                "account.move", "read", [[invoice_id]],
                {"fields": ["partner_id", "currency_id", "move_type", "journal_id"]}
            )[0]

            payment_type = "inbound" if inv_data["move_type"] == "out_invoice" else "outbound"

            # Find a suitable journal (bank or cash)
            journal_ids = execute(
                "account.journal", "search",
                [[["type", "in", ["bank", "cash"]]]],
                {"limit": 1}
            )
            journal_id = journal_ids[0] if journal_ids else inv_data.get("journal_id", [None])[0]

            payment_vals = {
                "payment_type": payment_type,
                "partner_id": inv_data["partner_id"][0] if isinstance(inv_data["partner_id"], list) else inv_data["partner_id"],
                "amount": float(amount),
                "journal_id": journal_id,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "ref": f"Payment for {invoice_number}",
            }

            raw = execute("account.payment", "create", [payment_vals])
            payment_id = raw[0] if isinstance(raw, list) else raw

            # Post the payment (validates it)
            execute("account.payment", "action_post", [[payment_id]])

            # Reconcile with the invoice
            payment_data = execute(
                "account.payment", "read", [[payment_id]],
                {"fields": ["move_id"]}
            )[0]
            move_id = payment_data["move_id"][0] if isinstance(payment_data.get("move_id"), list) else None

            if move_id:
                # Get payment lines and invoice lines for reconciliation
                try:
                    pay_lines = execute(
                        "account.move.line", "search",
                        [[["move_id", "=", move_id], ["account_id.reconcile", "=", True]]]
                    )
                    inv_lines = execute(
                        "account.move.line", "search",
                        [[["move_id", "=", invoice_id], ["account_id.reconcile", "=", True], ["reconciled", "=", False]]]
                    )
                    if pay_lines and inv_lines:
                        all_lines = pay_lines + inv_lines
                        execute("account.move.line", "reconcile", [all_lines])
                except Exception as rec_err:
                    logger.warning(f"Reconciliation attempt failed (payment still created): {rec_err}")

            logger.info(f"✅ Payment registered: {invoice_number} → payment ID {payment_id}")
            self._log(f"PAYMENT_REGISTERED invoice={invoice_number} amount={amount} payment_id={payment_id}")

            self._notify_whatsapp(
                f"💳 Payment registered: {invoice_number} | Amount: {amount:.2f}"
            )

            return {"success": True, "payment_id": payment_id, "error": None}

        except Exception as e:
            logger.error(f"register_payment failed: {e}")
            self._log(f"PAYMENT_FAILED invoice={invoice_number} error={e}")
            return {"success": False, "payment_id": None, "error": str(e)}

    def create_purchase_bill(
        self,
        vendor: str,
        amount: float,
        description: str = "",
        currency: str = "PKR",
    ) -> Dict[str, Any]:
        """
        Create a vendor bill (account.move with move_type=in_invoice) in Odoo.

        Args:
            vendor:      Vendor name (will be looked up or created in res.partner)
            amount:      Bill amount
            description: Line description
            currency:    Currency code (e.g. PKR, USD)

        Returns:
            {"success": bool, "bill_number": str|None, "odoo_record_id": int|None, "error": str|None}
        """
        if not vendor:
            return {"success": False, "bill_number": None, "odoo_record_id": None, "error": "vendor is required"}

        if os.getenv("ENABLE_ODOO", "false").lower() != "true":
            return {"success": False, "bill_number": None, "odoo_record_id": None, "error": "Odoo disabled"}

        try:
            import xmlrpc.client
            url      = os.getenv("ODOO_URL", "").rstrip("/")
            db       = os.getenv("ODOO_DB", "")
            user     = os.getenv("ODOO_USER", "")
            password = os.getenv("ODOO_API_KEY") or os.getenv("ODOO_PASSWORD", "")

            common  = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
            uid     = common.authenticate(db, user, password, {})
            if not uid:
                raise ValueError("Odoo auth failed")

            models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

            def execute(model, method, args, kwargs=None):
                return models.execute_kw(db, uid, password, model, method, args, kwargs or {})

            # Find or create vendor partner
            partner_ids = execute("res.partner", "search", [[["name", "=", vendor]]], {"limit": 1})
            if partner_ids:
                partner_id = partner_ids[0]
            else:
                raw = execute("res.partner", "create", [{"name": vendor, "supplier_rank": 1}])
                partner_id = raw[0] if isinstance(raw, list) else raw
                logger.info(f"Created vendor partner: {vendor} (ID {partner_id})")

            bill_date = datetime.now().strftime("%Y-%m-%d")

            bill_vals = {
                "move_type": "in_invoice",   # vendor bill
                "partner_id": int(partner_id),
                "invoice_date": bill_date,
                "ref": description or f"Purchase from {vendor}",
                "state": "draft",            # ALWAYS draft — never auto-post
                "invoice_line_ids": [(0, 0, {
                    "name": description or f"Purchase from {vendor}",
                    "quantity": 1.0,
                    "price_unit": float(amount),
                })]
            }

            raw_id = execute("account.move", "create", [bill_vals])
            record_id = raw_id[0] if isinstance(raw_id, list) else raw_id

            bill = execute(
                "account.move", "read", [[int(record_id)]],
                {"fields": ["name", "state"]}
            )[0]
            bill_number = bill.get("name") or f"BILL/{record_id}"

            logger.info(f"✅ Purchase bill created: {bill_number} (ID {record_id}) | {vendor} | {currency} {amount:.2f}")
            self._log(f"BILL_CREATED bill={bill_number} vendor={vendor} amount={currency} {amount:.2f} id={record_id}")

            self._notify_whatsapp(
                f"🧾 Purchase bill created: {bill_number} | {vendor} | {currency} {amount:,.2f}"
            )

            return {
                "success": True,
                "bill_number": bill_number,
                "odoo_record_id": record_id,
                "error": None,
            }

        except Exception as e:
            logger.error(f"create_purchase_bill failed: {e}")
            self._log(f"BILL_FAILED vendor={vendor} error={e}")
            return {"success": False, "bill_number": None, "odoo_record_id": None, "error": str(e)}

    def _notify_whatsapp(self, message: str):
        """Send a generic WhatsApp notification (non-fatal if it fails)."""
        try:
            from cloud_agent.src.notifications.whatsapp_notifier import _send_in_thread
            _send_in_thread(message, "odoo_operation")
        except Exception as e:
            logger.debug(f"WhatsApp notify skipped: {e}")

    def _send_whatsapp_confirmation(self, draft: OdooDraft, result: Dict[str, Any]):
        """Send WhatsApp notification on successful Odoo creation."""
        try:
            from cloud_agent.src.notifications.whatsapp_notifier import notify_task_completed
            invoice_num = result.get("invoice_number", "N/A")
            email_note = f" · email sent to {draft.customer_email}" if result.get("email_sent") else ""
            notify_task_completed(
                task_type="odoo_invoice",
                details=f"Invoice {invoice_num} created in Odoo | {draft.customer} | {draft.currency} {draft.amount:.2f}{email_note}"
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
