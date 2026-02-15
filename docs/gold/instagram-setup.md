# Instagram MCP Setup Guide

**Feature**: Gold Tier - Phase 2B Social Media Integration
**Created**: 2026-02-14
**Status**: Production Ready

## Overview

The Instagram MCP server enables automated posting of images and stories to Instagram Business Accounts via the Instagram Basic Display API. This guide covers converting to a Business Account, creating a Facebook App, and configuring the MCP server.

---

## Prerequisites

- Instagram account (will be converted to Business Account)
- Facebook Page (required for Instagram Business Account)
- Facebook App with Instagram permissions
- Python 3.11+ installed
- Personal AI Employee Gold Tier deployed

---

## Step 1: Convert to Instagram Business Account

1. **Link Instagram to Facebook Page**:
   - Open Instagram app on mobile
   - Go to **Settings** → **Account** → **Switch to Professional Account**
   - Select **Business**
   - Choose category for your business
   - Link to your Facebook Page

2. **Verify Business Account**:
   - Go to Instagram profile
   - Should see **Professional Dashboard** button
   - Note: Creator accounts also work, but Business is recommended

---

## Step 2: Create Facebook App (if not done)

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click **My Apps** → **Create App**
3. Select **Business** as app type
4. Fill in app details and create
5. Note **App ID** and **App Secret**

---

## Step 3: Add Instagram Product

1. In your app dashboard, go to **Add Product**
2. Find **Instagram Basic Display** → Click **Set Up**
3. Scroll to **User Token Generator**
4. Click **Add or Remove Instagram Testers**
5. Add your Instagram Business Account username
6. Open Instagram → **Settings** → **Apps and Websites** → **Tester Invites**
7. Accept the invitation from your app

---

## Step 4: Configure Instagram Basic Display

1. In app dashboard, go to **Instagram Basic Display** → **Basic Display**
2. Click **Create New App**
3. Fill in:
   - **Display Name**: "Personal AI Employee"
   - **Valid OAuth Redirect URIs**: `https://localhost:8000/callback`
   - **Deauthorize Callback URL**: `https://localhost:8000/deauthorize`
   - **Data Deletion Request URL**: `https://localhost:8000/data-deletion`
4. Save changes
5. Note your **Instagram App ID** and **Instagram App Secret**

---

## Step 5: Generate Access Token

### Option A: Using User Token Generator (Quick Testing)

1. Go to **Instagram Basic Display** → **User Token Generator**
2. Click **Generate Token** next to your Instagram account
3. Authorize the app in popup
4. Copy the **User Access Token** (starts with `IGQV...`)
5. **Extend token to long-lived** (60 days):
   ```bash
   curl -X GET "https://graph.instagram.com/access_token" \
     -d "grant_type=ig_exchange_token" \
     -d "client_secret=YOUR_INSTAGRAM_APP_SECRET" \
     -d "access_token=YOUR_SHORT_LIVED_TOKEN"
   ```

### Option B: Using OAuth Flow (Production)

1. Construct authorization URL:
   ```
   https://api.instagram.com/oauth/authorize?
     client_id=YOUR_INSTAGRAM_APP_ID
     &redirect_uri=https://localhost:8000/callback
     &scope=user_profile,user_media
     &response_type=code
   ```
2. Visit URL, authorize app
3. Exchange code for access token:
   ```bash
   curl -X POST "https://api.instagram.com/oauth/access_token" \
     -d "client_id=YOUR_INSTAGRAM_APP_ID" \
     -d "client_secret=YOUR_INSTAGRAM_APP_SECRET" \
     -d "grant_type=authorization_code" \
     -d "redirect_uri=https://localhost:8000/callback" \
     -d "code=AUTHORIZATION_CODE"
   ```

---

## Step 6: Get Instagram User ID

Using the access token from Step 5:

```bash
curl -X GET "https://graph.instagram.com/me?fields=id,username&access_token=YOUR_ACCESS_TOKEN"
```

**Response**:
```json
{
  "id": "17841400123456789",
  "username": "your_instagram_username"
}
```

Save the **id** value - this is your `INSTAGRAM_USER_ID`.

---

## Step 7: Configure .env

Add to your `.env` file:

```bash
# Instagram MCP (required for Gold tier hackathon)
INSTAGRAM_APP_ID=your-instagram-app-id
INSTAGRAM_APP_SECRET=your-instagram-app-secret
INSTAGRAM_ACCESS_TOKEN=your-instagram-long-lived-token
INSTAGRAM_USER_ID=your-instagram-user-id
```

---

## Step 8: Configure MCP Server

Update `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "instagram-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/personal-ai-employee/mcp_servers/instagram_mcp/server.py"],
      "env": {
        "INSTAGRAM_ACCESS_TOKEN": "your-long-lived-token",
        "INSTAGRAM_USER_ID": "your-user-id"
      }
    }
  }
}
```

---

## Step 9: Prepare Test Images

Instagram requires images to be hosted at publicly accessible URLs. For testing:

**Option A: Use a public image hosting service**:
- [Imgur](https://imgur.com/) (free, no account needed for testing)
- Upload test image, copy direct link

**Option B: Host locally with ngrok**:
```bash
# Terminal 1: Start local server
cd /path/to/images
python -m http.server 8080

# Terminal 2: Expose with ngrok
ngrok http 8080

# Use ngrok URL in posts: https://abc123.ngrok.io/image.jpg
```

**Image Requirements**:
- Format: JPEG or PNG
- Min width: 320px
- Max width: 1440px
- Aspect ratio: 4:5 to 1.91:1 (portrait to landscape)
- Max file size: 8MB

---

## Step 10: Test MCP Server

**Test 1: List tools**
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python mcp_servers/instagram_mcp/server.py
```

**Test 2: Create test post**
```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"create_post","arguments":{"caption":"Test post from Personal AI Employee 🤖 #AI #Automation","image_url":"https://i.imgur.com/your-test-image.jpg"}}}' | \
  python mcp_servers/instagram_mcp/server.py
```

**Expected Output**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "post_id": "18123456789012345",
    "post_url": "https://www.instagram.com/p/18123456789012345",
    "posted_at": "2026-02-14T10:30:00"
  }
}
```

**Verify**: Check your Instagram profile to see the test post.

---

## Step 11: Create Vault Folders

```bash
cd vault
mkdir -p Pending_Approval/Social/Instagram
mkdir -p Approved/Social/Instagram
```

---

## Step 12: Integration Test

**Create a test draft**:
```bash
cat > vault/Pending_Approval/Social/Instagram/INSTAGRAM_POST_2026-02-14.md <<EOF
---
action: create_post
caption: |
  ✨ Exciting updates from our team!

  We've been working on cutting-edge AI automation that helps businesses scale efficiently.

  #AI #Automation #Tech #Innovation #BusinessGrowth
image_url: https://i.imgur.com/example.jpg
scheduled_date: 2026-02-14
character_count: 150
requires_image: true
status: pending_approval
generated_at: 2026-02-14T10:00:00
---

# Instagram Post Draft

[Content above in frontmatter]
EOF
```

**Approve the draft**:
```bash
mv vault/Pending_Approval/Social/Instagram/INSTAGRAM_POST_2026-02-14.md \
   vault/Approved/Social/Instagram/
```

**Wait 30 seconds** → Approval watcher invokes Instagram MCP

**Verify**:
- Check `vault/Logs/MCP_Actions/` for log entry
- Check Instagram profile for posted content

---

## Troubleshooting

### Error: "AUTH_FAILED: INSTAGRAM_ACCESS_TOKEN not configured"

**Solution**: Verify token in `.env` and `mcp.json`, restart watchers

### Error: "API_ERROR: Invalid image URL"

**Cause**: Image URL not publicly accessible or invalid format

**Solution**:
1. Test URL in browser - should download/display image
2. Ensure URL is HTTPS (Instagram requires HTTPS)
3. Verify image meets requirements (JPEG/PNG, correct size)

### Error: "API_ERROR: Unsupported media type"

**Cause**: Image aspect ratio out of range

**Solution**: Resize image to 4:5 (1080x1350px) or 1:1 (1080x1080px)

### Token expires after 60 days

**Solution**: Refresh token monthly:
```bash
curl -X GET "https://graph.instagram.com/refresh_access_token" \
  -d "grant_type=ig_refresh_token" \
  -d "access_token=YOUR_CURRENT_TOKEN"
```

### Error: "Rate limit exceeded"

**Cause**: Instagram limits: 25 posts/day, 100 stories/day

**Solution**: System automatically backs off. Check `vault/Needs_Action/` for retry

---

## Rate Limits & Best Practices

**Instagram API Limits**:
- 25 posts per day (feed posts)
- 100 stories per day
- 200 API calls per hour

**Best Practices**:
- Post 1-3 times per day for optimal engagement
- Use high-quality images (1080x1080px recommended)
- Include 5-10 relevant hashtags
- Post during peak hours (11am-1pm, 7pm-9pm)

---

## Security Checklist

- [ ] Access token in `.env` only (never commit)
- [ ] Regular token refresh (every 50 days)
- [ ] Test images in staging before production
- [ ] Monitor API usage in Facebook Developer dashboard

---

## Next Steps

- Configure Twitter MCP: `docs/gold/twitter-setup.md`
- Test multi-platform posting workflow
- Review Phase 2B testing guide: `docs/gold/phase2b-testing.md`

---

**Congratulations!** Your Instagram MCP is configured. The AI Employee can now create Instagram posts with your approval.
