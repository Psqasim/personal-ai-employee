# Facebook MCP Setup Guide

**Feature**: Gold Tier - Phase 2B Social Media Integration
**Created**: 2026-02-14
**Status**: Production Ready

## Overview

The Facebook MCP server enables automated posting to Facebook Pages via the Facebook Graph API. This guide walks through creating a Facebook App, obtaining required permissions, generating access tokens, and configuring the MCP server.

---

## Prerequisites

- Facebook account with admin access to a Facebook Page
- Python 3.11+ installed
- Personal AI Employee Gold Tier deployed

---

## Step 1: Create Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click **My Apps** → **Create App**
3. Select **Business** as app type
4. Fill in app details:
   - **App Name**: "Personal AI Employee"
   - **App Contact Email**: Your email
   - **Business Account**: Select or create one
5. Click **Create App**
6. Note your **App ID** and **App Secret** (Settings → Basic)

---

## Step 2: Configure App Permissions

1. In your app dashboard, go to **App Review** → **Permissions and Features**
2. Request the following permissions:
   - **pages_manage_posts**: Required for posting to Pages
   - **pages_read_engagement**: Required for reading Page feed
3. Fill out the permission request form (explain you're building a personal automation tool)
4. Wait for approval (typically 1-3 business days)

**Note**: For development/testing, you can use your own Page without approval.

---

## Step 3: Add Facebook Page

1. Go to **Settings** → **Basic**
2. Scroll to **App Domains**, add your domain (or localhost for testing)
3. Go to **Add Product** → **Facebook Login** → **Settings**
4. Add **Valid OAuth Redirect URIs**: `http://localhost:8000/callback`
5. Save changes

---

## Step 4: Generate Page Access Token

### Option A: Using Graph API Explorer (Quick Testing)

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from dropdown
3. Click **Get Token** → **Get Page Access Token**
4. Select the Page you want to post to
5. Grant permissions when prompted
6. Copy the **Page Access Token** (starts with `EAAA...`)
7. **Extend token to long-lived** (60 days):
   ```bash
   curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token" \
     -d "grant_type=fb_exchange_token" \
     -d "client_id=YOUR_APP_ID" \
     -d "client_secret=YOUR_APP_SECRET" \
     -d "fb_exchange_token=YOUR_SHORT_LIVED_TOKEN"
   ```

### Option B: Using OAuth Flow (Production)

1. Construct OAuth URL:
   ```
   https://www.facebook.com/v18.0/dialog/oauth?
     client_id=YOUR_APP_ID
     &redirect_uri=http://localhost:8000/callback
     &scope=pages_manage_posts,pages_read_engagement
   ```
2. Visit URL in browser, authorize
3. Exchange code for access token:
   ```bash
   curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token" \
     -d "client_id=YOUR_APP_ID" \
     -d "client_secret=YOUR_APP_SECRET" \
     -d "redirect_uri=http://localhost:8000/callback" \
     -d "code=AUTHORIZATION_CODE"
   ```

---

## Step 5: Get Your Page ID

1. Go to your Facebook Page
2. Click **About** → **Page Info**
3. Scroll to **Page ID** (or use Graph API Explorer: `/me/accounts`)

**Alternative via Graph API Explorer**:
```bash
curl -X GET "https://graph.facebook.com/v18.0/me/accounts" \
  -d "access_token=YOUR_USER_ACCESS_TOKEN"
```

---

## Step 6: Configure .env

Add to your `.env` file:

```bash
# Facebook MCP (required for Gold tier hackathon)
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret
FACEBOOK_ACCESS_TOKEN=your-facebook-page-access-token
FACEBOOK_PAGE_ID=your-facebook-page-id
```

**Security Note**: Never commit `.env` to version control. Page access tokens are sensitive credentials.

---

## Step 7: Configure MCP Server

Update `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "facebook-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/personal-ai-employee/mcp_servers/facebook_mcp/server.py"],
      "env": {
        "FACEBOOK_ACCESS_TOKEN": "your-page-access-token",
        "FACEBOOK_PAGE_ID": "your-page-id"
      }
    }
  }
}
```

**Replace**:
- `/absolute/path/to/personal-ai-employee` with your actual repo path
- `your-page-access-token` with the long-lived token from Step 4
- `your-page-id` with the Page ID from Step 5

---

## Step 8: Test MCP Server

**Test 1: List tools**
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python mcp_servers/facebook_mcp/server.py
```

**Expected Output**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {"name": "create_post", ...},
      {"name": "read_feed", ...}
    ]
  }
}
```

**Test 2: Create test post**
```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"create_post","arguments":{"message":"Test post from Personal AI Employee 🤖"}}}' | \
  python mcp_servers/facebook_mcp/server.py
```

**Expected Output**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "post_id": "123456789_987654321",
    "post_url": "https://www.facebook.com/123456789_987654321",
    "posted_at": "2026-02-14T10:30:00"
  }
}
```

**Verify**: Check your Facebook Page to see the test post.

---

## Step 9: Create Vault Approval Folders

```bash
cd vault
mkdir -p Pending_Approval/Social/Facebook
mkdir -p Approved/Social/Facebook
```

---

## Step 10: Integration Test

**Create a test draft**:
```bash
cat > vault/Pending_Approval/Social/Facebook/FACEBOOK_POST_2026-02-14.md <<EOF
---
action: create_post
post_content: |
  🚀 Excited to share our latest project update!

  We've been building amazing AI automation tools that help businesses save time and increase productivity.

  #AI #Automation #BusinessGrowth
scheduled_date: 2026-02-14
character_count: 150
status: pending_approval
generated_at: 2026-02-14T10:00:00
---

# Facebook Post Draft

[Content above in frontmatter]
EOF
```

**Approve the draft**:
```bash
mv vault/Pending_Approval/Social/Facebook/FACEBOOK_POST_2026-02-14.md \
   vault/Approved/Social/Facebook/
```

**Wait 30 seconds** → Approval watcher should invoke Facebook MCP and post to Facebook

**Verify**:
- Check `vault/Logs/MCP_Actions/YYYY-MM-DD.md` for log entry
- Check your Facebook Page for the posted content

---

## Troubleshooting

### Error: "AUTH_FAILED: FACEBOOK_ACCESS_TOKEN not configured"

**Cause**: Token not set in environment or mcp.json

**Solution**:
1. Verify `.env` has `FACEBOOK_ACCESS_TOKEN=...`
2. Verify `mcp.json` has token in env section
3. Restart watchers: `./scripts/gold_watcher.sh restart`

### Error: "AUTH_FAILED: Facebook access token expired or insufficient permissions"

**Cause**: Page Access Token expired (60-day limit)

**Solution**:
1. Generate new long-lived token (Step 4)
2. Update `.env` and `mcp.json`
3. Restart watchers

### Error: "RATE_LIMITED: Facebook API rate limit exceeded"

**Cause**: Too many posts in short time (Facebook limit: ~100 posts/hour)

**Solution**:
1. Wait 60 minutes before retrying
2. System automatically backs off and retries
3. Check `vault/Needs_Action/` for retry instructions

### Error: "API_ERROR: 190 - Error validating access token"

**Cause**: Token format invalid or app not approved

**Solution**:
1. Verify token copied correctly (no spaces, full token)
2. Check App Review status for permissions
3. Regenerate token if corrupted

### Posts not appearing on Facebook Page

**Cause**: Token may be user token instead of Page token

**Solution**:
1. Ensure you're using **Page Access Token** (not user token)
2. Use Graph API Explorer → **Get Page Access Token** (not user token)
3. Verify Page ID matches the Page you're posting to

---

## Token Refresh Schedule

**Facebook Page Access Tokens expire after 60 days**

**Recommended maintenance**:
- **Weekly**: Check `vault/Logs/MCP_Actions/` for auth errors
- **Monthly**: Proactively refresh token (Steps 4-6)
- **Set calendar reminder**: Refresh token every 50 days

---

## Rate Limits & Best Practices

**Facebook Graph API Limits**:
- ~100 posts per hour per Page
- Rate limits vary by app usage tier
- System automatically backs off on 429 errors

**Best Practices**:
- Limit posts to 2-3 per day for organic engagement
- Schedule posts during peak engagement hours (9am-5pm)
- Avoid duplicate content (Facebook may flag as spam)

---

## Security Checklist

- [ ] `.env` file in `.gitignore`
- [ ] Page Access Token never committed to git
- [ ] App Secret never exposed in client-side code
- [ ] Token stored in environment variables only
- [ ] Regular token rotation (every 50 days)

---

## Next Steps

- Configure Instagram MCP: `docs/gold/instagram-setup.md`
- Configure Twitter MCP: `docs/gold/twitter-setup.md`
- Test multi-platform posting workflow
- Review Phase 2B testing guide: `docs/gold/phase2b-testing.md`

---

**Congratulations!** Your Facebook MCP is now configured. The AI Employee can now draft and post to Facebook with your approval.
