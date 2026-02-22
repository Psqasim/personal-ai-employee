---
id: "0013"
title: Quick Create Modal + Oracle VM Deployment
stage: general
date: 2026-02-22
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: ps_qasim
command: "Build unified Quick Create modal + deploy dashboard to Oracle Cloud VM"
labels: ["quick-create-modal","ai-generation","oracle-deployment","nextjs","pm2","bugfix"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - nextjs_dashboard/components/QuickCreateModal.tsx
  - nextjs_dashboard/app/api/ai-generate/route.ts
  - nextjs_dashboard/app/dashboard/layout.tsx
  - nextjs_dashboard/app/api/tasks/create/route.ts
  - nextjs_dashboard/app/login/page.tsx
  - deployment/oracle/deploy_dashboard.sh
tests:
  - Manual: dashboard accessible at http://129.151.151.212:3000
  - Manual: AI generation working for all 4 tab types
  - Manual: WhatsApp direct-send without approval
  - Manual: internal curl returns HTTP 200
---

## Prompt

Build a unified Quick Create modal combining LinkedIn, Email, WhatsApp, and Invoice into ONE modal with Claude AI generation for all 4 types. Fix 3 bugs found after testing (invoice type mapping, WhatsApp approval routing, Enter key double-fire). Deploy Next.js dashboard to Oracle Cloud VM (129.151.151.212) so it's accessible 24/7 from phone/anywhere. Push all changes and merge to main.

## Response snapshot

1. Created `QuickCreateModal.tsx` — single modal with 4 tabs (Email, WhatsApp, Invoice, LinkedIn), each with Claude AI generation via `✨ Generate` button.
2. Created `/api/ai-generate/route.ts` — Claude API endpoint that generates email (subject+body), WhatsApp (message), invoice (JSON), admin-only.
3. Updated `layout.tsx` — replaced two buttons (🔗 LinkedIn + ➕ New Task) with single `✨ Quick Create` button.
4. Fixed 3 bugs: invoice `taskType="odoo"` → mapped to `"invoice"` for API; WhatsApp now writes to `Approved/WhatsApp/` directly (no approval needed); Enter key `e.preventDefault()` stops double-fire.
5. Fixed Next.js 16 build error: `useSearchParams()` wrapped in `<Suspense>` in `login/page.tsx`.
6. Created `deployment/oracle/deploy_dashboard.sh`.
7. Built Next.js locally (100s), rsynced `.next/` (237MB) to Oracle VM (workaround for 1GB RAM constraint).
8. Configured `.env.local` on Oracle VM with `AUTH_TRUST_HOST=true` and `NEXTAUTH_URL=http://129.151.151.212:3000`.
9. Opened UFW port 3000, user added Oracle Security List ingress rule.
10. Dashboard live at http://129.151.151.212:3000 — PM2 online, HTTP 200 confirmed.

## Outcome

- ✅ Impact: Dashboard now live 24/7 on Oracle Cloud VM; unified Quick Create with Claude AI for all task types; WhatsApp sends directly without approval gate from dashboard
- 🧪 Tests: Internal curl HTTP 200, PM2 online 0% CPU 14MB RAM, all 4 AI generation types verified
- 📁 Files: 6 files created/modified (modal, API route, layout, tasks API, login page, deploy script)
- 🔁 Next prompts: WhatsApp command routing (send "!invoice Ali 5000" → vault draft); More Odoo features (contacts, payments, purchase bills); A2A agent coordination
- 🧠 Reflection: Build-then-rsync is the correct pattern for low-RAM VMs. Oracle has two firewall layers (UFW + Security List) — both must be opened. AUTH_TRUST_HOST needed for IP-based NextAuth access.

## Evaluation notes (flywheel)

- Failure modes observed: Oracle VM 1GB RAM insufficient for Next.js Turbopack build; multiple npm install processes exhausted RAM; UntrustedHost error without AUTH_TRUST_HOST
- Graders run and results (PASS/FAIL): HTTP 200 internal PASS, PM2 online PASS, external access PASS after Security List rule
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Add Cloudflare Tunnel for HTTPS access without port exposure
