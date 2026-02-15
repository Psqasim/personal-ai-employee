#!/usr/bin/env python3
"""
Email MCP Server - SMTP send via JSON-RPC 2.0

Implements Model Context Protocol for email sending using SMTP.
Supports Gmail and custom SMTP servers with authentication.

Tools:
- send_email: Send email via SMTP

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
"""

import sys
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any


def send_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Send email via SMTP.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body (plain text)

    Returns:
        Dict with message_id and sent_at

    Raises:
        Exception: On SMTP errors (auth failed, network error, etc.)
    """
    # Get SMTP config from environment
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

    if not smtp_user or not smtp_password:
        raise Exception("SMTP credentials not configured (SMTP_USER, SMTP_PASSWORD)")

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to SMTP server (SSL or STARTTLS)
        if smtp_use_ssl:
            # Use SSL (port 465)
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
            server.login(smtp_user, smtp_password)
        else:
            # Use STARTTLS (port 587)
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            server.starttls()
            server.login(smtp_user, smtp_password)

        # Send email
        server.send_message(msg)
        server.quit()

        # Generate message_id (simplified)
        message_id = f"msg_{int(datetime.now().timestamp())}"
        sent_at = datetime.now().isoformat()

        return {
            "message_id": message_id,
            "sent_at": sent_at
        }

    except smtplib.SMTPAuthenticationError as e:
        raise Exception(f"SMTP_AUTH_FAILED: {e}")
    except smtplib.SMTPException as e:
        raise Exception(f"SMTP_ERROR: {e}")
    except Exception as e:
        raise Exception(f"NETWORK_ERROR: {e}")


def tools_list() -> Dict[str, Any]:
    """List available tools in this MCP server"""
    return {
        "tools": [
            {
                "name": "send_email",
                "description": "Send an email via SMTP",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email body (plain text)"}
                    },
                    "required": ["to", "subject", "body"]
                }
            }
        ]
    }


def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle JSON-RPC 2.0 request.

    Args:
        request: JSON-RPC request dict

    Returns:
        JSON-RPC response dict
    """
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    try:
        if method == "tools/list":
            result = tools_list()
            return {"jsonrpc": "2.0", "id": request_id, "result": result}

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "send_email":
                result = send_email(
                    to=arguments.get("to"),
                    subject=arguments.get("subject"),
                    body=arguments.get("body")
                )
                return {"jsonrpc": "2.0", "id": request_id, "result": result}
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {tool_name}"}
                }

        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": str(e)}
        }


def main():
    """Main loop: read JSON-RPC requests from stdin, write responses to stdout"""
    for line in sys.stdin:
        if not line.strip():
            continue

        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()
