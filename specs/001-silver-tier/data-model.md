# Data Model: Silver Tier Entities

**Feature**: 001-silver-tier
**Date**: 2026-02-11
**Purpose**: Define entities, relationships, and data structures for Silver tier implementation

## Entity Definitions

### 1. AIAnalysisResult

**Purpose**: Represents the output of Claude API analysis for a single task

**Attributes**:
- `task_id` (string): Unique identifier for the analyzed task (hash of title)
- `priority` (enum): "High" | "Medium" | "Low"
- `category` (enum): "Work" | "Personal" | "Urgent" | "Uncategorized"
- `reasoning` (string): Brief explanation for priority/category assignment (max 100 chars)
- `confidence` (float): 0.0-1.0 confidence score from API
- `api_cost` (float): Estimated cost in USD for this API call
- `cached` (boolean): True if response retrieved from cache
- `fallback` (boolean): True if Bronze defaults used (API unavailable)
- `timestamp` (datetime): When analysis was performed (ISO 8601)

**Relationships**:
- One-to-one with VaultFile (each file analyzed once per 24h cache window)
- Stored in vault/Logs/API_Cache/{hash}.json (24h TTL)

**Validation Rules**:
- priority must be in ["High", "Medium", "Low"]
- category must be in ["Work", "Personal", "Urgent", "Uncategorized"]
- confidence must be 0.0 ≤ confidence ≤ 1.0
- cached and fallback cannot both be True

**State Transitions**:
- Fresh analysis: cached=False, fallback=False
- Cache hit: cached=True, fallback=False
- API failure: cached=False, fallback=True (priority="Medium", category="Uncategorized")

---

### 2. EmailTask (extends VaultFile)

**Purpose**: Represents an email-sourced task created by Gmail watcher

**Attributes (inherited from VaultFile)**:
- `filename` (string): Relative path (e.g., "Inbox/EMAIL_123abc.md")
- `date_added` (datetime): When file was created (ISO 8601)
- `status` (enum): "Inbox" | "Needs Action" | "Done"
- `priority` (enum): "High" | "Medium" | "Low" (from AI analysis)

**Additional Attributes (email-specific)**:
- `email_id` (string): Gmail message ID (unique, used in filename)
- `sender_email` (string): From address (e.g., "client@example.com")
- `subject` (string): Email subject line (max 200 chars)
- `snippet` (string): First 200 chars of email body
- `received_timestamp` (datetime): When email was received (from Gmail API)

**YAML Frontmatter Format**:
```yaml
---
type: email
from: client@example.com
subject: Urgent invoice request
received: 2026-02-11T14:30:00Z
priority: high
status: pending
---
```

**Relationships**:
- Stored in vault/Inbox/EMAIL_{email_id}.md
- Appears in Dashboard.md table
- Processed email ID tracked in vault/Logs/gmail_processed_ids.txt (prevent duplicates)

**Validation Rules**:
- email_id must be unique (Gmail message ID)
- sender_email must match email regex pattern
- snippet length ≤ 200 chars

---

### 3. WhatsAppTask (extends VaultFile)

**Purpose**: Represents a WhatsApp message task created by WhatsApp watcher

**Attributes (inherited from VaultFile)**:
- `filename` (string): Relative path (e.g., "Inbox/WHATSAPP_chat123_20260211143000.md")
- `date_added` (datetime): When file was created
- `status` (enum): "Inbox" | "Needs Action" | "Done"
- `priority` (enum): "High" | "Medium" | "Low" (from AI analysis or keyword match)

**Additional Attributes (WhatsApp-specific)**:
- `chat_id` (string): WhatsApp chat identifier (hashed contact/group ID)
- `contact_name` (string): Display name from WhatsApp Web
- `matched_keywords` (array[string]): Keywords that triggered task creation (e.g., ["urgent", "invoice"])
- `message_preview` (string): First 200 chars of message

**YAML Frontmatter Format**:
```yaml
---
type: whatsapp
from: Client Name
received: 2026-02-11T14:30:00Z
keywords: ["urgent", "invoice"]
priority: high
status: pending
---
```

**Relationships**:
- Stored in vault/Inbox/WHATSAPP_{chat_id}_{timestamp}.md
- Appears in Dashboard.md table

**Validation Rules**:
- matched_keywords must be subset of WHATSAPP_KEYWORDS env var
- If "urgent" in keywords, priority defaults to "high" (before AI analysis)
- timestamp in filename format: YYYYMMDDHHMMSS

---

### 4. LinkedInPost

**Purpose**: Represents a drafted LinkedIn post awaiting approval

**Attributes**:
- `post_id` (string): Unique identifier (LINKEDIN_POST_{YYYY-MM-DD})
- `scheduled_date` (date): When post should be published (YYYY-MM-DD)
- `business_goal` (string): Business goal from Company_Handbook.md that inspired this post
- `post_content` (string): Draft post text (max 3000 chars, LinkedIn limit)
- `character_count` (int): Length of post_content
- `status` (enum): "pending_approval" | "approved" | "posted" | "rejected"
- `created_timestamp` (datetime): When draft was generated

**YAML Frontmatter Format**:
```yaml
---
type: linkedin_post
scheduled_date: 2026-02-12
status: pending_approval
character_count: 482
business_goal: Increase brand awareness for AI consulting services
---
```

**Relationships**:
- Stored in vault/Pending_Approval/LinkedIn/LINKEDIN_POST_{date}.md (pending)
- Moved to vault/Approved/LinkedIn/ when user approves
- Moved to vault/Done/LinkedIn/ after posted (not implemented in Silver, deferred to Gold)

**Validation Rules**:
- character_count ≤ 3000 (LinkedIn post limit)
- scheduled_date must be today or future date
- business_goal must exist in Company_Handbook.md

**State Transitions**:
- Create: status="pending_approval", file in Pending_Approval/LinkedIn/
- User approves: Move to Approved/LinkedIn/, status="approved"
- User rejects: Move to Rejected/ (not implemented in Silver)
- Posted (Gold tier): Move to Done/LinkedIn/, status="posted"

---

### 5. Plan

**Purpose**: Represents a multi-step plan file for complex tasks

**Attributes**:
- `plan_id` (string): Unique identifier (PLAN_{task_name}_{date})
- `objective` (string): High-level goal (e.g., "Launch Q1 marketing campaign")
- `steps` (array[PlanStep]): Ordered list of plan steps
- `total_steps` (int): Length of steps array
- `completed_steps` (int): Count of steps with status="completed"
- `approval_required` (boolean): True if any step requires approval
- `estimated_time` (string): Human-readable time estimate (e.g., "2 weeks")
- `created_timestamp` (datetime): When plan was generated
- `status` (enum): "pending" | "in_progress" | "completed" | "blocked"

**YAML Frontmatter Format**:
```yaml
---
objective: Launch Q1 marketing campaign with budget allocation
steps: 5
approval_required: true
estimated_time: 2 weeks
created: 2026-02-11T14:30:00Z
status: pending
---
```

**Relationships**:
- Stored in vault/Plans/PLAN_{task_name}_{date}.md
- Contains many PlanSteps (numbered checklist in markdown body)
- Referenced in Dashboard.md with progress tracking (e.g., "Plan: 3/5 steps completed")

**Validation Rules**:
- total_steps must equal len(steps)
- completed_steps ≤ total_steps
- status="completed" requires completed_steps == total_steps

---

### 6. PlanStep

**Purpose**: Represents a single step within a Plan

**Attributes**:
- `step_number` (int): 1-indexed position in plan
- `description` (string): What needs to be done (max 200 chars)
- `status` (enum): "pending" | "in_progress" | "completed" | "blocked"
- `dependencies` (array[int]): Step numbers that must complete first
- `approval_required` (boolean): True if step needs human approval before execution

**Markdown Format** (inside Plan.md body):
```markdown
1. [ ] Research competitor pricing (estimated: 2 hours)
2. [ ] Draft budget proposal [Blocked by: 1] (estimated: 1 hour)
3. [ ] Get approval from stakeholder [APPROVAL REQUIRED]
4. [x] Create campaign landing page (estimated: 4 hours)
5. [ ] Launch campaign [Blocked by: 3, 4]
```

**Relationships**:
- Many-to-one with Plan (embedded in Plan.md file)
- Dependencies reference other PlanSteps by step_number

**Validation Rules**:
- step_number must be unique within plan
- dependencies cannot reference self or non-existent steps
- If status="blocked", must have unresolved dependencies

**State Transitions**:
- User checks checkbox: `[ ]` → `[x]`, status="completed"
- If all dependencies completed: status transitions from "blocked" to "pending"

---

### 7. APIUsageLog

**Purpose**: Represents a single Claude API call for cost tracking

**Attributes**:
- `log_id` (string): UUID for this log entry
- `timestamp` (datetime): When API call was made (ISO 8601)
- `request_type` (enum): "priority_analysis" | "categorization" | "plan_generation" | "linkedin_draft"
- `input_tokens` (int): Tokens sent to API (prompt + task content)
- `output_tokens` (int): Tokens received from API (response)
- `estimated_cost_usd` (float): Cost for this call (input + output pricing)
- `cache_hit` (boolean): True if response was from cache (cost=0)
- `model` (string): Claude model used (e.g., "claude-3-5-sonnet-20241022")

**Log File Format** (vault/Logs/API_Usage/YYYY-MM.md):
```markdown
# API Usage Log: February 2026

## Daily Summary
- 2026-02-11: 42 calls, $0.0504 total
- 2026-02-10: 38 calls, $0.0456 total

## Detailed Log

| Timestamp | Request Type | Input Tokens | Output Tokens | Cost (USD) | Cache Hit | Model |
|-----------|--------------|--------------|---------------|------------|-----------|-------|
| 2026-02-11T14:30:45Z | priority_analysis | 152 | 48 | $0.0012 | No | claude-3-5-sonnet-20241022 |
| 2026-02-11T14:31:12Z | priority_analysis | 148 | 45 | $0.0011 | Yes | claude-3-5-sonnet-20241022 |
```

**Relationships**:
- Aggregated daily in vault/Logs/API_Usage/YYYY-MM.md
- Cached responses stored in vault/Logs/API_Cache/{hash}.json

**Validation Rules**:
- input_tokens, output_tokens must be > 0 (unless cache_hit=True)
- estimated_cost_usd = (input_tokens * $3.00/1M) + (output_tokens * $15.00/1M)
- If cache_hit=True, estimated_cost_usd must be 0.0

---

### 8. WatcherStatus

**Purpose**: Represents the runtime status of a specific watcher process

**Attributes**:
- `watcher_type` (enum): "gmail" | "whatsapp" | "linkedin" | "bronze"
- `status` (enum): "active" | "paused" | "error"
- `last_poll_time` (datetime): When watcher last checked for updates
- `next_poll_time` (datetime): When watcher will poll next
- `error_message` (string | null): Error description if status="error"
- `restart_count` (int): Number of times watcher has auto-restarted (via PM2)

**Display in Dashboard.md** (Silver Tier Status section):
```markdown
## Silver Tier Status
- **AI Analysis**: ✓ Enabled (Cost Today: $0.05)
- **Gmail Watcher**: ✓ Active (last poll: 2026-02-11 14:28)
- **WhatsApp Watcher**: ✓ Active (last poll: 2026-02-11 14:29)
- **LinkedIn Generator**: ⏸ Paused (next run: 2026-02-12 09:00)
```

**Relationships**:
- Displayed in Dashboard.md "Silver Tier Status" section
- Updated by each watcher process on every poll cycle

**Validation Rules**:
- last_poll_time ≤ current_time
- next_poll_time > last_poll_time
- If status="error", error_message must not be null

---

## Entity Relationship Diagram (ERD)

```text
VaultFile (Bronze)
    ↓ (extends)
EmailTask ────→ AIAnalysisResult (priority/category)
    ↓
WhatsAppTask ──→ AIAnalysisResult (priority/category)
    ↓
Dashboard ──────→ Shows all VaultFiles (Inbox, Needs_Action, Done)

LinkedInPost ───→ Pending_Approval/ folder
    ↓ (user moves file)
Approved/ folder ─→ MCP action execution

Plan ───→ Contains multiple PlanSteps
    ↓
PlanStep ───→ Dependencies (other PlanSteps)

APIUsageLog ───→ Aggregated in API_Usage/YYYY-MM.md
    ↓
Cached responses stored in API_Cache/{hash}.json

WatcherStatus ──→ Displayed in Dashboard.md "Silver Tier Status"
```

---

## Data Validation & Integrity

**Atomic Operations** (inherited from Bronze):
- Dashboard.md updates use temp file → backup → rename pattern
- All file writes validate markdown syntax before committing

**Concurrency Safety**:
- Multiple watchers write to different files (EMAIL_*, WHATSAPP_*, LINKEDIN_*)
- Dashboard.md updated by single Bronze watcher (no Silver concurrent writes)
- API cache uses hash-based filenames (no collisions)

**Backup Strategy** (inherited from Bronze):
- Dashboard.md: Backup before every update (Dashboard.md.bak.TIMESTAMP)
- Keep last 5 backups, prune after 7 days
- Automatic restore on corruption detection

---

**Data Model Status**: Complete. Entities align with spec requirements and support Silver tier features while maintaining Bronze compatibility.
