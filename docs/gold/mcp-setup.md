# MCP Server Configuration Guide

**Purpose**: Configure Model Context Protocol (MCP) servers for Gold tier

This guide explains how to set up the 3 MCP servers (Email, WhatsApp, LinkedIn) in your Claude Code configuration.

---

## Overview

**MCP Servers**:
1. **email-mcp** - Send emails via SMTP
2. **whatsapp-mcp** - Send WhatsApp messages via Playwright
3. **linkedin-mcp** - Post to LinkedIn via API v2

**Configuration File**: `~/.config/claude-code/mcp.json`

---

## Step 1: Create MCP Configuration File

### 1.1 Check if File Exists

```bash
ls -la ~/.config/claude-code/mcp.json
```

### 1.2 Create Configuration

Create or edit `~/.config/claude-code/mcp.json`:

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
        "LINKEDIN_ACCESS_TOKEN": "your-oauth-token",
        "LINKEDIN_AUTHOR_URN": "urn:li:person:your-id"
      }
    },
    "odoo-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_servers/odoo_mcp/server.py"],
      "env": {
        "ODOO_URL": "https://your-odoo-instance.odoo.com",
        "ODOO_DB": "your-database-name",
        "ODOO_USER": "admin@example.com",
        "ODOO_PASSWORD": "your-odoo-password"
      }
    }
  }
}
```

**IMPORTANT**: Replace `/absolute/path/to/` with your actual project path!

---

## Step 2: Test Each MCP Server

### 2.1 Test Email MCP

```bash
echo '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}' | python mcp_servers/email_mcp/server.py
```

**Expected output**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "send_email",
        "description": "Send email via SMTP"
      }
    ]
  }
}
```

### 2.2 Test WhatsApp MCP

```bash
echo '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}' | python mcp_servers/whatsapp_mcp/server.py
```

**Expected**: Returns `authenticate_qr` and `send_message` tools

### 2.3 Test LinkedIn MCP

```bash
echo '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}' | python mcp_servers/linkedin_mcp/server.py
```

**Expected**: Returns `create_post` tool

---

## Step 3: Configure Environment Variables

Instead of hardcoding in `mcp.json`, use environment variables:

### 3.1 Update .env File

```bash
# Email MCP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# WhatsApp MCP
WHATSAPP_SESSION_PATH=/home/user/.whatsapp_session

# LinkedIn MCP
LINKEDIN_ACCESS_TOKEN=your-oauth-token
LINKEDIN_AUTHOR_URN=urn:li:person:your-id

# Odoo MCP (Optional)
ODOO_URL=https://your-odoo-instance.odoo.com
ODOO_DB=your-database-name
ODOO_USER=admin@example.com
ODOO_PASSWORD=your-odoo-password
```

### 3.2 Load Environment Before Running

```bash
# Option 1: Source .env
set -a; source .env; set +a
python scripts/run_approval_watcher.py

# Option 2: Use python-dotenv
# Already implemented in agent_skills/ modules
```

---

## Troubleshooting

### Server Not Active

**Error**:
```json
{
  "error": {
    "code": -32603,
    "message": "Server not responding"
  }
}
```

**Solution**:
1. Check server path is absolute
2. Verify Python can execute server.py
3. Check environment variables are set

### Authentication Failed

**Email MCP**:
- Check Gmail App Password (16 characters, no spaces)
- Verify 2FA is enabled on Google account

**WhatsApp MCP**:
- Re-authenticate: `python scripts/whatsapp_qr_setup.py`

**LinkedIn MCP**:
- Verify OAuth token hasn't expired (60-day lifespan)
- Check author URN is correct

---

## Health Checks

The `mcp_client.py` module includes health check functionality that runs automatically on startup:

```python
from agent_skills.mcp_client import get_mcp_client

client = get_mcp_client()

# Check if MCP servers are healthy
print("Email MCP:", "✓" if client.health_check("email-mcp") else "✗")
print("WhatsApp MCP:", "✓" if client.health_check("whatsapp-mcp") else "✗")
print("LinkedIn MCP:", "✓" if client.health_check("linkedin-mcp") else "✗")
print("Odoo MCP:", "✓" if client.health_check("odoo-mcp") else "✗")
```

Health check results are displayed in `vault/Dashboard.md` under the **Gold Tier Status** section.

---

## Odoo MCP Setup (Optional)

**Prerequisites**:
- Odoo 19+ instance (Community or Enterprise)
- Admin or API user credentials

**Configuration**:
1. Add Odoo credentials to `.env`
2. Test Odoo MCP server:
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python mcp_servers/odoo_mcp/server.py
   ```

**Expected**: Returns `create_draft_invoice` and `create_draft_expense` tools

**Reference**: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html

---

## Next Steps

✅ Follow `docs/gold/testing-guide.md` for full workflow testing
