# Contract: Email MCP Server

**MCP Server**: `@modelcontextprotocol/server-email`
**Configuration**: `~/.config/claude-code/mcp.json`
**Authentication**: Gmail OAuth2 (reuses tokens from Gmail watcher)

## MCP Server Configuration

```json
{
  "servers": [
    {
      "name": "email",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-email"],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "/home/user/.config/personal-ai-employee/gmail_credentials.json",
        "GMAIL_TOKEN_PATH": "/home/user/.config/personal-ai-employee/gmail_token.json"
      }
    }
  ]
}
```

## Tool: send_email

**Schema**:
```typescript
{
  "name": "send_email",
  "description": "Send an email via Gmail",
  "parameters": {
    "to": {
      "type": "string",
      "description": "Recipient email address"
    },
    "subject": {
      "type": "string",
      "description": "Email subject line"
    },
    "body": {
      "type": "string",
      "description": "Email body (plain text or HTML)"
    },
    "attachments": {
      "type": "array",
      "items": {"type": "string"},
      "description": "File paths to attach (optional)"
    }
  },
  "required": ["to", "subject", "body"]
}
```

## Human-in-the-Loop Approval Workflow

### Step 1: Create Approval Request

When email send is needed, create approval file:

**File**: `vault/Pending_Approval/Email/REPLY_{email_id}.md`

**Content**:
```markdown
---
action: send_email
to: client@example.com
subject: Re: Proposal Request
created: 2026-02-11T15:00:00Z
status: pending_approval
---

## Email Draft

Dear Client,

Thank you for your proposal request. I will have the proposal ready by end of day.

Best regards,
[Your Name]

## To Approve
Move this file to `vault/Approved/Email/`

## To Reject
Move this file to `vault/Rejected/Email/`
```

### Step 2: User Approves

User moves file: `vault/Pending_Approval/Email/` → `vault/Approved/Email/`

### Step 3: Orchestrator Executes MCP Action

Orchestrator watches `vault/Approved/Email/`, calls MCP server:

```python
from mcp import use_mcp_tool

async def execute_approved_email(approval_file: Path):
    # Parse approval file
    metadata = parse_yaml_frontmatter(approval_file)
    body = extract_markdown_body(approval_file)

    # Call MCP email server
    result = await use_mcp_tool("email", "send_email", {
        "to": metadata["to"],
        "subject": metadata["subject"],
        "body": body
    })

    # Log action
    log_mcp_action("email_send", metadata, result)

    # Move to Done
    shutil.move(approval_file, f"vault/Done/Email/{approval_file.name}")
```

### Step 4: Log Action

**File**: `vault/Logs/MCP_Actions/YYYY-MM-DD.md`

**Content**:
```markdown
| Timestamp | Action | Target | Status | Result |
|-----------|--------|--------|--------|--------|
| 2026-02-11T15:05:00Z | send_email | client@example.com | success | Message ID: abc123 |
```

## Error Handling

- **MCP server unavailable**: Log error, move approval back to Pending_Approval/ with error note
- **Gmail API error**: Same as above, with specific error message from API
- **User rejects**: File moved to `vault/Rejected/Email/`, no action taken

---

**Contract Status**: Complete. Ready for integration with human-in-the-loop approval workflow.
