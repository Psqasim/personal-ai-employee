# Phase 3 Testing Guide: Cloud Agent Deployment

**Feature**: Platinum Tier - Phase 3 (Cloud Agent + PM2 + Email Execution)
**Date**: 2026-02-16
**Prerequisites**: Oracle Cloud VM setup complete, deployment scripts ready

---

## Overview

Phase 3 implements:
1. ✅ Oracle Cloud VM with Ubuntu 22.04
2. ✅ Cloud Agent orchestrator (email drafting)
3. ✅ PM2 process management
4. ✅ Git sync (60s batched commits)
5. ✅ Email draft generation and execution

**Test Scope**: Verify Cloud Agent can draft emails and sync to Git.

---

## Test Environment

### Local Machine (Your Laptop)
- **OS**: Linux/macOS/Windows WSL
- **Git**: Configured with SSH access to GitHub
- **Python**: 3.11+
- **Vault**: Local vault synced with Git remote

### Cloud VM (Oracle Cloud)
- **Instance**: VM.Standard.A1.Flex (4 OCPU, 24GB RAM)
- **OS**: Ubuntu 22.04 LTS (ARM64)
- **IP**: 129.80.x.x (replace with your VM IP)
- **PM2**: Installed and configured

---

## Pre-Test Checklist

- [ ] Oracle Cloud VM provisioned and SSH accessible
- [ ] Git remote repository created (private)
- [ ] SSH keys added to GitHub (both Local and Cloud)
- [ ] `.env.cloud` configured on Cloud VM
- [ ] `.env.local` configured on Local machine
- [ ] `requirements.txt` dependencies installed (both sides)
- [ ] PM2 installed on Cloud VM
- [ ] Vault structure exists (Inbox/, Pending_Approval/, Done/, etc.)

---

## Test 1: Cloud Agent Initialization

**Objective**: Verify Cloud Agent starts without errors

### Steps

1. **SSH into Cloud VM**:
   ```bash
   ssh ubuntu@129.80.x.x
   cd /opt/personal-ai-employee
   ```

2. **Check .env.cloud**:
   ```bash
   cat .env.cloud | grep -E "VAULT_PATH|CLAUDE_API_KEY|GIT_REMOTE_URL"
   ```

   **Expected**: All three variables set

3. **Test orchestrator manually**:
   ```bash
   source venv/bin/activate
   python cloud_agent/src/orchestrator.py
   ```

   **Expected output**:
   ```
   2026-02-16 10:00:00 - [CLOUD-ORCH] - INFO - Cloud Orchestrator initialized
   2026-02-16 10:00:00 - [CLOUD-ORCH] - INFO - 🚀 Cloud Orchestrator started
   ```

4. **Press `Ctrl+C`** to stop

5. **Check logs**:
   ```bash
   # No errors in output
   ```

**Pass Criteria**:
- ✅ Orchestrator starts without errors
- ✅ Environment validation passes
- ✅ Git manager initializes successfully

---

## Test 2: Git Sync Service

**Objective**: Verify Git sync commits and pushes changes

### Steps

1. **Start git_sync manually**:
   ```bash
   cd /opt/personal-ai-employee
   source venv/bin/activate
   python cloud_agent/src/git_sync.py &
   ```

   **Expected output**:
   ```
   2026-02-16 10:05:00 - [CLOUD-GIT] - INFO - Git manager initialized: git@github.com:user/vault.git
   2026-02-16 10:05:00 - [CLOUD-GIT] - INFO - 🚀 Cloud Git Sync started (interval: 60s)
   ```

2. **Create a test file**:
   ```bash
   echo "# Test file from Cloud Agent" > vault/Inbox/test_cloud_sync.md
   ```

3. **Wait 65 seconds** (60s interval + processing time)

4. **Check Git log**:
   ```bash
   cd vault
   git log -1
   ```

   **Expected**:
   ```
   commit abc123def456...
   Author: Cloud Agent <cloud-agent@oracle-vm>
   Date:   ...

       1 file updated
   ```

5. **Verify push to remote**:
   ```bash
   git status
   ```

   **Expected**: `Your branch is up to date with 'origin/main'`

6. **Stop git_sync**:
   ```bash
   jobs  # Note job number (e.g., [1])
   kill %1
   ```

**Pass Criteria**:
- ✅ Git sync commits changes automatically
- ✅ Commit message summarizes changes
- ✅ Push to remote succeeds
- ✅ No errors in logs

---

## Test 3: PM2 Process Management

**Objective**: Verify PM2 starts and manages Cloud Agent processes

### Steps

1. **Start Cloud Agent with PM2**:
   ```bash
   cd /opt/personal-ai-employee
   pm2 start ecosystem.config.js
   ```

   **Expected output**:
   ```
   [PM2] Starting /opt/personal-ai-employee/cloud_agent/src/orchestrator.py in fork mode
   [PM2] Done.
   ```

2. **List processes**:
   ```bash
   pm2 list
   ```

   **Expected**:
   ```
   ┌─────┬──────────────────────┬─────────┬─────────┬──────────┐
   │ id  │ name                 │ status  │ ↺       │ cpu      │
   ├─────┼──────────────────────┼─────────┼─────────┼──────────┤
   │ 0   │ cloud_orchestrator   │ online  │ 0       │ 0.2%     │
   │ 1   │ git_sync_cloud       │ online  │ 0       │ 0.1%     │
   └─────┴──────────────────────┴─────────┴─────────┴──────────┘
   ```

3. **View logs**:
   ```bash
   pm2 logs --lines 20
   ```

   **Expected**: Logs from both processes, no errors

4. **Restart single process**:
   ```bash
   pm2 restart cloud_orchestrator
   ```

   **Expected**: Process restarts, status remains `online`

5. **Test auto-restart on crash**:
   ```bash
   pm2 delete cloud_orchestrator
   pm2 start ecosystem.config.js --only cloud_orchestrator
   pm2 list  # Should show online
   ```

6. **Save PM2 state**:
   ```bash
   pm2 save
   ```

**Pass Criteria**:
- ✅ Both processes start successfully
- ✅ `pm2 list` shows status `online`
- ✅ Logs show no errors
- ✅ Processes restart after crash
- ✅ PM2 state saved for boot persistence

---

## Test 4: Email Draft Generation

**Objective**: Verify Cloud Agent drafts email replies

### Steps

1. **Ensure Cloud Agent running**:
   ```bash
   pm2 list
   # cloud_orchestrator should be online
   ```

2. **Create test email in Inbox**:
   ```bash
   cat > vault/Inbox/EMAIL_test_001.md <<'EOF'
   ---
   email_id: test_001
   from: john.doe@example.com
   subject: Meeting Request - Q1 Planning
   priority: High
   received: 2026-02-16T10:00:00Z
   ---

   Hi there,

   Could we schedule a meeting next week to discuss Q1 planning?
   I'm available Tuesday or Wednesday afternoon.

   Best regards,
   John Doe
   EOF
   ```

3. **Wait 5 minutes** (orchestrator cycle: 300s)

4. **Check Pending_Approval folder**:
   ```bash
   ls -la vault/Pending_Approval/Email/
   ```

   **Expected**: New file `EMAIL_DRAFT_test_001.md`

5. **Verify draft content**:
   ```bash
   cat vault/Pending_Approval/Email/EMAIL_DRAFT_test_001.md
   ```

   **Expected**:
   - YAML frontmatter with `draft_id`, `to`, `subject`, `status: pending`
   - Draft body with professional reply
   - Appropriate greeting and signature

6. **Check Dashboard update**:
   ```bash
   tail -20 vault/Dashboard.md
   ```

   **Expected**: Entry under `## Updates` section mentioning email draft

7. **Check API usage log**:
   ```bash
   cat vault/Logs/API_Usage/$(date +%Y-%m-%d).md
   ```

   **Expected**: Entry for `email_draft` task type

8. **Verify Git sync**:
   ```bash
   cd vault
   git log -1
   ```

   **Expected**: Commit with message `1 email draft`

**Pass Criteria**:
- ✅ Email draft created in Pending_Approval/Email/
- ✅ Draft has valid YAML frontmatter
- ✅ Draft body is professional and relevant
- ✅ Dashboard updated with draft notification
- ✅ API usage logged
- ✅ Changes committed and pushed to Git

---

## Test 5: End-to-End Email Workflow

**Objective**: Full workflow from email arrival to draft sync

### Steps

1. **Simulate email arrival** (Cloud VM):
   ```bash
   cat > vault/Inbox/EMAIL_urgent_002.md <<'EOF'
   ---
   email_id: urgent_002
   from: alice.smith@client.com
   subject: [URGENT] Invoice Payment Delay
   priority: High
   received: 2026-02-16T14:00:00Z
   ---

   Hi,

   We haven't received the invoice from last month yet.
   This is delaying our payment. Could you please send it ASAP?

   Thanks,
   Alice
   EOF
   ```

2. **Wait 5 minutes** for orchestrator cycle

3. **Check draft created** (Cloud VM):
   ```bash
   ls vault/Pending_Approval/Email/EMAIL_DRAFT_urgent_002.md
   ```

4. **Wait 60 seconds** for Git sync

5. **Pull changes on Local machine**:
   ```bash
   # On Local machine
   cd ~/personal-ai-employee/vault
   git pull origin main
   ```

6. **Verify draft arrived**:
   ```bash
   ls Pending_Approval/Email/EMAIL_DRAFT_urgent_002.md
   cat Pending_Approval/Email/EMAIL_DRAFT_urgent_002.md
   ```

7. **Move to Approved** (simulate dashboard approval):
   ```bash
   mkdir -p Approved/Email
   mv Pending_Approval/Email/EMAIL_DRAFT_urgent_002.md Approved/Email/
   ```

8. **Commit and push**:
   ```bash
   git add .
   git commit -m "Local: Approved email draft urgent_002"
   git push origin main
   ```

9. **Verify sync on Cloud VM**:
   ```bash
   # SSH to Cloud VM
   cd /opt/personal-ai-employee/vault
   git pull origin main
   ls Approved/Email/EMAIL_DRAFT_urgent_002.md
   ```

**Pass Criteria**:
- ✅ Email processed on Cloud
- ✅ Draft created automatically
- ✅ Draft synced to Local via Git
- ✅ Local can approve (move file)
- ✅ Approval synced back to Cloud
- ✅ Full round-trip <10 minutes

---

## Test 6: PM2 Startup on Boot

**Objective**: Verify processes auto-start after VM reboot

### Steps

1. **Enable PM2 startup**:
   ```bash
   pm2 startup systemd
   # Follow the command shown (sudo ...)
   pm2 save
   ```

2. **Reboot VM**:
   ```bash
   sudo reboot
   ```

3. **Wait 2 minutes**, then SSH back in

4. **Check PM2 processes**:
   ```bash
   pm2 list
   ```

   **Expected**: Both processes online

5. **Check logs**:
   ```bash
   pm2 logs --lines 10
   ```

   **Expected**: Processes started successfully after boot

**Pass Criteria**:
- ✅ PM2 auto-starts on boot
- ✅ All processes online after reboot
- ✅ No manual intervention required

---

## Troubleshooting

### Issue: Cloud Orchestrator fails to start

**Symptoms**:
```
[CLOUD-ORCH] - ERROR - Environment validation failed
```

**Fix**:
1. Check `.env.cloud` exists and has all required variables
2. Verify `VAULT_PATH` points to valid directory
3. Check `CLAUDE_API_KEY` is valid (starts with `sk-ant-`)
4. Run: `python cloud_agent/src/orchestrator.py` for detailed error

---

### Issue: Git sync push fails

**Symptoms**:
```
[CLOUD-GIT] - ERROR - Push failed after retries
```

**Fix**:
1. Test SSH connection: `ssh -T git@github.com`
2. Check SSH key added to ssh-agent: `ssh-add -l`
3. Verify Git remote accessible: `git remote -v`
4. Check GitHub SSH keys in Settings → SSH and GPG keys

---

### Issue: Email drafts not created

**Symptoms**: No files in `Pending_Approval/Email/` after 5 minutes

**Fix**:
1. Check orchestrator logs: `pm2 logs cloud_orchestrator`
2. Verify `Inbox/` has EMAIL_*.md files
3. Check Claude API key is valid in `.env.cloud`
4. Test draft generator manually:
   ```bash
   python -c "from agent_skills.draft_generator import generate_email_draft; print('OK')"
   ```

---

### Issue: PM2 processes crash loop

**Symptoms**: `pm2 list` shows `errored` status, high restart count

**Fix**:
1. View error logs: `pm2 logs cloud_orchestrator --err`
2. Common causes:
   - Missing `.env.cloud`
   - Invalid vault path
   - Python import errors
3. Stop all: `pm2 delete all`
4. Fix issue, then restart: `pm2 start ecosystem.config.js`

---

## Success Criteria

### Phase 3 Complete ✅

- [x] Oracle Cloud VM provisioned (Ubuntu 22.04, 4 OCPU, 24GB RAM)
- [x] Cloud Agent orchestrator running (PM2)
- [x] Git sync operational (60s batched commits)
- [x] Email drafts generated automatically
- [x] Drafts synced to Git remote
- [x] PM2 auto-starts on boot
- [x] No errors in logs for 1 hour continuous operation

### Performance Benchmarks

- **Email draft generation**: <15 seconds from inbox to draft
- **Git sync latency**: <10 seconds per cycle
- **PM2 restart time**: <5 seconds
- **Full email workflow**: <10 minutes (inbox → draft → sync → approve → sync)

---

## Next Steps

1. **Phase 4**: Setup Local Agent and Next.js Dashboard
2. **Phase 5**: Implement WhatsApp notifications
3. **Phase 6**: Deploy Odoo Community on Cloud VM
4. **Integration Testing**: Full dual-agent workflow (Cloud drafts, Local approves, Email sends)

---

## Test Report Template

```markdown
# Phase 3 Test Report

**Date**: YYYY-MM-DD
**Tester**: [Your Name]
**Environment**: Oracle Cloud VM + Local Machine

## Test Results

| Test | Status | Notes |
|------|--------|-------|
| Cloud Agent Init | ✅ PASS | |
| Git Sync | ✅ PASS | |
| PM2 Management | ✅ PASS | |
| Email Draft Gen | ✅ PASS | |
| End-to-End Flow | ✅ PASS | |
| PM2 Boot Startup | ✅ PASS | |

## Issues Found

1. [Issue description if any]
   - **Severity**: Low/Medium/High
   - **Resolution**: [How it was fixed]

## Performance Metrics

- Email draft latency: X seconds
- Git sync cycle time: X seconds
- PM2 restart time: X seconds

## Conclusion

Phase 3 testing: ✅ COMPLETE / ⚠️ PARTIAL / ❌ FAILED

Ready for Phase 4: YES / NO

---

**Sign-off**: [Your Name] | [Date]
```

---

**Phase 3 testing guide complete. Follow tests sequentially for systematic validation.**
