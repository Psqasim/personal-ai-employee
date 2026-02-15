# LinkedIn MCP Server Contract

**Server Name**: `linkedin-mcp`
**Protocol**: JSON-RPC 2.0 over stdin/stdout
**Purpose**: Post to LinkedIn via LinkedIn API v2 (OAuth2 authenticated)

---

## Tools

### 1. create_post

**Description**: Create a LinkedIn post on behalf of the authenticated user

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "text": {
      "type": "string",
      "description": "Post content (plain text, supports newlines)",
      "maxLength": 3000
    },
    "author_urn": {
      "type": "string",
      "description": "LinkedIn author URN (format: urn:li:person:xxxxx)",
      "pattern": "^urn:li:person:[A-Za-z0-9-]+$"
    }
  },
  "required": ["text", "author_urn"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "post_id": {
      "type": "string",
      "description": "LinkedIn post ID (activity URN)"
    },
    "post_url": {
      "type": "string",
      "format": "uri",
      "description": "Public URL to view the post"
    },
    "posted_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

**Error Codes**:
- `-32000`: `AUTH_FAILED` - LinkedIn access token invalid or expired
- `-32001`: `RATE_LIMITED` - LinkedIn API rate limit exceeded (429)
- `-32002`: `INVALID_TOKEN` - Access token malformed or revoked
- `-32003`: `NETWORK_ERROR` - Network request failed
- `-32004`: `POST_TOO_LONG` - Text exceeds 3000 character limit

**Example Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "create_post",
    "arguments": {
      "text": "Most business owners spend 5+ hours/day on email and admin tasks.\n\nHere's what I learned after implementing AI automation:\n- Email triage cut from 2 hours to 15 minutes\n- Meeting scheduling fully automated\n- Client follow-ups never missed\n\nThe secret? Combining AI drafts with human oversight. You get speed + quality.\n\nWhat's your biggest time drain? Comment below.",
      "author_urn": "urn:li:person:abc123xyz"
    }
  }
}
```

**Example Success Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "post_id": "urn:li:activity:7030123456789",
    "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:7030123456789",
    "posted_at": "2026-02-13T14:30:00Z"
  }
}
```

**Example Rate Limit Error**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32001,
    "message": "RATE_LIMITED: Retry after 3600 seconds (1 hour)"
  }
}
```

---

### 2. get_feed (Optional - Future Enhancement)

**Description**: Retrieve recent posts from user's LinkedIn feed

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "max_results": {
      "type": "integer",
      "default": 10,
      "minimum": 1,
      "maximum": 50
    }
  }
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "posts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "author": {"type": "string"},
          "text": {"type": "string", "maxLength": 500},
          "engagement": {
            "type": "object",
            "properties": {
              "likes": {"type": "integer"},
              "comments": {"type": "integer"}
            }
          }
        }
      }
    }
  }
}
```

---

## Configuration

**Environment Variables**:
```bash
LINKEDIN_ACCESS_TOKEN=your-oauth2-access-token
LINKEDIN_AUTHOR_URN=urn:li:person:your-linkedin-id
```

**OAuth2 Token Setup**:
1. Create LinkedIn app at https://www.linkedin.com/developers/apps
2. Request scopes: `w_member_social` (post creation)
3. Complete OAuth2 flow to get access token
4. Token validity: 60 days (refresh required periodically)

---

## Implementation Notes

**LinkedIn API v2 Endpoint**:
```
POST https://api.linkedin.com/v2/ugcPosts
```

**Request Headers**:
```
Authorization: Bearer {LINKEDIN_ACCESS_TOKEN}
Content-Type: application/json
X-Restli-Protocol-Version: 2.0.0
```

**Request Body** (create_post):
```json
{
  "author": "urn:li:person:abc123xyz",
  "lifecycleState": "PUBLISHED",
  "specificContent": {
    "com.linkedin.ugc.ShareContent": {
      "shareCommentary": {
        "text": "Post content here..."
      },
      "shareMediaCategory": "NONE"
    }
  },
  "visibility": {
    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
  }
}
```

**Rate Limits** (LinkedIn API):
- 100 posts/day per user
- 10 posts/hour per user
- Handle 429 responses → back off 60 minutes

**Error Recovery**:
- 401 Unauthorized → token expired, create `vault/Needs_Action/linkedin_token_expired.md`
- 429 Rate Limited → update draft status to `rate_limited_retry`, retry after 60min
- 5xx Server Error → retry 3 times (exponential backoff)

---

## Testing

```bash
# Test create_post
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"create_post","arguments":{"text":"Test post","author_urn":"urn:li:person:test"}}}' | LINKEDIN_ACCESS_TOKEN=your-token python mcp_servers/linkedin_mcp/server.py

# Expected: {"jsonrpc":"2.0","id":1,"result":{"post_id":"urn:li:activity:...","post_url":"...","posted_at":"..."}}
```

---

## Security Considerations

- Access token has write permissions → store securely in .env
- Never log full access token → sanitize to "...last4chars" in logs
- Token expiry: monitor 401 responses, notify human to refresh token
- Post content sanitization: first 50 chars logged to MCP action log
