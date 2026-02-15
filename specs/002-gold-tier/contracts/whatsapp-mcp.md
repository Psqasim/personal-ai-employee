# WhatsApp MCP Server Contract

**Server Name**: `whatsapp-mcp`
**Protocol**: JSON-RPC 2.0 over stdin/stdout
**Purpose**: Automate WhatsApp Web via Playwright (send messages, authenticate via QR code)

---

## Tools

### 1. authenticate_qr

**Description**: Display QR code for WhatsApp Web authentication (first-time setup or session expired)

**Input Schema**:
```json
{
  "type": "object",
  "properties": {}
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "qr_code_base64": {
      "type": "string",
      "description": "QR code image as base64-encoded PNG"
    },
    "status": {
      "type": "string",
      "enum": ["waiting", "authenticated"],
      "description": "Authentication status"
    }
  }
}
```

**Error Codes**:
- `-32000`: `SESSION_PATH_INVALID` - WHATSAPP_SESSION_PATH not writable
- `-32001`: `BROWSER_LAUNCH_FAILED` - Playwright browser failed to launch

**Example Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "authenticate_qr",
    "arguments": {}
  }
}
```

**Example Response** (waiting for scan):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "status": "waiting"
  }
}
```

---

### 2. send_message

**Description**: Send a WhatsApp message to a contact/chat

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "chat_id": {
      "type": "string",
      "description": "Contact name or chat ID (as shown in WhatsApp Web)"
    },
    "message": {
      "type": "string",
      "description": "Message text",
      "maxLength": 5000
    }
  },
  "required": ["chat_id", "message"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "message_id": {
      "type": "string",
      "description": "Timestamp-based message ID"
    },
    "sent_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

**Error Codes**:
- `-32000`: `SESSION_EXPIRED` - WhatsApp Web session expired (QR auth required)
- `-32001`: `CHAT_NOT_FOUND` - Contact/chat not found in WhatsApp
- `-32002`: `NETWORK_ERROR` - Network connection failed
- `-32003`: `ELEMENT_NOT_FOUND` - WhatsApp UI elements changed (selector update needed)

**Example Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "send_message",
    "arguments": {
      "chat_id": "John Doe",
      "message": "Got it! Will process the payment today. Expect confirmation by 5 PM. - Sarah"
    }
  }
}
```

**Example Success Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "message_id": "msg_1707849700",
    "sent_at": "2026-02-13T14:25:00Z"
  }
}
```

---

### 3. get_chats (Optional - Future Enhancement)

**Description**: List recent chats with unread messages

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "unread_only": {
      "type": "boolean",
      "default": true
    }
  }
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "chats": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "name": {"type": "string"},
          "last_message": {"type": "string", "maxLength": 100},
          "unread_count": {"type": "integer"}
        }
      }
    }
  }
}
```

---

## Configuration

**Environment Variables**:
```bash
WHATSAPP_SESSION_PATH=/home/user/.whatsapp_session  # Playwright session storage
WHATSAPP_POLL_INTERVAL=30                           # Polling interval (seconds)
```

**Session Persistence**:
- Use `browser_context.storage_state(path=WHATSAPP_SESSION_PATH)` after QR auth
- Load with `browser.new_context(storage_state=WHATSAPP_SESSION_PATH)` on subsequent runs
- Session remains valid for weeks/months (until WhatsApp logs out)

---

## Implementation Notes

**Playwright Selectors** (as of 2026-01):
```python
SEARCH_BOX = 'div[contenteditable="true"][data-tab="3"]'
MESSAGE_INPUT = 'div[contenteditable="true"][data-tab="10"]'
SEND_BUTTON = 'button[data-tab="11"]'
QR_CODE = 'canvas[aria-label="Scan this QR code to link a device!"]'
```

**Session Expiry Detection**:
```python
page.goto('https://web.whatsapp.com')
try:
    # If session valid, conversation panel appears
    page.wait_for_selector('div[data-testid="conversation-panel-wrapper"]', timeout=5000)
except TimeoutError:
    # Check if QR code present (session expired)
    if page.query_selector(QR_CODE):
        raise SessionExpiredError()
```

**Error Recovery**:
- Network timeout → retry 3 times (5s, 10s, 20s backoff)
- Element not found → check if logged out, if not → notify human (selectors may have changed)
- Message send confirmation → wait for message to appear in chat history

---

## Testing

```bash
# Test authenticate_qr (requires display server for QR code rendering)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"authenticate_qr","arguments":{}}}' | python mcp_servers/whatsapp_mcp/server.py

# Test send_message (requires valid session)
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"send_message","arguments":{"chat_id":"Test Contact","message":"Test message"}}}' | python mcp_servers/whatsapp_mcp/server.py
```

---

## Security Considerations

- Session files contain authentication tokens → store in secure location (`.gitignore`)
- Never log full message content → sanitize to first 50 chars in MCP action logs
- Playwright runs in headless mode for automated sends → QR auth requires headed mode (one-time)
