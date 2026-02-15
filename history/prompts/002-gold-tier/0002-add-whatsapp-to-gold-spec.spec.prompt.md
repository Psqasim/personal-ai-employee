---
id: "0002"
title: Add WhatsApp to Gold Spec
stage: spec
date: 2026-02-13
surface: agent
model: claude-sonnet-4-5-20250929
feature: 002-gold-tier
branch: 002-gold-tier
user: ps_qasim
command: /sp.specify
labels: ["spec","gold-tier","whatsapp","draft-generation","playwright","mcp"]
links:
  spec: specs/002-gold-tier/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-gold-tier/spec.md
  - specs/002-gold-tier/checklists/requirements.md
  - history/prompts/002-gold-tier/0002-add-whatsapp-to-gold-spec.spec.prompt.md
tests:
  - none (spec phase, tests defined in Definition of Done)
---

## Prompt

Update Gold spec to add WhatsApp integration, then create plan:

1. Add User Story: WhatsApp Integration (Priority P1)
   - Monitor all WhatsApp messages via WhatsApp Web automation
   - Create WHATSAPP_*.md files in Inbox/ for all messages
   - Detect important messages (keywords: urgent, meeting, payment, deadline)
   - AI drafts replies → Pending_Approval/WhatsApp/
   - User approves → Move to Approved/WhatsApp/
   - AI sends via WhatsApp Web automation

2. Add requirements for:
   - Playwright browser automation for WhatsApp Web
   - QR code authentication setup
   - Message polling every 30 seconds
   - Keyword detection for important messages
   - Draft generation with approval workflow
   - Auto-send after approval

3. Add setup documentation requirement:
   - docs/gold/whatsapp-setup.md
   - Include: WhatsApp Web authentication process
   - Include: Playwright installation
   - Include: Session management
   - Include: Testing checklist

4. Keep existing LinkedIn feature as-is

Update specs/002-gold-tier/spec.md with WhatsApp story, then generate implementation plan.

## Response snapshot

Updated Gold Tier spec (`specs/002-gold-tier/spec.md`) with WhatsApp Integration:

- **New User Story 3** (Priority P1): WhatsApp Draft Generation & Auto-Send with 9 acceptance scenarios
- **18 New Functional Requirements** (FR-G016–FR-G033): WhatsApp watcher, keyword detection, draft generation, Playwright auto-send, QR auth, session persistence
- **Renumbered existing FRs**: Old FR-G016–FR-G044 → FR-G034–FR-G062 (shifted by 18)
- **Updated Success Criteria**: Added SC-G004 for WhatsApp metrics (90% draft gen within 15s, 20+ messages/day handled); renumbered SC-G005–SC-G013
- **Updated Definition of Done**: 7 user stories, 62 FRs, 13 SCs, added WhatsApp integration test + session persistence test + setup docs requirement
- **New Key Entity**: WhatsAppDraft (draft_id, original_message_id, to, chat_id, draft_body, status, generated_at, sent_at, keywords_matched)
- **Updated Dependencies**: Added whatsapp-mcp (Playwright automation), WHATSAPP_SESSION_PATH, WHATSAPP_POLL_INTERVAL, WHATSAPP_KEYWORDS in .env
- **New Documentation Requirement**: docs/gold/whatsapp-setup.md with QR auth, Playwright install, session mgmt, testing checklist
- **Edge Cases Added**: WhatsApp session expiry, media handling, multi-message thread handling

## Outcome

- ✅ Impact: WhatsApp integration fully specified with all requirements, acceptance scenarios, and documentation needs. Gold tier now covers 3 major communication channels (Email, WhatsApp, LinkedIn) with AI-driven draft-and-approve workflow
- 🧪 Tests: WhatsApp integration test, session persistence test defined in Definition of Done (gates 8, 14, 15)
- 📁 Files: specs/002-gold-tier/spec.md (updated), specs/002-gold-tier/checklists/requirements.md (updated)
- 🔁 Next prompts: `/sp.plan 002-gold-tier` to generate implementation plan
- 🧠 Reflection: WhatsApp integration aligns with Silver tier's WhatsApp watcher but upgrades to full draft-and-send capability (vs Silver's monitor-only). All spec checklist items still pass.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): requirements checklist PASS (all items)
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Run /sp.plan to decompose 62 FRs into implementation tasks
