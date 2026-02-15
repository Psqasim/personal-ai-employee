# WhatsApp Web Setup Guide

**Purpose**: Configure WhatsApp Web automation via Playwright for Gold tier

This guide walks through setting up WhatsApp Web browser automation so your AI assistant can send WhatsApp messages after approval.

---

## Overview

**Technology**: Playwright (browser automation)
**Cost**: FREE (uses your personal WhatsApp account)
**Authentication**: QR code scan (one-time, session persists ~30 days)
**Session Storage**: Saved to disk, survives restarts

---

## Step 1: Install Playwright

### 1.1 Install Python Package

Playwright should already be installed from Silver tier requirements, but verify:

```bash
pip install playwright>=1.40.0
```

### 1.2 Install Chromium Browser

Download the Chromium browser for Playwright:

```bash
playwright install chromium
```

**Expected output**:
```
Downloading Chromium 119.0.6045.9 (playwright build v1091)
119.0.6045.9 downloaded to /home/user/.cache/ms-playwright/chromium-1091
```

---

## Step 2: Authenticate WhatsApp Web (One-Time Setup)

### 2.1 Run QR Code Setup Script

```bash
python scripts/whatsapp_qr_setup.py
```

**What happens**:
1. ✅ Chromium browser opens in headed mode
2. ✅ Navigates to https://web.whatsapp.com
3. ✅ Displays QR code on screen
4. ⏳ Waits for you to scan the QR code with your phone

### 2.2 Scan QR Code with Your Phone

1. **Open WhatsApp on your phone**
2. **Go to Settings → Linked Devices**
3. **Tap "Link a Device"**
4. **Scan the QR code** displayed in the browser

**Expected result**:
```
✓ WhatsApp Web authenticated successfully!
✓ Session saved to: /home/user/.whatsapp_session
```

### 2.3 Verify Session Files Created

```bash
ls -la ~/.whatsapp_session/
```

**Expected files**:
```
.whatsapp_session/
├── cookies.json
├── localStorage.json
└── sessionStorage.json
```

---

## Step 3: Configure .env Variables

Add WhatsApp configuration to your `.env` file:

```bash
# WhatsApp Web Configuration
WHATSAPP_SESSION_PATH=/home/user/.whatsapp_session
WHATSAPP_POLL_INTERVAL=30
WHATSAPP_KEYWORDS=urgent,payment,meeting,deadline,invoice,asap
```

---

## Step 4: Test WhatsApp Watcher

```bash
python scripts/whatsapp_watcher.py
```

**Expected**: Messages with keywords create files in `vault/Inbox/WHATSAPP_*.md`

---

## Troubleshooting

### Session Expired Error

**Solution**: Re-run QR setup
```bash
python scripts/whatsapp_qr_setup.py
```

Sessions expire after ~30 days of inactivity.

---

## Next Steps

✅ Follow `docs/gold/testing-guide.md` for full workflow testing
