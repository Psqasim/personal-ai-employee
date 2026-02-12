# Contract: Claude API Integration

**API Provider**: Anthropic
**Endpoint**: `https://api.anthropic.com/v1/messages`
**SDK**: `anthropic>=0.18.0` (Python)
**Authentication**: API Key (x-api-key header)

## Request Specification

### Priority Analysis Request

**Method**: POST `/v1/messages`

**Headers**:
```http
x-api-key: {CLAUDE_API_KEY}
anthropic-version: 2023-06-01
content-type: application/json
```

**Body**:
```json
{
  "model": "claude-3-5-sonnet-20241022",
  "max_tokens": 100,
  "system": "You are a task prioritization assistant. Analyze the task and respond ONLY with JSON in this exact format: {\"priority\": \"High\"|\"Medium\"|\"Low\", \"category\": \"Work\"|\"Personal\"|\"Urgent\"|\"Uncategorized\", \"reasoning\": \"<brief explanation in max 100 chars>\"}",
  "messages": [
    {
      "role": "user",
      "content": "Analyze this task:\n\nTitle: {task_title}\nContent: {task_snippet_200_chars}"
    }
  ]
}
```

**Timeout**: 5 seconds (FR-S006)

**Rate Limiting**: Max 10 requests/minute, max 100 requests/day (FR-S007)

## Response Specification

### Success Response (200 OK)

```json
{
  "id": "msg_01ABC123",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "{\"priority\": \"High\", \"category\": \"Work\", \"reasoning\": \"Client-facing with end-of-day deadline\"}"
    }
  ],
  "model": "claude-3-5-sonnet-20241022",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 152,
    "output_tokens": 48
  }
}
```

**Parsing**:
1. Extract `content[0].text` → JSON string
2. Parse JSON → priority, category, reasoning
3. Calculate cost: `(input_tokens * $3.00/1M) + (output_tokens * $15.00/1M)`

### Error Responses

**401 Unauthorized** (invalid API key):
```json
{
  "type": "error",
  "error": {
    "type": "authentication_error",
    "message": "invalid x-api-key"
  }
}
```
**Action**: Log error, fall back to Bronze defaults (Priority="Medium")

**429 Too Many Requests** (rate limit):
```json
{
  "type": "error",
  "error": {
    "type": "rate_limit_error",
    "message": "Number of requests per minute has been exceeded"
  }
}
```
**Action**: Wait 60 seconds, retry (max 3 retries)

**500 Internal Server Error**:
```json
{
  "type": "error",
  "error": {
    "type": "api_error",
    "message": "Internal server error"
  }
}
```
**Action**: Log error, fall back to Bronze defaults

### Timeout (5 seconds):
**Action**: Raise `asyncio.TimeoutError`, fall back to Bronze defaults

## Cost Structure

**Model**: claude-3-5-sonnet-20241022
- Input: $3.00 per million tokens
- Output: $15.00 per million tokens

**Typical Request Cost** (priority analysis):
- Input: ~150 tokens (prompt + task title + 200 char snippet)
- Output: ~50 tokens (structured JSON response)
- Cost: $(150 * 3.00 / 1M) + (50 * 15.00 / 1M) = $0.00045 + $0.00075 = **$0.0012 per request**

**Daily Target**: <$0.10 for 100 tasks
- With caching (30% hit rate): 100 * 0.70 * $0.0012 = **$0.084/day** ✓

## Implementation Contract

```python
from anthropic import AsyncAnthropic
import asyncio
import json

async def analyze_priority(task_title: str, task_snippet: str) -> dict:
    """
    Analyze task priority using Claude API.

    Args:
        task_title: Task title (max 100 chars)
        task_snippet: First 200 chars of task content

    Returns:
        {
            "priority": "High"|"Medium"|"Low",
            "category": "Work"|"Personal"|"Urgent"|"Uncategorized",
            "reasoning": str,
            "cost": float,
            "cached": bool,
            "fallback": bool
        }

    Raises:
        ValueError: If inputs invalid
    """
    client = AsyncAnthropic(
        api_key=os.getenv("CLAUDE_API_KEY"),
        timeout=5.0
    )

    system_prompt = (
        "You are a task prioritization assistant. "
        "Respond ONLY with JSON: "
        "{\"priority\": \"High\"|\"Medium\"|\"Low\", "
        "\"category\": \"Work\"|\"Personal\"|\"Urgent\"|\"Uncategorized\", "
        "\"reasoning\": \"<max 100 chars>\"}"
    )

    try:
        response = await client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=100,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"Analyze this task:\n\nTitle: {task_title}\nContent: {task_snippet[:200]}"
            }]
        )

        # Parse structured JSON response
        result = json.loads(response.content[0].text)

        # Calculate cost
        usage = response.usage
        cost = (usage.input_tokens * 3.00 / 1_000_000) + (usage.output_tokens * 15.00 / 1_000_000)

        return {
            **result,
            "cost": cost,
            "cached": False,
            "fallback": False
        }

    except (asyncio.TimeoutError, Exception) as e:
        log_warning(f"API call failed: {e}")
        return {
            "priority": "Medium",
            "category": "Uncategorized",
            "reasoning": "API unavailable, using Bronze defaults",
            "cost": 0.0,
            "cached": False,
            "fallback": True
        }
```

## Testing Contract

**Unit Tests** (mock API responses):
```python
@pytest.mark.asyncio
async def test_analyze_priority_success(mock_anthropic_client):
    # Mock successful API response
    mock_response = {
        "content": [{"text": '{"priority": "High", "category": "Work", "reasoning": "Client deadline"}'}],
        "usage": {"input_tokens": 150, "output_tokens": 50}
    }
    mock_anthropic_client.messages.create.return_value = mock_response

    result = await analyze_priority("Urgent client proposal", "Client needs this by EOD")

    assert result["priority"] == "High"
    assert result["category"] == "Work"
    assert result["cost"] == pytest.approx(0.0012, rel=1e-4)
    assert result["fallback"] is False

@pytest.mark.asyncio
async def test_analyze_priority_timeout_fallback():
    # Mock timeout scenario
    with pytest.raises(asyncio.TimeoutError):
        # Simulate timeout after 5 seconds
        pass

    result = await analyze_priority("Test task", "Content")

    assert result["priority"] == "Medium"  # Bronze default
    assert result["fallback"] is True
    assert result["cost"] == 0.0
```

---

**Contract Status**: Complete. Ready for implementation in `agent_skills/ai_analyzer.py`.
