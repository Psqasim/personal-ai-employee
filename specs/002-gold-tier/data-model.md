# Data Model: Gold Tier Entities

**Feature**: 002-gold-tier | **Date**: 2026-02-13 | **Phase**: 1

## Summary

This document defines all data entities for Gold tier, including draft objects (Email, WhatsApp, LinkedIn), plan execution state, MCP action logs, and CEO Briefing. All entities are file-based (Obsidian markdown with YAML frontmatter) to maintain local-first architecture.

---

## Entities

### 1. EmailDraft

**Location**: `vault/Pending_Approval/Email/EMAIL_DRAFT_{id}.md` → `vault/Approved/Email/` → `vault/Done/`

**Purpose**: AI-generated email reply awaiting human approval

**Fields**:
```yaml
draft_id: string           # Unique ID (timestamp-based)
original_email_id: string  # Reference to EMAIL_{id}.md in vault/Inbox/
to: string                 # Recipient email address
subject: string            # Email subject line
draft_body: string         # AI-generated email body
status: enum               # pending_approval | approved | rejected | sent | failed
generated_at: datetime     # When draft was created
sent_at: datetime | null   # When email was sent (null until sent)
action: "send_email"       # MCP action type (for approval watcher)
mcp_server: "email-mcp"    # MCP server to invoke
```

**State Transitions**:
```
pending_approval (file in Pending_Approval/Email/)
  ├─> approved (file moved to Approved/Email/, triggers email-mcp)
  │     └─> sent (MCP success, moved to Done/)
  │     └─> failed (MCP error, moved to Needs_Action/)
  └─> rejected (file moved to Rejected/, logged and archived)
```

**Example File** (`EMAIL_DRAFT_1707849600.md`):
```yaml
---
draft_id: EMAIL_DRAFT_1707849600
original_email_id: EMAIL_abc123
to: client@example.com
subject: "Re: Project proposal review"
draft_body: |
  Hi John,

  Thank you for sharing the project proposal. I've reviewed the details and have a few questions:

  1. What's the expected timeline for Phase 1?
  2. Can we discuss budget allocation in our next meeting?

  Let me know your availability this week.

  Best regards,
  Sarah Chen
status: pending_approval
generated_at: 2026-02-13T14:20:00Z
sent_at: null
action: send_email
mcp_server: email-mcp
---

# Email Draft

**Original Email**: [[vault/Inbox/EMAIL_abc123]]
**To**: client@example.com
**Subject**: Re: Project proposal review

## Draft Body

[See YAML frontmatter above]

## Approval

- Move to `vault/Approved/Email/` to send
- Move to `vault/Rejected/` to discard
```

**Validation Rules**:
- `to` must be valid email format
- `draft_body` max 5000 characters
- `original_email_id` must exist in vault/Inbox/
- `status` transitions must be sequential (no jumping)

---

### 2. WhatsAppDraft

**Location**: `vault/Pending_Approval/WhatsApp/WHATSAPP_DRAFT_{chat_id}_{timestamp}.md` → `vault/Approved/WhatsApp/` → `vault/Done/`

**Purpose**: AI-generated WhatsApp reply for important messages

**Fields**:
```yaml
draft_id: string              # Unique ID
original_message_id: string   # Reference to WHATSAPP_{chat_id}_{timestamp}.md
to: string                    # Contact name (as shown in WhatsApp Web)
chat_id: string               # WhatsApp chat identifier (from original message)
draft_body: string            # AI-generated reply (max 500 chars)
status: enum                  # pending_approval | approved | rejected | sent | failed
generated_at: datetime
sent_at: datetime | null
keywords_matched: array       # Keywords that triggered draft (e.g., ["urgent", "payment"])
action: "send_message"
mcp_server: "whatsapp-mcp"
```

**State Transitions**: Same as EmailDraft

**Example File** (`WHATSAPP_DRAFT_client_chat_1707849700.md`):
```yaml
---
draft_id: WHATSAPP_DRAFT_client_chat_1707849700
original_message_id: WHATSAPP_client_chat_1707849600
to: "John Doe"
chat_id: "client_chat"
draft_body: "Got it! Will process the payment today. Expect confirmation by 5 PM. - Sarah"
status: pending_approval
generated_at: 2026-02-13T14:25:00Z
sent_at: null
keywords_matched: ["urgent", "payment"]
action: send_message
mcp_server: whatsapp-mcp
---

# WhatsApp Draft Reply

**Original Message**: [[vault/Inbox/WHATSAPP_client_chat_1707849600]]
**To**: John Doe
**Keywords**: urgent, payment

## Draft Message

"Got it! Will process the payment today. Expect confirmation by 5 PM. - Sarah"

## Approval

- Move to `vault/Approved/WhatsApp/` to send
- Move to `vault/Rejected/` to discard
```

**Validation Rules**:
- `draft_body` max 500 characters (enforce brevity)
- `to` must be non-empty contact name
- `chat_id` must match original message
- `keywords_matched` must be subset of configured keywords (WHATSAPP_KEYWORDS in .env)

---

### 3. LinkedInDraft

**Location**: `vault/Pending_Approval/LinkedIn/LINKEDIN_POST_{YYYY-MM-DD}.md` → `vault/Approved/LinkedIn/` → `vault/Done/`

**Purpose**: AI-generated LinkedIn post aligned with business goals

**Fields**:
```yaml
draft_id: string
scheduled_date: date         # Date for posting (max 1 post/day)
business_goal_reference: string  # Section from Company_Handbook.md referenced
post_content: string         # AI-generated post body
character_count: int         # Length of post_content (max 3000)
status: enum                 # pending_approval | approved | rejected | posted | failed | rate_limited_retry
generated_at: datetime
posted_at: datetime | null
action: "create_post"
mcp_server: "linkedin-mcp"
```

**State Transitions**:
```
pending_approval
  ├─> approved
  │     └─> posted (MCP success)
  │     └─> rate_limited_retry (LinkedIn API 429, retry after 60min)
  │     └─> failed (MCP error)
  └─> rejected
```

**Example File** (`LINKEDIN_POST_2026-02-14.md`):
```yaml
---
draft_id: LINKEDIN_POST_2026-02-14
scheduled_date: 2026-02-14
business_goal_reference: "Promote AI automation services"
post_content: |
  Most business owners spend 5+ hours/day on email and admin tasks.

  Here's what I learned after implementing AI automation:
  - Email triage cut from 2 hours to 15 minutes
  - Meeting scheduling fully automated
  - Client follow-ups never missed

  The secret? Combining AI drafts with human oversight. You get speed + quality.

  What's your biggest time drain? Comment below.
character_count: 412
status: pending_approval
generated_at: 2026-02-13T14:30:00Z
posted_at: null
action: create_post
mcp_server: linkedin-mcp
---

# LinkedIn Post Draft

**Scheduled Date**: 2026-02-14
**Business Goal**: Promote AI automation services
**Character Count**: 412/3000

## Post Content

[See YAML frontmatter above]

## Approval

- Move to `vault/Approved/LinkedIn/` to publish
- Move to `vault/Rejected/` to discard
```

**Validation Rules**:
- `post_content` max 3000 characters
- `scheduled_date` must be unique (max 1 post/day)
- `business_goal_reference` must exist in Company_Handbook.md
- Auto-truncate at sentence boundary if exceeds 3000 chars

---

### 4. Plan

**Location**: `vault/Plans/PLAN_{name}_{date}.md`

**Purpose**: Multi-step execution plan (Silver creates, Gold executes)

**Fields**:
```yaml
plan_id: string
objective: string            # High-level goal (e.g., "Onboard new client")
steps: array<PlanStep>       # Ordered list of steps
total_steps: int
completed_steps: int         # Count of steps with status=completed
status: enum                 # awaiting_approval | executing | completed | blocked | escalated
approval_required: bool      # Always true (Gold tier requires approval before execution)
estimated_time: string       # Human estimate (e.g., "30 minutes")
approval_file_path: string   # Path to approval file (vault/Pending_Approval/Plans/...)
iteration_count: int         # Ralph Wiggum loop iterations used (max 10)
created_at: datetime
started_at: datetime | null
completed_at: datetime | null
```

**State Transitions**:
```
awaiting_approval (file in Plans/, approval request in Pending_Approval/Plans/)
  ├─> executing (approval granted, Ralph Wiggum loop starts)
  │     ├─> completed (all steps done)
  │     ├─> blocked (step failed after 3 retries)
  │     └─> escalated (max 10 iterations reached without completion)
  └─> rejected (approval denied)
```

**Example File** (`PLAN_onboarding_2026-02-13.md`):
```yaml
---
plan_id: PLAN_onboarding_2026-02-13
objective: "Onboard new client - send intro email, schedule kick-off, post LinkedIn announcement"
steps:
  - step_num: 1
    description: "Send intro email to client"
    action_type: "mcp_email"
    action_params:
      to: "newclient@example.com"
      subject: "Welcome to our services"
      body: "[AI-generated intro email]"
    dependencies: []
    status: "completed"
    mcp_action_log_id: "LOG_email_001"

  - step_num: 2
    description: "Create calendar invite for kick-off meeting"
    action_type: "mcp_calendar"
    action_params:
      title: "Client Kick-off Meeting"
      start: "2026-02-15T10:00:00Z"
      attendees: ["newclient@example.com"]
    dependencies: [1]
    status: "executing"
    mcp_action_log_id: null

  - step_num: 3
    description: "Post LinkedIn announcement about new partnership"
    action_type: "mcp_linkedin"
    action_params:
      text: "Excited to announce our partnership with..."
    dependencies: [1, 2]
    status: "pending"
    mcp_action_log_id: null

total_steps: 3
completed_steps: 1
status: "executing"
approval_required: true
estimated_time: "45 minutes"
approval_file_path: "vault/Pending_Approval/Plans/PLAN_onboarding_approval.md"
iteration_count: 2
created_at: 2026-02-13T14:00:00Z
started_at: 2026-02-13T14:10:00Z
completed_at: null
---

# Plan: Onboard New Client

## Objective
Onboard new client - send intro email, schedule kick-off, post LinkedIn announcement

## Steps

- [x] Step 1: Send intro email to client
- [ ] Step 2: Create calendar invite for kick-off meeting (Dependencies: Step 1)
- [ ] Step 3: Post LinkedIn announcement (Dependencies: Step 1, 2)

## Progress

**Status**: Executing
**Completed**: 1/3 steps
**Iterations Used**: 2/10
**Started**: 2026-02-13 at 14:10
```

**Validation Rules**:
- `steps` must have sequential `step_num` (1, 2, 3, ...)
- `dependencies` must reference valid step_num (no forward refs, no circular)
- `iteration_count` max 10
- `status` transitions must be sequential

---

### 5. PlanStep

**Purpose**: Single executable step within a Plan (embedded in Plan YAML)

**Fields**:
```yaml
step_num: int                # Sequential step number
description: string          # Human-readable action
action_type: enum            # mcp_email | mcp_whatsapp | mcp_linkedin | mcp_calendar | create_file | notify_human
action_params: object        # Parameters for action (structure varies by action_type)
dependencies: array<int>     # step_num values that must complete before this step
status: enum                 # pending | executing | completed | blocked
mcp_action_log_id: string | null  # Reference to MCP log entry (null until executed)
retry_count: int             # Number of retries attempted (max 3)
```

**Action Types**:
- `mcp_email`: Invoke email-mcp with `action_params: {to, subject, body}`
- `mcp_whatsapp`: Invoke whatsapp-mcp with `action_params: {chat_id, message}`
- `mcp_linkedin`: Invoke linkedin-mcp with `action_params: {text}`
- `mcp_calendar`: Invoke calendar-mcp with `action_params: {title, start, attendees}`
- `create_file`: Create vault file with `action_params: {file_path, content}`
- `notify_human`: Create notification with `action_params: {message}`

---

### 6. ExecutionState

**Location**: `vault/In_Progress/{plan_id}/state.md`

**Purpose**: Ralph Wiggum loop state (persisted for restart recovery)

**Fields**:
```yaml
plan_id: string
current_step: int             # Which step is executing (1-indexed)
iterations_remaining: int     # Ralph Wiggum loop iterations left (starts at 10)
last_action: string           # Description of last executed step
last_action_timestamp: datetime
loop_start_time: datetime
```

**Example File** (`vault/In_Progress/PLAN_onboarding_2026-02-13/state.md`):
```yaml
---
plan_id: PLAN_onboarding_2026-02-13
current_step: 2
iterations_remaining: 8
last_action: "Send intro email to client"
last_action_timestamp: 2026-02-13T14:15:00Z
loop_start_time: 2026-02-13T14:10:00Z
---

# Execution State

**Current Step**: 2/3
**Iterations Remaining**: 8/10
**Last Action**: Send intro email to client (completed at 14:15)
**Next Action**: Create calendar invite for kick-off meeting
```

**Validation Rules**:
- `current_step` must be ≤ total_steps in Plan
- `iterations_remaining` must be ≥ 0 and ≤ 10
- Updated atomically after each step completes (write to temp file, rename)

---

### 7. MCPActionLog

**Location**: `vault/Logs/MCP_Actions/YYYY-MM-DD.md` (append-only daily log)

**Purpose**: Audit trail of all MCP invocations

**Fields** (each log entry):
```yaml
log_id: string               # Unique log entry ID
mcp_server: string           # email-mcp | whatsapp-mcp | linkedin-mcp
action: string               # send_email | send_message | create_post
payload_summary: string      # Sanitized summary (no PII, max 50 chars)
outcome: string              # success | failed | rate_limited
plan_id: string | null       # Reference to Plan if part of plan execution
step_num: int | null         # Step number if part of plan
timestamp: datetime
human_approved: bool         # Always true (approval file required)
approval_file_path: string   # Path to approval file
error_message: string | null # Error details if outcome=failed
```

**Example Log Entry**:
```markdown
---
log_id: LOG_email_001
mcp_server: email-mcp
action: send_email
payload_summary: "To: newclient@example.com, Subject: Welcome to..."
outcome: success
plan_id: PLAN_onboarding_2026-02-13
step_num: 1
timestamp: 2026-02-13T14:15:00Z
human_approved: true
approval_file_path: vault/Approved/Plans/PLAN_onboarding_approval.md
error_message: null
---

**Action**: email-mcp.send_email
**Outcome**: Success ✓
**Timestamp**: 2026-02-13 14:15:00
**Plan**: PLAN_onboarding_2026-02-13 (Step 1)
**Approval**: vault/Approved/Plans/PLAN_onboarding_approval.md
```

**Validation Rules**:
- `human_approved` always true (enforced by approval watcher)
- `approval_file_path` must exist
- `payload_summary` max 50 chars (no full emails, messages, posts logged)
- Logs never deleted (retention: 90 days minimum per constitution)

---

### 8. CEOBriefing

**Location**: `vault/Briefings/YYYY-MM-DD_Monday_Briefing.md`

**Purpose**: Weekly executive summary (generated Sunday 23:00)

**Fields**:
```yaml
briefing_date: date          # Monday date (briefing is for the upcoming week)
week_start: date             # Previous Monday
week_end: date               # Previous Sunday
tasks_completed_count: int   # Count from vault/Done/ with last_modified in week range
tasks_pending_count: int     # Count from vault/Needs_Action/
proactive_suggestions: array<string>  # AI-generated suggestions (3+ items)
api_cost_week: float         # Total Claude API cost for the week
generated_by: enum           # ai | data_only (if Claude API unavailable)
generated_at: datetime
```

**Example File** (`vault/Briefings/2026-02-17_Monday_Briefing.md`):
```yaml
---
briefing_date: 2026-02-17
week_start: 2026-02-10
week_end: 2026-02-16
tasks_completed_count: 47
tasks_pending_count: 12
proactive_suggestions:
  - "5 high-priority emails unanswered for >24h - review vault/Inbox/"
  - "LinkedIn post pending approval for 3 days - approve or reject"
  - "Plan 'Client onboarding' blocked at Step 2 - calendar invite failed, retry needed"
api_cost_week: 0.08
generated_by: ai
generated_at: 2026-02-16T23:00:00Z
---

# CEO Briefing: Week of Feb 17, 2026

## Executive Summary

**Tasks Completed This Week**: 47
**Tasks Pending/Blocked**: 12
**API Cost**: $0.08 (target: <$0.10/day, on track)

## Week in Review (Feb 10 - Feb 16)

### Completed Tasks
- 23 email replies sent (15 via AI draft + approval)
- 18 WhatsApp messages handled (12 via AI draft)
- 6 LinkedIn posts published
- 2 multi-step plans completed

### Pending Items
- 8 tasks in vault/Needs_Action/ require attention
- 4 approval requests in vault/Pending_Approval/

## Proactive Suggestions

1. **5 high-priority emails unanswered for >24h** - Review vault/Inbox/ for EMAIL_* files with priority="High" and created_at >24h ago
2. **LinkedIn post pending approval for 3 days** - vault/Pending_Approval/LinkedIn/LINKEDIN_POST_2026-02-14.md waiting since Feb 13
3. **Plan 'Client onboarding' blocked at Step 2** - Calendar invite failed, retry needed or manual calendar creation

## Next Week Focus

- Clear backlog of pending emails
- Complete blocked plan (client onboarding)
- Maintain LinkedIn posting cadence (5 posts/week)
```

**Validation Rules**:
- Generated weekly (Sunday 23:00 cron job)
- `briefing_date` is next Monday after generation
- `proactive_suggestions` min 3 items (if AI available), max 10
- `api_cost_week` calculated from vault/Logs/API_Usage/

---

## Entity Relationships

```
EmailDraft --references--> EMAIL_{id}.md (inbox)
WhatsAppDraft --references--> WHATSAPP_{id}.md (inbox)
LinkedInDraft --references--> Company_Handbook.md (business goals)

Plan --contains--> PlanStep[] (embedded array)
Plan --tracked-by--> ExecutionState (state.md)

PlanStep --logs-to--> MCPActionLog (when executed)

All drafts (Email, WhatsApp, LinkedIn) --log-to--> MCPActionLog (on approval + send)

CEOBriefing --aggregates--> vault/Done/, vault/Needs_Action/, vault/Logs/API_Usage/
```

---

## File Naming Conventions

| Entity | Pattern | Example |
|--------|---------|---------|
| EmailDraft | `EMAIL_DRAFT_{timestamp}.md` | `EMAIL_DRAFT_1707849600.md` |
| WhatsAppDraft | `WHATSAPP_DRAFT_{chat_id}_{timestamp}.md` | `WHATSAPP_DRAFT_client_chat_1707849700.md` |
| LinkedInDraft | `LINKEDIN_POST_{YYYY-MM-DD}.md` | `LINKEDIN_POST_2026-02-14.md` |
| Plan | `PLAN_{name}_{date}.md` | `PLAN_onboarding_2026-02-13.md` |
| ExecutionState | `state.md` (in `In_Progress/{plan_id}/`) | `vault/In_Progress/PLAN_onboarding_2026-02-13/state.md` |
| MCPActionLog | `YYYY-MM-DD.md` (in `Logs/MCP_Actions/`) | `2026-02-13.md` |
| CEOBriefing | `YYYY-MM-DD_Monday_Briefing.md` | `2026-02-17_Monday_Briefing.md` |

---

## Summary

All entities are file-based (Obsidian markdown + YAML frontmatter) to maintain local-first architecture. State transitions are explicit, validation rules enforce data integrity, and relationships are clear. This model supports the full Gold tier workflow: draft generation → human approval → MCP execution → audit logging → weekly reporting.

**Next**: Generate MCP contracts and quickstart guide.
