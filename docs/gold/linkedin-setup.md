# LinkedIn API Setup Guide - Complete Step-by-Step

**Purpose**: Configure LinkedIn OAuth2 API access for automated posting

This guide walks through creating a LinkedIn app, getting OAuth2 tokens, and posting to your LinkedIn profile.

---

## Overview

**Technology**: LinkedIn API v2 + OAuth2
**Cost**: FREE (for personal posting)
**Time**: 30 minutes (includes app approval wait)
**What you'll get**: Access token to post on your LinkedIn profile

---

## Step 1: Create LinkedIn Developer App

### 1.1 Go to LinkedIn Developers Portal

Open: https://www.linkedin.com/developers/apps

**Login** with your LinkedIn account (the one you want to post from)

### 1.2 Click "Create app"

Fill in the form:

| Field | What to Enter |
|-------|---------------|
| **App name** | "Personal AI Employee" (or any name) |
| **LinkedIn Page** | Select your personal profile or company page |
| **Privacy policy URL** | https://example.com/privacy (can be temporary) |
| **App logo** | Upload any 300x300 image (required) |
| **Legal agreement** | Check the box to agree |

Click **"Create app"**

### 1.3 Copy Your App Credentials

After creating the app, you'll see:
- **Client ID**: Copy this (looks like: `78a1b2c3d4e5f6`)
- **Client Secret**: Copy this (looks like: `a1B2c3D4e5F6g7H8`)

**Save these!** You'll need them for OAuth2.

---

## Step 2: Request API Access (Important!)

### 2.1 Navigate to "Products" Tab

In your app dashboard, click the **"Products"** tab

### 2.2 Request "Share on LinkedIn" Product

Find **"Share on LinkedIn"** and click **"Request access"**

**For Personal Accounts**:
- ✅ Instant approval (usually)
- You can post to your personal profile immediately

**For Company Pages**:
- ⏳ Takes 1-3 business days
- LinkedIn reviews your request
- You'll get an email when approved

### 2.3 Wait for Approval (if needed)

Check your email for approval notification:
```
Subject: Your LinkedIn API request has been approved
```

Once approved, continue to Step 3.

---

## Step 3: Get OAuth2 Access Token

### 3.1 Generate Authorization URL

Open a text editor and fill in this URL template:

```
https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=https://example.com/callback&scope=w_member_social
```

**Replace**:
- `YOUR_CLIENT_ID` → Your Client ID from Step 1.3

**Example**:
```
https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=78a1b2c3d4e5f6&redirect_uri=https://example.com/callback&scope=w_member_social
```

### 3.2 Open URL in Browser

1. Paste the URL in your browser
2. Click **"Allow"** to authorize the app
3. You'll be redirected to: `https://example.com/callback?code=AQT...`

### 3.3 Copy Authorization Code

From the redirect URL, copy the `code` parameter:

```
https://example.com/callback?code=AQTxxx123...
                                   ^^^^^^^^^
                              Copy this part
```

**Note**: This code expires in 30 minutes! Use it quickly.

### 3.4 Exchange Code for Access Token

Open a terminal and run this curl command (replace values):

```bash
curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_AUTHORIZATION_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=https://example.com/callback"
```

**Replace**:
- `YOUR_AUTHORIZATION_CODE` → Code from Step 3.3
- `YOUR_CLIENT_ID` → Your Client ID
- `YOUR_CLIENT_SECRET` → Your Client Secret

**Response**:
```json
{
  "access_token": "AQVxxxxxxxxxxxxxxxxxxxxxx",
  "expires_in": 5184000
}
```

**Copy the `access_token`!** This is your LinkedIn OAuth token.

**Note**: Token expires in 60 days. You'll need to repeat this process to refresh it.

---

## Step 4: Get Your LinkedIn Person URN

### 4.1 Make API Call to Get Your Profile

Run this curl command (replace YOUR_ACCESS_TOKEN):

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     https://api.linkedin.com/v2/me
```

**Response**:
```json
{
  "localizedFirstName": "John",
  "localizedLastName": "Doe",
  "id": "abc123xyz"
}
```

### 4.2 Construct Your Author URN

Format: `urn:li:person:{id}`

If your `id` is `abc123xyz`, your URN is:
```
urn:li:person:abc123xyz
```

**Copy this!** You'll need it in `.env`

---

## Step 5: Add to .env Configuration

Open your `.env` file and add:

```bash
# LinkedIn API Configuration
LINKEDIN_ACCESS_TOKEN=AQVxxxxxxxxxxxxxxxxxxxxxx
LINKEDIN_AUTHOR_URN=urn:li:person:abc123xyz
```

**Replace**:
- `AQVxxx...` → Your access token from Step 3.4
- `abc123xyz` → Your person ID from Step 4.1

---

## Step 6: Test LinkedIn Posting

### 6.1 Generate a Test Post

```bash
python scripts/linkedin_generator.py --force
```

**Expected output**:
```
[linkedin_generator] Generating LinkedIn post...
[linkedin_generator] Draft saved: vault/Pending_Approval/LinkedIn/LINKEDIN_POST_2026-02-14.md
```

### 6.2 Check the Draft

```bash
cat vault/Pending_Approval/LinkedIn/LINKEDIN_POST_2026-02-14.md
```

You should see a LinkedIn post draft with AI-generated content based on your Company_Handbook.md.

### 6.3 Test MCP Server Directly (Optional)

```bash
echo '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "create_post",
    "arguments": {
      "text": "Test post from Personal AI Employee! 🤖",
      "author_urn": "urn:li:person:abc123xyz"
    }
  }
}' | .venv/bin/python mcp_servers/linkedin_mcp/server.py
```

**Expected output**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "post_id": "urn:li:share:1234567890",
    "post_url": "https://www.linkedin.com/feed/update/urn:li:share:1234567890",
    "timestamp": "2026-02-14T11:30:00Z"
  }
}
```

**⚠️ This will actually post to LinkedIn!** Check your profile to verify.

### 6.4 Test Full Approval Workflow

```bash
# 1. Start approval watcher
python scripts/run_approval_watcher.py &

# 2. Approve the draft
mv vault/Pending_Approval/LinkedIn/LINKEDIN_POST_2026-02-14.md \
   vault/Approved/LinkedIn/

# 3. Wait 5 seconds
sleep 5

# 4. Check if post was published
cat vault/Logs/MCP_Actions/$(date +%Y-%m-%d).md
```

**Check your LinkedIn profile** - the post should be live! 🎉

---

## Troubleshooting

### Issue 1: "Invalid access token" Error

**Symptoms**:
```json
{
  "error": "Invalid access token"
}
```

**Causes**:
1. Token expired (60-day lifespan)
2. Wrong token copied
3. Token has wrong scope

**Solution**:
```bash
# Regenerate token (Steps 3.1 - 3.4)
# Make sure scope includes: w_member_social
```

---

### Issue 2: "Insufficient permissions" Error

**Symptoms**:
```json
{
  "error": "Member does not have permission to create content"
}
```

**Causes**:
- "Share on LinkedIn" product not approved yet

**Solution**:
1. Check LinkedIn Developer Portal → Products tab
2. Verify "Share on LinkedIn" status is "Approved"
3. Wait for approval email if still pending

---

### Issue 3: Rate Limited (429 Error)

**Symptoms**:
```
[ERROR] Rate limited: 429 Too Many Requests
```

**LinkedIn Rate Limits**:
- **Personal accounts**: ~5-10 posts per day
- **Company pages**: ~25 posts per day

**Solution**:
```bash
# Wait 60 minutes before retrying
# Or reduce posting frequency in linkedin_generator.py
```

---

### Issue 4: "Invalid URN" Error

**Symptoms**:
```json
{
  "error": "Invalid author URN"
}
```

**Solution**:
```bash
# Verify your URN format
# Should be: urn:li:person:abc123xyz
# NOT: urn:li:member:abc123xyz (old format)

# Re-run Step 4 to get correct URN
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.linkedin.com/v2/me
```

---

### Issue 5: Token Expiry (60 Days)

**Symptoms**:
After 60 days, posts fail with "Invalid access token"

**Solution**:
LinkedIn tokens expire after 60 days. You must refresh manually:

**Option A: Generate New Token (Quick)**
- Repeat Steps 3.1 - 3.4
- Update `.env` with new token

**Option B: Implement Refresh Token Flow (Advanced)**
- Use OAuth2 refresh tokens (requires code changes)
- See: https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow

---

## Token Refresh Reminder

Set a calendar reminder for **55 days from today**:
```
Title: Refresh LinkedIn API Token
Description: Token expires in 5 days. Run OAuth flow again.
Link: file:///path/to/docs/gold/linkedin-setup.md
```

Or automate it:
```bash
# Add to crontab (runs monthly)
0 0 1 * * echo "LinkedIn token expires soon!" | mail -s "Token Refresh" you@example.com
```

---

## Security Best Practices

### 1. Protect Your Tokens

```bash
# Add to .gitignore (already done)
.env
*.env

# Set file permissions
chmod 600 .env
```

### 2. Never Commit Credentials

**Bad**:
```bash
LINKEDIN_ACCESS_TOKEN=AQVxxx...  # committed to git
```

**Good**:
```bash
# In .env (gitignored)
LINKEDIN_ACCESS_TOKEN=AQVxxx...
```

### 3. Rotate Tokens Regularly

- Refresh every 45 days (before 60-day expiry)
- Revoke old tokens when generating new ones

---

## Advanced: Posting to Company Pages

### Prerequisites

- Admin access to LinkedIn company page
- Company page verified
- Business verification may be required

### Steps

1. **Get Company Page ID**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee
   ```

2. **Use Organization URN**:
   ```bash
   # Instead of person URN
   LINKEDIN_AUTHOR_URN=urn:li:organization:12345678
   ```

3. **Post to Company Page**:
   Same workflow, but with organization URN

---

## LinkedIn API Resources

**Official Documentation**:
- Auth Guide: https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow
- Share API: https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin
- Rate Limits: https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/rate-limits

**Developer Portal**:
- Apps: https://www.linkedin.com/developers/apps
- Support: https://www.linkedin.com/help/linkedin/answer/a1654943

---

## Testing Checklist

Before going live:

- [ ] LinkedIn app created
- [ ] "Share on LinkedIn" product approved
- [ ] OAuth2 access token obtained
- [ ] Author URN retrieved
- [ ] `.env` configured with token and URN
- [ ] MCP server tested directly (test post published)
- [ ] Draft generation working
- [ ] Approval workflow tested
- [ ] MCP action logs created
- [ ] Calendar reminder set for token refresh (55 days)

---

## Summary

**Setup Time**: 30 minutes (including approval wait)
**Cost**: FREE
**Token Lifespan**: 60 days (must refresh)
**Rate Limit**: ~5-10 posts/day (personal), ~25/day (company)

**You can now**:
- ✅ Generate AI-powered LinkedIn posts
- ✅ Auto-post after human approval
- ✅ Track all posting activity in logs
- ✅ Maintain professional LinkedIn presence

**Next Steps**:
1. ✅ Test email workflow: `docs/gold/email-setup.md`
2. ✅ Test WhatsApp workflow: `docs/gold/whatsapp-setup.md`
3. ✅ Run full integration tests: `docs/gold/testing-guide.md`
