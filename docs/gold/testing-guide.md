# Gold Tier Testing Guide

**Purpose**: End-to-end testing for Gold tier MVP (Tasks T001-T030)

This guide walks through testing each user story independently to verify the complete Gold tier implementation.

---

## Prerequisites

Before testing, ensure:
- ✅ All Gold tier dependencies installed: `pip install -r requirements-gold.txt`
- ✅ Playwright Chromium installed: `playwright install chromium`
- ✅ `.env` configured with Gold tier variables
- ✅ MCP servers configured in `~/.config/claude-code/mcp.json`
- ✅ WhatsApp authenticated (if testing US3): `python scripts/whatsapp_qr_setup.py`
- ✅ Gmail app password generated (if testing US1): See `docs/gold/email-setup.md`
- ✅ LinkedIn OAuth token obtained (if testing US2): See `docs/gold/linkedin-setup.md`

---

## Test 1: Email Draft Generation & Send (User Story 1)

**Goal**: AI drafts email replies, user approves, email MCP sends

### Steps

1. **Create test email task**:
   ```bash
   cat > vault/Inbox/EMAIL_test_001.md <<EOF
   ---
   type: email
   from: testclient@example.com
   subject: Project Proposal Review
   priority: High
   status: new
   ---

   # Test Email

   Can you review the attached project proposal and provide feedback by Friday?
   EOF
   ```

2. **Start Gmail watcher**:
   ```bash
   python scripts/gmail_watcher.py
   ```

3. **Wait 15 seconds** → Draft should appear in `vault/Pending_Approval/Email/`

4. **Verify draft**:
   - Open `vault/Pending_Approval/Email/EMAIL_DRAFT_*.md` in Obsidian
   - Check YAML frontmatter (to, subject, draft_body)
   - Review AI-generated email content

5. **Approve draft**:
   - In Obsidian, drag file from `Pending_Approval/Email/` to `Approved/Email/`

6. **Start approval watcher** (in separate terminal):
   ```bash
   python scripts/run_approval_watcher.py
   ```

7. **Wait 30 seconds** → Email MCP should send email

8. **Verify**:
   - Check your Gmail sent folder for sent email
   - Check `vault/Logs/MCP_Actions/YYYY-MM-DD.md` for log entry
   - File should be moved to `vault/Done/`

### Expected Results

- ✅ Draft generated within 15s
- ✅ Draft validation passed (valid email, <5000 chars)
- ✅ Email sent successfully via SMTP
- ✅ Action logged with `human_approved=true`
- ✅ File moved to `vault/Done/`

---

## Test 2: LinkedIn Post Generation & Publish (User Story 2)

**Goal**: AI generates LinkedIn post, user approves, LinkedIn MCP publishes

### Steps

1. **Ensure Company_Handbook.md has Business Goals section**:
   ```bash
   echo "## Business Goals\nPromote AI automation services and thought leadership" >> vault/Company_Handbook.md
   ```

2. **Generate LinkedIn draft (force mode)**:
   ```bash
   python scripts/linkedin_generator.py --force
   ```

3. **Verify draft**:
   - Check `vault/Pending_Approval/LinkedIn/LINKEDIN_POST_*.md`
   - Review post content (should have hook, value, CTA structure)
   - Check character count ≤ 3000

4. **Approve draft**:
   - Drag file to `vault/Approved/LinkedIn/`

5. **Wait 30 seconds** (approval watcher should be running from Test 1)

6. **Verify**:
   - Check your LinkedIn profile feed for new post
   - Check `vault/Logs/MCP_Actions/` for log entry
   - File moved to `vault/Done/`

### Expected Results

- ✅ Post generated with business goals alignment
- ✅ Character count ≤ 3000 (auto-truncated if needed)
- ✅ Post published to LinkedIn successfully
- ✅ Action logged
- ✅ Deduplication works (running `--force` again creates retry file, not duplicate)

---

## Test 3: WhatsApp Draft Generation & Send (User Story 3)

**Goal**: AI detects important WhatsApp messages, drafts replies, auto-sends after approval

### Steps

1. **Ensure WhatsApp session authenticated**:
   ```bash
   # If not already done
   python scripts/whatsapp_qr_setup.py
   ```

2. **Create test WhatsApp message task**:
   ```bash
   cat > vault/Inbox/WHATSAPP_test_001.md <<EOF
   ---
   type: whatsapp
   from: John Doe
   chat_id: john_doe_chat
   message_preview: "Urgent: Need payment confirmation for invoice #1234 by EOD"
   priority: High
   timestamp: $(date -Iseconds)
   status: new
   ---

   # WhatsApp Message

   Urgent: Need payment confirmation for invoice #1234 by EOD
   EOF
   ```

3. **Start WhatsApp watcher**:
   ```bash
   python scripts/whatsapp_watcher.py
   ```

4. **Wait 30 seconds** → Draft should appear in `vault/Pending_Approval/WhatsApp/`

5. **Verify draft**:
   - Check `vault/Pending_Approval/WhatsApp/WHATSAPP_DRAFT_*.md`
   - Verify keywords matched (should include "urgent", "payment")
   - Check draft_body ≤ 500 chars

6. **Approve draft**:
   - Drag file to `vault/Approved/WhatsApp/`

7. **Wait 30 seconds** (approval watcher running)

8. **Verify**:
   - Check WhatsApp Web for sent message (to contact "John Doe")
   - Check `vault/Logs/MCP_Actions/` for log entry
   - File moved to `vault/Done/`

### Expected Results

- ✅ Keywords detected correctly ("urgent", "payment")
- ✅ Priority set to "High" based on keywords
- ✅ Draft generated (brief, professional, <500 chars)
- ✅ Message sent via Playwright automation
- ✅ Action logged

---

## Test 4: Foundational Infrastructure

**Goal**: Verify core Gold tier modules work correctly

### Test 4.1: MCP Client

```bash
cd /path/to/personal-ai-employee

# Test email MCP
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python mcp_servers/email_mcp/server.py

# Expected output: {"jsonrpc": "2.0", "id": 1, "result": {"tools": [...]}}
```

### Test 4.2: Draft Generator

```python
from agent_skills.draft_generator import generate_email_draft

test_email = {
    "email_id": "test_001",
    "from": "test@example.com",
    "subject": "Test Subject",
    "body": "Test body content",
    "priority": "High"
}

draft = generate_email_draft(test_email)
print(f"Draft generated: {draft['draft_id']}")
print(f"Draft body: {draft['draft_body'][:100]}...")
```

### Test 4.3: Vault Parser

```python
from agent_skills.vault_parser import parse_draft_file

draft = parse_draft_file("vault/Pending_Approval/Email/EMAIL_DRAFT_test.md", "email")
print(f"Parsed draft: {draft.draft_id}")
print(f"To: {draft.to}")
print(f"Subject: {draft.subject}")
```

### Test 4.4: Dashboard Updater

```python
from agent_skills.dashboard_updater import update_dashboard

success = update_dashboard(
    vault_path="vault",
    new_files=[("test_task.md", "Inbox")],
    ai_results=[("High", "Work")]
)
print(f"Dashboard updated: {success}")
```

---

## Test 5: Validation & Error Handling

### Test 5.1: Invalid Email Draft

Create draft with invalid recipient:
```python
from agent_skills.draft_generator import generate_email_draft

test_email = {
    "email_id": "test_invalid",
    "from": "invalid-email-format",  # Missing @ and domain
    "subject": "Test",
    "body": "Test",
    "priority": "High"
}

draft = generate_email_draft(test_email)
# Validation should fail in gmail_watcher.py
```

### Test 5.2: LinkedIn Character Limit

Generate very long LinkedIn post:
```bash
python scripts/linkedin_generator.py --force
# Check that post is auto-truncated to 3000 chars
```

### Test 5.3: WhatsApp Session Expiry

Simulate session expiry:
```bash
# Delete session file
rm $WHATSAPP_SESSION_PATH

# Run watcher
python scripts/whatsapp_watcher.py
# Should create vault/Needs_Action/whatsapp_session_expired.md
```

---

## Test 6: Approval Gate Enforcement (T017)

**Goal**: Verify NO MCP action executes without human approval

### Steps

1. **Create draft manually** (bypass watcher):
   ```bash
   cp vault/Pending_Approval/Email/EMAIL_DRAFT_test.md vault/Pending_Approval/Email/EMAIL_DRAFT_unauthorized.md
   ```

2. **Start approval watcher**:
   ```bash
   python scripts/run_approval_watcher.py
   ```

3. **DO NOT approve** (leave in Pending_Approval)

4. **Wait 5 minutes**

5. **Verify**:
   - No email sent (check Gmail sent folder)
   - No MCP action logged in `vault/Logs/MCP_Actions/`
   - File remains in `vault/Pending_Approval/Email/`

### Expected Results

- ✅ No unauthorized MCP invocations
- ✅ All logged actions have `human_approved=true`
- ✅ Approval file path present in every MCP log

---

## Test 7: Rejected Draft Handling (T025)

**Goal**: Verify rejected drafts create retry files

### Steps

1. **Generate LinkedIn draft**:
   ```bash
   python scripts/linkedin_generator.py --force
   ```

2. **Reject draft**:
   - Drag `LINKEDIN_POST_*.md` to `vault/Rejected/`

3. **Wait 1 hour** (or run rejection handler manually):
   ```python
   from scripts.linkedin_generator import handle_rejected_drafts
   handle_rejected_drafts("vault")
   ```

4. **Verify**:
   - Check `vault/Needs_Action/LINKEDIN_POST_*_retry.md` exists
   - File contains instructions for regeneration

### Expected Results

- ✅ Retry file created in `vault/Needs_Action/`
- ✅ Instructions clear for next steps
- ✅ Original draft preserved in `vault/Rejected/`

---

## Integration Test Summary

Run all tests in sequence:

```bash
# 1. Start all watchers
python scripts/gmail_watcher.py &
python scripts/whatsapp_watcher.py &
python scripts/run_approval_watcher.py &

# 2. Create test tasks
# (Use commands from Test 1-3)

# 3. Wait for drafts to generate (15-30s)

# 4. Approve all drafts
# (Move files in Obsidian)

# 5. Wait for MCP actions (30s)

# 6. Verify all actions logged and completed

# 7. Stop watchers
pkill -f gmail_watcher
pkill -f whatsapp_watcher
pkill -f approval_watcher
```

---

## Troubleshooting

### Watchers not detecting files

- Check `VAULT_PATH` environment variable
- Verify folders exist: `ls -la vault/Pending_Approval/`
- Check watcher logs for errors

### MCP actions failing

- Test MCP server directly (see Test 4.1)
- Check `.env` credentials are correct
- Verify `mcp.json` has absolute paths
- Check MCP server logs in terminal

### Drafts not generated

- Check Claude API key in `.env`: `echo $CLAUDE_API_KEY`
- Verify AI analysis enabled: `ENABLE_AI_ANALYSIS=true`
- Check draft_generator.py logs for errors

### Dashboard not updating

- Check vault_path is correct
- Verify Dashboard.md exists
- Check dashboard_updater.py logs

---

## Success Criteria (T001-T030 Complete)

✅ **All foundational modules working**:
- mcp_client, vault_parser, dashboard_updater, draft_generator, approval_watcher, plan_executor

✅ **All 3 MCP servers functional**:
- email-mcp, whatsapp-mcp, linkedin-mcp

✅ **All 3 user story workflows complete**:
- US1: Email draft → approve → send
- US2: LinkedIn draft → approve → post
- US3: WhatsApp draft → approve → send

✅ **All validation and safety checks passing**:
- Email format validation
- Character limit enforcement
- Approval gate enforcement (human_approved=true)
- Rejected draft handling

✅ **All setup documentation complete**:
- email-setup.md, whatsapp-setup.md, linkedin-setup.md, testing-guide.md

---

## Next Steps After T030

Once T001-T030 testing complete:
1. ✅ Commit progress: "Gold tier MVP complete (T001-T030)"
2. Continue with Phase 6: User Story 4 (Multi-Step Plan Execution - Ralph Wiggum loop)
3. Continue with Phase 7: User Story 5 (MCP Multi-Server Integration)
4. Continue with Phase 8: User Story 6 (CEO Briefing)
5. Polish and integration testing (Phase 10)

**Congratulations! Gold Tier MVP (T001-T030) is now functional! 🎉**
