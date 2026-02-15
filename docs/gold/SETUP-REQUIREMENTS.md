# Gold Tier Setup Requirements - API & Cloud Integrations

## ❓ Your Question: "Do I need to set up API integrations first?"

**SHORT ANSWER**: Yes! You need to set up these APIs/cloud services BEFORE the Gold tier can actually send emails, WhatsApp messages, or LinkedIn posts.

**GOOD NEWS**: You can test the CODE without APIs (drafts generate but won't send). Then add APIs when ready to go live.

---

## 🔄 Two Testing Modes

### Mode 1: CODE TESTING (No APIs Required) ✅ **YOU CAN DO THIS NOW**

Test that the code works without actually sending anything:

```bash
# 1. Install dependencies
pip install -r requirements-gold.txt

# 2. Set minimal .env (just for testing code)
cat > .env << EOF
VAULT_PATH=./vault
ENABLE_AI_ANALYSIS=false  # Set false to skip Claude API
TIER=gold
ENABLE_PLAN_EXECUTION=false  # Set false to test without sending
EOF

# 3. Test watchers (they'll generate drafts using templates, not AI)
python scripts/gmail_watcher.py
# ✓ Detects high-priority emails
# ✓ Creates draft files in vault/Pending_Approval/Email/
# ✗ Won't send (no SMTP configured)
```

**What This Tests**:
- ✅ File watching works
- ✅ Draft file creation works
- ✅ Approval workflow works (file move detection)
- ✅ Validation logic works
- ✅ Code has no bugs

**What This Doesn't Test**:
- ✗ AI draft generation (needs Claude API)
- ✗ Actual sending (needs SMTP, WhatsApp, LinkedIn APIs)

---

### Mode 2: FULL PRODUCTION (APIs Required) 🔐 **REQUIRES SETUP**

To actually SEND emails/messages/posts, you need these APIs:

---

## 📋 Required API Integrations (Priority Order)

### 1️⃣ **REQUIRED ALWAYS: Claude API** (For AI Draft Generation)

**What it does**: Generates intelligent email/WhatsApp/LinkedIn drafts
**Cost**: ~$0.02-$0.10 per day (based on usage)
**Setup Time**: 2 minutes

#### Setup Steps:
1. Go to https://console.anthropic.com/
2. Sign up / Log in
3. Go to **API Keys** → **Create Key**
4. Copy the key (starts with `sk-ant-api03-...`)
5. Add to `.env`:
   ```bash
   CLAUDE_API_KEY=sk-ant-api03-your-key-here
   CLAUDE_MODEL=claude-3-5-sonnet-20241022
   ENABLE_AI_ANALYSIS=true
   ```

**Test It**:
```bash
python3 -c "import anthropic; print('Claude API OK')"
```

---

### 2️⃣ **FOR EMAIL SENDING: Gmail SMTP** (via App Password)

**What it does**: Sends emails via Gmail
**Cost**: FREE (uses your Gmail account)
**Setup Time**: 5 minutes
**Detailed Guide**: `docs/gold/email-setup.md`

#### Quick Setup:
1. **Enable 2-Step Verification**:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification (required for app passwords)

2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - App: "Mail", Device: "Other (Custom)" → Name it "Personal AI"
   - Copy 16-character password (e.g., `abcd efgh ijkl mnop`)

3. **Add to `.env`**:
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=abcdefghijklmnop  # Remove spaces!
   ```

**Test It**:
```bash
# Test SMTP connection
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python mcp_servers/email_mcp/server.py
```

**Alternative**: Use any SMTP server (Outlook, Yahoo, custom):
```bash
# Outlook example
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-outlook-password
```

---

### 3️⃣ **FOR WHATSAPP SENDING: WhatsApp Web** (via Playwright)

**What it does**: Sends WhatsApp messages via browser automation
**Cost**: FREE (uses your WhatsApp account)
**Setup Time**: 5 minutes
**Detailed Guide**: `docs/gold/whatsapp-setup.md`

#### Quick Setup:
1. **Install Playwright Browser**:
   ```bash
   pip install playwright>=1.40.0
   playwright install chromium
   ```

2. **Authenticate WhatsApp Web (One-time)**:
   ```bash
   python scripts/whatsapp_qr_setup.py
   # Browser opens → Scan QR code with phone → Session saved
   ```

3. **Add to `.env`**:
   ```bash
   WHATSAPP_SESSION_PATH=/home/user/.whatsapp_session
   WHATSAPP_POLL_INTERVAL=30
   WHATSAPP_KEYWORDS=urgent,payment,invoice,deadline
   ```

**Test It**:
```bash
# Test session exists
ls -la ~/.whatsapp_session
# Should show session files
```

**Notes**:
- ✅ FREE (no WhatsApp Business API needed)
- ✅ Works with personal WhatsApp
- ⚠️ Session expires after ~30 days (re-scan QR code)
- ⚠️ Requires Chromium browser installed

---

### 4️⃣ **FOR LINKEDIN POSTING: LinkedIn API** (OAuth2)

**What it does**: Posts to your LinkedIn profile/company page
**Cost**: FREE (uses LinkedIn API v2)
**Setup Time**: 15-30 minutes (requires app approval)
**Detailed Guide**: `docs/gold/linkedin-setup.md`

#### Quick Setup:
1. **Create LinkedIn Developer App**:
   - Go to https://www.linkedin.com/developers/apps
   - Click "Create app"
   - Fill in app details (name, company page, logo)

2. **Request API Access**:
   - Request "Share on LinkedIn" product
   - Wait for approval (1-3 business days for company pages)
   - Personal accounts: instant approval

3. **Get OAuth2 Token**:
   ```bash
   # Follow OAuth2 flow (see docs/gold/linkedin-setup.md)
   # You'll get an access token like: AQV...xxx
   ```

4. **Add to `.env`**:
   ```bash
   LINKEDIN_ACCESS_TOKEN=AQV-your-token-here
   LINKEDIN_AUTHOR_URN=urn:li:person:your-id
   ```

**Test It**:
```bash
# Test API access
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python mcp_servers/linkedin_mcp/server.py
```

**Notes**:
- ✅ FREE for personal posting
- ⚠️ Token expires after 60 days (requires refresh)
- ⚠️ Company pages require business verification
- ⚠️ Rate limit: ~5 posts/day

---

## 🎯 Recommended Setup Order

### **Stage 1: Local Code Testing (No APIs) - START HERE**
**Time**: 10 minutes
**Cost**: $0

```bash
# 1. Install dependencies
pip install -r requirements-gold.txt

# 2. Create minimal .env
cp .env.example .env
# Edit: Set VAULT_PATH, ENABLE_AI_ANALYSIS=false, TIER=gold

# 3. Run watchers locally
python scripts/gmail_watcher.py
# ✓ Code runs without errors
# ✓ Drafts created (using templates, not AI)
```

**What You Can Test**:
- File watching
- Draft file creation
- Approval workflow (move files between folders)
- Validation logic
- Dashboard updates

---

### **Stage 2: AI Draft Generation (Claude API Only)**
**Time**: 5 minutes
**Cost**: ~$0.05/day (100 tasks)

```bash
# 1. Get Claude API key (https://console.anthropic.com/)

# 2. Update .env
CLAUDE_API_KEY=sk-ant-api03-...
ENABLE_AI_ANALYSIS=true

# 3. Test AI generation
python scripts/gmail_watcher.py
# ✓ AI generates intelligent drafts
# ✗ Still won't send (no SMTP)
```

**What You Can Test**:
- AI-generated email replies
- AI-generated WhatsApp messages
- AI-generated LinkedIn posts
- Draft quality and tone

---

### **Stage 3: Email Sending (Claude + Gmail SMTP)**
**Time**: 10 minutes
**Cost**: $0 (uses Gmail free tier)

```bash
# 1. Set up Gmail App Password (see above)

# 2. Update .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# 3. Start approval watcher
python scripts/run_approval_watcher.py

# 4. Approve a draft
# Move file: vault/Pending_Approval/Email/ → vault/Approved/Email/
# ✓ Email actually SENDS!
```

---

### **Stage 4: WhatsApp Sending (Claude + Gmail + WhatsApp)**
**Time**: 10 minutes
**Cost**: $0

```bash
# 1. Authenticate WhatsApp
python scripts/whatsapp_qr_setup.py

# 2. Start WhatsApp watcher
python scripts/whatsapp_watcher.py

# 3. Approve WhatsApp draft
# ✓ WhatsApp message SENDS!
```

---

### **Stage 5: LinkedIn Posting (All APIs)**
**Time**: 30 minutes (includes LinkedIn app approval wait)
**Cost**: $0

```bash
# 1. Create LinkedIn app, get OAuth2 token

# 2. Update .env
LINKEDIN_ACCESS_TOKEN=...
LINKEDIN_AUTHOR_URN=...

# 3. Generate and approve LinkedIn post
python scripts/linkedin_generator.py --force
# ✓ LinkedIn post PUBLISHES!
```

---

## ✅ What Works NOW (Without APIs)

You can test these RIGHT NOW without any API setup:

1. ✅ **File Structure**: All vault folders created
2. ✅ **Code Logic**: All modules importable and functional
3. ✅ **Watchers**: Detect new files in vault/Inbox/
4. ✅ **Draft Files**: Create draft markdown files
5. ✅ **Approval Flow**: Detect file moves to vault/Approved/
6. ✅ **Validation**: Email format, character limits
7. ✅ **Logging**: Create log files (without MCP actions)

**Commands to Run Now**:
```bash
# Test file watching
python scripts/gmail_watcher.py

# Test LinkedIn draft creation (template mode)
python scripts/linkedin_generator.py --force

# Test approval watcher
python scripts/run_approval_watcher.py
```

---

## ❌ What DOESN'T Work Without APIs

1. ❌ **AI Draft Generation**: Needs Claude API key
2. ❌ **Email Sending**: Needs Gmail SMTP credentials
3. ❌ **WhatsApp Sending**: Needs Playwright + WhatsApp session
4. ❌ **LinkedIn Posting**: Needs LinkedIn OAuth2 token

---

## 💰 Cost Summary

| Service | Cost | Required For |
|---------|------|-------------|
| **Claude API** | ~$0.05-$0.10/day | AI draft generation |
| **Gmail SMTP** | FREE | Email sending |
| **WhatsApp Web** | FREE | WhatsApp sending |
| **LinkedIn API** | FREE | LinkedIn posting |
| **Playwright** | FREE | WhatsApp automation |

**Total Monthly Cost**: ~$3-5 (just Claude API)

---

## 🚀 Quick Start Commands

### Option A: Test Code Only (No APIs)
```bash
pip install -r requirements-gold.txt
python scripts/gmail_watcher.py
# ✓ Code works, drafts create, but won't send
```

### Option B: Full Production (All APIs)
```bash
# 1. Get Claude API key → Add to .env
# 2. Get Gmail app password → Add to .env
# 3. Authenticate WhatsApp → Run whatsapp_qr_setup.py
# 4. Get LinkedIn token → Add to .env
# 5. Start all watchers
./scripts/gold_watcher.sh  # (Create this to run all watchers)
```

---

## 📞 Need Help?

**Setup Guides**:
- Email: `docs/gold/email-setup.md`
- WhatsApp: `docs/gold/whatsapp-setup.md`
- LinkedIn: `docs/gold/linkedin-setup.md`
- Testing: `docs/gold/testing-guide.md`

**Common Issues**:
- Claude API: https://docs.anthropic.com/
- Gmail SMTP: https://support.google.com/accounts/answer/185833
- WhatsApp: https://playwright.dev/
- LinkedIn: https://learn.microsoft.com/en-us/linkedin/

---

## ✨ Summary

**YES, you need API integrations** - but you can test the CODE first without them!

**Recommended path**:
1. ✅ **Test code now** (no APIs) - verify logic works
2. ✅ **Add Claude API** - test AI generation
3. ✅ **Add Gmail SMTP** - test email sending
4. ✅ **Add WhatsApp** (optional) - test messaging
5. ✅ **Add LinkedIn** (optional) - test posting

**Minimum to get started**: Just **Claude API** ($3-5/month)
**Full features**: All 4 APIs (~30 min setup time, mostly free)
