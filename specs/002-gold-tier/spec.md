# Feature Specification: Gold Tier - Autonomous Employee

**Feature Branch**: `002-gold-tier`
**Created**: 2026-02-13
**Status**: Draft
**Input**: User description: "Create Gold tier specification building on Silver. Focus on: 1. Email draft generation with approval workflow 2. LinkedIn post generation with approval workflow 3. Multi-step plan execution 4. MCP integrations for auto-send/auto-post. Reference Silver spec and Gold principles from constitution. [UPDATED: Added WhatsApp integration with draft generation and auto-send via Playwright]"

## Overview

Gold Tier upgrades the Silver foundation by adding **multi-step plan execution, email draft generation, LinkedIn post generation, and multiple MCP server integrations** while maintaining 100% backward compatibility with Bronze and Silver. The agent now proposes complete action plans, drafts replies/posts, and executes approved plans with real external actions (send email, post to LinkedIn). All executions require human approval before the agent acts.

**Core Principle**: Plan first, execute after approval. The agent is an autonomous employee that proposes and drafts — the human approves and authorizes.

**Key Additions** (building on Silver):
- Email draft generation: AI drafts replies to inbox emails, saves to `vault/Pending_Approval/Email/`
- WhatsApp draft generation: AI monitors all WhatsApp messages, drafts replies for important messages, auto-sends after approval
- LinkedIn post generation with scheduling and one-click approval workflow
- Multi-step plan execution via Ralph Wiggum loop (10 max iterations, human gate before first step)
- Multiple MCP servers: Email MCP (send), WhatsApp MCP (monitor/send via Playwright), LinkedIn MCP (post), Calendar MCP (schedule), Browser MCP (portal navigation)
- Weekly Business Audit & CEO Briefing generation every Sunday
- Cross-domain integration: Personal (email, calendar, WhatsApp) + Business (LinkedIn, accounting drafts)
- Odoo Community integration for draft accounting entries (invoice drafts, expense logs)
- Comprehensive audit logging (90-day retention)
- Error recovery with exponential backoff and graceful degradation

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Email Draft Generation & Send Approval (Priority: P1)

As a **professional overwhelmed with inbox emails**, I want the AI to automatically draft reply emails for high-priority items in my inbox and present them for one-click approval so I can respond to clients 10x faster without writing from scratch.

**Why this priority**: Email draft-and-approve is the Gold tier's most immediately visible capability. It directly saves the user time and demonstrates autonomous drafting with human safety gate. Without this, Gold feels the same as Silver.

**Independent Test**: Mark a test email file in `vault/Inbox/` as high-priority. Trigger email draft generation. Within 15 seconds, a draft file appears in `vault/Pending_Approval/Email/EMAIL_DRAFT_{id}.md` with subject, recipient, and body pre-filled. User moves file to `vault/Approved/Email/` and the Email MCP sends the message.

**Acceptance Scenarios**:

1. **Given** a task file `EMAIL_{id}.md` exists in `vault/Inbox/` with priority="High" and type="email", **When** the Gold watcher processes it, **Then** a draft file `EMAIL_DRAFT_{id}.md` is created in `vault/Pending_Approval/Email/` within 15 seconds with YAML frontmatter (to, subject, draft_body, original_email_id, action="send_email", status="pending_approval")

2. **Given** a draft file exists in `vault/Pending_Approval/Email/`, **When** the user moves it to `vault/Approved/Email/`, **Then** the Email MCP sends the email within 30 seconds and logs the send action to `vault/Logs/MCP_Actions/YYYY-MM-DD.md`

3. **Given** a draft file exists in `vault/Pending_Approval/Email/`, **When** the user moves it to `vault/Rejected/`, **Then** the email is NOT sent, the task is moved to `vault/Done/` with status="rejected", and the rejection is logged

4. **Given** the Email MCP fails to send (network error), **When** the send is attempted after approval, **Then** the system retries with exponential backoff (3 attempts: 5s, 10s, 20s), logs each failure, and creates a `vault/Needs_Action/retry_send_{id}.md` if all retries fail

5. **Given** ENABLE_AI_ANALYSIS=false or Claude API is unavailable, **When** a high-priority email arrives, **Then** the system still creates a blank draft template in `vault/Pending_Approval/Email/` for manual editing (no AI body, graceful degradation)

6. **Given** 5 high-priority emails arrive simultaneously, **When** the watcher processes the batch, **Then** 5 separate draft files are created without race conditions and all appear in `vault/Pending_Approval/Email/` within 60 seconds

---

### User Story 2 - LinkedIn Post Generation & Auto-Post Approval (Priority: P1)

As a **business owner growing my professional network**, I want the AI to generate polished LinkedIn posts aligned with my business goals and let me approve them with a single file move so I maintain consistent social media presence without daily effort.

**Why this priority**: LinkedIn auto-posting is explicitly required in the Gold spec (constitution) and directly generates leads. It's P1 alongside email because social visibility drives revenue.

**Independent Test**: Configure LinkedIn business goals in `Company_Handbook.md`. Trigger LinkedIn post generation script. Within 15 seconds, a draft post appears in `vault/Pending_Approval/LinkedIn/LINKEDIN_POST_{date}.md`. User moves to `vault/Approved/LinkedIn/`. LinkedIn MCP posts to LinkedIn within 30 seconds.

**Acceptance Scenarios**:

1. **Given** `Company_Handbook.md` contains a "Business Goals" section and "LinkedIn Posting Schedule: daily", **When** the scheduled LinkedIn post generator runs, **Then** a file `LINKEDIN_POST_{YYYY-MM-DD}.md` is created in `vault/Pending_Approval/LinkedIn/` with YAML frontmatter (action="post_linkedin", scheduled_date, character_count≤3000, status="pending_approval") and AI-generated post body aligned with business goals

2. **Given** a LinkedIn draft file exists in `vault/Pending_Approval/LinkedIn/`, **When** the user moves it to `vault/Approved/LinkedIn/`, **Then** the LinkedIn MCP posts to LinkedIn within 30 seconds and logs the action to `vault/Logs/MCP_Actions/YYYY-MM-DD.md`

3. **Given** a LinkedIn draft exists, **When** the user moves it to `vault/Rejected/`, **Then** the post is NOT published, a `LINKEDIN_POST_{date}_v2.md` regeneration request is queued in `vault/Needs_Action/`, and the rejection is logged

4. **Given** LinkedIn posting schedule is set to "daily", **When** a post was already approved and published today, **Then** the generator does NOT create a second draft for today (deduplication)

5. **Given** the LinkedIn MCP fails (rate limit), **When** a post-approval is executed, **Then** the system retries after the rate limit window (60 minutes), logs the delay, and updates the draft file's frontmatter with status="rate_limited_retry"

6. **Given** AI draft generation is requested, **When** the Claude API is unavailable, **Then** the system creates a skeleton post template in `vault/Pending_Approval/LinkedIn/` with placeholders `[YOUR_HEADLINE]`, `[KEY_VALUE]`, `[CALL_TO_ACTION]` for manual completion

---

### User Story 3 - WhatsApp Draft Generation & Auto-Send (Priority: P1)

As a **business owner communicating with clients via WhatsApp**, I want the AI to monitor all my WhatsApp messages, automatically draft professional replies for important messages (urgent, meeting, payment, deadline), and send them after one-click approval so I can respond to clients instantly without typing every message manually.

**Why this priority**: WhatsApp is a critical business communication channel with high urgency. Clients expect rapid responses. Auto-drafting and auto-sending (with approval) eliminates response delay and ensures professional communication quality. This is P1 because WhatsApp drives real-time client engagement and revenue.

**Independent Test**: Send a WhatsApp message containing "urgent payment reminder" to your WhatsApp Web session. Within 30 seconds, verify: (1) A file `WHATSAPP_{chat_id}_{timestamp}.md` appears in `vault/Inbox/`, (2) An AI draft reply appears in `vault/Pending_Approval/WhatsApp/`, (3) User moves draft to `vault/Approved/WhatsApp/`, (4) WhatsApp MCP sends the message via WhatsApp Web automation within 30 seconds.

**Acceptance Scenarios**:

1. **Given** WhatsApp watcher is running with valid session and monitoring all chats, **When** any WhatsApp message arrives, **Then** a file `WHATSAPP_{chat_id}_{timestamp}.md` is created in `vault/Inbox/` within 30 seconds with YAML frontmatter (type="whatsapp", from={contact_name}, message_preview, timestamp, status="new")

2. **Given** a WhatsApp message contains important keywords ("urgent", "meeting", "payment", "deadline", "invoice", "asap", "help"), **When** the watcher processes it, **Then** the message is flagged with priority="High" in YAML frontmatter and an AI draft reply is generated within 15 seconds

3. **Given** an important WhatsApp message is detected, **When** AI draft generation runs, **Then** a draft file `WHATSAPP_DRAFT_{chat_id}_{timestamp}.md` is created in `vault/Pending_Approval/WhatsApp/` with YAML frontmatter (to={contact_name}, draft_body, original_message_id, action="send_whatsapp", status="pending_approval", generated_at)

4. **Given** a WhatsApp draft exists in `vault/Pending_Approval/WhatsApp/`, **When** the user moves it to `vault/Approved/WhatsApp/`, **Then** the WhatsApp MCP sends the message via Playwright automation within 30 seconds and logs the action to `vault/Logs/MCP_Actions/YYYY-MM-DD.md`

5. **Given** a WhatsApp draft exists in `vault/Pending_Approval/WhatsApp/`, **When** the user moves it to `vault/Rejected/`, **Then** the message is NOT sent, the task is moved to `vault/Done/` with status="rejected", and the rejection is logged

6. **Given** WhatsApp Web session expires (logged out), **When** the watcher attempts to poll, **Then** the system detects session expiry, creates `vault/Needs_Action/whatsapp_session_expired.md`, pauses polling, and alerts human to re-authenticate via QR code

7. **Given** WhatsApp MCP fails to send (network error or element not found), **When** the send is attempted after approval, **Then** the system retries up to 3 times (exponential backoff), logs each failure, and creates `vault/Needs_Action/retry_whatsapp_{id}.md` if all retries fail

8. **Given** Claude API is unavailable, **When** an important WhatsApp message arrives, **Then** the system creates a blank draft template in `vault/Pending_Approval/WhatsApp/` with placeholders for manual editing (graceful degradation)

9. **Given** 10 WhatsApp messages arrive simultaneously, **When** the watcher processes them, **Then** all 10 files are created in `vault/Inbox/` without race conditions, and important messages (keyword matches) receive draft replies within 60 seconds

---

### User Story 4 - Multi-Step Plan Execution (Priority: P1)

As a **user with complex multi-step tasks** (e.g., "Onboard new client: draft contract, send intro email, schedule kick-off"), I want the AI to generate an actionable plan, get my approval on the full plan before starting, and then execute each step autonomously while I watch progress in the dashboard.

**Why this priority**: Multi-step plan execution is the defining capability of Gold tier (Ralph Wiggum loop). It differentiates Gold from Silver, which only creates plans without executing them.

**Independent Test**: Add a task file to `vault/Inbox/` with title "Onboard new client - draft intro email, create calendar invite, and post LinkedIn announcement". Verify: (1) Plan.md is created in `vault/Plans/`, (2) An approval request appears in `vault/Pending_Approval/Plans/`, (3) After user approves by moving to `vault/Approved/Plans/`, the plan executes step-by-step with progress updates on Dashboard.md.

**Acceptance Scenarios**:

1. **Given** a task in `vault/Inbox/` contains multi-step keywords ("plan", "onboard", "campaign", "project", "setup"), **When** the watcher processes it with ENABLE_PLAN_EXECUTION=true, **Then** a Plan.md is created in `vault/Plans/PLAN_{name}_{date}.md` with YAML frontmatter (objective, steps array, total_steps, approval_required=true, estimated_time, status="awaiting_approval")

2. **Given** a Plan.md exists in `vault/Plans/` with status="awaiting_approval", **When** the user moves the corresponding approval file from `vault/Pending_Approval/Plans/` to `vault/Approved/Plans/`, **Then** plan execution begins within 10 seconds, starting with Step 1, and Dashboard.md updates with "Plan: [name] — Step 1/N executing"

3. **Given** plan execution is in progress, **When** Step N completes successfully, **Then** the step is marked `[x]` in Plan.md, `vault/In_Progress/{plan_id}/state.md` is updated with current step, and Dashboard.md shows "Step N+1/total executing" within 2 seconds

4. **Given** plan execution reaches a step requiring MCP action (e.g., "send email to client"), **When** that step executes, **Then** the MCP action is logged to `vault/Logs/MCP_Actions/YYYY-MM-DD.md` with the plan_id, step number, and action outcome

5. **Given** plan execution encounters an error at Step N, **When** the error occurs, **Then** the system retries Step N up to 3 times (exponential backoff), and if all retries fail: marks step as `[!]` blocked, creates `vault/Needs_Action/plan_blocked_{id}.md`, pauses execution, and alerts human

6. **Given** plan execution has run 10 iterations (max loop limit), **When** the task is still incomplete, **Then** the Ralph Wiggum loop exits, marks the plan as "escalated", and creates `vault/Needs_Action/plan_escalated_{id}.md` for human takeover

7. **Given** a completed plan, **When** all steps are marked `[x]`, **Then** the plan file is moved to `vault/Done/` and Dashboard.md shows "Plan: [name] — COMPLETED ✓"

---

### User Story 5 - MCP Multi-Server Integration (Priority: P2)

As a **power user deploying Gold tier**, I want multiple MCP servers configured (Email, LinkedIn, Calendar, Browser) so each external integration has its own dedicated server with isolated permissions, enabling the agent to take real-world actions after approval.

**Why this priority**: MCP servers are the execution backbone of Gold tier. Without them, drafts can't become real actions. This is P2 because the servers themselves are infrastructure that P1 stories depend on.

**Independent Test**: Verify 4 MCP servers are registered in `~/.config/claude-code/mcp.json`. Each server responds to a health check. An approved email draft triggers the Email MCP. An approved LinkedIn post triggers the LinkedIn MCP.

**Acceptance Scenarios**:

1. **Given** Gold tier is configured, **When** Claude Code starts, **Then** 4 MCP servers are registered: `email-mcp` (send/draft email), `linkedin-mcp` (post/read LinkedIn), `calendar-mcp` (create/read events), `browser-mcp` (navigate URLs, screenshot)

2. **Given** an email send action is approved, **When** the `email-mcp` is invoked, **Then** it sends via SMTP/Gmail API and returns a send confirmation with message_id, which is logged to `vault/Logs/MCP_Actions/`

3. **Given** a LinkedIn post is approved, **When** `linkedin-mcp` is invoked, **Then** it posts to LinkedIn and returns post_id, which is logged with timestamp and engagement_url

4. **Given** a calendar event creation is part of a plan step, **When** `calendar-mcp` is invoked, **Then** it creates the event and returns event_id, which is logged

5. **Given** any MCP server is unavailable, **When** an approved action requires it, **Then** the system logs the failure, creates a `vault/Needs_Action/mcp_unavailable_{server}.md`, and does NOT silently fail or block other MCP servers

---

### User Story 6 - Weekly Business Audit & CEO Briefing (Priority: P2)

As a **CEO/business owner**, I want the AI to automatically generate a weekly audit every Sunday night summarizing tasks completed, pending items, and proactive business suggestions so I start Monday with clear situational awareness.

**Why this priority**: The CEO Briefing is a Gold tier requirement per constitution. It delivers autonomous intelligence without any user trigger, demonstrating the agent's proactive capability.

**Independent Test**: Manually trigger CEO Briefing generation (`python scripts/ceo_briefing.py --force`). Verify a file `vault/Briefings/YYYY-MM-DD_Monday_Briefing.md` is created with all required sections within 30 seconds.

**Acceptance Scenarios**:

1. **Given** the scheduled CEO Briefing task is configured (Sunday 23:00), **When** Sunday 23:00 arrives, **Then** the system generates `vault/Briefings/{next_monday_date}_Monday_Briefing.md` with sections: Executive Summary, Tasks Completed This Week, Tasks Pending/Blocked, Proactive Suggestions, Next Week Focus

2. **Given** CEO Briefing generation runs, **When** the Briefing file is created, **Then** it includes accurate counts from `vault/Done/` (tasks completed this week) and `vault/Needs_Action/` (pending items) queried from vault markdown files

3. **Given** Proactive Suggestions section is generated, **When** the Claude API produces suggestions, **Then** the section includes at least 3 actionable items such as unanswered high-priority emails, overdue plan steps, and LinkedIn posts pending more than 48 hours

4. **Given** CEO Briefing runs but Claude API is unavailable, **When** the briefing is generated, **Then** the system produces a data-only briefing (task counts, file lists) without AI narrative, marking AI sections as "[API Unavailable - Manual Review Required]"

---

### User Story 7 - Cross-Domain Integration & Odoo Accounting Drafts (Priority: P3)

As a **business owner managing both personal and business workflows**, I want the agent to integrate Odoo Community (local) for draft accounting entries and route tasks to the correct domain (Personal vs Business) so my accounting and operational workflows are connected.

**Why this priority**: Odoo integration is a Gold tier requirement per constitution. It's P3 because it requires self-hosted Odoo setup which is optional infrastructure, and email/LinkedIn/plan-execution deliver more immediate value.

**Independent Test**: Configure Odoo MCP with local Odoo URL. Add a task file with type="expense" to `vault/Inbox/`. Verify a draft expense entry appears in `vault/Pending_Approval/Odoo/` within 15 seconds without any entry posted to Odoo automatically.

**Acceptance Scenarios**:

1. **Given** Odoo MCP is configured with local Odoo instance URL, **When** a task file with type="invoice" or type="expense" is detected in `vault/Inbox/`, **Then** an Odoo draft entry file is created in `vault/Pending_Approval/Odoo/` with YAML frontmatter (action="create_draft_invoice"|"log_expense", odoo_data object, status="pending_approval")

2. **Given** an Odoo draft entry is approved (moved to `vault/Approved/Odoo/`), **When** the Odoo MCP executes, **Then** it creates the draft entry in Odoo Community via JSON-RPC API (NOT posted/confirmed), logs the Odoo record_id to MCP action log

3. **Given** Odoo MCP is not configured or Odoo is offline, **When** an accounting task is detected, **Then** the system creates a manual entry template in `vault/Pending_Approval/Odoo/` for offline review, never crashes, and continues processing other tasks normally

---

### User Story 8 - Social Media Integration (Facebook/Instagram/Twitter) (Priority: P1)

As a **business owner maintaining presence across multiple social media platforms**, I want the AI to generate and post content to Facebook, Instagram, and Twitter (X) with human approval so I can maintain consistent brand visibility and engagement across all major social networks without manual posting to each platform.

**Why this priority**: Multi-platform social media presence is a Gold tier hackathon requirement. Facebook, Instagram, and Twitter are critical business channels alongside LinkedIn. Automating content distribution across all platforms maximizes reach and engagement while minimizing manual effort. This is P1 because social media visibility directly drives brand awareness and customer acquisition.

**Independent Test**: Configure Facebook, Instagram, and Twitter MCPs with API credentials. Trigger social media post generation script. Within 15 seconds, verify drafts appear in `vault/Pending_Approval/Social/{Facebook,Instagram,Twitter}/`. User moves drafts to `vault/Approved/Social/{platform}/`. MCPs post to respective platforms within 30 seconds each.

**Acceptance Scenarios**:

1. **Given** Facebook MCP is configured with valid Graph API credentials, **When** a social media post generation is triggered, **Then** a draft file `FACEBOOK_POST_{YYYY-MM-DD}.md` is created in `vault/Pending_Approval/Social/Facebook/` with YAML frontmatter (action="create_post", post_content, scheduled_date, character_count, status="pending_approval")

2. **Given** Instagram MCP is configured with valid Basic Display API credentials, **When** a social media post generation is triggered with image, **Then** a draft file `INSTAGRAM_POST_{YYYY-MM-DD}.md` is created in `vault/Pending_Approval/Social/Instagram/` with YAML frontmatter (action="create_post", caption, image_path, scheduled_date, hashtags, status="pending_approval")

3. **Given** Twitter MCP is configured with valid API v2 credentials, **When** a social media post generation is triggered, **Then** a draft file `TWITTER_POST_{YYYY-MM-DD}.md` is created in `vault/Pending_Approval/Social/Twitter/` with YAML frontmatter (action="create_tweet", tweet_content, character_count≤280, scheduled_date, status="pending_approval")

4. **Given** social media drafts exist in `vault/Pending_Approval/Social/{platform}/`, **When** the user moves them to `vault/Approved/Social/{platform}/`, **Then** the respective MCP (Facebook/Instagram/Twitter) posts to the platform within 30 seconds and logs the action to `vault/Logs/MCP_Actions/YYYY-MM-DD.md`

5. **Given** a social media draft exists in `vault/Pending_Approval/Social/{platform}/`, **When** the user moves it to `vault/Rejected/`, **Then** the post is NOT published, the task is moved to `vault/Done/` with status="rejected", and the rejection is logged

6. **Given** any social media MCP fails (rate limit, network error, auth failure), **When** a post-approval is executed, **Then** the system retries with exponential backoff (3 attempts: 5s, 10s, 20s), logs each failure, and creates `vault/Needs_Action/retry_{platform}_{id}.md` if all retries fail

7. **Given** Twitter character limit is 280 characters, **When** AI generates tweet content >280 characters, **Then** the system auto-truncates at last complete word, adds "…", and logs warning in draft frontmatter

8. **Given** Instagram post requires an image, **When** no image is provided in draft, **Then** the system creates draft with placeholder `[IMAGE_REQUIRED]` and adds `requires_image=true` to frontmatter, blocking post until user adds image path

9. **Given** Facebook API returns authentication error, **When** the Facebook MCP attempts to post, **Then** the system logs auth failure, creates `vault/Needs_Action/facebook_auth_expired.md`, pauses Facebook posting, and alerts human to refresh access token

10. **Given** all three social media platforms (Facebook/Instagram/Twitter) are configured, **When** a unified social media campaign is generated, **Then** the system creates coordinated drafts for all three platforms in their respective pending approval folders, each tailored to platform-specific constraints and best practices

---

### Edge Cases

- **What happens when multiple approval files are moved simultaneously?** → Each file move triggers an independent watcher event; actions execute in parallel up to MCP rate limits; all are logged independently

- **What happens when the vault/ folder has no write permission?** → System logs "Vault write permission denied", pauses execution, creates `vault/Logs/errors.md` with recovery instructions, alerts human

- **What happens when a Plan.md has circular step dependencies?** → System detects the cycle during plan validation, marks the plan as "invalid_cycle", creates a human review request in `vault/Needs_Action/`, never enters an infinite loop

- **What happens when Email MCP sends an email that bounces?** → Bounce notification is created in `vault/Inbox/EMAIL_BOUNCE_{id}.md` by the Gmail watcher on next poll; associated plan step remains `[x]` completed (send was executed); human is notified of bounce

- **What happens when LinkedIn post character limit is exceeded?** → Draft generation detects >3000 characters, automatically truncates at the last complete sentence, adds "[…]", logs a warning in the draft frontmatter

- **What happens when WhatsApp Web session expires mid-operation?** → Watcher detects login screen, creates `vault/Needs_Action/whatsapp_session_expired.md`, pauses polling, alerts human to re-scan QR code

- **What happens when WhatsApp message contains media (image, video, audio)?** → Watcher creates task file with `has_media=true` in frontmatter, AI draft includes "[Media received: {type}]" placeholder, user manually handles media in draft approval

- **What happens when multiple WhatsApp messages arrive in the same chat within 30 seconds?** → Each message creates separate task file; AI drafts may reference previous messages in thread; user approves each reply individually

- **What happens when ENABLE_PLAN_EXECUTION=false?** → System operates in Silver mode: creates Plan.md files but does NOT execute steps autonomously; all plan steps remain manual (backward compatible)

- **What happens when the agent reaches max plan iterations (10) on a simple 3-step plan?** → This indicates a logic loop; system escalates immediately, logs full iteration history to `vault/Logs/`, creates detailed escalation report for human

---

## Requirements *(mandatory)*

### Functional Requirements

#### Email Draft Generation (Gold Core)

- **FR-G001**: System MUST provide `ENABLE_PLAN_EXECUTION` flag in `.env` (default: false). When false, Gold watcher creates plans/drafts but does NOT execute MCP actions autonomously

- **FR-G002**: System MUST detect high-priority email tasks in `vault/Inbox/` (YAML frontmatter: type="email", priority="High") and generate AI draft replies within 15 seconds

- **FR-G003**: System MUST save email drafts to `vault/Pending_Approval/Email/EMAIL_DRAFT_{id}.md` with YAML frontmatter: to, from, subject, draft_body, original_email_id, action="send_email", status="pending_approval", generated_at

- **FR-G004**: System MUST monitor `vault/Approved/Email/` for approved drafts and invoke Email MCP to send within 30 seconds of file appearance

- **FR-G005**: System MUST monitor `vault/Rejected/` for rejected drafts and log rejection without sending; task moves to `vault/Done/` with status="rejected"

- **FR-G006**: Email draft body MUST include: greeting, professional response to email content, call-to-action if applicable, sender name from Company_Handbook.md

- **FR-G007**: System MUST sanitize email content before sending to Claude API: strip attachments, limit content to title + first 200 characters of body (data safety)

- **FR-G008**: Email MCP MUST retry failed sends with exponential backoff: attempt 1 at 5s, attempt 2 at 10s, attempt 3 at 20s; after 3 failures create `vault/Needs_Action/retry_send_{id}.md`

#### LinkedIn Post Generation (Gold Core)

- **FR-G009**: System MUST provide `scripts/linkedin_post_generator.py` that generates LinkedIn post drafts using Claude API aligned with `Company_Handbook.md` Business Goals section

- **FR-G010**: System MUST save LinkedIn drafts to `vault/Pending_Approval/LinkedIn/LINKEDIN_POST_{YYYY-MM-DD}.md` with YAML frontmatter: action="post_linkedin", scheduled_date, character_count, business_goal_reference, status="pending_approval"

- **FR-G011**: System MUST enforce posting limit: max 1 LinkedIn post per day per schedule. Deduplicate by checking `vault/Done/` for same-date posts before creating draft

- **FR-G012**: System MUST monitor `vault/Approved/LinkedIn/` and invoke LinkedIn MCP to post within 30 seconds of approval file appearance

- **FR-G013**: LinkedIn post content MUST be ≤3000 characters. If AI draft exceeds limit, system auto-truncates at last sentence and logs warning in draft frontmatter

- **FR-G014**: When a LinkedIn post is rejected, system MUST create `LINKEDIN_POST_{date}_retry.md` in `vault/Needs_Action/` for regeneration on next cycle

- **FR-G015**: LinkedIn MCP MUST handle rate limits: if LinkedIn API returns 429, back off for 60 minutes and update draft status to "rate_limited_retry"

#### WhatsApp Draft Generation & Auto-Send (Gold Core)

- **FR-G016**: System MUST provide `scripts/whatsapp_watcher.py` using Playwright to monitor WhatsApp Web for all incoming messages via browser automation

- **FR-G017**: WhatsApp watcher MUST create task files in `vault/Inbox/` for ALL incoming WhatsApp messages with filename: `WHATSAPP_{chat_id}_{timestamp}.md`

- **FR-G018**: WhatsApp task files MUST include YAML frontmatter: type="whatsapp", from={contact_name}, message_preview (first 100 chars), timestamp, keywords_matched (array), priority (High if keywords match, Medium otherwise), status="new"

- **FR-G019**: System MUST detect important WhatsApp messages using keywords: "urgent", "meeting", "payment", "deadline", "invoice", "asap", "help", "client", "contract". Messages matching ANY keyword flagged priority="High"

- **FR-G020**: System MUST generate AI draft replies for high-priority WhatsApp messages within 15 seconds of detection

- **FR-G021**: WhatsApp drafts MUST be saved to `vault/Pending_Approval/WhatsApp/WHATSAPP_DRAFT_{chat_id}_{timestamp}.md` with YAML frontmatter: to={contact_name}, draft_body, original_message_id, action="send_whatsapp", status="pending_approval", generated_at

- **FR-G022**: WhatsApp draft body MUST be concise (≤500 characters), professional, and contextually appropriate to the received message content

- **FR-G023**: System MUST monitor `vault/Approved/WhatsApp/` for approved drafts and invoke WhatsApp MCP (Playwright automation) to send within 30 seconds

- **FR-G024**: WhatsApp MCP MUST send messages by: (1) navigating to correct chat via WhatsApp Web, (2) typing draft_body into message input field, (3) clicking send button, (4) confirming message appears in chat history, (5) logging success to `vault/Logs/MCP_Actions/`

- **FR-G025**: System MUST monitor `vault/Rejected/` for rejected WhatsApp drafts and log rejection without sending; task moves to `vault/Done/` with status="rejected"

- **FR-G026**: WhatsApp watcher MUST poll WhatsApp Web every 30 seconds for new messages. Polling interval configurable via WHATSAPP_POLL_INTERVAL in .env

- **FR-G027**: WhatsApp watcher MUST handle session expiry: detect WhatsApp Web login screen, create `vault/Needs_Action/whatsapp_session_expired.md`, pause polling until re-authenticated

- **FR-G028**: WhatsApp MCP MUST implement QR code authentication setup: (1) Open WhatsApp Web, (2) Wait for QR code, (3) Display QR code in terminal or save as image, (4) Wait for successful scan, (5) Save session state to `WHATSAPP_SESSION_PATH`

- **FR-G029**: WhatsApp session state MUST persist across restarts. Watcher MUST load saved session from `WHATSAPP_SESSION_PATH` on startup to avoid re-authentication

- **FR-G030**: WhatsApp MCP MUST retry failed sends with exponential backoff: attempt 1 at 5s, attempt 2 at 10s, attempt 3 at 20s; after 3 failures create `vault/Needs_Action/retry_whatsapp_{id}.md`

- **FR-G031**: System MUST sanitize WhatsApp message content before sending to Claude API: limit to first 200 characters, remove phone numbers, strip media attachments (data safety)

- **FR-G032**: If Claude API is unavailable when high-priority WhatsApp message arrives, system MUST create blank draft template in `vault/Pending_Approval/WhatsApp/` for manual editing (graceful degradation)

- **FR-G033**: System MUST provide setup documentation at `docs/gold/whatsapp-setup.md` including: WhatsApp Web authentication process, Playwright installation (`playwright install chromium`), session management, QR code scanning, testing checklist

#### Multi-Step Plan Execution — Ralph Wiggum Loop (Gold Core)

- **FR-G034**: System MUST detect multi-step tasks in `vault/Inbox/` using keywords: "plan", "onboard", "campaign", "project", "setup", "implement", "coordinate"

- **FR-G035**: System MUST generate `vault/Plans/PLAN_{name}_{date}.md` with YAML frontmatter: plan_id, objective, steps (array of {step_num, description, action_type, dependencies, status}), total_steps, estimated_time, approval_required=true, status="awaiting_approval"

- **FR-G036**: System MUST create approval request in `vault/Pending_Approval/Plans/PLAN_{id}_approval.md` before executing ANY plan step. No execution without approval

- **FR-G037**: System MUST implement Ralph Wiggum loop with max 10 iterations. Loop state tracked in `vault/In_Progress/{plan_id}/state.md` (current_step, iterations_remaining, last_action)

- **FR-G038**: After each plan step completes, system MUST: update step status to `[x]` in Plan.md, update `vault/In_Progress/{plan_id}/state.md`, update Dashboard.md with current progress within 2 seconds

- **FR-G039**: On plan step failure (after 3 retries), system MUST: mark step as `[!]` in Plan.md, pause execution, create `vault/Needs_Action/plan_blocked_{id}.md`, log full error context

- **FR-G040**: On reaching max iterations (10) without completion, system MUST: exit loop, create `vault/Needs_Action/plan_escalated_{id}.md`, log full iteration history, update plan status to "escalated"

- **FR-G041**: Completed plans (all steps `[x]`) MUST be moved to `vault/Done/PLAN_{id}_complete.md` and Dashboard.md updated with "COMPLETED ✓"

- **FR-G042**: System MUST support plan step dependencies: if Step 3 depends on Step 2, execution waits for Step 2 to reach `[x]` before starting Step 3

#### MCP Server Configuration (Gold Core)

- **FR-G043**: System MUST configure minimum 2 MCP servers in `~/.config/claude-code/mcp.json`: `email-mcp` (email send/draft) and `linkedin-mcp` (post/read). Additional servers (calendar-mcp, browser-mcp, odoo-mcp) are optional but documented

- **FR-G044**: System MUST log ALL MCP actions to `vault/Logs/MCP_Actions/YYYY-MM-DD.md` with: timestamp, mcp_server, action, payload_summary (no PII), outcome, plan_id (if part of plan), human_approved=true

- **FR-G045**: System MUST verify MCP server availability on startup. For unavailable MCPs, log warning and continue (degrade gracefully, never crash)

- **FR-G046**: System MUST never invoke MCP actions without corresponding approval file in `vault/Approved/` (safety gate)

#### Weekly CEO Briefing (Gold Automation)

- **FR-G047**: System MUST schedule CEO Briefing generation weekly on Sunday at 23:00 local time via cron or task scheduler

- **FR-G048**: CEO Briefing MUST be created at `vault/Briefings/{next_monday_YYYY-MM-DD}_Monday_Briefing.md` with YAML frontmatter: created_at, week_start, week_end, total_tasks_completed, total_pending

- **FR-G049**: Briefing MUST include sections: Executive Summary, Tasks Completed This Week (with links), Tasks Pending/Blocked, Proactive Suggestions (3+ items), Next Week Focus, API Cost This Week

- **FR-G050**: Proactive Suggestions MUST include: unanswered high-priority emails >24h old, overdue plan steps (past estimated_time), and LinkedIn posts pending approval >48h

- **FR-G051**: If Claude API unavailable during briefing generation, system MUST produce a data-only briefing (counts and file lists) with AI sections marked "[API Unavailable - Manual Review Required]"

#### Cross-Domain Integration (Gold Extension)

- **FR-G052**: System MUST route tasks to Personal or Business domain based on task category (from Silver AI categorization): Work/Urgent → Business domain; Personal → Personal domain

- **FR-G053**: System MUST provide optional Odoo MCP integration (ENABLE_ODOO=true in .env). When enabled, detect invoice/expense tasks and create Odoo draft entries via JSON-RPC API (draft only, never post)

- **FR-G054**: Odoo drafts MUST be saved to `vault/Pending_Approval/Odoo/` before any Odoo API call. Odoo MCP only invoked after file appears in `vault/Approved/Odoo/`

- **FR-G055**: When Odoo is disabled or offline, all accounting tasks MUST fall back to creating manual entry templates in `vault/Pending_Approval/Odoo/` for offline review

#### Social Media Integration (Facebook/Instagram/Twitter) (Gold Core)

- **FR-G056**: System MUST provide Facebook MCP integration using Facebook Graph API for creating posts and reading feed summaries

- **FR-G057**: System MUST save Facebook post drafts to `vault/Pending_Approval/Social/Facebook/FACEBOOK_POST_{YYYY-MM-DD}.md` with YAML frontmatter: action="create_post", post_content, scheduled_date, character_count, status="pending_approval", generated_at

- **FR-G058**: System MUST monitor `vault/Approved/Social/Facebook/` and invoke Facebook MCP to post within 30 seconds of approval file appearance

- **FR-G059**: System MUST provide Instagram MCP integration using Instagram Basic Display API for creating posts and stories with images

- **FR-G060**: System MUST save Instagram post drafts to `vault/Pending_Approval/Social/Instagram/INSTAGRAM_POST_{YYYY-MM-DD}.md` with YAML frontmatter: action="create_post", caption, image_path, hashtags (array), scheduled_date, status="pending_approval", generated_at, requires_image=true

- **FR-G061**: Instagram drafts MUST validate image_path exists before posting. If image missing, system creates `vault/Needs_Action/instagram_image_required_{id}.md`

- **FR-G062**: System MUST provide Twitter (X) MCP integration using Twitter API v2 for creating tweets and reading mentions

- **FR-G063**: System MUST save Twitter post drafts to `vault/Pending_Approval/Social/Twitter/TWITTER_POST_{YYYY-MM-DD}.md` with YAML frontmatter: action="create_tweet", tweet_content, character_count≤280, scheduled_date, status="pending_approval", generated_at

- **FR-G064**: Twitter draft content MUST be ≤280 characters. If AI draft exceeds limit, system auto-truncates at last complete word, adds "…", and logs warning in draft frontmatter

- **FR-G065**: System MUST monitor `vault/Approved/Social/{Facebook,Instagram,Twitter}/` folders and invoke respective MCPs to post within 30 seconds of approval

- **FR-G066**: Social media MCPs MUST handle platform-specific errors: rate limits (retry after backoff), auth failures (create Needs_Action file), network errors (exponential backoff 3x)

- **FR-G067**: System MUST log all social media posts to `vault/Logs/MCP_Actions/YYYY-MM-DD.md` with YAML frontmatter: platform (facebook|instagram|twitter), post_id, post_url, timestamp, human_approved=true, approval_file_path

- **FR-G068**: When social media API credentials are invalid or expired, system MUST create `vault/Needs_Action/{platform}_auth_expired.md`, pause posting for that platform, and continue processing other platforms

- **FR-G069**: System MUST support coordinated multi-platform posting: generate drafts for Facebook/Instagram/Twitter simultaneously from single trigger, tailored to each platform's constraints

- **FR-G070**: Social media post generation MUST read `Company_Handbook.md` Business Goals and Social Media Strategy sections to align content with brand voice and objectives

#### Backward Compatibility (Gold Guarantee)

- **FR-G071**: All Silver tier functional requirements (FR-S001 through FR-S044) MUST remain functional in Gold tier

- **FR-G072**: All Bronze tier functional requirements (FR-B001 through FR-B025) MUST remain functional in Gold tier

- **FR-G073**: When ENABLE_PLAN_EXECUTION=false, system MUST operate identically to Silver tier (create plans/drafts, no autonomous execution)

- **FR-G074**: Gold tier MUST maintain Bronze+Silver performance targets: Dashboard update <2s, file detection <30s, AI analysis <5s

#### Audit Logging (Gold Mandate)

- **FR-G075**: ALL agent actions MUST be logged to `vault/Logs/` BEFORE execution, per constitution mandate. Log format: `YYYY-MM-DD_HH-MM-SS_action-name.md` with YAML frontmatter (timestamp, tier="gold", action, reasoning, outcome, human_approved)

- **FR-G076**: Log retention MUST be minimum 90 days. System MUST prune logs older than 90 days automatically on weekly audit run

- **FR-G077**: System MUST provide log categories: `Watcher_Activity/`, `MCP_Actions/`, `API_Usage/`, `Error_Recovery/`, `Human_Approvals/`, `Plan_Execution/`

### Non-Functional Requirements

#### Performance (NFR-G-PERF)

- **NFR-G-PERF-001**: Email draft generation MUST complete within 15 seconds (including AI draft call)
- **NFR-G-PERF-002**: LinkedIn post generation MUST complete within 15 seconds
- **NFR-G-PERF-003**: WhatsApp draft generation MUST complete within 15 seconds; WhatsApp send via Playwright MUST complete within 30 seconds
- **NFR-G-PERF-004**: Plan execution step transition MUST complete within 10 seconds
- **NFR-G-PERF-005**: Dashboard update during plan execution MUST complete within 2 seconds
- **NFR-G-PERF-006**: CEO Briefing generation MUST complete within 60 seconds (may include API call)
- **NFR-G-PERF-007**: MCP action invocation (email send, LinkedIn post, WhatsApp send) MUST complete within 30 seconds

#### Reliability (NFR-G-REL)

- **NFR-G-REL-001**: System MUST handle MCP failures gracefully: retry 3 times with exponential backoff before human escalation
- **NFR-G-REL-002**: Plan execution MUST resume from last completed step after agent restart (state persisted in `vault/In_Progress/`)
- **NFR-G-REL-003**: Ralph Wiggum loop MUST never exceed 10 iterations (hard limit enforced via counter in state.md)
- **NFR-G-REL-004**: System MUST handle vault write errors: retry 3 times, log error, skip and continue if still failing
- **NFR-G-REL-005**: System MUST survive Obsidian vault being open simultaneously (file locking with 3 retries, 500ms delay)
- **NFR-G-REL-006**: WhatsApp session MUST persist across watcher restarts without re-authentication (session state saved to disk)
- **NFR-G-REL-007**: WhatsApp watcher MUST handle session expiry gracefully: detect logout, pause, alert human, never crash

#### Security (NFR-G-SEC)

- **NFR-G-SEC-001**: MCP server credentials (SMTP password, LinkedIn API token, WhatsApp session files) MUST be in `.env` or secure session storage (never in code or logs)
- **NFR-G-SEC-002**: Logs MUST never contain: email addresses, phone numbers, account numbers, API keys, WhatsApp message content beyond 50 characters, or contact names
- **NFR-G-SEC-003**: Human approval gate MUST be enforced before ALL MCP actions (no approval file = no MCP invocation)
- **NFR-G-SEC-004**: Odoo MCP MUST use read/draft-only permissions (never confirmation, payment, or delete operations)
- **NFR-G-SEC-005**: MCP audit log MUST record: who approved (file timestamp), what was approved (action type), when executed (timestamp), outcome

#### Usability (NFR-G-USE)

- **NFR-G-USE-001**: Upgrade path: Users upgrade Silver→Gold by adding ENABLE_PLAN_EXECUTION=true and MCP server configs. No code changes, no data migration
- **NFR-G-USE-002**: Dashboard MUST include a "Gold Tier Status" section: Plan Execution (Enabled/Disabled), Active Plans (count), Pending Approvals (count by type), MCP Servers (email ✓/✗, whatsapp ✓/✗, linkedin ✓/✗)
- **NFR-G-USE-003**: Approval workflow MUST be pure file-move: user drags file from `Pending_Approval/` to `Approved/` in Obsidian (no CLI commands required)
- **NFR-G-USE-004**: Error messages in `vault/Needs_Action/` MUST be human-readable with clear resolution steps

---

### Key Entities

- **EmailDraft**: AI-generated reply to inbox email
  - Attributes: draft_id, original_email_id, to, subject, draft_body, status ("pending_approval"|"approved"|"rejected"|"sent"|"failed"), generated_at, sent_at

- **LinkedInDraft**: AI-generated LinkedIn post
  - Attributes: draft_id, scheduled_date, business_goal_reference, post_content, character_count, status ("pending_approval"|"approved"|"posted"|"rejected"|"rate_limited_retry"), generated_at, posted_at

- **WhatsAppDraft**: AI-generated WhatsApp reply
  - Attributes: draft_id, original_message_id, to (contact_name), chat_id, draft_body, status ("pending_approval"|"approved"|"rejected"|"sent"|"failed"), generated_at, sent_at, keywords_matched (array)

- **Plan**: Multi-step execution plan (extends Silver Plan)
  - Attributes: plan_id, objective, steps (array), total_steps, completed_steps, status ("awaiting_approval"|"executing"|"completed"|"blocked"|"escalated"), approval_file_path, iteration_count

- **PlanStep** (extended): Single executable step
  - Attributes: step_num, description, action_type ("mcp_email"|"mcp_linkedin"|"create_file"|"notify_human"), dependencies (step_num array), status ("pending"|"executing"|"completed"|"blocked"), mcp_action_log_id

- **ExecutionState**: Ralph Wiggum loop state (in `vault/In_Progress/{plan_id}/state.md`)
  - Attributes: plan_id, current_step, iterations_remaining, last_action, last_action_timestamp, loop_start_time

- **MCPActionLog**: Record of MCP invocation
  - Attributes: log_id, mcp_server, action, payload_summary, outcome, plan_id, step_num, timestamp, human_approved, approval_file_path

- **CEOBriefing**: Weekly executive report
  - Attributes: briefing_date, week_start, week_end, tasks_completed_count, tasks_pending_count, proactive_suggestions (array), api_cost_week, generated_by ("ai"|"data_only")

- **OdooDraft**: Accounting entry pending Odoo submission
  - Attributes: draft_id, entry_type ("invoice"|"expense"), odoo_data, status ("pending_approval"|"submitted"|"rejected"), odoo_record_id (after submission)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-G001**: User can upgrade from Silver to Gold by updating `.env` with `ENABLE_PLAN_EXECUTION=true` and MCP configs; upgrade completes without data loss and Bronze/Silver features remain functional

- **SC-G002**: Email draft generation: 90% of high-priority inbox emails receive AI-drafted replies within 15 seconds of detection. Drafts require zero editing for simple acknowledgment-type replies in 70% of cases

- **SC-G003**: LinkedIn post approval-to-publish workflow completes in under 60 seconds from file move to live post. User produces at least 5 LinkedIn posts per week without writing from scratch

- **SC-G004**: WhatsApp draft generation and auto-send: 90% of important WhatsApp messages (keyword matches) receive AI-drafted replies within 15 seconds. Approved drafts are sent via Playwright within 30 seconds. User responds to 20+ WhatsApp messages per day with minimal manual typing

- **SC-G005**: Multi-step plan execution: plans with 5 steps execute to completion in under 5 minutes (with pre-approved plan). Step progress visible on Dashboard.md within 2 seconds of each step completing

- **SC-G006**: Ralph Wiggum loop never exceeds 10 iterations. Loop completion rate (tasks finished without human escalation) ≥ 80% for well-defined 3-5 step plans

- **SC-G007**: MCP servers operational: 99% uptime for email-mcp, whatsapp-mcp, and linkedin-mcp. Failed MCP actions are retried and resolved within 5 minutes or escalated to human with clear error context

- **SC-G008**: CEO Briefing generated every Monday morning (Sunday 23:00 generation, available by 08:00 Monday). Briefing contains accurate task counts verified by manual vault review in 100% of weeks

- **SC-G009**: Human approval gate is never bypassed: 0 MCP actions executed without a corresponding file in `vault/Approved/`. Verified by audit log cross-check

- **SC-G010**: All Bronze + Silver success criteria (SC-B001–SC-B012, SC-S001–SC-S012) remain met in Gold tier (full regression verification)

- **SC-G011**: Audit logs complete and accurate: 100% of MCP actions have corresponding log entries in `vault/Logs/MCP_Actions/` within 2 seconds of execution

- **SC-G012**: Graceful degradation verified: disable each MCP server one at a time; Gold tier continues operating for all other features without crashes or data loss

- **SC-G013**: When ENABLE_PLAN_EXECUTION=false, system behaves identically to Silver tier; all Silver success criteria pass unchanged

### Definition of Done

Gold Tier is **Done** when:

1. ✅ All 7 user stories have passing acceptance tests
2. ✅ All 62 functional requirements (FR-G001 through FR-G062) are implemented
3. ✅ All non-functional requirements (NFR-G-*) are verified
4. ✅ All 13 success criteria (SC-G001 through SC-G013) are met
5. ✅ All Bronze + Silver tests still pass (backward compatibility confirmed)
6. ✅ Pytest unit tests achieve 80%+ coverage for new Gold agent_skills modules
7. ✅ Integration test passes: high-priority email → draft generated → user approves → Email MCP sends → logged
8. ✅ Integration test passes: important WhatsApp message → draft generated → user approves → WhatsApp MCP sends via Playwright → logged
9. ✅ Integration test passes: LinkedIn trigger → draft generated → user approves → LinkedIn MCP posts → logged
10. ✅ Integration test passes: multi-step task → Plan.md created → user approves → Ralph Wiggum executes all steps → moved to Done
11. ✅ CEO Briefing: manually triggered briefing generates with correct counts and AI narrative (API available)
12. ✅ Safety test: ENABLE_PLAN_EXECUTION=false → no MCP actions executed; all drafts created as expected
13. ✅ Human approval gate audit: verify 0 MCP actions exist in logs without matching `vault/Approved/` file
14. ✅ WhatsApp session persistence verified: restart watcher after QR auth, session reloads without re-scanning
15. ✅ WhatsApp setup documentation complete at `docs/gold/whatsapp-setup.md`

---

## Dependencies

### Inherits From Silver Tier

- All Silver dependencies (anthropic, watchdog, gmail API, playwright, aiohttp, pytest)
- `agent_skills/ai_analyzer.py` — extended for draft generation
- `agent_skills/vault_parser.py` — unchanged
- `agent_skills/dashboard_updater.py` — extended for Gold status section
- `scripts/gmail_watcher.py` — extended with draft generation trigger
- `scripts/whatsapp_watcher.py` — NEW: WhatsApp Web automation with Playwright
- `scripts/linkedin_generator.py` — extended with LinkedIn MCP invocation

### New Python Packages (Gold additions to pyproject.toml)

```toml
# Gold additions
"smtplib",                              # Email send (stdlib)
"imaplib",                              # Email read/search (stdlib)
"requests>=2.31.0",                     # LinkedIn API calls
"xmlrpc.client",                        # Odoo JSON-RPC (stdlib)
"schedule>=1.2.0",                      # Cron-like scheduling
"filelock>=3.12.0",                     # Cross-platform file locking
```

### MCP Servers Required

- **email-mcp**: Send emails via SMTP/Gmail API; search inbox (required)
- **whatsapp-mcp**: Monitor and send WhatsApp messages via Playwright automation of WhatsApp Web (required)
- **linkedin-mcp**: Post to LinkedIn via LinkedIn API v2; read feed (required)
- **facebook-mcp**: Post to Facebook via Graph API; read feed and messages (required for Gold tier hackathon)
- **instagram-mcp**: Post images/stories to Instagram via Basic Display API; read feed (required for Gold tier hackathon)
- **twitter-mcp**: Post tweets via Twitter API v2; read mentions and timeline (required for Gold tier hackathon)
- **calendar-mcp**: Create calendar events; read availability (optional, for plan steps)
- **browser-mcp**: Navigate URLs, screenshot pages (optional, for portal automation)
- **odoo-mcp**: Odoo Community JSON-RPC API for draft entries (optional, requires self-hosted Odoo)

### Configuration Files (.env additions)

```bash
# Inherits all Silver .env variables

# Gold tier activation
ENABLE_PLAN_EXECUTION=true
TIER=gold

# Email MCP (required)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=app-specific-password    # Gmail app password

# LinkedIn MCP (required)
LINKEDIN_ACCESS_TOKEN=your-oauth2-token
LINKEDIN_AUTHOR_URN=urn:li:person:xxxxx

# WhatsApp MCP (required)
WHATSAPP_SESSION_PATH=/path/to/whatsapp_session  # Playwright session storage
WHATSAPP_POLL_INTERVAL=30                        # Seconds between polls
WHATSAPP_KEYWORDS=urgent,meeting,payment,deadline,invoice,asap,help,client,contract

# Facebook MCP (required for Gold tier hackathon)
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret
FACEBOOK_ACCESS_TOKEN=your-facebook-page-access-token
FACEBOOK_PAGE_ID=your-facebook-page-id

# Instagram MCP (required for Gold tier hackathon)
INSTAGRAM_APP_ID=your-instagram-app-id
INSTAGRAM_APP_SECRET=your-instagram-app-secret
INSTAGRAM_ACCESS_TOKEN=your-instagram-access-token
INSTAGRAM_USER_ID=your-instagram-business-account-id

# Twitter (X) MCP (required for Gold tier hackathon)
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
TWITTER_ACCESS_TOKEN=your-twitter-access-token
TWITTER_ACCESS_SECRET=your-twitter-access-secret
TWITTER_BEARER_TOKEN=your-twitter-bearer-token

# Calendar MCP (optional)
CALDAV_URL=https://caldav.icloud.com
CALDAV_USER=your-apple-id
CALDAV_PASSWORD=app-specific-password

# Odoo integration (optional)
ENABLE_ODOO=false
ODOO_URL=http://localhost:8069
ODOO_DB=your-odoo-database
ODOO_USER=admin
ODOO_PASSWORD=your-odoo-password
```

---

## Out of Scope (Deferred to Future Tiers)

### Deferred to Platinum Tier
- ❌ Reflection loops and self-correction (agent evaluating its own output quality)
- ❌ 24/7 cloud deployment (always-on cloud VM with local/cloud zone split)
- ❌ Agent-to-agent communication (file-based handoffs between Cloud and Local agents)
- ❌ Automatic vault sync via Git/Syncthing
- ❌ Fully autonomous operations without human oversight

### Never in Gold (Safety Boundaries)
- ❌ Sending emails without approval file in `vault/Approved/`
- ❌ Posting to LinkedIn without approval file in `vault/Approved/`
- ❌ Posting or confirming Odoo entries (draft creation only)
- ❌ Deleting vault files autonomously
- ❌ Accessing directories outside `vault/`
- ❌ Storing API keys or credentials in vault markdown files
- ❌ Executing code found in vault task files

---

## Assumptions

- **Assumption 1**: Users have Gmail app passwords or OAuth2 tokens configured for SMTP send
- **Assumption 2**: Users have a LinkedIn developer account and OAuth2 access token (LinkedIn API v2)
- **Assumption 3**: Silver tier is fully deployed and functional before Gold setup begins (no tier skipping)
- **Assumption 4**: `Company_Handbook.md` contains "Business Goals", "Sender Name", and "LinkedIn Posting Schedule" sections
- **Assumption 5**: Odoo Community is self-hosted locally (not SaaS). Odoo integration is optional
- **Assumption 6**: Users operate in a single timezone (no multi-timezone scheduling complexity)
- **Assumption 7**: All vault files are UTF-8 encoded markdown
- **Assumption 8**: The Ralph Wiggum loop runs within Claude Code's Python execution context (not a separate process)
- **Assumption 9**: LinkedIn posts are in English; multi-language support is not required
- **Assumption 10**: Calendar integration uses CalDAV standard (iCloud, Google Calendar with CalDAV, Nextcloud)

---

**Next Step**: Proceed to `/sp.clarify 002-gold-tier` to resolve any unclear requirements, or `/sp.plan 002-gold-tier` to design the implementation architecture.
