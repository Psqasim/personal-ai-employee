# MCP Protocol Patterns

**Protocol**: JSON-RPC 2.0 over stdin/stdout
**Version**: 1.0
**Purpose**: Common patterns for all MCP servers in Gold tier

---

## Protocol Overview

**MCP (Model Context Protocol)** enables communication between Claude Code (client) and external tool servers (MCP servers) via JSON-RPC 2.0 messages exchanged over stdin/stdout.

**Key Principles**:
- **Language-agnostic**: Servers can be written in any language (Python, Go, Rust, Node.js)
- **Process isolation**: Each MCP server runs as separate process with isolated permissions
- **Synchronous communication**: Client sends request → server processes → server responds
- **Stateless**: Each request is independent (session state managed by client)

---

## Message Formats

### Request Format (Client → Server)

```json
{
  "jsonrpc": "2.0",
  "id": <integer>,
  "method": "<method_name>",
  "params": {
    "name": "<tool_name>",
    "arguments": {
      "<arg1>": "<value1>",
      "<arg2>": "<value2>"
    }
  }
}
```

**Fields**:
- `jsonrpc`: Always "2.0" (JSON-RPC version)
- `id`: Request ID (integer, unique per request, used to match responses)
- `method`: RPC method (typically "tools/call" for tool invocation, "tools/list" for discovery)
- `params.name`: Tool name (e.g., "send_email", "send_message")
- `params.arguments`: Tool-specific parameters

### Success Response Format (Server → Client)

```json
{
  "jsonrpc": "2.0",
  "id": <integer>,
  "result": {
    "<output_field1>": "<value1>",
    "<output_field2>": "<value2>"
  }
}
```

**Fields**:
- `jsonrpc`: Always "2.0"
- `id`: Matches request ID
- `result`: Tool output (structure defined by tool contract)

### Error Response Format (Server → Client)

```json
{
  "jsonrpc": "2.0",
  "id": <integer>,
  "error": {
    "code": <integer>,
    "message": "<error_message>"
  }
}
```

**Standard Error Codes**:
- `-32700`: Parse error (invalid JSON)
- `-32600`: Invalid request (missing required fields)
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error
- `-32000` to `-32099`: Server-defined errors (see specific MCP contracts)

---

## Common Methods

### 1. tools/list

**Purpose**: Discover available tools in MCP server (server introspection)

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "send_email",
        "description": "Send an email via SMTP",
        "inputSchema": {
          "type": "object",
          "properties": {
            "to": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"}
          },
          "required": ["to", "subject", "body"]
        }
      }
    ]
  }
}
```

### 2. tools/call

**Purpose**: Invoke a specific tool with arguments

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "send_email",
    "arguments": {
      "to": "user@example.com",
      "subject": "Test",
      "body": "Test message"
    }
  }
}
```

**Response**: See tool-specific contract (e.g., email-mcp.md)

---

## Server Implementation Template (Python)

```python
#!/usr/bin/env python3
import sys
import json
import os
from typing import Any, Dict

class MCPServer:
    def __init__(self):
        self.tools = self._register_tools()

    def _register_tools(self) -> Dict[str, callable]:
        """Register available tools"""
        return {
            "tool_name": self.tool_name_impl
        }

    def tool_name_impl(self, **kwargs) -> Dict[str, Any]:
        """Tool implementation"""
        # Tool logic here
        return {"result_field": "value"}

    def handle_tools_list(self) -> Dict[str, Any]:
        """Respond to tools/list"""
        return {
            "tools": [
                {
                    "name": "tool_name",
                    "description": "Tool description",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "param1": {"type": "string"}
                        },
                        "required": ["param1"]
                    }
                }
            ]
        }

    def handle_tools_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a tool"""
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")

        tool_func = self.tools[name]
        return tool_func(**arguments)

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process JSON-RPC request"""
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        try:
            if method == "tools/list":
                result = self.handle_tools_list()
            elif method == "tools/call":
                result = self.handle_tools_call(params["name"], params.get("arguments", {}))
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }

            return {"jsonrpc": "2.0", "id": req_id, "result": result}

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            }

    def run(self):
        """Main loop: read from stdin, write to stdout"""
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                response = self.handle_request(request)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError as e:
                # Invalid JSON → parse error
                print(json.dumps({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
                }), flush=True)

if __name__ == "__main__":
    server = MCPServer()
    server.run()
```

---

## Client Configuration (~/.config/claude-code/mcp.json)

```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_servers/email_mcp/server.py"],
      "env": {
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "your-email@gmail.com",
        "SMTP_PASSWORD": "your-app-password"
      }
    },
    "whatsapp-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_servers/whatsapp_mcp/server.py"],
      "env": {
        "WHATSAPP_SESSION_PATH": "/home/user/.whatsapp_session"
      }
    },
    "linkedin-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_servers/linkedin_mcp/server.py"],
      "env": {
        "LINKEDIN_ACCESS_TOKEN": "your-oauth2-token",
        "LINKEDIN_AUTHOR_URN": "urn:li:person:xxxxx"
      }
    }
  }
}
```

**Configuration Notes**:
- `command`: Executable (python, node, go binary)
- `args`: Arguments passed to command
- `env`: Environment variables (credentials, config paths)
- Absolute paths required (no `~/` expansion)

---

## Error Handling Best Practices

1. **Network Errors**: Retry 3 times with exponential backoff (5s, 10s, 20s)
2. **Authentication Errors**: Do NOT retry automatically → notify human (create escalation file)
3. **Rate Limits**: Back off for specified duration (e.g., LinkedIn 429 → 60min wait)
4. **Timeout**: 30 seconds per MCP invocation → if no response, assume hung and escalate
5. **Logging**: Log ALL MCP invocations (sanitized) to `vault/Logs/MCP_Actions/`

---

## Security Best Practices

1. **Credentials in .env**: Never hardcode in server code
2. **Least Privilege**: Each MCP server only has credentials it needs (email-mcp can't access LinkedIn)
3. **Input Validation**: Validate all arguments before execution (email format, character limits)
4. **Output Sanitization**: Log only first 50 chars of sensitive data (email body, messages)
5. **Timeout Enforcement**: Kill hung MCP processes after 30s

---

## Testing MCP Servers

**Manual Test** (command-line):
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python server.py

# Expected: {"jsonrpc":"2.0","id":1,"result":{"tools":[...]}}
```

**Unit Test** (Python):
```python
import json
import subprocess

def test_mcp_server_tools_list():
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    proc = subprocess.Popen(
        ["python", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, _ = proc.communicate(input=json.dumps(request).encode())
    response = json.loads(stdout.decode())

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "result" in response
    assert "tools" in response["result"]
```

---

## Summary

All Gold tier MCP servers (email, whatsapp, linkedin) follow this JSON-RPC 2.0 protocol over stdin/stdout. This ensures:
- **Consistency**: Same request/response format across all servers
- **Testability**: Easy to test with mock stdin/stdout
- **Isolation**: Each server runs as separate process with isolated permissions
- **Extensibility**: Easy to add new MCP servers (calendar, odoo, browser) following same pattern

**Next**: Generate quickstart.md with setup instructions
