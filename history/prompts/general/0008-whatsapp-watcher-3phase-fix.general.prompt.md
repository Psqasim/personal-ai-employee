---
id: "0008"
title: WhatsApp Watcher 3-Phase Fix & AI Replies
stage: green
date: 2026-02-17
surface: agent
model: claude-sonnet-4-5-20250929
feature: whatsapp-auto-reply
branch: 003-platinum-tier
user: Psqasim
command: fix whatsapp watcher ai replies + push merge
labels: ["whatsapp", "playwright", "pm2", "anthropic", "auto-reply", "platinum-tier"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - scripts/whatsapp_watcher.py
tests:
  - PM2 live test: 3 chats replied with real AI text
  - Urdu message: replied in Urdu (السلام علیکم...)
  - "What is Qasim doing?": replied "working on AI automation projects"
---

## Prompt

yes now mesg he reply this "Thanks for your message! Qasim will reply soon. — Qasim's Assistant" this also i again mesg qasim what he doing then same mesg reply like whatsapp away mesg like? he say qasim do etc like normal like tell ? also in the fix this push and merge it code

## Response snapshot

Fixed WhatsApp watcher with 3-phase cycle to prevent browser crash during Claude API call:

**Root cause**: `generate_reply()` (Claude Haiku API, takes 30-60s) was called WHILE browser was open → browser timed out and crashed → `BrowserContext.close` error → PM2 restarted → `anthropic` module not yet visible in new process → fallback reply.

**Fix — 3-phase cycle**:
- Phase 1 (browser open): Read all N chats, store `(sender, last_msg)` tuples, **close browser**
- Phase 2 (no browser): Call Claude Haiku API for each message (can take as long as needed)
- Phase 3 (browser open again): Click each chat, fill reply, press Enter, **close browser**

**Improved system prompt** for more contextual replies:
- Tells Claude who Qasim is (software engineer, AI automation)
- Replies in SAME language as incoming message (Urdu → Urdu)
- If asked what Qasim is doing → "working on AI automation projects"

**PM2 logs confirming success**:
```
📩 MUHAMMAD QASIM: What he doing qasim
💬 MUHAMMAD QASIM → Qasim is currently working on some AI automation projects! H...
✅ Sent to MUHAMMAD QASIM
💬 Blue Shit → السلام علیکم! میں اردو میں جواب دے سکتا ہوں...
✅ Sent to Blue Shit
```

Merged to main, pushed to GitHub.

## Outcome

- ✅ Impact: WhatsApp auto-reply bot now generates real Claude Haiku AI replies instead of static fallback. Replies are contextual, same-language, and describe Qasim's work.
- 🧪 Tests: Live PM2 test — 3 chats read & replied in one cycle (MUHAMMAD QASIM, Homie, Blue Shit). Urdu reply confirmed. "What is Qasim doing?" answered correctly.
- 📁 Files: scripts/whatsapp_watcher.py (157 insertions, 104 deletions)
- 🔁 Next prompts: Fix duplicate reply bug (same chat replied twice), Oracle Cloud deployment
- 🧠 Reflection: Key insight — never call slow external APIs while Playwright browser is open. Always close browser first, then do API work, then reopen browser to act.

## Evaluation notes (flywheel)

- Failure modes observed: BrowserContext.close crash when Claude API takes >30s; anthropic not in PM2's Python path; fill() works for Unicode/Urdu
- Graders run and results (PASS/FAIL): Live PM2 — PASS (✅ Sent to 3 contacts with real AI text)
- Prompt variant (if applicable): null
- Next experiment: Fix duplicate reply (same sender detected twice in row_map build loop during Phase 3)
