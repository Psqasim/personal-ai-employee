# Email Setup Guide (Gmail API + SMTP)

**Gold Tier Feature**: Email draft generation with approval and auto-send via Gmail SMTP

## Prerequisites
- Gmail account with 2-Step Verification enabled
- Python 3.11+ installed
- Personal AI Employee Gold tier deployed

---

## Step 1: Enable 2-Step Verification

1. Go to **Google Account Security**: https://myaccount.google.com/security
2. Scroll to "Signing in to Google"
3. Click **2-Step Verification** → Follow setup instructions
4. Choose your preferred 2FA method (phone, authenticator app, etc.)

---

## Step 2: Generate Gmail App Password

1. Go to **App Passwords**: https://myaccount.google.com/apppasswords
   - If you don't see this option, ensure 2-Step Verification is enabled
2. Click **Select app** → Choose "Mail"
3. Click **Select device** → Choose "Other (Custom name)"
4. Enter name: **Personal AI Employee Gold**
5. Click **Generate**
6. Google will display a 16-character password (e.g., `abcd efgh ijkl mnop`)
7. **IMPORTANT**: Copy this password immediately - you can't view it again!

---

## Step 3: Configure Environment Variables

Add to your `.env` file:

```bash
# Email MCP (SMTP Send)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop  # App password from Step 2 (remove spaces)
```

**Example**:
```bash
SMTP_USER=john.doe@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
```

---

## Step 4: Configure MCP Server

Add to `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/personal-ai-employee/mcp_servers/email_mcp/server.py"],
      "env": {
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "your-email@gmail.com",
        "SMTP_PASSWORD": "your-app-password"
      }
    }
  }
}
```

**Replace**:
- `/absolute/path/to/personal-ai-employee` → Your actual repo path
- `your-email@gmail.com` → Your Gmail address
- `your-app-password` → App password from Step 2

---

## Step 5: Test Email MCP

Test the MCP server directly:

```bash
cd /path/to/personal-ai-employee

# Test tools/list
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python mcp_servers/email_mcp/server.py

# Expected output:
# {"jsonrpc": "2.0", "id": 1, "result": {"tools": [{"name": "send_email", ...}]}}

# Test send_email (sends real email!)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"send_email","arguments":{"to":"your-email@gmail.com","subject":"Test from Email MCP","body":"This is a test email from Personal AI Employee Gold tier."}}}' | python mcp_servers/email_mcp/server.py

# Expected output:
# {"jsonrpc": "2.0", "id": 1, "result": {"message_id": "msg_1707849600", "sent_at": "2026-02-14T..."}}
```

**Check your Gmail inbox** → You should receive the test email.

---

## Step 6: Verify Gold Tier Integration

1. Open `vault/Dashboard.md` in Obsidian
2. Check **Gold Tier Status** section:
   ```markdown
   **MCP Servers**:
   - email-mcp: ✓ Active
   ```

If it shows `✗ Inactive`, check:
- `.env` file has correct `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`
- `mcp.json` has correct absolute paths
- No typos in app password

---

## Troubleshooting

### Error: "SMTP_AUTH_FAILED"

**Cause**: Invalid app password or 2-Step Verification not enabled

**Solution**:
1. Verify 2-Step Verification is ON: https://myaccount.google.com/security
2. Regenerate app password: https://myaccount.google.com/apppasswords
3. Copy password WITHOUT spaces (16 chars total)
4. Update `.env` and `mcp.json` with new password
5. Restart Gold watchers

### Error: "SMTP_ERROR: Connection refused"

**Cause**: Firewall blocking SMTP port 587

**Solution**:
1. Check firewall settings (allow outbound SMTP)
2. Try alternate port: `SMTP_PORT=465` (SSL instead of TLS)
3. Verify network connectivity: `telnet smtp.gmail.com 587`

### Error: "Parse error" when testing MCP

**Cause**: Invalid JSON in test command

**Solution**:
- Ensure JSON is properly escaped (use single quotes around full JSON string)
- Remove newlines from JSON
- Validate JSON with online validator

---

## Custom SMTP Server (Optional)

If not using Gmail, update `.env`:

```bash
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=your-username
SMTP_PASSWORD=your-password
```

Common providers:
- **Outlook/Hotmail**: `smtp-mail.outlook.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587`
- **Custom server**: Check your provider's SMTP settings

---

## Security Best Practices

1. **Never commit** `.env` or `mcp.json` to version control
2. **Rotate app passwords** every 90 days
3. **Use separate app password** for each application
4. **Monitor Gmail security**: https://myaccount.google.com/security
5. **Review sent emails** regularly in `vault/Logs/MCP_Actions/`

---

## Next Steps

Once email MCP is working:
1. ✓ Email drafts will be generated in `vault/Pending_Approval/Email/`
2. ✓ Approve by moving to `vault/Approved/Email/`
3. ✓ Email MCP auto-sends within 30 seconds
4. ✓ All actions logged to `vault/Logs/MCP_Actions/`

**Related Guides**:
- WhatsApp Setup: `docs/gold/whatsapp-setup.md`
- LinkedIn Setup: `docs/gold/linkedin-setup.md`
- MCP Configuration: `docs/gold/mcp-setup.md`
