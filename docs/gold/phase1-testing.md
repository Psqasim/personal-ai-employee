# Phase 1 Testing Guide - Gold Tier Core Features

**Phase**: Gold Tier Phase 1 - Core Autonomous Features
**Features**: Ralph Wiggum Loop (T036-T042) + Weekly CEO Briefing (T052-T055)
**Created**: 2026-02-14

---

## Overview

This document provides comprehensive testing procedures for Phase 1 of Gold Tier implementation:

1. **PART A: Ralph Wiggum Loop** - Autonomous multi-step task execution
2. **PART B: Weekly CEO Briefing** - Automated weekly business summaries

---

## Prerequisites

Before testing, ensure:

- ✅ Gold tier dependencies installed: `pip install -r requirements-gold.txt`
- ✅ Vault structure exists: `vault/Inbox/`, `vault/Plans/`, `vault/Pending_Approval/Plans/`, `vault/Approved/Plans/`, `vault/Done/`, `vault/Needs_Action/`, `vault/In_Progress/`, `vault/Briefings/`
- ✅ `.env` configured with `ENABLE_PLAN_EXECUTION=true`, `TIER=gold`
- ✅ MCP servers available (email-mcp, whatsapp-mcp, linkedin-mcp) for plan step execution

---

## PART A: Ralph Wiggum Loop Testing

### Feature Overview

The Ralph Wiggum loop autonomously executes multi-step plans with:
- **Max 10 iterations** before human escalation
- **State persistence** to `vault/In_Progress/{plan_id}/state.md`
- **Dependency checking** before executing each step
- **Retry logic** (3 attempts with exponential backoff)
- **Automatic escalation** to `vault/Needs_Action/` on failure

---

### Test 1: Plan Generation from Multi-Step Task

**Objective**: Verify plan_generator.py detects multi-step keywords and generates Plan.md

**Steps**:

1. Create a test task file in `vault/Inbox/`:

```bash
cat > vault/Inbox/TEST_onboarding_001.md <<'EOF'
---
type: task
priority: High
subject: Onboard new client - Sarah Chen
created_at: 2026-02-14T10:00:00Z
---

# Client Onboarding Task

Onboard new client Sarah Chen:

1. Send welcome email to sarah.chen@example.com with subject "Welcome to our services"
2. Create WhatsApp message to notify team about new client
3. Post LinkedIn announcement about new partnership

Please execute this plan autonomously.
EOF
```

2. Run plan generator in single-scan mode:

```bash
cd /mnt/d/gov\ ai\ code/QUATER\ 4\ part\ 2/hacakthon/personal-ai-employee
python scripts/plan_generator.py --vault vault --once
```

**Expected Results**:

- ✅ Plan file created: `vault/Plans/PLAN_onboard-new-client-sarah-chen_YYYY-MM-DD_HHMMSS.md`
- ✅ Approval request created: `vault/Pending_Approval/Plans/PLAN_*_approval.md`
- ✅ Plan contains 3 steps with correct action_types:
  - Step 1: `action_type: mcp_email`
  - Step 2: `action_type: mcp_whatsapp`
  - Step 3: `action_type: mcp_linkedin`
- ✅ Plan frontmatter has `status: awaiting_approval`

**Validation**:

```bash
# Check plan file exists
ls -la vault/Plans/PLAN_*

# Check approval request exists
ls -la vault/Pending_Approval/Plans/PLAN_*_approval.md

# View plan content
cat vault/Plans/PLAN_*.md
```

---

### Test 2: Plan Approval Workflow

**Objective**: Verify approval file-move triggers plan execution

**Steps**:

1. Move approval file to trigger execution:

```bash
# Find the approval file
APPROVAL_FILE=$(ls vault/Pending_Approval/Plans/PLAN_*_approval.md | head -n 1)

# Move to Approved/ to trigger execution
mkdir -p vault/Approved/Plans
mv "$APPROVAL_FILE" vault/Approved/Plans/
```

2. Manually trigger plan watcher (or wait for automatic polling):

```bash
# Note: T044 (plan_watcher.py) is not implemented in Phase 1
# For now, manually test plan_executor

python -c "
import asyncio
from agent_skills.plan_executor import execute_plan_ralph_wiggum_loop

# Find plan file
import glob
plan_files = glob.glob('vault/Plans/PLAN_*.md')
if plan_files:
    plan_file = plan_files[0]
    plan_id = plan_file.split('/')[-1].replace('.md', '')
    print(f'Executing plan: {plan_id}')
    asyncio.run(execute_plan_ralph_wiggum_loop(plan_id, 'vault'))
"
```

**Expected Results**:

- ✅ Execution state created: `vault/In_Progress/{plan_id}/state.md`
- ✅ State shows `iterations_remaining: 10` initially
- ✅ Plan steps execute sequentially (respecting dependencies)
- ✅ Each step logs to `vault/Logs/MCP_Actions/YYYY-MM-DD.md`
- ✅ On completion, plan moves to `vault/Done/`

**Validation**:

```bash
# Check execution state
cat vault/In_Progress/PLAN_*/state.md

# Check MCP action logs
cat vault/Logs/MCP_Actions/$(date +%Y-%m-%d).md

# Check if plan completed
ls -la vault/Done/PLAN_*.md
```

---

### Test 3: Ralph Wiggum Loop State Persistence

**Objective**: Verify loop can resume from saved state after interruption

**Steps**:

1. Create a plan with 5 steps

2. Start execution, then manually interrupt after step 2 completes

3. Check state file:

```bash
cat vault/In_Progress/PLAN_*/state.md
# Should show: current_step: 3, iterations_remaining: 8
```

4. Resume execution:

```bash
python -c "
import asyncio
from agent_skills.plan_executor import execute_plan_ralph_wiggum_loop

# Resume from state
asyncio.run(execute_plan_ralph_wiggum_loop('PLAN_test_resume', 'vault'))
"
```

**Expected Results**:

- ✅ Execution resumes from step 3 (not step 1)
- ✅ Iterations_remaining decrements correctly
- ✅ No duplicate MCP invocations for completed steps

---

### Test 4: Error Handling & Retry Logic

**Objective**: Verify retry logic with exponential backoff and escalation after max retries

**Steps**:

1. Create a plan with a step that will fail (e.g., email to invalid address)

2. Execute plan

3. Monitor retry behavior

**Expected Results**:

- ✅ Step retries 3 times (wait: 10s, 20s, 40s)
- ✅ After 3 failed retries, step marked as `blocked`
- ✅ Escalation file created: `vault/Needs_Action/plan_blocked_{plan_id}.md`
- ✅ Plan execution stops (does not continue to next step)

**Validation**:

```bash
# Check for escalation file
ls -la vault/Needs_Action/plan_blocked_*.md

# Read escalation details
cat vault/Needs_Action/plan_blocked_*.md
```

---

### Test 5: Max Iteration Escalation

**Objective**: Verify loop exits after 10 iterations and escalates to human

**Steps**:

1. Create a plan with a blocking step (dependency never met)

2. Execute plan

3. Let it run until max iterations

**Expected Results**:

- ✅ Loop exits after 10 iterations (does not run infinitely)
- ✅ Plan status updated to `escalated`
- ✅ Escalation file created: `vault/Needs_Action/plan_escalated_{plan_id}.md`
- ✅ Escalation file includes full iteration history

**Validation**:

```bash
# Check plan status in Plan.md
grep "status:" vault/Plans/PLAN_*.md

# Check escalation file
cat vault/Needs_Action/plan_escalated_*.md
```

---

## PART B: Weekly CEO Briefing Testing

### Feature Overview

The CEO Briefing generator creates weekly executive summaries every Sunday at 23:00 containing:
- **Task completion counts** (from `vault/Done/`)
- **Pending items** (from `vault/Needs_Action/`)
- **API cost summary** (from `vault/Logs/API_Usage/`)
- **Proactive suggestions** (data-based insights)

---

### Test 6: Manual Briefing Generation

**Objective**: Verify briefing generation with --force flag

**Steps**:

1. Create test data in vault (simulate week's activity):

```bash
# Create completed tasks in vault/Done/
mkdir -p vault/Done
cat > vault/Done/EMAIL_test_001.md <<'EOF'
---
subject: Project proposal review
priority: High
completed_at: 2026-02-10T14:30:00Z
---
Completed email task
EOF

cat > vault/Done/WHATSAPP_test_002.md <<'EOF'
---
subject: Client follow-up
priority: Medium
completed_at: 2026-02-12T09:15:00Z
---
Completed WhatsApp task
EOF

# Create pending items in vault/Needs_Action/
mkdir -p vault/Needs_Action
cat > vault/Needs_Action/plan_blocked_test.md <<'EOF'
---
plan_id: PLAN_test
escalation_reason: Step failed after 3 retries
---
# Plan Escalation
EOF

# Create API usage log
mkdir -p vault/Logs/API_Usage
cat > vault/Logs/API_Usage/2026-02-10.md <<'EOF'
---
date: 2026-02-10
---
# API Usage Log

- Request 1: cost_usd: 0.02
- Request 2: cost_usd: 0.03
EOF

cat > vault/Logs/API_Usage/2026-02-12.md <<'EOF'
---
date: 2026-02-12
---
# API Usage Log

- Request 1: cost_usd: 0.01
EOF
```

2. Generate briefing:

```bash
python scripts/ceo_briefing.py --vault vault --force
```

**Expected Results**:

- ✅ Briefing file created: `vault/Briefings/YYYY-MM-DD_Monday_Briefing.md`
- ✅ Briefing contains accurate task counts (e.g., `tasks_completed_count: 2`)
- ✅ Briefing contains accurate pending count (e.g., `tasks_pending_count: 1`)
- ✅ Briefing contains accurate API cost (e.g., `api_cost_week: 0.06`)
- ✅ Briefing contains 3+ proactive suggestions
- ✅ Week range calculated correctly (previous Monday-Sunday)

**Validation**:

```bash
# Check briefing file exists
ls -la vault/Briefings/*.md

# Read briefing content
cat vault/Briefings/*.md

# Verify YAML frontmatter
head -n 15 vault/Briefings/*.md
```

---

### Test 7: Briefing Date Calculation

**Objective**: Verify week_start, week_end, briefing_date are calculated correctly

**Steps**:

1. Run briefing generator on different days of the week

2. Check frontmatter dates

**Expected Results**:

- ✅ `week_start` is previous Monday (00:00)
- ✅ `week_end` is previous Sunday (23:59)
- ✅ `briefing_date` is next Monday (00:00) after week_end

**Test Cases**:

| Today's Date | Expected week_start | Expected week_end | Expected briefing_date |
|--------------|---------------------|-------------------|------------------------|
| 2026-02-14 (Friday) | 2026-02-10 (Mon) | 2026-02-16 (Sun) | 2026-02-17 (Mon) |
| 2026-02-16 (Sunday) | 2026-02-03 (Mon) | 2026-02-09 (Sun) | 2026-02-10 (Mon) |
| 2026-02-17 (Monday) | 2026-02-10 (Mon) | 2026-02-16 (Sun) | 2026-02-17 (Mon) |

**Validation**:

```bash
# Check frontmatter dates in briefing
grep -E "(week_start|week_end|briefing_date):" vault/Briefings/*.md
```

---

### Test 8: Proactive Suggestions Generation

**Objective**: Verify proactive suggestions are data-driven and actionable

**Steps**:

1. Create test scenarios:

```bash
# Scenario A: Old pending approval (3+ days old)
mkdir -p vault/Pending_Approval/Email
cat > vault/Pending_Approval/Email/EMAIL_DRAFT_old.md <<'EOF'
---
draft_id: EMAIL_DRAFT_old
status: pending_approval
---
Old draft
EOF

# Set file modification time to 3 days ago
touch -t $(date -d '3 days ago' +%Y%m%d%H%M) vault/Pending_Approval/Email/EMAIL_DRAFT_old.md

# Scenario B: Plan with low iterations remaining
mkdir -p vault/In_Progress/PLAN_test_low_iterations
cat > vault/In_Progress/PLAN_test_low_iterations/state.md <<'EOF'
---
plan_id: PLAN_test_low_iterations
iterations_remaining: 2
---
EOF

# Scenario C: High-priority email > 24h old in Inbox
mkdir -p vault/Inbox
cat > vault/Inbox/EMAIL_urgent.md <<'EOF'
---
type: email
priority: High
subject: Urgent client issue
---
EOF
touch -t $(date -d '30 hours ago' +%Y%m%d%H%M) vault/Inbox/EMAIL_urgent.md
```

2. Generate briefing:

```bash
python scripts/ceo_briefing.py --vault vault --force
```

**Expected Results**:

- ✅ Suggestion 1: Mentions old pending approval (3 days old)
- ✅ Suggestion 2: Mentions plan with low iterations (2/10 remaining)
- ✅ Suggestion 3: Mentions high-priority emails unanswered for >24h
- ✅ All suggestions are actionable (include file paths, action steps)

**Validation**:

```bash
# Read Proactive Suggestions section
sed -n '/## Proactive Suggestions/,/## Next Week Focus/p' vault/Briefings/*.md
```

---

### Test 9: Briefing Scheduling (Sunday 23:00)

**Objective**: Verify scheduled briefing runs every Sunday at 23:00

**Steps**:

1. Start briefing in scheduled mode:

```bash
python scripts/ceo_briefing.py --vault vault --schedule &
```

2. Wait until Sunday 23:00 (or simulate time for testing)

**Expected Results**:

- ✅ Briefing auto-generated on Sunday at 23:00
- ✅ Process runs continuously (does not exit after generation)
- ✅ Next briefing scheduled for following Sunday

**Note**: For quick testing, modify the schedule in `ceo_briefing.py` temporarily:

```python
# Change from:
schedule.every().sunday.at("23:00").do(job)

# To (for testing):
schedule.every().minute.do(job)  # Runs every minute
```

**Validation**:

```bash
# Check process is running
ps aux | grep ceo_briefing

# Check briefing files are generated
ls -lat vault/Briefings/
```

---

## Integration Test: Full Workflow

### Test 10: End-to-End Autonomous Execution

**Objective**: Verify complete autonomous flow from task creation to briefing generation

**Steps**:

1. **Day 1**: Create multi-step task in `vault/Inbox/`

2. **Day 1**: Plan generator detects and creates Plan.md + approval request

3. **Day 1**: Human approves plan (moves to `vault/Approved/Plans/`)

4. **Day 2**: Ralph Wiggum loop executes plan autonomously (all steps complete)

5. **Day 2**: Plan moves to `vault/Done/`

6. **Sunday**: CEO Briefing auto-generates, includes completed plan in "Week in Review"

**Expected Results**:

- ✅ Full autonomous execution (no errors)
- ✅ All steps logged to `vault/Logs/MCP_Actions/`
- ✅ Plan appears in briefing as completed task
- ✅ No items in `vault/Needs_Action/` (no escalations)

---

## Troubleshooting

### Common Issues

**Issue 1**: Plan executor can't find MCP servers

**Solution**:
```bash
# Check MCP server paths in mcp_client.py
# Verify MCP servers exist:
ls -la mcp_servers/email_mcp/server.py
ls -la mcp_servers/whatsapp_mcp/server.py
ls -la mcp_servers/linkedin_mcp/server.py
```

**Issue 2**: Briefing shows 0 completed tasks despite tasks in vault/Done/

**Solution**:
```bash
# Check file modification times
stat vault/Done/*.md

# Ensure tasks were moved to Done/ during the week being analyzed
```

**Issue 3**: Ralph Wiggum loop doesn't resume from saved state

**Solution**:
```bash
# Check state file exists and is readable
cat vault/In_Progress/PLAN_*/state.md

# Verify YAML frontmatter is valid (no syntax errors)
```

---

## Success Criteria

### PART A: Ralph Wiggum Loop

- ✅ All 5 tests (Test 1-5) pass
- ✅ Plans execute autonomously with max 10 iterations
- ✅ State persists correctly across restarts
- ✅ Error handling works (3 retries + escalation)
- ✅ No infinite loops (max iteration exit works)

### PART B: CEO Briefing

- ✅ All 4 tests (Test 6-9) pass
- ✅ Briefing generates with accurate data
- ✅ Proactive suggestions are data-driven and actionable
- ✅ Scheduling works (Sunday 23:00)
- ✅ Week date calculation is correct

### Overall

- ✅ No regressions in Bronze/Silver features
- ✅ All implemented tasks (T036-T042, T052-T055) validated
- ✅ Documentation complete and accurate
- ✅ Code follows project constitution (local-first, vault integrity, audit logging)

---

## Next Steps

After Phase 1 testing is complete:

1. **Address any test failures** - Fix bugs and re-run tests
2. **Complete remaining US4 tasks** - T043-T045 (plan watcher, dashboard integration)
3. **Phase 2 Implementation** - Continue with additional Gold tier features
4. **Production Deployment** - Deploy to production environment with monitoring

---

**Testing Guide Version**: 1.0
**Last Updated**: 2026-02-14
**Maintained By**: Personal AI Employee (Gold Tier)
