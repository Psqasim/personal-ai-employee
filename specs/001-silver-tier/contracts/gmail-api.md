# Contract: Gmail API Integration

**API Provider**: Google
**Endpoint**: `https://gmail.googleapis.com/gmail/v1/users/me/messages`
**SDK**: `google-api-python-client>=2.80.0` (Python)
**Authentication**: OAuth2 with refresh token

## OAuth2 Flow

**Scopes**:
- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/gmail.labels`

**Token Storage**: `~/.config/personal-ai-employee/gmail_token.json`

**Auto-Refresh**: Token refreshes automatically on expiry (60-day lifetime)

## Request: List Important Emails

**Method**: GET `/gmail/v1/users/me/messages?q=is:unread is:important`

**Query Parameters**:
- `q`: `is:unread is:important` (filter for unread, important emails)
- `maxResults`: 10 (process 10 emails per poll cycle)

**Poll Interval**: 120 seconds (2 minutes, configurable via `GMAIL_POLL_INTERVAL`)

## Response: Message List

```json
{
  "messages": [
    {"id": "123abc", "threadId": "456def"},
    {"id": "789ghi", "threadId": "012jkl"}
  ],
  "resultSizeEstimate": 2
}
```

## Request: Get Message Details

**Method**: GET `/gmail/v1/users/me/messages/{id}?format=metadata&metadataHeaders=From&metadataHeaders=Subject`

## Response: Message Metadata

```json
{
  "id": "123abc",
  "threadId": "456def",
  "snippet": "Client requesting proposal by end of day...",
  "payload": {
    "headers": [
      {"name": "From", "value": "client@example.com"},
      {"name": "Subject", "value": "Urgent: Proposal Request"}
    ]
  },
  "internalDate": "1707656400000"
}
```

## Error Handling

- **403 Forbidden**: OAuth2 token expired → Re-run `setup_gmail_auth.py`
- **429 Rate Limit**: Exponential backoff (60s, 120s, 240s)
- **500 Server Error**: Retry on next poll cycle

## Task File Generation

**Filename**: `vault/Inbox/EMAIL_{message_id}.md`

**Content**:
```markdown
---
type: email
from: client@example.com
subject: Urgent: Proposal Request
received: 2026-02-11T14:30:00Z
priority: high
status: pending
---

## Email Content
Client requesting proposal by end of day...

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
```

**Duplicate Prevention**: Track processed message IDs in `vault/Logs/gmail_processed_ids.txt`

---

**Contract Status**: Complete. Ready for implementation in `watchers/gmail_watcher.py`.
