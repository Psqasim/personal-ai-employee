# Twitter (X) MCP Setup Guide

**Feature**: Gold Tier - Phase 2B Social Media Integration
**Created**: 2026-02-14
**Status**: Production Ready

## Overview

The Twitter MCP server enables automated tweet posting via Twitter API v2. This guide covers creating a Twitter Developer account, obtaining Elevated access, generating API credentials, and configuring the MCP server.

---

## Prerequisites

- Twitter (X) account
- Phone number verified on Twitter account
- Python 3.11+ installed
- Personal AI Employee Gold Tier deployed

---

## Step 1: Apply for Twitter Developer Account

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Click **Sign up** (or **Sign in** if you have an account)
3. Complete the application:
   - **What's your name?**: Your full name
   - **Country**: Your country
   - **What's your use case?**: Select **Exploring the API** or **Building tools for yourself**
   - **Will you make Twitter content/data available to government entities?**: Typically **No** for personal use
4. Describe your use case (example below)
5. Accept Terms of Service
6. Verify your email

**Example Use Case Description**:
```
I'm building a personal AI automation system that helps me manage my social media presence. The system will:
1. Generate draft tweets aligned with my business goals
2. Post tweets after I manually approve them (human-in-the-loop)
3. Read mentions to help me engage with my audience

This is for personal use only, not for analyzing trends or selling data. Average usage: 5-10 tweets per day.
```

---

## Step 2: Apply for Elevated Access

**Standard access limits**:
- Tweet creation: 1,500 tweets/month
- Tweet reads: 500 tweets/month

**Elevated access limits**:
- Tweet creation: 100,000 tweets/month
- Tweet reads: 2,000,000 tweets/month

**To apply for Elevated**:

1. Go to [Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Click **Products** → **Twitter API v2**
3. Click **Elevate** or **Apply for Elevated**
4. Answer questions about intended use:
   - **Will your app use Tweet, Retweet, Like, Follow, or Direct Message functionality?**: Yes
   - **Do you intend to analyze Twitter data?**: No (for posting only)
   - **Will your product, service, or analysis make Twitter content available to government?**: No
5. Provide detailed description (similar to Step 1)
6. Submit application
7. **Wait for approval** (typically 1-2 business days, can take up to 7 days)

---

## Step 3: Create a Project and App

1. In [Developer Portal](https://developer.twitter.com/en/portal/dashboard), click **Projects & Apps**
2. Click **+ Create Project**
3. Fill in project details:
   - **Project name**: "Personal AI Employee"
   - **Use case**: Choose appropriate category (e.g., "Making a bot")
   - **Project description**: Brief description of your automation
4. Click **Next**
5. Create an App:
   - **App name**: "AI Employee Bot" (must be unique across Twitter)
   - Click **Complete**
6. **Save your API Keys** (shown once only):
   - API Key
   - API Secret
   - Bearer Token
7. Click **App settings** to configure

---

## Step 4: Configure App Permissions

1. In your app dashboard, go to **Settings** tab
2. Scroll to **User authentication settings**
3. Click **Set up**
4. Configure OAuth 2.0:
   - **App permissions**: **Read and Write** (required for posting)
   - **Type of App**: **Web App** or **Automated App or Bot**
   - **Callback URI**: `http://localhost:8000/callback`
   - **Website URL**: Your website or `https://example.com`
5. Save changes

---

## Step 5: Generate Access Tokens

### Option A: Using OAuth 2.0 User Context (Recommended)

1. Go to app **Keys and tokens** tab
2. Under **Authentication Tokens**, click **Generate** for **Access Token and Secret**
3. Save:
   - **Access Token** (starts with long alphanumeric string)
   - **Access Secret** (starts with long alphanumeric string)
4. These tokens represent YOUR Twitter account

### Option B: Using Bearer Token Only (Simpler)

1. Go to app **Keys and tokens** tab
2. Under **Bearer Token**, click **Regenerate** if needed
3. Save the **Bearer Token**
4. Note: Bearer token alone allows posting on behalf of the app

**For Personal AI Employee**: Use Bearer Token (Option B) for simplicity.

---

## Step 6: Configure .env

Add to your `.env` file:

```bash
# Twitter (X) MCP (required for Gold tier hackathon)
TWITTER_API_KEY=your-api-key
TWITTER_API_SECRET=your-api-secret
TWITTER_ACCESS_TOKEN=your-access-token
TWITTER_ACCESS_SECRET=your-access-secret
TWITTER_BEARER_TOKEN=your-bearer-token
```

**Note**: For posting tweets, only `TWITTER_BEARER_TOKEN` is strictly required.

---

## Step 7: Configure MCP Server

Update `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "twitter-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/personal-ai-employee/mcp_servers/twitter_mcp/server.py"],
      "env": {
        "TWITTER_BEARER_TOKEN": "your-bearer-token"
      }
    }
  }
}
```

---

## Step 8: Test MCP Server

**Test 1: List tools**
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python mcp_servers/twitter_mcp/server.py
```

**Expected Output**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {"name": "create_tweet", ...},
      {"name": "read_mentions", ...}
    ]
  }
}
```

**Test 2: Create test tweet**
```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"create_tweet","arguments":{"text":"Test tweet from Personal AI Employee 🤖 #AI"}}}' | \
  TWITTER_BEARER_TOKEN=your-token python mcp_servers/twitter_mcp/server.py
```

**Expected Output**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tweet_id": "1234567890123456789",
    "tweet_url": "https://twitter.com/i/web/status/1234567890123456789",
    "posted_at": "2026-02-14T10:30:00"
  }
}
```

**Verify**: Check your Twitter profile (@your_username) to see the test tweet.

---

## Step 9: Create Vault Folders

```bash
cd vault
mkdir -p Pending_Approval/Social/Twitter
mkdir -p Approved/Social/Twitter
```

---

## Step 10: Integration Test

**Create a test draft**:
```bash
cat > vault/Pending_Approval/Social/Twitter/TWITTER_POST_2026-02-14.md <<EOF
---
action: create_tweet
tweet_content: |
  🚀 Just automated my Twitter posting with AI!

  Building an autonomous digital employee that manages my social media while I focus on what matters.

  #AI #Automation #ProductivityHack
scheduled_date: 2026-02-14
character_count: 178
status: pending_approval
generated_at: 2026-02-14T10:00:00
---

# Twitter Tweet Draft

[Content above in frontmatter]
EOF
```

**Approve the draft**:
```bash
mv vault/Pending_Approval/Social/Twitter/TWITTER_POST_2026-02-14.md \
   vault/Approved/Social/Twitter/
```

**Wait 30 seconds** → Approval watcher invokes Twitter MCP

**Verify**:
- Check `vault/Logs/MCP_Actions/` for log entry
- Check your Twitter profile for the tweet

---

## Troubleshooting

### Error: "AUTH_FAILED: TWITTER_BEARER_TOKEN not configured"

**Solution**:
1. Verify `.env` has `TWITTER_BEARER_TOKEN=...`
2. Verify `mcp.json` has token in env section
3. Restart watchers: `./scripts/gold_watcher.sh restart`

### Error: "AUTH_FAILED: Twitter bearer token invalid"

**Cause**: Bearer token expired or regenerated

**Solution**:
1. Go to [Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Navigate to your app → **Keys and tokens**
3. Regenerate Bearer Token
4. Update `.env` and `mcp.json`
5. Restart watchers

### Error: "API_ERROR: 403 - Forbidden"

**Cause**: App permissions insufficient or Elevated access not approved

**Solution**:
1. Verify app has **Read and Write** permissions
2. Check if Elevated access is approved (Products → Twitter API v2)
3. If Standard access, ensure you haven't exceeded 1,500 tweets/month limit

### Error: "INVALID_INPUT: Tweet text exceeds 280 characters"

**Cause**: Tweet content too long

**Solution**:
1. System should auto-truncate in draft_generator.py
2. Manually edit draft to reduce character count
3. Verify truncation logic working correctly

### Error: "RATE_LIMITED: Twitter API rate limit exceeded"

**Cause**: Exceeded 50 tweets per 15 minutes

**Solution**:
1. Wait 15 minutes before retrying
2. System automatically backs off and retries
3. Check `vault/Needs_Action/` for retry instructions

### Tweet posted but URL shows "This page doesn't exist"

**Cause**: Tweet URL format requires username, not just ID

**Solution**:
1. Normal behavior - tweet is posted successfully
2. To get proper URL, need to fetch user ID separately
3. Tweet is accessible via Twitter profile and API

---

## Rate Limits & Best Practices

**Twitter API v2 Limits** (Elevated Access):
- **Tweets per day**: 2,400 (standard limit)
- **Tweets per 15 minutes**: 50
- **Read requests per 15 minutes**: 180

**Best Practices**:
- Tweet 5-10 times per day maximum (organic engagement)
- Schedule tweets during peak hours (9am-12pm, 5pm-6pm)
- Use hashtags (2-3 relevant hashtags max)
- Engage with replies and mentions
- Avoid identical/similar tweets (flagged as spam)

---

## Character Limit Handling

**280 Character Limit**:
- System auto-truncates at last complete word
- Adds "…" if truncated
- Logs warning in draft frontmatter

**Tips for staying under limit**:
- Keep tweets concise and impactful
- Use link shorteners for URLs
- Abbreviate where appropriate
- Use thread feature for longer thoughts (not implemented in v1)

---

## Security Checklist

- [ ] Bearer Token in `.env` only (never commit)
- [ ] API Keys stored securely
- [ ] Access Tokens never exposed in logs
- [ ] Regular token rotation if compromised
- [ ] Monitor unusual activity in Twitter Analytics

---

## Next Steps

- Test multi-platform posting (Facebook/Instagram/Twitter)
- Configure coordinated social media campaigns
- Review Phase 2B testing guide: `docs/gold/phase2b-testing.md`

---

**Congratulations!** Your Twitter MCP is configured. The AI Employee can now create tweets with your approval.
