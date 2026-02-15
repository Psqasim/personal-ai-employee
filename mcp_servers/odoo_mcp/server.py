#!/usr/bin/env python3
"""
Odoo MCP Server - JSON-RPC 2.0 Interface for Odoo Accounting

This MCP server enables draft invoice and expense creation in Odoo via JSON-RPC.
All entries are created as DRAFTS only (never auto-confirmed/posted) to maintain
human oversight per Gold Tier safety requirements.

Tools:
- create_draft_invoice: Create draft invoice in Odoo (status=draft)
- create_draft_expense: Create draft expense entry in Odoo (status=draft)

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
Task: T056 [US7] Implement odoo_mcp/server.py
Reference: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html
"""

import os
import sys
import json
import xmlrpc.client
from typing import Dict, Any, Optional
from datetime import datetime


class OdooMCPServer:
    """Odoo MCP Server using XML-RPC protocol"""

    def __init__(self):
        """Initialize Odoo connection from environment variables"""
        self.url = os.getenv("ODOO_URL")
        self.db = os.getenv("ODOO_DB")
        self.username = os.getenv("ODOO_USER")
        self.password = os.getenv("ODOO_PASSWORD")

        # Validate required env vars
        if not all([self.url, self.db, self.username, self.password]):
            raise ValueError(
                "Missing Odoo credentials. Required: ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD"
            )

        # XML-RPC endpoints
        self.common_url = f"{self.url}/xmlrpc/2/common"
        self.models_url = f"{self.url}/xmlrpc/2/object"

        # Authenticate and get user ID
        self.uid = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Odoo and store UID"""
        try:
            common = xmlrpc.client.ServerProxy(self.common_url, allow_none=True)
            self.uid = common.authenticate(self.db, self.username, self.password, {})

            if not self.uid:
                raise Exception("Authentication failed: Invalid credentials")

            print(f"[odoo-mcp] Authenticated as UID {self.uid}", file=sys.stderr)

        except Exception as e:
            raise Exception(f"ODOO_AUTH_FAILED: {str(e)}")

    def _execute_kw(self, model: str, method: str, args: list, kwargs: dict = None):
        """
        Execute Odoo model method via XML-RPC.

        Args:
            model: Odoo model name (e.g., 'account.move')
            method: Method to call (e.g., 'create', 'search', 'read')
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Method result

        Raises:
            Exception: On Odoo API error
        """
        kwargs = kwargs or {}

        try:
            models = xmlrpc.client.ServerProxy(self.models_url, allow_none=True)
            result = models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model,
                method,
                args,
                kwargs
            )
            return result

        except xmlrpc.client.Fault as e:
            raise Exception(f"ODOO_API_ERROR: {e.faultString}")
        except Exception as e:
            raise Exception(f"ODOO_CONNECTION_ERROR: {str(e)}")

    def create_draft_invoice(
        self,
        customer: str,
        amount: float,
        description: str,
        invoice_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create draft invoice in Odoo (status=draft, never auto-posted).

        Args:
            customer: Customer name or ID
            amount: Invoice amount (float)
            description: Invoice description/reference
            invoice_date: Optional invoice date (YYYY-MM-DD), defaults to today

        Returns:
            {
                "odoo_record_id": int,
                "invoice_number": str (auto-generated),
                "status": "draft",
                "created_at": str (ISO timestamp)
            }

        Raises:
            Exception: On Odoo API error
        """
        # Default to today if no date provided
        if not invoice_date:
            invoice_date = datetime.now().strftime("%Y-%m-%d")

        # Search for customer by name (simplified - in production, would handle partner resolution)
        # For now, use customer string as reference
        partner_id = self._find_or_create_partner(customer)

        # Create invoice (account.move with move_type='out_invoice')
        invoice_data = {
            "move_type": "out_invoice",  # Customer invoice
            "partner_id": partner_id,
            "invoice_date": invoice_date,
            "ref": description,  # Reference/description
            "state": "draft",  # CRITICAL: Always draft, never auto-post
            "invoice_line_ids": [(0, 0, {
                "name": description,
                "quantity": 1,
                "price_unit": amount,
            })]
        }

        try:
            # Create invoice (returns record ID)
            record_id = self._execute_kw("account.move", "create", [[invoice_data]])

            # Read back invoice details
            invoice = self._execute_kw(
                "account.move",
                "read",
                [[record_id]],
                {"fields": ["name", "state", "create_date"]}
            )[0]

            return {
                "odoo_record_id": record_id,
                "invoice_number": invoice["name"],
                "status": invoice["state"],  # Should be 'draft'
                "created_at": invoice["create_date"]
            }

        except Exception as e:
            raise Exception(f"Failed to create draft invoice: {str(e)}")

    def create_draft_expense(
        self,
        vendor: str,
        amount: float,
        description: str,
        expense_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create draft expense entry in Odoo (status=draft, never auto-posted).

        Args:
            vendor: Vendor/supplier name or ID
            amount: Expense amount (float)
            description: Expense description/reference
            expense_date: Optional expense date (YYYY-MM-DD), defaults to today

        Returns:
            {
                "odoo_record_id": int,
                "expense_number": str (auto-generated),
                "status": "draft",
                "created_at": str (ISO timestamp)
            }

        Raises:
            Exception: On Odoo API error
        """
        # Default to today if no date provided
        if not expense_date:
            expense_date = datetime.now().strftime("%Y-%m-%d")

        # Find or create vendor partner
        partner_id = self._find_or_create_partner(vendor)

        # Create expense (account.move with move_type='in_invoice')
        expense_data = {
            "move_type": "in_invoice",  # Vendor bill/expense
            "partner_id": partner_id,
            "invoice_date": expense_date,
            "ref": description,
            "state": "draft",  # CRITICAL: Always draft, never auto-post
            "invoice_line_ids": [(0, 0, {
                "name": description,
                "quantity": 1,
                "price_unit": amount,
            })]
        }

        try:
            # Create expense (returns record ID)
            record_id = self._execute_kw("account.move", "create", [[expense_data]])

            # Read back expense details
            expense = self._execute_kw(
                "account.move",
                "read",
                [[record_id]],
                {"fields": ["name", "state", "create_date"]}
            )[0]

            return {
                "odoo_record_id": record_id,
                "expense_number": expense["name"],
                "status": expense["state"],  # Should be 'draft'
                "created_at": expense["create_date"]
            }

        except Exception as e:
            raise Exception(f"Failed to create draft expense: {str(e)}")

    def _find_or_create_partner(self, partner_name: str) -> int:
        """
        Find partner by name or create if not exists.

        Args:
            partner_name: Partner name to search/create

        Returns:
            Partner ID (int)
        """
        try:
            # Search for existing partner
            partner_ids = self._execute_kw(
                "res.partner",
                "search",
                [[["name", "=", partner_name]]],
                {"limit": 1}
            )

            if partner_ids:
                return partner_ids[0]

            # Create new partner if not found
            partner_id = self._execute_kw(
                "res.partner",
                "create",
                [[{"name": partner_name}]]
            )

            print(f"[odoo-mcp] Created new partner: {partner_name} (ID: {partner_id})", file=sys.stderr)
            return partner_id

        except Exception as e:
            raise Exception(f"Failed to resolve partner '{partner_name}': {str(e)}")


# JSON-RPC 2.0 Request Handler
def handle_jsonrpc_request(request: Dict) -> Dict:
    """
    Handle JSON-RPC 2.0 request.

    Args:
        request: JSON-RPC request dict

    Returns:
        JSON-RPC response dict
    """
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params", {})

    try:
        # Initialize Odoo server
        server = OdooMCPServer()

        # Handle tools/list
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "create_draft_invoice",
                            "description": "Create draft invoice in Odoo (status=draft, never auto-posted)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "customer": {"type": "string", "description": "Customer name"},
                                    "amount": {"type": "number", "description": "Invoice amount"},
                                    "description": {"type": "string", "description": "Invoice description"},
                                    "invoice_date": {"type": "string", "description": "Invoice date (YYYY-MM-DD)", "optional": True}
                                },
                                "required": ["customer", "amount", "description"]
                            }
                        },
                        {
                            "name": "create_draft_expense",
                            "description": "Create draft expense entry in Odoo (status=draft, never auto-posted)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "vendor": {"type": "string", "description": "Vendor/supplier name"},
                                    "amount": {"type": "number", "description": "Expense amount"},
                                    "description": {"type": "string", "description": "Expense description"},
                                    "expense_date": {"type": "string", "description": "Expense date (YYYY-MM-DD)", "optional": True}
                                },
                                "required": ["vendor", "amount", "description"]
                            }
                        }
                    ]
                }
            }

        # Handle tools/call
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "create_draft_invoice":
                result = server.create_draft_invoice(
                    customer=arguments.get("customer"),
                    amount=arguments.get("amount"),
                    description=arguments.get("description"),
                    invoice_date=arguments.get("invoice_date")
                )
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }

            elif tool_name == "create_draft_expense":
                result = server.create_draft_expense(
                    vendor=arguments.get("vendor"),
                    amount=arguments.get("amount"),
                    description=arguments.get("description"),
                    expense_date=arguments.get("expense_date")
                )
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }

        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    except Exception as e:
        error_code = -32000  # Server error
        if "AUTH_FAILED" in str(e):
            error_code = -32000
        elif "CONNECTION_ERROR" in str(e):
            error_code = -32001

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": error_code,
                "message": str(e)
            }
        }


def main():
    """
    Main entry point - read JSON-RPC requests from stdin, write responses to stdout.
    """
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = handle_jsonrpc_request(request)
            print(json.dumps(response), flush=True)

        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()
