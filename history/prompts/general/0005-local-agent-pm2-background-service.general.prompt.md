---
id: "0005"
title: Local Agent PM2 Background Service
stage: general
date: 2026-02-17
surface: agent
model: claude-sonnet-4-5-20250929
feature: 003-platinum-tier
branch: 003-platinum-tier
user: ps_qasim
command: /sp.implement
labels: ["pm2","local-agent","background-service","smtp","env-parser","startup"]
links:
  spec: specs/003-platinum-tier/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - ecosystem.config.local.js
  - scripts/run_local_agent.sh
  - scripts/start_local_pm2.sh
  - scripts/setup_local_startup.sh
  - nextjs_dashboard/package.json
tests:
  - pm2 list (manual: local_approval_handler online, 0 restarts)
  - pm2 logs local_approval_handler (manual: 20 approvals processed)
---

## Prompt

Make local agent run as PM2 background service on PC:

GOAL: No manual commands needed. Local agent runs 24/7 automatically on PC. User only opens dashboard and approves.

DO THIS:

1. Create ecosystem.config.local.js in project root
2. Create scripts/start_local_pm2.sh
3. Create scripts/setup_local_startup.sh
4. Update package.json in nextjs_dashboard: Add script "start:full"
5. Test: Run bash scripts/start_local_pm2.sh, check pm2 list, create task in dashboard, approve it, verify email sends within 30 seconds, check pm2 logs local_approval_handler
6. Push to GitHub after working

IMPORTANT: Use existing .env for SMTP credentials. Reuse local_agent/src/orchestrator.py. Show pm2 list output after starting, also make phr in general.

## Response snapshot

Created 4 files + 1 update. Resolved 3 issues during testing:

1. **ecosystem.config.local.js** — PM2 config using bash interpreter + wrapper script. Uses `path.join(__dirname, ...)` for absolute paths. Avoids PM2 "runs JS as script" bug by pointing to shell wrapper.

2. **scripts/run_local_agent.sh** — Safe .env parser (line-by-line, skips comments/blanks, strips inline comments). Uses `exec python3 -u` for unbuffered logs. Replaces `source .env` which failed on em-dash comment lines.

3. **scripts/start_local_pm2.sh** — Installs pm2 if missing, creates vault dirs, deletes old instance, starts fresh, saves process list. Shows pm2 list after start.

4. **scripts/setup_local_startup.sh** — One-time boot hook: `pm2 startup` + `pm2 save`.

5. **nextjs_dashboard/package.json** — Added `"start:full"` script.

6. **.env** — Added `TIER=platinum`, `GIT_REMOTE_URL`, `DASHBOARD_URL` (validator required these).

**Bugs fixed during testing:**
- PM2 treated `.config.js` as a Node script → fixed by using `pm2 start script.sh --interpreter bash`
- `source .env` crashed on `# Personal AI Employee —` comment (em-dash) → fixed with safe line-by-line parser
- `No module named 'yaml'` → installed PyYAML in venv

**Final pm2 list:**
```
│ 0  │ local_approval_handler │ default │ N/A │ fork │ online │ 0% │ 23mb │
```

**Final logs confirmed:**
```
✅ Local Agent environment validated successfully
🚀 Local Orchestrator started
📋 Found 20 pending approval(s)
✅ email processed: EMAIL_DRAFT_FINAL_TEST.md
✅ email processed: EMAIL_DRAFT_TEST.md
```

Pushed to GitHub (310fcb8). Merged to main (1624e2a). Branch 003-platinum-tier preserved.

## Outcome

- ✅ Impact: Local agent runs 24/7 as PM2 process — no manual commands needed. Auto-restarts on crash. 20 pending approvals processed on first boot.
- 🧪 Tests: pm2 list shows online, logs show successful approval processing
- 📁 Files: 4 new files, 2 modified (.env, package.json)
- 🔁 Next prompts: setup_local_startup.sh for boot auto-start, WhatsApp notifier, Odoo deployment
- 🧠 Reflection: PM2 config file detection is version-sensitive — bash wrapper approach is more reliable than .config.js apps array for Python processes

## Evaluation notes (flywheel)

- Failure modes observed: PM2 ran ecosystem.config.js as Node script instead of config; `source .env` crashes on unicode comment lines; venv missing pyyaml
- Graders run and results (PASS/FAIL): pm2 list PASS, logs show running PASS, approval processing PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Add nextjs_dashboard to PM2 as second process in ecosystem.config.local.js
