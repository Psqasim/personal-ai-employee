# Tasks: Gold Tier - Autonomous Employee

**Input**: Design documents from `/specs/002-gold-tier/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Tests**: Not explicitly requested in spec - focusing on implementation tasks only.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create Gold tier vault folder structure: vault/Pending_Approval/{Email,WhatsApp,LinkedIn,Plans,Odoo}/, vault/Approved/{Email,WhatsApp,LinkedIn,Plans,Odoo}/, vault/Rejected/, vault/In_Progress/, vault/Briefings/, vault/Logs/{MCP_Actions,Human_Approvals,Plan_Execution}/
- [X] T002 Create requirements-gold.txt with Gold dependencies: schedule>=1.2.0, filelock>=3.12.0, requests>=2.31.0, and verify playwright>=1.40.0 from Silver
- [X] T003 [P] Update .env template with Gold tier variables: ENABLE_PLAN_EXECUTION, TIER, SMTP_HOST/PORT/USER/PASSWORD, LINKEDIN_ACCESS_TOKEN/AUTHOR_URN, WHATSAPP_SESSION_PATH/POLL_INTERVAL/KEYWORDS
- [X] T004 [P] Create docs/gold/ directory structure: docs/gold/whatsapp-setup.md (placeholder), docs/gold/mcp-setup.md (placeholder), docs/gold/ceo-briefing-config.md (placeholder)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement mcp_client.py in agent_skills/mcp_client.py: JSON-RPC 2.0 request builder, stdin/stdout communication, error handling (code: -32000 to -32099), timeout enforcement (30s)
- [X] T006 [P] Extend vault_parser.py in agent_skills/vault_parser.py: add parse_draft_file() for EmailDraft/WhatsAppDraft/LinkedInDraft YAML frontmatter parsing, add parse_plan_file() for Plan entity parsing
- [X] T007 [P] Extend dashboard_updater.py in agent_skills/dashboard_updater.py: add Gold Tier Status section with Plan Execution enabled/disabled, Active Plans count, Pending Approvals counts, MCP Servers status (email ✓/✗, whatsapp ✓/✗, linkedin ✓/✗)
- [X] T008 Create draft_generator.py in agent_skills/draft_generator.py: generate_email_draft(), generate_whatsapp_draft(), generate_linkedin_draft() with Claude API calls, sanitization (200 chars max for prompts), graceful fallback to templates when API unavailable
- [X] T009 Create approval_watcher.py in agent_skills/approval_watcher.py: monitor vault/Approved/* folders, detect file-move events via watchdog, trigger MCP invocations via mcp_client, implement filelock for race condition handling
- [X] T010 [P] Implement plan_executor.py in agent_skills/plan_executor.py: Ralph Wiggum loop implementation with max 10 iterations, state persistence to vault/In_Progress/{plan_id}/state.md, dependency checking, retry logic (3 attempts with exponential backoff), escalation to vault/Needs_Action/

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Email Draft Generation & Send Approval (Priority: P1) 🎯 MVP

**Goal**: AI drafts replies to high-priority inbox emails, user approves with file move, Email MCP sends

**Independent Test**: Create EMAIL_test_001.md in vault/Inbox/ with priority="High" → Draft appears in vault/Pending_Approval/Email/ within 15s → Move to vault/Approved/Email/ → Email MCP sends within 30s → Logged to vault/Logs/MCP_Actions/

### MCP Server for User Story 1

- [X] T011 [US1] Implement email_mcp/server.py: register send_email tool, implement SMTP send via smtplib, handle auth errors (code: -32000), implement retry logic (3 attempts: 5s, 10s, 20s backoff), return message_id and sent_at timestamp
- [X] T012 [US1] Implement email_mcp/config.json template with placeholders for SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
- [X] T013 [US1] Add email_mcp to ~/.config/claude-code/mcp.json configuration template in quickstart.md

### Watcher for User Story 1

- [X] T014 [US1] Extend scripts/gmail_watcher.py: detect high-priority email tasks (type="email", priority="High") in vault/Inbox/, invoke draft_generator.generate_email_draft(), save EmailDraft to vault/Pending_Approval/Email/EMAIL_DRAFT_{id}.md with YAML frontmatter (to, subject, draft_body, original_email_id, action="send_email", status="pending_approval")

### Approval Handler for User Story 1

- [X] T015 [US1] Implement email approval handler in scripts/approval_watcher.py: monitor vault/Approved/Email/, parse EmailDraft files, invoke mcp_client.call_tool("email-mcp", "send_email", params), log to vault/Logs/MCP_Actions/YYYY-MM-DD.md, move to vault/Done/ on success, move to vault/Needs_Action/ on failure after 3 retries

### Validation for User Story 1

- [X] T016 [US1] Add email draft validation in draft_generator.py: validate recipient email format, enforce 5000 char max for draft_body, sanitize content (strip attachments, limit to title + first 200 chars)
- [X] T017 [US1] Add human approval gate enforcement in approval_watcher.py: verify approval file exists before MCP invocation, log approval_file_path to MCP action log with human_approved=true

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - LinkedIn Post Generation & Auto-Post (Priority: P1)

**Goal**: AI generates LinkedIn posts aligned with business goals, user approves, LinkedIn MCP posts

**Independent Test**: Trigger LinkedIn generator → Draft appears in vault/Pending_Approval/LinkedIn/ within 15s → Move to vault/Approved/LinkedIn/ → LinkedIn MCP posts within 30s → Verify post live on LinkedIn

### MCP Server for User Story 2

- [X] T018 [P] [US2] Implement linkedin_mcp/server.py: register create_post tool, implement LinkedIn API v2 POST /ugcPosts with OAuth2 bearer token, handle auth errors (code: -32000), handle rate limits (code: -32001, back off 60 min), return post_id and post_url
- [X] T019 [US2] Implement linkedin_mcp/config.json template with placeholders for LINKEDIN_ACCESS_TOKEN, LINKEDIN_AUTHOR_URN
- [X] T020 [US2] Add linkedin_mcp to ~/.config/claude-code/mcp.json configuration template in quickstart.md

### Generator for User Story 2

- [X] T021 [US2] Extend scripts/linkedin_generator.py: read Company_Handbook.md Business Goals section, invoke draft_generator.generate_linkedin_draft(), save LinkedInDraft to vault/Pending_Approval/LinkedIn/LINKEDIN_POST_{YYYY-MM-DD}.md with YAML frontmatter (scheduled_date, business_goal_reference, post_content, character_count, action="create_post", status="pending_approval")
- [X] T022 [US2] Add LinkedIn posting schedule logic in linkedin_generator.py: check vault/Done/ for same-date posts (deduplication), enforce max 1 post/day, read posting schedule from Company_Handbook.md (daily/weekly)

### Approval Handler for User Story 2

- [X] T023 [US2] Implement LinkedIn approval handler in scripts/approval_watcher.py: monitor vault/Approved/LinkedIn/, parse LinkedInDraft files, invoke mcp_client.call_tool("linkedin-mcp", "create_post", params), handle rate_limited_retry status (update draft file, retry after 60 min), log to vault/Logs/MCP_Actions/

### Validation for User Story 2

- [X] T024 [US2] Add LinkedIn draft validation in draft_generator.py: enforce 3000 char max for post_content, auto-truncate at last sentence if exceeds limit, log warning in draft frontmatter when truncated
- [X] T025 [US2] Add rejected draft handling in approval_watcher.py: detect files moved to vault/Rejected/, create LINKEDIN_POST_{date}_retry.md in vault/Needs_Action/ for regeneration

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - WhatsApp Draft Generation & Auto-Send (Priority: P1)

**Goal**: AI monitors all WhatsApp messages, drafts replies for important ones, auto-sends after approval via Playwright

**Independent Test**: Send WhatsApp message containing "urgent payment" → Task file appears in vault/Inbox/ within 30s → Draft appears in vault/Pending_Approval/WhatsApp/ within 15s → Move to vault/Approved/WhatsApp/ → WhatsApp MCP sends via Playwright within 30s

### MCP Server for User Story 3

- [X] T026 [P] [US3] Implement whatsapp_mcp/server.py: register authenticate_qr and send_message tools, implement Playwright browser launch (chromium), implement QR code detection and display (base64 PNG), implement session state persistence to WHATSAPP_SESSION_PATH, implement message send (navigate to chat, type message, click send, confirm in history)
- [X] T027 [US3] Add WhatsApp selectors in whatsapp_mcp/server.py: SEARCH_BOX='div[contenteditable="true"][data-tab="3"]', MESSAGE_INPUT='div[contenteditable="true"][data-tab="10"]', SEND_BUTTON='button[data-tab="11"]', QR_CODE='canvas[aria-label="Scan this QR code to link a device!"]'
- [X] T028 [US3] Implement whatsapp_mcp/config.json template with placeholder for WHATSAPP_SESSION_PATH
- [X] T029 [US3] Add whatsapp_mcp to ~/.config/claude-code/mcp.json configuration template in quickstart.md

### Watcher for User Story 3

- [X] T030 [US3] Implement scripts/whatsapp_watcher.py: launch Playwright browser with saved session, poll WhatsApp Web every WHATSAPP_POLL_INTERVAL seconds (default 30), detect new messages, create WHATSAPP_{chat_id}_{timestamp}.md in vault/Inbox/ with YAML frontmatter (type="whatsapp", from={contact_name}, message_preview, timestamp, keywords_matched, priority, status="new")
- [X] T031 [US3] Add keyword detection in whatsapp_watcher.py: read WHATSAPP_KEYWORDS from .env, check message content for keyword matches, set priority="High" if ANY keyword matches, set priority="Medium" otherwise
- [X] T032 [US3] Add session expiry detection in whatsapp_watcher.py: detect WhatsApp Web login screen (QR code present), create vault/Needs_Action/whatsapp_session_expired.md, pause polling until re-authenticated

### Draft Generator for User Story 3

- [X] T033 [US3] Extend draft_generator.py: implement generate_whatsapp_draft() with context-aware reply generation, enforce 500 char max for draft_body, sanitize input (limit to first 200 chars, remove phone numbers, strip media attachments), save WhatsAppDraft to vault/Pending_Approval/WhatsApp/WHATSAPP_DRAFT_{chat_id}_{timestamp}.md

### Approval Handler for User Story 3

- [X] T034 [US3] Implement WhatsApp approval handler in scripts/approval_watcher.py: monitor vault/Approved/WhatsApp/, parse WhatsAppDraft files, invoke mcp_client.call_tool("whatsapp-mcp", "send_message", params), retry 3 times on failure (exponential backoff), log to vault/Logs/MCP_Actions/, move to vault/Done/ on success

### Setup Script for User Story 3

- [X] T035 [US3] Create scripts/whatsapp_qr_setup.py: launch Playwright in headed mode, open WhatsApp Web, wait for QR code, display QR code in terminal or save as image, wait for successful scan, save session state to WHATSAPP_SESSION_PATH, confirm authentication success

**Checkpoint**: All 3 P1 draft-and-send user stories should now be independently functional

---

## Phase 6: User Story 4 - Multi-Step Plan Execution (Priority: P1)

**Goal**: AI generates multi-step plans, user approves full plan, Ralph Wiggum loop executes steps autonomously

**Independent Test**: Create task file with "Onboard new client - draft intro email, create calendar invite, post LinkedIn announcement" → Plan.md created in vault/Plans/ → Approval request in vault/Pending_Approval/Plans/ → Approve → Ralph Wiggum executes all steps → Moved to vault/Done/

### Plan Generator for User Story 4

- [X] T036 [US4] Extend scripts/gmail_watcher.py or create scripts/plan_generator.py: detect multi-step keywords ("plan", "onboard", "campaign", "project", "setup") in vault/Inbox/ tasks, invoke Claude API to generate Plan with objective and steps array, save Plan.md to vault/Plans/PLAN_{name}_{date}.md with YAML frontmatter (plan_id, objective, steps, total_steps, approval_required=true, status="awaiting_approval")
- [X] T037 [US4] Implement PlanStep generation logic: parse user task description, identify discrete steps, assign action_type (mcp_email, mcp_whatsapp, mcp_linkedin, create_file, notify_human), extract action_params, detect step dependencies

### Plan Approval for User Story 4

- [X] T038 [US4] Create approval request in plan_generator.py: save PLAN_{id}_approval.md to vault/Pending_Approval/Plans/ with plan summary, steps preview, human approval instruction (move to vault/Approved/Plans/ to execute)

### Ralph Wiggum Loop for User Story 4

- [X] T039 [US4] Implement Ralph Wiggum loop in plan_executor.py: initialize ExecutionState with iterations_remaining=10, iterate through plan steps, check dependencies before executing each step, update current_step in state.md after each completion, decrement iterations_remaining
- [X] T040 [US4] Add step execution in plan_executor.py: parse action_type, invoke appropriate MCP server (email-mcp, whatsapp-mcp, linkedin-mcp) via mcp_client, create vault file for create_file actions, create notification for notify_human actions, mark step as [x] in Plan.md
- [X] T041 [US4] Add error handling in plan_executor.py: retry failed steps 3 times (exponential backoff), mark step as [!] if all retries fail, pause execution, create vault/Needs_Action/plan_blocked_{id}.md with error details and recovery instructions
- [X] T042 [US4] Add max iteration escalation in plan_executor.py: check if iterations_remaining=0 and plan incomplete, exit loop, create vault/Needs_Action/plan_escalated_{id}.md with full iteration history, update plan status to "escalated"
- [X] T043 [US4] Add plan completion in plan_executor.py: check if all steps marked [x], move Plan.md to vault/Done/, update Dashboard.md with "Plan: [name] - COMPLETED ✓", clean up vault/In_Progress/{plan_id}/

### Plan Watcher for User Story 4

- [X] T044 [US4] Create scripts/plan_watcher.py: monitor vault/Approved/Plans/ for approved plan files, parse Plan.md, initialize ExecutionState in vault/In_Progress/{plan_id}/state.md, invoke plan_executor.execute_plan(), update Dashboard.md with plan progress

### Dashboard Integration for User Story 4

- [X] T045 [US4] Extend dashboard_updater.py: add Active Plans section showing plan_id, objective, current_step, total_steps, status, iterations_used/max, add Pending Approvals count for vault/Pending_Approval/Plans/

**Checkpoint**: Multi-step plan execution (Ralph Wiggum loop) should now be fully functional

---

## Phase 7: User Story 5 - MCP Multi-Server Integration (Priority: P2)

**Goal**: Multiple MCP servers configured with health checks, graceful degradation, comprehensive logging

**Independent Test**: Verify 3 MCP servers (email-mcp, whatsapp-mcp, linkedin-mcp) respond to health checks → Approved actions trigger correct MCP → All actions logged to vault/Logs/MCP_Actions/

### MCP Configuration for User Story 5

- [X] T046 [P] [US5] Create mcp.json configuration template in docs/gold/mcp-setup.md: include email-mcp, whatsapp-mcp, linkedin-mcp with command, args (absolute paths), env variables
- [X] T047 [US5] Add MCP server health check in mcp_client.py: invoke tools/list method on startup for each configured server, log server status (active/inactive) to Dashboard.md, continue execution if server unavailable (graceful degradation)

### MCP Action Logging for User Story 5

- [X] T048 [US5] Implement MCP action logging in approval_watcher.py: create log entry in vault/Logs/MCP_Actions/YYYY-MM-DD.md BEFORE MCP invocation with YAML frontmatter (log_id, mcp_server, action, payload_summary (max 50 chars, no PII), outcome, plan_id, step_num, timestamp, human_approved=true, approval_file_path)
- [X] T049 [US5] Add MCP error logging in mcp_client.py: log all MCP errors (auth failed, network error, rate limited) to vault/Logs/Error_Recovery/, create escalation file in vault/Needs_Action/ if 3 retries fail

### MCP Safety Gates for User Story 5

- [X] T050 [US5] Enforce approval gate in approval_watcher.py: verify approval file exists in vault/Approved/* before ANY MCP invocation, never invoke MCP without approval_file_path, audit by cross-checking vault/Logs/MCP_Actions/ against vault/Approved/
- [X] T051 [US5] Add approval file movement logging in approval_watcher.py: log all file moves from Pending_Approval/ to Approved/ or Rejected/ to vault/Logs/Human_Approvals/ with timestamp, file path, destination

**Checkpoint**: MCP infrastructure should be fully instrumented with logging and safety gates

---

## Phase 8: User Story 6 - Weekly Business Audit & CEO Briefing (Priority: P2)

**Goal**: Auto-generate weekly CEO Briefing every Sunday 23:00 with task summaries, proactive suggestions

**Independent Test**: Manually trigger `python scripts/ceo_briefing.py --force` → Briefing file created in vault/Briefings/YYYY-MM-DD_Monday_Briefing.md within 60s → Contains accurate task counts, proactive suggestions, API cost summary

### CEO Briefing Generator for User Story 6

- [X] T052 [P] [US6] Create scripts/ceo_briefing.py: calculate week_start/week_end (previous Monday-Sunday), query vault/Done/ for tasks completed in date range, count tasks in vault/Needs_Action/, calculate total Claude API cost from vault/Logs/API_Usage/, generate CEOBriefing file in vault/Briefings/YYYY-MM-DD_Monday_Briefing.md
- [X] T053 [US6] Add proactive suggestions generation in ceo_briefing.py: invoke Claude API with vault context (pending approvals, blocked plans, old emails), generate 3+ actionable suggestions, handle API unavailable case (mark as "[API Unavailable - Manual Review Required]", generate data-only briefing)
- [X] T054 [US6] Add briefing scheduling in ceo_briefing.py: use schedule library to run every Sunday at 23:00, use --force flag for manual testing, save briefing with next Monday date as filename

### Briefing Content for User Story 6

- [X] T055 [US6] Implement briefing sections in ceo_briefing.py: Executive Summary (task counts, API cost), Week in Review (completed tasks list with file links), Pending Items (vault/Needs_Action/ summary), Proactive Suggestions (3+ AI-generated items), Next Week Focus (AI-generated or data-based priorities)

**Checkpoint**: CEO Briefing should auto-generate weekly with accurate data and AI insights

---

## Phase 9: User Story 7 - Cross-Domain Integration & Odoo Accounting (Priority: P3)

**Goal**: Odoo MCP for draft accounting entries, Personal vs Business domain routing

**Independent Test**: Configure Odoo MCP with local Odoo URL → Add task with type="expense" to vault/Inbox/ → Draft expense entry appears in vault/Pending_Approval/Odoo/ within 15s → Approve → Odoo MCP creates draft in Odoo (not posted) → Logged

### Odoo MCP for User Story 7

- [X] T056 [P] [US7] Implement odoo_mcp/server.py: register create_draft_invoice and create_draft_expense tools, implement Odoo JSON-RPC authentication, implement draft entry creation (status=draft, never confirm/post), handle auth errors (code: -32000), return odoo_record_id
- [X] T057 [US7] Implement odoo_mcp/config.json template with placeholders for ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD
- [X] T058 [US7] Add odoo_mcp to ~/.config/claude-code/mcp.json configuration template (optional) in quickstart.md

### Odoo Draft Generator for User Story 7

- [X] T059 [US7] Create odoo draft detection logic in scripts/gmail_watcher.py or create scripts/odoo_watcher.py: detect tasks with type="invoice" or type="expense", parse task content for odoo_data (customer, amount, description), save OdooDraft to vault/Pending_Approval/Odoo/ with YAML frontmatter (draft_id, entry_type, odoo_data, action="create_draft_invoice"|"create_draft_expense", status="pending_approval")

### Odoo Approval Handler for User Story 7

- [X] T060 [US7] Implement Odoo approval handler in scripts/approval_watcher.py: monitor vault/Approved/Odoo/, parse OdooDraft files, invoke mcp_client.call_tool("odoo-mcp", action, params), log to vault/Logs/MCP_Actions/ with odoo_record_id
- [X] T061 [US7] Add Odoo graceful degradation in odoo_watcher.py: check if ENABLE_ODOO=true in .env, if Odoo MCP unavailable or disabled, create manual entry template in vault/Pending_Approval/Odoo/ for offline review, never crash

### Cross-Domain Routing for User Story 7

- [X] T062 [US7] Implement domain routing logic in scripts/gmail_watcher.py: read task category from Silver AI categorization, route Work/Urgent tasks to Business domain (LinkedIn, Odoo), route Personal tasks to Personal domain (calendar, email), update task frontmatter with domain="Personal"|"Business"

**Checkpoint**: Odoo integration should work for draft entries with full safety (never auto-post)

---

## Phase 2B: Social Media Integration (Facebook/Instagram/Twitter)

**Purpose**: Implement Gold tier hackathon requirement for Facebook, Instagram, and Twitter integration with approval workflows

**⚠️ HACKATHON REQUIREMENT**: Gold tier requires Facebook, Instagram, and Twitter integration per hackathon spec

### Facebook MCP for User Story 8

- [ ] T085 [P] [US8] Implement facebook_mcp/server.py: register create_post and read_feed tools, implement Facebook Graph API integration (POST /me/feed), handle auth errors (code: -32000), handle rate limits (code: -32001, back off 60 min), return post_id and post_url
- [ ] T086 [US8] Implement facebook_mcp/config.json template with placeholders for FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID
- [ ] T087 [US8] Add facebook_mcp to ~/.config/claude-code/mcp.json configuration template in quickstart.md
- [ ] T088 [US8] Create docs/gold/facebook-setup.md: Facebook App creation, Graph API access token generation, Page access permissions, testing commands, troubleshooting (token expiry, permissions errors)

### Instagram MCP for User Story 8

- [ ] T089 [P] [US8] Implement instagram_mcp/server.py: register create_post and create_story tools, implement Instagram Basic Display API integration, handle image upload requirements, handle auth errors (code: -32000), return post_id and post_url
- [ ] T090 [US8] Implement instagram_mcp/config.json template with placeholders for INSTAGRAM_APP_ID, INSTAGRAM_APP_SECRET, INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID
- [ ] T091 [US8] Add instagram_mcp to ~/.config/claude-code/mcp.json configuration template in quickstart.md
- [ ] T092 [US8] Create docs/gold/instagram-setup.md: Instagram Business Account setup, Basic Display API access token, image requirements (formats, sizes), testing commands, troubleshooting (token expiry, media upload errors)

### Twitter (X) MCP for User Story 8

- [ ] T093 [P] [US8] Implement twitter_mcp/server.py: register create_tweet and read_mentions tools, implement Twitter API v2 integration (POST /2/tweets), handle 280 character limit, handle auth errors (code: -32000), handle rate limits (code: -32001, back off 15 min), return tweet_id and tweet_url
- [ ] T094 [US8] Implement twitter_mcp/config.json template with placeholders for TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET, TWITTER_BEARER_TOKEN
- [ ] T095 [US8] Add twitter_mcp to ~/.config/claude-code/mcp.json configuration template in quickstart.md
- [ ] T096 [US8] Create docs/gold/twitter-setup.md: Twitter Developer Account setup, API v2 authentication (OAuth 2.0), elevated access requirements, testing commands, troubleshooting (rate limits, character truncation)

### Social Media Draft Generator for User Story 8

- [ ] T097 [US8] Extend draft_generator.py: implement generate_facebook_post(), generate_instagram_post(), generate_twitter_tweet() with Claude API calls, enforce platform constraints (Twitter 280 chars, Instagram requires image, Facebook 63,206 chars max), align with Company_Handbook.md Social Media Strategy
- [ ] T098 [US8] Create scripts/social_media_generator.py: read Company_Handbook.md Business Goals and Social Media Strategy, generate coordinated multi-platform drafts (Facebook/Instagram/Twitter), save drafts to vault/Pending_Approval/Social/{Facebook,Instagram,Twitter}/ with YAML frontmatter (platform, action, content, scheduled_date, character_count, status="pending_approval")
- [ ] T099 [US8] Add platform-specific validation in draft_generator.py: Twitter ≤280 chars (auto-truncate at last word), Instagram requires_image=true, Facebook <63,206 chars, log warnings in draft frontmatter when auto-adjusted

### Social Media Approval Handler for User Story 8

- [ ] T100 [US8] Implement social media approval handlers in scripts/approval_watcher.py: monitor vault/Approved/Social/{Facebook,Instagram,Twitter}/, parse draft files, invoke mcp_client.call_tool("{platform}-mcp", action, params), retry 3 times on failure (exponential backoff), log to vault/Logs/MCP_Actions/
- [ ] T101 [US8] Add social media error handling in approval_watcher.py: detect platform-specific errors (Facebook/Instagram/Twitter auth expiry, rate limits), create vault/Needs_Action/{platform}_error_{id}.md with recovery instructions, continue processing other platforms

### Vault Folder Structure for User Story 8

- [ ] T102 [US8] Create vault folder structure for social media: vault/Pending_Approval/Social/{Facebook,Instagram,Twitter}/, vault/Approved/Social/{Facebook,Instagram,Twitter}/

### Integration Testing for User Story 8

- [ ] T103 [P] [US8] Create integration test for Facebook workflow in tests/integration/test_facebook_workflow.py: social media trigger → Facebook draft generated → user approves → Facebook MCP posts (mock Graph API) → logged
- [ ] T104 [P] [US8] Create integration test for Instagram workflow in tests/integration/test_instagram_workflow.py: social media trigger with image → Instagram draft generated → user approves → Instagram MCP posts (mock API) → logged
- [ ] T105 [P] [US8] Create integration test for Twitter workflow in tests/integration/test_twitter_workflow.py: social media trigger → Twitter tweet draft generated → user approves → Twitter MCP posts (mock API v2) → logged
- [ ] T106 [P] [US8] Create integration test for multi-platform posting in tests/integration/test_multi_platform_workflow.py: single trigger → coordinated drafts for all 3 platforms → all posted after approval

**Checkpoint**: All social media MCPs (Facebook/Instagram/Twitter) should be functional with approval workflows

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Documentation

- [ ] T063 [P] Complete docs/gold/whatsapp-setup.md: WhatsApp Web authentication process, Playwright installation (`playwright install chromium`), QR code setup with scripts/whatsapp_qr_setup.py, session management (WHATSAPP_SESSION_PATH), session expiry recovery, testing checklist
- [ ] T064 [P] Complete docs/gold/mcp-setup.md: MCP server configuration in ~/.config/claude-code/mcp.json, environment variables for each server, testing commands (echo JSON-RPC request | python server.py), troubleshooting (server not active, auth failures)
- [ ] T065 [P] Complete docs/gold/ceo-briefing-config.md: CEO Briefing customization options, scheduling configuration (Sunday 23:00), proactive suggestions tuning, data sources (vault folders), manual trigger with --force flag
- [ ] T066 [P] Update quickstart.md: complete all TODOs, verify all setup steps are accurate, add troubleshooting section for WhatsApp session expired, LinkedIn rate limited, Email MCP auth failed, Ralph Wiggum loop escalated
- [ ] T107 [P] Create docs/gold/phase2b-testing.md: comprehensive test procedures for Phase 2B social media MCPs (Facebook/Instagram/Twitter), including setup verification, API authentication tests, posting tests, approval workflow validation, error handling tests, multi-platform coordination tests

### Watcher Orchestration

- [ ] T067 Create scripts/gold_watcher.sh: supervisor script to start all Gold watchers (gmail_watcher.py, whatsapp_watcher.py, linkedin_generator.py, approval_watcher.py, plan_watcher.py, ceo_briefing.py), implement via PM2 or supervisord, add health checks, add graceful shutdown

### Configuration Management

- [ ] T068 Create .env.example for Gold tier: include all Silver variables plus Gold additions (ENABLE_PLAN_EXECUTION, TIER, SMTP_*, LINKEDIN_*, WHATSAPP_*, ODOO_*), add comments for required vs optional variables

### Error Recovery

- [ ] T069 Implement vault write error handling in all watchers: retry vault writes 3 times with 500ms delay using filelock, log errors to vault/Logs/Error_Recovery/, skip and continue if write fails after retries (never crash)
- [ ] T070 [P] Add Obsidian compatibility checks in all vault writers: verify YAML frontmatter syntax, preserve wiki links ([[...]]), preserve tags (#...), atomic file writes (write to .tmp, rename), backup before modify (.bak.YYYY-MM-DD_HH-MM-SS, keep last 5)

### Performance Optimization

- [ ] T071 Add caching for Claude API responses in draft_generator.py: cache draft responses for 24h TTL using hash of (task_id, task_content), reduce API cost by avoiding regeneration for identical tasks
- [ ] T072 Add API cost tracking in draft_generator.py: log every Claude API call to vault/Logs/API_Usage/ with request_id, model, prompt_tokens, completion_tokens, cost_usd, timestamp, create alerts at $0.10, $0.25, $0.50 daily thresholds

### Backward Compatibility Validation

- [ ] T073 Add ENABLE_PLAN_EXECUTION=false mode check: verify system creates plans/drafts but does NOT execute MCP actions when flag is false, verify Silver behavior preserved (all Silver tests pass)
- [ ] T074 [P] Verify Bronze+Silver features work in Gold: file watching, dashboard updates, Gmail watcher, AI analysis, all vault operations unchanged, no regressions in performance (Dashboard update <2s, file detection <30s)

### Integration Testing

- [ ] T075 [P] Create integration test for Email workflow in tests/integration/test_email_workflow.py: high-priority email → draft generated → user approves (mock file move) → Email MCP sends (mock SMTP) → logged
- [ ] T076 [P] Create integration test for WhatsApp workflow in tests/integration/test_whatsapp_workflow.py: important WhatsApp message → draft generated → user approves → WhatsApp MCP sends (mock Playwright) → logged
- [ ] T077 [P] Create integration test for LinkedIn workflow in tests/integration/test_linkedin_workflow.py: LinkedIn trigger → draft generated → user approves → LinkedIn MCP posts (mock API) → logged
- [ ] T078 [P] Create integration test for Plan execution in tests/integration/test_plan_execution.py: multi-step task → Plan.md created → user approves → Ralph Wiggum executes all steps (mock MCPs) → moved to Done
- [ ] T079 [P] Create integration test for CEO Briefing in tests/integration/test_ceo_briefing.py: manually trigger briefing → file created with accurate counts → proactive suggestions present (mock Claude API)

### Safety Validation

- [ ] T080 Run human approval gate audit: cross-check all entries in vault/Logs/MCP_Actions/ against vault/Approved/ to verify 0 MCP actions executed without approval_file_path, verify human_approved=true for all logs
- [ ] T081 Validate Ralph Wiggum loop max iterations: create test plan with blocking step, verify loop exits at 10 iterations, verify escalation file created, verify no infinite loop possible

### Final Validation

- [ ] T082 Run quickstart.md end-to-end validation: follow all 10 setup steps on clean system, execute all 4 test scenarios (email, whatsapp, linkedin, multi-step plan), verify all pass
- [ ] T083 Verify all 62 functional requirements implemented: FR-G001 through FR-G062, cross-check against spec.md, verify all acceptance scenarios pass
- [ ] T084 Run regression test suite: verify all Bronze + Silver tests still pass (backward compatibility), verify no performance degradation, verify vault integrity preserved

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational phase completion
  - US1 (Email) - Can start after Foundational
  - US2 (LinkedIn) - Can start after Foundational
  - US3 (WhatsApp) - Can start after Foundational
  - US4 (Multi-Step Plans) - Can start after Foundational
  - US5 (MCP Integration) - Can start after Foundational
  - US6 (CEO Briefing) - Can start after Foundational
  - US7 (Odoo) - Can start after Foundational
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (Email - P1)**: No dependencies on other stories - RECOMMENDED MVP START
- **User Story 2 (LinkedIn - P1)**: No dependencies on other stories - Can run in parallel with US1
- **User Story 3 (WhatsApp - P1)**: No dependencies on other stories - Can run in parallel with US1, US2
- **User Story 4 (Multi-Step Plans - P1)**: Depends on US1, US2, US3 for MCP actions in plan steps (mcp_email, mcp_linkedin, mcp_whatsapp) - Implement after P1 draft stories complete
- **User Story 5 (MCP Integration - P2)**: Infrastructure for all stories - Can start early or in parallel
- **User Story 6 (CEO Briefing - P2)**: No dependencies - Can run in parallel
- **User Story 7 (Odoo - P3)**: No dependencies - Optional, can be deferred

### Within Each User Story

- MCP servers before watchers/generators (need tool to invoke)
- Draft generators before approval handlers (need draft format)
- Approval handlers before integration tests (need full workflow)
- Validation after implementation (verify correctness)

### Parallel Opportunities

- **Setup Phase**: All tasks (T001-T004) can run in parallel
- **Foundational Phase**: T006, T007, T008 can run in parallel (different files)
- **User Stories (after Foundational complete)**:
  - US1, US2, US3, US5, US6 can all start in parallel (different domains)
  - US4 should start after US1/US2/US3 (depends on MCP actions being available)
- **Within Each User Story**:
  - MCP server + watcher + generator can be developed in parallel (if interfaces defined)
  - Integration tests (Phase 10) can all run in parallel (T075-T079)
  - Documentation tasks (T063-T066) can all run in parallel

---

## Parallel Example: Phase 3 (User Story 1)

```bash
# Launch MCP server + watcher together:
Task: "Implement email_mcp/server.py with send_email tool"
Task: "Extend gmail_watcher.py with draft generation trigger"

# After both complete, launch validation tasks:
Task: "Add email draft validation in draft_generator.py"
Task: "Add human approval gate enforcement in approval_watcher.py"
```

---

## Implementation Strategy

### MVP First (P1 User Stories Only)

**Recommended MVP Scope**: User Stories 1, 2, 3 (Email + LinkedIn + WhatsApp draft-and-send)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T010) - CRITICAL BLOCKER
3. Complete Phase 3: User Story 1 - Email (T011-T017)
4. **STOP and VALIDATE**: Test email draft → approve → send independently
5. Complete Phase 4: User Story 2 - LinkedIn (T018-T025)
6. **STOP and VALIDATE**: Test LinkedIn draft → approve → post independently
7. Complete Phase 5: User Story 3 - WhatsApp (T026-T035)
8. **STOP and VALIDATE**: Test WhatsApp draft → approve → send independently
9. **MVP READY**: Deploy/demo email + LinkedIn + WhatsApp auto-drafting with human approval

**Then add**: User Story 4 (Multi-Step Plans) to enable autonomous task execution

### Incremental Delivery

1. **Foundation** (Phase 1+2): Setup + mcp_client + draft_generator + approval_watcher → Foundation ready
2. **MVP v1** (Phase 3): Email draft-and-send → Test independently → Deploy
3. **MVP v2** (Phase 4): LinkedIn post-and-publish → Test independently → Deploy
4. **MVP v3** (Phase 5): WhatsApp draft-and-send → Test independently → Deploy
5. **Gold v1** (Phase 6): Multi-step plan execution (Ralph Wiggum loop) → Test independently → Deploy
6. **Gold v2** (Phase 8): CEO Briefing → Test independently → Deploy
7. **Gold v3 (Optional)** (Phase 9): Odoo accounting drafts → Test independently → Deploy

Each increment adds value without breaking previous features.

### Parallel Team Strategy

With multiple developers:

1. **Team completes Foundation together** (Phase 1+2)
2. **Once Foundational is done**:
   - Developer A: User Story 1 (Email) - T011-T017
   - Developer B: User Story 2 (LinkedIn) - T018-T025
   - Developer C: User Story 3 (WhatsApp) - T026-T035
   - Developer D: User Story 5 (MCP Infrastructure) - T046-T051
3. **After P1 stories complete**:
   - Developer A+B: User Story 4 (Multi-Step Plans) - T036-T045
   - Developer C: User Story 6 (CEO Briefing) - T052-T055
   - Developer D: User Story 7 (Odoo) - T056-T062 (optional)
4. **Polish phase**: All developers work on Phase 10 tasks in parallel

---

## Notes

- **[P] tasks** = different files, no dependencies on incomplete tasks, can run in parallel
- **[Story] label** maps task to specific user story for traceability
- **Each user story should be independently completable and testable** - validate after each story
- **Commit after each task or logical group** for rollback safety
- **Stop at any checkpoint** to validate story independently before moving to next priority
- **CRITICAL: Foundational phase (T005-T010) BLOCKS all user stories** - complete first
- **Tests not included** because spec did not explicitly request TDD approach
- **MVP recommendation**: Phase 1+2+3+4+5 (Email + LinkedIn + WhatsApp draft-and-send)
- **Gold tier differentiator**: Phase 6 (Ralph Wiggum loop for multi-step execution)

---

## Summary

- **Total Tasks**: 84
- **Task Breakdown by User Story**:
  - Setup (Phase 1): 4 tasks
  - Foundational (Phase 2): 6 tasks (BLOCKS all stories)
  - US1 (Email - P1): 7 tasks
  - US2 (LinkedIn - P1): 8 tasks
  - US3 (WhatsApp - P1): 10 tasks
  - US4 (Multi-Step Plans - P1): 10 tasks
  - US5 (MCP Integration - P2): 6 tasks
  - US6 (CEO Briefing - P2): 4 tasks
  - US7 (Odoo - P3): 7 tasks
  - Polish (Phase 10): 22 tasks
- **Parallel Opportunities**: 20+ tasks marked [P] across all phases
- **Independent Test Criteria**: Defined for each user story
- **MVP Scope**: Phases 1+2+3+4+5 (30 tasks) = Email + LinkedIn + WhatsApp draft-and-send
- **Full Gold Tier**: All 84 tasks = All 7 user stories + Ralph Wiggum loop + CEO Briefing + Odoo

**Next Step**: Begin implementation with Phase 1 Setup (T001-T004), then proceed to Foundational phase (T005-T010) before starting any user story work.
