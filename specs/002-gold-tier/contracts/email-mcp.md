# Email MCP Server Contract

**Server Name**: `email-mcp`
**Protocol**: JSON-RPC 2.0 over stdin/stdout
**Purpose**: Send emails via SMTP, search inbox via IMAP (optional)

---

## Tools

### 1. send_email

**Description**: Send an email via configured SMTP server

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "to": {
      "type": "string",
      "description": "Recipient email address",
      "format": "email"
    },
    "subject": {
      "type": "string",
      "description": "Email subject line",
      "maxLength": 200
    },
    "body": {
      "type": "string",
      "description": "Email body (plain text)",
      "maxLength": 10000
    }
  },
  "required": ["to", "subject", "body"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "message_id": {
      "type": "string",
      "description": "Unique message ID (SMTP server generated or timestamp-based)"
    },
    "sent_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp when email was sent"
    }
  },
  "required": ["message_id", "sent_at"]
}
```

**Error Codes**:
- `-32000`: `SMTP_AUTH_FAILED` - SMTP authentication failed (check credentials)
- `-32001`: `NETWORK_ERROR` - Network connection failed
- `-32002`: `INVALID_EMAIL` - Recipient email address invalid format
- `-32003`: `SMTP_SEND_FAILED` - SMTP send command rejected by server

**Example Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "send_email",
    "arguments": {
      "to": "client@example.com",
      "subject": "Re: Project proposal review",
      "body": "Hi John,\n\nThank you for the proposal. I'll review and get back to you by Friday.\n\nBest regards,\nSarah"
    }
  }
}
```

**Example Success Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "message_id": "msg_1707849600",
    "sent_at": "2026-02-13T14:20:00Z"
  }
}
```

**Example Error Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32000,
    "message": "SMTP_AUTH_FAILED: Invalid credentials for smtp.gmail.com"
  }
}
```

---

### 2. get_inbox (Optional - Future Enhancement)

**Description**: Search inbox for emails matching filter

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "filter": {
      "type": "string",
      "description": "IMAP search query (e.g., 'is:important', 'from:client@example.com')",
      "default": "ALL"
    },
    "max_results": {
      "type": "integer",
      "description": "Maximum number of emails to return",
      "default": 10,
      "minimum": 1,
      "maximum": 100
    }
  }
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "emails": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "from": {"type": "string"},
          "subject": {"type": "string"},
          "snippet": {"type": "string", "maxLength": 200},
          "received_at": {"type": "string", "format": "date-time"}
        }
      }
    }
  }
}
```

---

## Configuration

**Environment Variables** (passed via `~/.config/claude-code/mcp.json`):
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587                    # TLS port
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Gmail app password (not account password)
```

**Gmail App Password Setup**:
1. Go to Google Account → Security → 2-Step Verification → App Passwords
2. Generate app password for "Mail"
3. Use generated password in SMTP_PASSWORD

---

## Implementation Notes

- Use `smtplib` (Python stdlib) for SMTP
- Use `imaplib` (Python stdlib) for IMAP (get_inbox)
- Always use TLS (`starttls()`) for security
- Timeout for SMTP operations: 30 seconds
- Log all sends to MCP action log (sanitize body to first 50 chars)

---

## Testing

```bash
# Test send_email
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"send_email","arguments":{"to":"test@example.com","subject":"Test","body":"Test message"}}}' | python mcp_servers/email_mcp/server.py

# Expected output (if configured correctly):
# {"jsonrpc":"2.0","id":1,"result":{"message_id":"msg_...","sent_at":"2026-02-13T..."}}
```
