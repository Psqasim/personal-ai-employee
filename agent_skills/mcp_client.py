"""
MCP Client - JSON-RPC 2.0 Communication with MCP Servers

This module provides an abstraction for invoking MCP (Model Context Protocol) servers
via JSON-RPC 2.0 over stdin/stdout. It handles request building, error handling,
timeout enforcement, and retry logic.

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
"""

import json
import subprocess
import sys
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class MCPError:
    """MCP error response structure"""
    code: int
    message: str
    data: Optional[Dict] = None


class MCPClient:
    """
    JSON-RPC 2.0 client for MCP server communication.

    Supports:
    - Request building (tools/list, tools/call)
    - Error handling (codes -32000 to -32099)
    - Timeout enforcement (30s default)
    - Retry logic (configurable)
    """

    def __init__(self, timeout: int = 180):
        """
        Initialize MCP client.

        Args:
            timeout: Max seconds to wait for MCP response (default: 180)
                    Increased to 180s (3 minutes) to accommodate browser automation
                    workflows (WhatsApp Web, LinkedIn) in headless mode which require:
                    - Browser launch: 5-10s
                    - Page load (headless can be slow): 10-30s
                    - DOM interactions: 5-10s per operation
                    - Waits and retries: 10-20s
                    Total: ~60-90s typical, 180s with safety margin for headless
        """
        self.timeout = timeout
        self._request_id = 0

    def _next_request_id(self) -> int:
        """Generate sequential request IDs"""
        self._request_id += 1
        return self._request_id

    def _build_request(self, method: str, params: Optional[Dict] = None) -> Dict:
        """
        Build JSON-RPC 2.0 request.

        Args:
            method: JSON-RPC method (e.g., "tools/call", "tools/list")
            params: Method parameters

        Returns:
            JSON-RPC request dict
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": method
        }
        if params:
            request["params"] = params
        return request

    def call_tool(
        self,
        mcp_server: str,
        tool_name: str,
        arguments: Dict[str, Any],
        retry_count: int = 3,
        retry_delay: int = 5
    ) -> Dict[str, Any]:
        """
        Call an MCP server tool via JSON-RPC.

        Args:
            mcp_server: MCP server name (e.g., "email-mcp", "whatsapp-mcp")
            tool_name: Tool name to invoke (e.g., "send_email", "send_message")
            arguments: Tool arguments dict
            retry_count: Number of retries on failure (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 5)

        Returns:
            Tool result dict on success

        Raises:
            MCPError: On MCP server error
            TimeoutError: If server doesn't respond within timeout
            subprocess.SubprocessError: If MCP server process fails
        """
        request = self._build_request(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            }
        )

        # Get MCP server command from config (would be loaded from mcp.json in production)
        # For now, construct from server name
        server_command = self._get_server_command(mcp_server)

        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(retry_count):
            try:
                response = self._invoke_mcp_server(server_command, request)

                # Check for JSON-RPC error
                if "error" in response:
                    error = MCPError(
                        code=response["error"]["code"],
                        message=response["error"]["message"],
                        data=response["error"].get("data")
                    )

                    # Check if error is retriable (network, timeout, etc.)
                    if error.code in [-32000, -32001, -32002]:  # Server errors
                        last_error = error
                        if attempt < retry_count - 1:
                            # Exponential backoff
                            wait_time = retry_delay * (2 ** attempt)
                            time.sleep(wait_time)
                            continue

                    raise Exception(f"MCP Error {error.code}: {error.message}")

                # Success
                return response.get("result", {})

            except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                last_error = e
                if attempt < retry_count - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                raise

        # All retries exhausted
        raise Exception(f"MCP call failed after {retry_count} retries: {last_error}")

    def list_tools(self, mcp_server: str) -> list:
        """
        List available tools from MCP server.

        Args:
            mcp_server: MCP server name

        Returns:
            List of tool definitions
        """
        request = self._build_request(method="tools/list")
        server_command = self._get_server_command(mcp_server)
        response = self._invoke_mcp_server(server_command, request)

        if "error" in response:
            raise Exception(f"MCP Error: {response['error']['message']}")

        return response.get("result", {}).get("tools", [])

    def _invoke_mcp_server(self, command: list, request: Dict) -> Dict:
        """
        Invoke MCP server process via stdin/stdout.

        Args:
            command: MCP server command and args (e.g., ["python", "server.py"])
            request: JSON-RPC request dict

        Returns:
            JSON-RPC response dict

        Raises:
            subprocess.TimeoutExpired: If server doesn't respond within timeout
            subprocess.SubprocessError: If process fails
        """
        request_json = json.dumps(request) + "\n"

        try:
            # Ensure MCP server inherits environment variables (especially for LinkedIn/WhatsApp tokens)
            import os
            env = os.environ.copy()

            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            stdout, stderr = process.communicate(
                input=request_json,
                timeout=self.timeout
            )

            if process.returncode != 0:
                raise subprocess.SubprocessError(
                    f"MCP server exited with code {process.returncode}: {stderr}"
                )

            # Parse JSON response
            response = json.loads(stdout.strip())
            return response

        except subprocess.TimeoutExpired:
            process.kill()
            raise TimeoutError(f"MCP server timed out after {self.timeout}s")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from MCP server: {e}")

    def _get_server_command(self, mcp_server: str) -> list:
        """
        Get MCP server command from server name.

        In production, this would load from ~/.config/claude-code/mcp.json.
        For now, construct based on naming convention.

        Args:
            mcp_server: Server name (e.g., "email-mcp")

        Returns:
            Command list (e.g., ["python", "mcp_servers/email_mcp/server.py"])
        """
        # Map server names to commands
        # TODO: Load from mcp.json in production
        # Use sys.executable to get the current Python interpreter (handles venv correctly)
        python_exe = sys.executable
        server_map = {
            "email-mcp": [python_exe, "mcp_servers/email_mcp/server.py"],
            "whatsapp-mcp": [python_exe, "mcp_servers/whatsapp_mcp/server.py"],
            "linkedin-mcp": [python_exe, "mcp_servers/linkedin_mcp/server.py"],
            "twitter-mcp": [python_exe, "mcp_servers/twitter_mcp/server.py"],
            "odoo-mcp": [python_exe, "mcp_servers/odoo_mcp/server.py"]
        }

        if mcp_server not in server_map:
            raise ValueError(f"Unknown MCP server: {mcp_server}")

        return server_map[mcp_server]

    def health_check(self, mcp_server: str) -> bool:
        """
        Check if MCP server is healthy (can respond to tools/list).

        Args:
            mcp_server: Server name

        Returns:
            True if server responds, False otherwise
        """
        try:
            tools = self.list_tools(mcp_server)
            return len(tools) >= 0  # Any response means healthy
        except Exception:
            return False


# Module-level singleton for convenience
_client_instance: Optional[MCPClient] = None


def get_mcp_client(timeout: int = 180) -> MCPClient:
    """
    Get or create MCP client singleton.

    Args:
        timeout: Request timeout in seconds (default: 180s for headless browser operations)

    Returns:
        MCPClient instance
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = MCPClient(timeout=timeout)
    return _client_instance


# Example usage
if __name__ == "__main__":
    # Example: Call email MCP to send email
    client = get_mcp_client()

    try:
        result = client.call_tool(
            mcp_server="email-mcp",
            tool_name="send_email",
            arguments={
                "to": "example@example.com",
                "subject": "Test Email",
                "body": "This is a test email from MCP client."
            }
        )
        print(f"Email sent: {result}")
    except Exception as e:
        print(f"Failed to send email: {e}")
