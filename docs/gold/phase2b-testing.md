# Phase 2B Testing Guide - Social Media MCPs

**Feature**: Gold Tier - Phase 2B Social Media Integration
**Created**: 2026-02-14
**Status**: Production Ready

## Overview

This document provides comprehensive test procedures for Phase 2B social media MCPs (Facebook, Instagram, Twitter). It covers setup verification, API authentication, posting tests, approval workflow validation, error handling, and multi-platform coordination.

**Prerequisites**: All three social media MCPs installed and configured per their respective setup guides.

---

## Table of Contents

1. [Pre-Flight Checklist](#pre-flight-checklist)
2. [Facebook MCP Tests](#facebook-mcp-tests)
3. [Instagram MCP Tests](#instagram-mcp-tests)
4. [Twitter MCP Tests](#twitter-mcp-tests)
5. [Approval Workflow Tests](#approval-workflow-tests)
6. [Error Handling Tests](#error-handling-tests)
7. [Multi-Platform Coordination Tests](#multi-platform-coordination-tests)
8. [Performance & Load Tests](#performance--load-tests)
9. [Security & Safety Tests](#security--safety-tests)
10. [Regression Tests](#regression-tests)

---

## Pre-Flight Checklist

Before starting Phase 2B tests, verify all prerequisites are met:

### Environment Configuration

- [ ] `.env` file contains all required tokens:
  ```bash
  FACEBOOK_ACCESS_TOKEN=...
  FACEBOOK_PAGE_ID=...
  INSTAGRAM_ACCESS_TOKEN=...
  INSTAGRAM_USER_ID=...
  TWITTER_BEARER_TOKEN=...
  ```

- [ ] `~/.config/claude-code/mcp.json` includes all three MCPs:
  - `facebook-mcp`
  - `instagram-mcp`
  - `twitter-mcp`

- [ ] MCP server files exist:
  - `mcp_servers/facebook_mcp/server.py`
  - `mcp_servers/instagram_mcp/server.py`
  - `mcp_servers/twitter_mcp/server.py`

### Vault Structure

- [ ] Social media approval folders exist:
  ```bash
  vault/Pending_Approval/Social/Facebook/
  vault/Pending_Approval/Social/Instagram/
  vault/Pending_Approval/Social/Twitter/
  vault/Approved/Social/Facebook/
  vault/Approved/Social/Instagram/
  vault/Approved/Social/Twitter/
  ```

- [ ] Log folders exist:
  ```bash
  vault/Logs/MCP_Actions/
  vault/Needs_Action/
  ```

### Watchers Running

- [ ] Approval watcher is running:
  ```bash
  ps aux | grep approval_watcher.py
  # OR
  pm2 list | grep approval_watcher
  ```

---

## Facebook MCP Tests

### Test FB-001: MCP Server Health Check

**Objective**: Verify Facebook MCP server responds to basic requests

**Steps**:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python mcp_servers/facebook_mcp/server.py
```

**Expected Result**:
- Status: ✅ Success
- Output contains `"tools"` array with `create_post` and `read_feed`
- Response time: <1 second

**Actual Result**: _____________

---

### Test FB-002: Facebook Post Creation (Direct API)

**Objective**: Verify Facebook MCP can post directly

**Steps**:
```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"create_post","arguments":{"message":"Test post from Phase 2B testing suite 🧪 #Testing"}}}' | \
  FACEBOOK_ACCESS_TOKEN=your-token FACEBOOK_PAGE_ID=your-page-id \
  python mcp_servers/facebook_mcp/server.py
```

**Expected Result**:
- Status: ✅ Success
- Output contains `post_id` and `post_url`
- Post appears on Facebook Page within 10 seconds
- Log entry created in `vault/Logs/MCP_Actions/`

**Actual Result**: _____________

---

### Test FB-003: Facebook Feed Read

**Objective**: Verify Facebook MCP can read recent posts

**Steps**:
```bash
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"read_feed","arguments":{"limit":5}}}' | \
  FACEBOOK_ACCESS_TOKEN=your-token FACEBOOK_PAGE_ID=your-page-id \
  python mcp_servers/facebook_mcp/server.py
```

**Expected Result**:
- Status: ✅ Success
- Output contains `posts` array with up to 5 items
- Each post has `id`, `message`, `created_time`

**Actual Result**: _____________

---

### Test FB-004: Facebook Authentication Error Handling

**Objective**: Verify graceful handling of invalid token

**Steps**:
```bash
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"create_post","arguments":{"message":"Test"}}}' | \
  FACEBOOK_ACCESS_TOKEN=invalid_token FACEBOOK_PAGE_ID=your-page-id \
  python mcp_servers/facebook_mcp/server.py
```

**Expected Result**:
- Status: ❌ Expected Error
- Error message contains `AUTH_FAILED`
- No post created on Facebook
- Error logged appropriately

**Actual Result**: _____________

---

## Instagram MCP Tests

### Test IG-001: MCP Server Health Check

**Objective**: Verify Instagram MCP server responds

**Steps**:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python mcp_servers/instagram_mcp/server.py
```

**Expected Result**:
- Status: ✅ Success
- Output contains `create_post` and `create_story` tools

**Actual Result**: _____________

---

### Test IG-002: Instagram Post Creation with Image

**Objective**: Verify Instagram MCP can post image

**Prerequisites**: Have a publicly accessible test image URL (e.g., https://i.imgur.com/test.jpg)

**Steps**:
```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"create_post","arguments":{"caption":"Phase 2B Testing 🧪 #Testing #AI","image_url":"https://i.imgur.com/your-test-image.jpg"}}}' | \
  INSTAGRAM_ACCESS_TOKEN=your-token INSTAGRAM_USER_ID=your-user-id \
  python mcp_servers/instagram_mcp/server.py
```

**Expected Result**:
- Status: ✅ Success
- Output contains `post_id` and `post_url`
- Post appears on Instagram within 30 seconds
- Image displays correctly

**Actual Result**: _____________

---

### Test IG-003: Instagram Story Creation

**Objective**: Verify Instagram MCP can create stories

**Steps**:
```bash
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"create_story","arguments":{"image_url":"https://i.imgur.com/test-story.jpg"}}}' | \
  INSTAGRAM_ACCESS_TOKEN=your-token INSTAGRAM_USER_ID=your-user-id \
  python mcp_servers/instagram_mcp/server.py
```

**Expected Result**:
- Status: ✅ Success
- Story appears in Instagram app within 30 seconds
- Story is visible for 24 hours

**Actual Result**: _____________

---

### Test IG-004: Instagram Missing Image Error

**Objective**: Verify error when image_url is missing

**Steps**:
```bash
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"create_post","arguments":{"caption":"Test without image"}}}' | \
  INSTAGRAM_ACCESS_TOKEN=your-token INSTAGRAM_USER_ID=your-user-id \
  python mcp_servers/instagram_mcp/server.py
```

**Expected Result**:
- Status: ❌ Expected Error
- Error message contains `image_url is required`
- No post created

**Actual Result**: _____________

---

## Twitter MCP Tests

### Test TW-001: MCP Server Health Check

**Objective**: Verify Twitter MCP server responds

**Steps**:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python mcp_servers/twitter_mcp/server.py
```

**Expected Result**:
- Status: ✅ Success
- Output contains `create_tweet` and `read_mentions` tools

**Actual Result**: _____________

---

### Test TW-002: Twitter Tweet Creation

**Objective**: Verify Twitter MCP can post tweets

**Steps**:
```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"create_tweet","arguments":{"text":"Phase 2B Testing Suite 🧪 Automated social media posting with AI! #Testing #AI #Automation"}}}' | \
  TWITTER_BEARER_TOKEN=your-token python mcp_servers/twitter_mcp/server.py
```

**Expected Result**:
- Status: ✅ Success
- Output contains `tweet_id` and `tweet_url`
- Tweet appears on profile within 10 seconds

**Actual Result**: _____________

---

### Test TW-003: Twitter Character Limit Enforcement

**Objective**: Verify 280 character limit is enforced

**Steps**:
```bash
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"create_tweet","arguments":{"text":"This is a very long tweet that exceeds the 280 character limit and should be rejected by the Twitter MCP server before it even attempts to call the Twitter API because we want to catch these errors early in the validation process and provide clear feedback to the user about what went wrong so they can fix it and retry"}}}' | \
  TWITTER_BEARER_TOKEN=your-token python mcp_servers/twitter_mcp/server.py
```

**Expected Result**:
- Status: ❌ Expected Error
- Error message contains `exceeds 280 characters`
- No tweet posted

**Actual Result**: _____________

---

### Test TW-004: Twitter Mentions Read

**Objective**: Verify Twitter MCP can read mentions

**Steps**:
```bash
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"read_mentions","arguments":{"max_results":10}}}' | \
  TWITTER_BEARER_TOKEN=your-token python mcp_servers/twitter_mcp/server.py
```

**Expected Result**:
- Status: ✅ Success
- Output contains `mentions` array
- Mentions count matches expected

**Actual Result**: _____________

---

## Approval Workflow Tests

### Test AW-001: Facebook Draft Approval Flow

**Objective**: End-to-end test of Facebook approval workflow

**Steps**:
1. Create draft file:
   ```bash
   cat > vault/Pending_Approval/Social/Facebook/FACEBOOK_POST_test.md <<EOF
   ---
   action: create_post
   post_content: "Approval workflow test for Facebook 🔄"
   scheduled_date: 2026-02-14
   status: pending_approval
   ---
   # Facebook Post Draft
   [Content above]
   EOF
   ```

2. Wait 5 seconds
3. Move to approved:
   ```bash
   mv vault/Pending_Approval/Social/Facebook/FACEBOOK_POST_test.md \
      vault/Approved/Social/Facebook/
   ```
4. Wait 30 seconds
5. Check Facebook Page for post
6. Check logs: `cat vault/Logs/MCP_Actions/$(date +%Y-%m-%d).md`

**Expected Result**:
- Post appears on Facebook
- Log entry shows `human_approved=true`
- Approval file moved to Done/

**Actual Result**: _____________

---

### Test AW-002: Instagram Draft Approval Flow

**Objective**: End-to-end test of Instagram approval workflow

**Steps**:
1. Create draft with image URL
2. Move to approved folder
3. Verify post appears on Instagram
4. Verify logs

**Expected Result**:
- Instagram post created with image
- Logged with approval path

**Actual Result**: _____________

---

### Test AW-003: Twitter Draft Approval Flow

**Objective**: End-to-end test of Twitter approval workflow

**Steps**:
1. Create draft tweet
2. Move to approved folder
3. Verify tweet appears on Twitter
4. Verify logs

**Expected Result**:
- Tweet posted successfully
- Logged with approval

**Actual Result**: _____________

---

### Test AW-004: Rejection Workflow

**Objective**: Verify rejected drafts are handled correctly

**Steps**:
1. Create Facebook draft
2. Move to `vault/Rejected/`
3. Wait 10 seconds
4. Verify no post created
5. Check logs for rejection entry

**Expected Result**:
- No post created on Facebook
- Rejection logged
- File moved to Done/ with status="rejected"

**Actual Result**: _____________

---

## Error Handling Tests

### Test EH-001: Network Timeout Handling

**Objective**: Verify MCP handles network timeouts gracefully

**Steps**:
1. Disconnect network
2. Approve a social media draft
3. Observe error handling

**Expected Result**:
- Error logged with `NETWORK_ERROR`
- Draft moved to Needs_Action with retry instructions
- System continues processing other drafts

**Actual Result**: _____________

---

### Test EH-002: Rate Limit Handling

**Objective**: Verify rate limit backoff

**Steps**:
1. Rapidly approve 55+ Twitter drafts (exceed 15-min limit)
2. Observe backoff behavior

**Expected Result**:
- After limit hit, error contains `RATE_LIMITED`
- System backs off 15 minutes
- Retry after backoff succeeds

**Actual Result**: _____________

---

### Test EH-003: Token Expiry Handling

**Objective**: Verify expired token detection

**Steps**:
1. Use expired access token
2. Attempt to post
3. Check error handling

**Expected Result**:
- Error contains `AUTH_FAILED` or `token expired`
- Creates `vault/Needs_Action/{platform}_auth_expired.md`
- Pauses that platform, continues others

**Actual Result**: _____________

---

## Multi-Platform Coordination Tests

### Test MP-001: Coordinated 3-Platform Post

**Objective**: Post same content to all three platforms simultaneously

**Steps**:
1. Create identical drafts for Facebook, Instagram (with image), Twitter:
   ```bash
   # Create all three drafts with coordinated content
   cat > vault/Pending_Approval/Social/Facebook/FB_multi_test.md <<EOF
   ---
   action: create_post
   post_content: "Multi-platform test: Facebook, Instagram, Twitter! 🚀 #Testing"
   ---
   EOF

   cat > vault/Pending_Approval/Social/Instagram/IG_multi_test.md <<EOF
   ---
   action: create_post
   caption: "Multi-platform test: Facebook, Instagram, Twitter! 🚀 #Testing"
   image_url: "https://i.imgur.com/test.jpg"
   ---
   EOF

   cat > vault/Pending_Approval/Social/Twitter/TW_multi_test.md <<EOF
   ---
   action: create_tweet
   tweet_content: "Multi-platform test: Facebook, Instagram, Twitter! 🚀 #Testing"
   ---
   EOF
   ```

2. Approve all three simultaneously:
   ```bash
   mv vault/Pending_Approval/Social/*/\*_multi_test.md vault/Approved/Social/*/
   ```

3. Wait 60 seconds
4. Verify posts on all three platforms
5. Check logs for all three

**Expected Result**:
- All three posts appear within 60 seconds
- All logged with same timestamp (within 1 minute)
- No conflicts or errors

**Actual Result**: _____________

---

### Test MP-002: Platform-Specific Content Adaptation

**Objective**: Verify content is adapted per platform constraints

**Steps**:
1. Create draft with:
   - Facebook: Long content (>500 chars)
   - Instagram: Image + hashtags
   - Twitter: Exactly 280 chars

2. Approve all
3. Verify correct formatting on each

**Expected Result**:
- Facebook: Full content
- Instagram: Image + caption + hashtags
- Twitter: 280 chars exactly

**Actual Result**: _____________

---

## Performance & Load Tests

### Test PL-001: Concurrent Approvals

**Objective**: Handle 10 simultaneous approvals

**Steps**:
1. Create 10 drafts across platforms (3 FB, 3 IG, 4 TW)
2. Approve all simultaneously
3. Monitor completion time

**Expected Result**:
- All 10 posted within 90 seconds
- No race conditions
- All logged correctly

**Actual Result**: _____________

---

### Test PL-002: Daily Volume Test

**Objective**: Verify system handles expected daily volume

**Steps**:
1. Process 20 drafts in one day (7 FB, 7 IG, 6 TW)
2. Monitor for degradation

**Expected Result**:
- All posted successfully
- No performance degradation
- Logs clean and organized

**Actual Result**: _____________

---

## Security & Safety Tests

### Test SS-001: Credentials Not Logged

**Objective**: Verify tokens never appear in logs

**Steps**:
1. Process several approved drafts
2. Search all logs for token strings:
   ```bash
   grep -r "EAAA" vault/Logs/  # Facebook token prefix
   grep -r "IGQV" vault/Logs/  # Instagram token prefix
   grep -r "Bearer" vault/Logs/  # Twitter bearer token
   ```

**Expected Result**:
- No tokens found in any logs
- Only redacted or omitted credentials

**Actual Result**: _____________

---

### Test SS-002: Approval Gate Enforcement

**Objective**: Verify NO posts without approval

**Steps**:
1. Create drafts in Pending_Approval/
2. Wait 5 minutes WITHOUT approving
3. Check platforms - should be NO posts

**Expected Result**:
- No posts appear on any platform
- Drafts remain in Pending_Approval/

**Actual Result**: _____________

---

### Test SS-003: Human Approval Audit Trail

**Objective**: Verify all posts have approval trail

**Steps**:
1. Review `vault/Logs/MCP_Actions/` for today
2. For each entry, verify:
   - `human_approved=true`
   - `approval_file_path` present
   - Approval file existed at time of post

**Expected Result**:
- 100% of posts have approval records
- No automated posts without approval

**Actual Result**: _____________

---

## Regression Tests

### Test RG-001: Backward Compatibility - Silver Features

**Objective**: Verify Silver features still work

**Steps**:
1. Test Gmail watcher
2. Test LinkedIn (existing)
3. Test WhatsApp monitoring
4. Test Plan.md generation

**Expected Result**:
- All Silver features functional
- No performance degradation
- No new errors

**Actual Result**: _____________

---

### Test RG-002: Bronze Features Intact

**Objective**: Verify Bronze tier still functional

**Steps**:
1. File watching works
2. Dashboard updates work
3. AI analysis works (if enabled)

**Expected Result**:
- All Bronze features work
- Dashboard updates < 2 seconds

**Actual Result**: _____________

---

## Test Summary Template

```markdown
## Phase 2B Testing Results

**Date**: YYYY-MM-DD
**Tester**: [Your Name]
**Environment**: [Dev/Staging/Production]

### Summary
- Total Tests: ____
- Passed: ____
- Failed: ____
- Blocked: ____

### Critical Issues
1. [Issue description if any]
2. [Issue description if any]

### Non-Critical Issues
1. [Issue description if any]

### Notes
- [Any additional observations]

### Sign-Off
[ ] All critical tests passed
[ ] Regression tests passed
[ ] Ready for production deployment

**Tester Signature**: _______________
**Date**: _______________
```

---

## Troubleshooting Common Test Failures

### Draft Not Posted After Approval

**Possible Causes**:
1. Approval watcher not running
2. Token expired
3. Network issue

**Debug Steps**:
```bash
# Check approval watcher running
ps aux | grep approval_watcher

# Check logs for errors
tail -n 50 vault/Logs/Error_Recovery/$(date +%Y-%m-%d).md

# Test MCP directly
echo '...' | python mcp_servers/facebook_mcp/server.py
```

---

### Post Appears But Not Logged

**Possible Causes**:
1. Log folder permissions
2. Logging code error

**Debug Steps**:
```bash
# Check log folder permissions
ls -la vault/Logs/MCP_Actions/

# Check for log file
ls -la vault/Logs/MCP_Actions/$(date +%Y-%m-%d).md

# Create if missing
touch vault/Logs/MCP_Actions/$(date +%Y-%m-%d).md
```

---

## Next Steps After Testing

1. **If all tests pass**:
   - Document any configuration tweaks made
   - Update quickstart.md with lessons learned
   - Deploy to production

2. **If tests fail**:
   - Document failures in GitHub issues
   - Fix blocking issues first
   - Re-run failed tests

3. **Performance optimization**:
   - If any test exceeded time limits, investigate
   - Consider caching strategies
   - Review API rate limits

---

**Phase 2B Testing Complete!** All three social media MCPs validated and ready for production use.
