# Phase 1 Testing Guide - Platinum Tier Foundation

**Feature**: 003-platinum-tier | **Phase**: 1 (Setup + Git Vault Sync)
**Status**: Implementation in progress (T001-T030)
**Date**: 2026-02-15

---

## Completed Tasks (T001-T018)

### ✅ Phase 1: Setup (T001-T008)
- **T001**: Dual-agent project structure created
- **T002**: Python dependencies (requirements.txt with GitPython, bcrypt, psutil, pytest)
- **T003**: Next.js 16 installed (TypeScript, Tailwind, App Router)
- **T004**: ESLint + Prettier configured
- **T005**: pytest infrastructure (pytest.ini, markers for integration/e2e)
- **T006**: .env.cloud.example + .env.local.example (security partition templates)
- **T007**: .gitignore updated (*.session, .env.cloud, credentials.json, vault/.secrets/)
- **T008**: Git pre-commit hook installed (blocks sensitive files)

### ✅ Phase 2: Foundational (T009-T016)
- **T009**: CloudAgent entity (agent_skills/entities.py)
- **T010**: LocalAgent entity (agent_skills/entities.py)
- **T011**: GitSyncState entity (agent_skills/entities.py)
- **T012**: git_manager.py (commit, push, pull, conflict detection, retry logic)
- **T013**: claim_manager.py (claim-by-move atomic file operations)
- **T014**: api_usage_tracker.py (Claude API cost logging)
- **T015**: Vault subdirectories (Logs/Cloud/, Logs/Local/, Logs/API_Usage/, Logs/MCP_Health/)
- **T016**: env_validator.py (Cloud vs Local security partition enforcement)

### ✅ Phase 3: User Story 4 - Git Sync (Partial: T017-T018)
- **T017**: Cloud git_sync.py (60s batched commits + push with retry)
- **T018**: Local git_sync.py (60s pull + auto-resolve Dashboard.md conflicts)

---

## Critical Verification Steps

### 1. Git Sync Bidirectional Test

**Objective**: Verify Cloud pushes and Local pulls successfully without data loss

**Steps**:
1. **Setup**:
   ```bash
   # On Cloud VM
   cd /opt/personal-ai-employee
   python cloud_agent/src/git_sync.py &

   # On Local machine
   cd ~/personal-ai-employee
   python local_agent/src/git_sync.py &
   ```

2. **Cloud → Local Test**:
   - Cloud: Create file `vault/Inbox/test_cloud_push.md`
   - Wait 60s for Cloud to commit + push
   - Verify Cloud logs show: "✅ Sync complete"
   - Wait 60s for Local to pull
   - Local: Verify `vault/Inbox/test_cloud_push.md` exists

3. **Local → Cloud Test**:
   - Local: Create file `vault/Inbox/test_local_push.md`
   - Local: `git add . && git commit -m "Local: test" && git push`
   - Wait 60s for Cloud to pull
   - Cloud: Verify `vault/Inbox/test_local_push.md` exists

**Success Criteria**:
- ✅ Cloud commits appear in `git log` with "Cloud:" prefix
- ✅ Local pulls complete without errors
- ✅ Both agents see each other's changes within 120s
- ✅ No file corruption or merge conflicts

**Failure Modes**:
- ❌ Push fails after 3 retries → Check network, SSH keys
- ❌ Pull shows conflicts → Check conflict resolution logs in `vault/Logs/Local/git_conflicts.md`
- ❌ Files not syncing → Check `.gitignore` doesn't block test files

---

### 2. Conflict Resolution Test

**Objective**: Verify Dashboard.md conflicts auto-resolve (accept Cloud /Updates/, keep Local main)

**Steps**:
1. **Create conflict scenario**:
   - Local: Edit `vault/Dashboard.md` (add task to table)
   - Local: Commit but DON'T push: `git add . && git commit -m "Local: dashboard update"`
   - Cloud: Edit `vault/Dashboard.md` (add to /## Updates/)
   - Cloud: Wait 60s for Cloud to commit + push
   - Local: Wait 60s for Local to pull → CONFLICT expected

2. **Verify auto-resolution**:
   - Check Local logs: Should show "⚠️ Merge conflicts detected: ['Dashboard.md']"
   - Check Local logs: Should show "✅ Dashboard.md conflict auto-resolved"
   - Check `vault/Logs/Local/git_conflicts.md`: Should log resolution
   - Verify `vault/Dashboard.md`: Contains BOTH Local table changes AND Cloud /Updates/

**Success Criteria**:
- ✅ Dashboard.md conflict auto-resolved without manual intervention
- ✅ Cloud's /## Updates/ section preserved
- ✅ Local's main content (task table) preserved
- ✅ Conflict logged to `vault/Logs/Local/git_conflicts.md`

**Failure Modes**:
- ❌ Rebase stuck → Local logs show "Manual conflict resolution required"
- ❌ Data loss → Check git history: `git log --all --oneline Dashboard.md`
- ❌ Infinite conflict loop → Abort rebase, manual merge required

---

### 3. Security Partition Test

**Objective**: Verify Cloud Agent NEVER accesses sensitive credentials

**Steps**:
1. **Cloud environment validation**:
   ```bash
   # On Cloud VM
   python -c "from agent_skills.env_validator import EnvValidator; EnvValidator.validate_cloud_agent()"
   ```
   - Expected: "✅ Cloud Agent environment validated successfully"
   - If fails: Check `.env.cloud` for prohibited variables

2. **Check Cloud .env**:
   ```bash
   # On Cloud VM
   cat .env.cloud | grep -E "SMTP_PASSWORD|WHATSAPP_SESSION_PATH|ODOO_PASSWORD"
   ```
   - Expected: No matches (empty output)
   - If matches found: **SECURITY VIOLATION** - remove immediately

3. **Check Git history for leaks**:
   ```bash
   git log --all -p | grep -E "SMTP_PASSWORD|sk-ant-api" | head -20
   ```
   - Expected: No matches
   - If matches found: **CRITICAL** - rewrite Git history (`git filter-branch`) or rotate credentials

4. **Test pre-commit hook**:
   ```bash
   # Try to commit .env file (should be blocked)
   git add .env.cloud
   git commit -m "Test: should be blocked"
   ```
   - Expected: "🚨 COMMIT BLOCKED - Sensitive files detected!"
   - If commits anyway: Pre-commit hook not installed, run: `cp deployment/git-hooks/pre-commit .git/hooks/`

**Success Criteria**:
- ✅ Cloud .env has NO sensitive credentials (SMTP, WhatsApp session, banking)
- ✅ Pre-commit hook blocks .env, *.session, credentials.json
- ✅ Git history clean (no leaked secrets)
- ✅ .gitignore includes all sensitive patterns

**Failure Modes**:
- ❌ Cloud .env contains SMTP_PASSWORD → **SECURITY RISK** - delete and restart Cloud agent
- ❌ Secrets in Git history → Rotate ALL credentials, rewrite history
- ❌ Pre-commit hook bypassed → Check `.git/hooks/pre-commit` executable

---

### 4. Claim-by-Move Race Condition Test

**Objective**: Verify only ONE agent processes a task (prevents duplicate sends)

**Setup**: Both Cloud and Local running, same task in `/Needs_Action/`

**Steps**:
1. **Create test task**:
   ```bash
   echo "---\ntitle: Test Race Condition\n---\nTest task content" > vault/Needs_Action/RACE_TEST_001.md
   ```

2. **Trigger both agents simultaneously**:
   - Cloud: Claims via `claim_manager.claim_task(RACE_TEST_001.md)`
   - Local: Claims via `claim_manager.claim_task(RACE_TEST_001.md)`
   - **Only ONE should succeed** (first to move file wins)

3. **Verify claim ownership**:
   ```bash
   # Check which agent claimed it
   ls vault/In_Progress/cloud/ | grep RACE_TEST
   ls vault/In_Progress/local/ | grep RACE_TEST
   ```
   - Expected: File exists in ONLY ONE directory (cloud OR local, not both)

**Success Criteria**:
- ✅ Only ONE agent successfully claims task
- ✅ Second agent receives `False` from `claim_task()` (already claimed)
- ✅ No duplicate processing
- ✅ Task ownership clear (file in `/In_Progress/{agent}/`)

**Failure Modes**:
- ❌ Both agents claim same task → **RACE CONDITION BUG** - file copied, not moved
- ❌ Task disappears → Check file permissions, filesystem issues
- ❌ Both agents process task → Check MCP action logs for duplicates

---

### 5. Backward Compatibility Test (Gold Tier)

**Objective**: Verify all Gold tier features still work when `ENABLE_CLOUD_AGENT=false`

**Steps**:
1. **Set Gold tier mode**:
   ```bash
   # In .env (Local)
   TIER=gold
   ENABLE_CLOUD_AGENT=false
   ```

2. **Run Gold tier watchers**:
   ```bash
   python scripts/gmail_watcher.py &
   python scripts/whatsapp_watcher.py &
   python scripts/plan_watcher.py &
   ```

3. **Test Gold success criteria** (SC-G001 through SC-G013):
   - Email draft generation (SC-G002)
   - LinkedIn post generation (SC-G009)
   - WhatsApp draft generation (SC-G016)
   - Plan execution (Ralph Wiggum loop) (SC-G034)
   - CEO Briefing generation (SC-G047)

**Success Criteria**:
- ✅ All Gold tier features functional
- ✅ No errors related to Cloud Agent (should be disabled)
- ✅ Vault sync via Git (manual `git push/pull` still works)
- ✅ No breaking changes to existing scripts

**Failure Modes**:
- ❌ Import errors for Platinum modules → Check `sys.path` in watchers
- ❌ Gold scripts expect Cloud Agent → Refactor to check `ENABLE_CLOUD_AGENT` flag
- ❌ Tests fail → Run `pytest tests/unit/ -m "not platinum"` to verify Gold tests

---

## Integration Test Commands

### Run All Integration Tests
```bash
# Phase 2 tests (foundation)
pytest tests/integration/test_dual_agent_sync.py -v

# Git sync tests
pytest tests/integration/test_git_conflict.py -v

# Claim-by-move tests
pytest tests/integration/test_claim_by_move.py -v

# Full suite
pytest tests/integration/ -v --tb=short
```

### Manual Testing Checklist

- [ ] Git sync bidirectional (Cloud → Local, Local → Cloud)
- [ ] Dashboard.md conflict auto-resolution
- [ ] Security partition (Cloud .env validation)
- [ ] Pre-commit hook blocks sensitive files
- [ ] Claim-by-move prevents race conditions
- [ ] Backward compatibility (Gold tier features work)
- [ ] API usage logging (check `vault/Logs/API_Usage/`)
- [ ] Environment validation (Cloud vs Local)

---

## Known Issues & Workarounds

### Issue 1: SSH Key Authentication Fails
**Symptom**: Git push/pull fails with "Permission denied (publickey)"
**Fix**: Add SSH key to GitHub:
```bash
cat ~/.ssh/id_ed25519.pub  # Copy output
# GitHub → Settings → SSH Keys → New SSH key → Paste
ssh -T git@github.com  # Test connection
```

### Issue 2: Dashboard.md Conflict Loop
**Symptom**: Same conflict appears every sync cycle
**Fix**: Manual merge required:
```bash
git checkout --ours Dashboard.md  # Keep Local version
git add Dashboard.md
git rebase --continue
```

### Issue 3: .gitignore Not Blocking Files
**Symptom**: Sensitive files committed despite .gitignore
**Fix**: Files already tracked, must untrack:
```bash
git rm --cached .env.cloud  # Remove from Git, keep local file
git commit -m "Untrack .env.cloud"
```

---

## Next Steps (T019-T030)

**Remaining tasks for Phase 1 completion**:
- T019-T024: Complete Git sync implementation (conflict resolution, retry, state persistence, failure alerts)
- T025-T027: Integration tests (dual-agent sync, claim-by-move, conflict resolution)
- T028-T030: Cloud/Local orchestrator skeletons + environment validation

**After Phase 1**:
- Run full test suite: `pytest tests/integration/ -v`
- Deploy to Cloud VM (Oracle Cloud)
- Monitor for 24 hours
- Proceed to Phase 2 (Next.js Dashboard - US2)

---

**Testing Status**: Foundation ready for Git sync verification
**Blocker**: None (all prerequisites complete)
**Next**: Complete T019-T030 + run integration tests
