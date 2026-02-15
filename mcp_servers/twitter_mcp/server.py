#!/usr/bin/env python3
"""
Twitter (X) MCP Server - Twitter API v2 via JSON-RPC 2.0

Implements Model Context Protocol for Twitter tweet creation using Twitter API v2.
Requires Twitter Developer Account with Elevated access and OAuth 2.0 credentials.

Tools:
- create_tweet: Create a tweet (formerly "post")
- read_mentions: Read recent mentions

Author: Personal AI Employee (Gold Tier - Phase 2B)
Created: 2026-02-14
"""

import sys
import json
import os
from datetime import datetime
from typing import Dict, Any
import requests


def create_tweet(text: str) -> Dict[str, Any]:
    """
    Create a tweet via Twitter API v2.

    Args:
        text: Tweet content (max 280 chars for standard accounts)

    Returns:
        Dict with tweet_id and tweet_url
    """
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        raise Exception("AUTH_FAILED: TWITTER_BEARER_TOKEN not configured")

    # Validate text length
    if len(text) > 280:
        raise Exception("INVALID_INPUT: Tweet text exceeds 280 characters")

    # Twitter API v2 endpoint
    url = "https://api.twitter.com/2/tweets"

    # Build request payload
    payload = {
        "text": text
    }

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    try:
        # Make API request
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        # Handle rate limiting
        if response.status_code == 429:
            raise Exception("RATE_LIMITED: Twitter API rate limit exceeded. Retry after 15 minutes")

        # Handle auth errors
        if response.status_code == 401 or response.status_code == 403:
            raise Exception("AUTH_FAILED: Twitter bearer token invalid or insufficient permissions")

        # Handle other errors
        if response.status_code >= 400:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_message = error_data.get('detail', response.text)
            if 'errors' in error_data:
                error_message = error_data['errors'][0].get('message', error_message)
            raise Exception(f"API_ERROR: {response.status_code} - {error_message}")

        # Extract tweet ID from response
        response_data = response.json()
        tweet_data = response_data.get("data", {})
        tweet_id = tweet_data.get("id", "unknown")

        # Construct tweet URL (requires knowing username - simplified here)
        # For production, fetch user ID from /2/users/me first
        tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"

        return {
            "tweet_id": tweet_id,
            "tweet_url": tweet_url,
            "posted_at": datetime.now().isoformat()
        }

    except requests.exceptions.Timeout:
        raise Exception("NETWORK_ERROR: Request timed out")
    except requests.exceptions.RequestException as e:
        raise Exception(f"NETWORK_ERROR: {e}")


def read_mentions(max_results: int = 10) -> Dict[str, Any]:
    """
    Read recent mentions of the authenticated user.

    Args:
        max_results: Number of mentions to retrieve (default: 10, max: 100)

    Returns:
        Dict with mentions array
    """
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        raise Exception("AUTH_FAILED: TWITTER_BEARER_TOKEN not configured")

    # First, get user ID
    user_url = "https://api.twitter.com/2/users/me"
    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }

    try:
        # Get authenticated user ID
        user_response = requests.get(user_url, headers=headers, timeout=30)

        if user_response.status_code >= 400:
            raise Exception(f"API_ERROR: Failed to get user ID - {user_response.status_code}")

        user_data = user_response.json()
        user_id = user_data.get("data", {}).get("id")

        if not user_id:
            raise Exception("API_ERROR: Could not retrieve user ID")

        # Get mentions
        mentions_url = f"https://api.twitter.com/2/users/{user_id}/mentions"

        params = {
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,author_id,text"
        }

        response = requests.get(mentions_url, headers=headers, params=params, timeout=30)

        # Handle errors
        if response.status_code >= 400:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_message = error_data.get('detail', response.text)
            raise Exception(f"API_ERROR: {response.status_code} - {error_message}")

        # Extract mentions
        response_data = response.json()
        mentions = response_data.get("data", [])

        return {
            "mentions": mentions,
            "count": len(mentions)
        }

    except requests.exceptions.Timeout:
        raise Exception("NETWORK_ERROR: Request timed out")
    except requests.exceptions.RequestException as e:
        raise Exception(f"NETWORK_ERROR: {e}")


def tools_list() -> Dict[str, Any]:
    """List available tools"""
    return {
        "tools": [
            {
                "name": "create_tweet",
                "description": "Create a tweet via Twitter API v2 (max 280 chars)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Tweet content (max 280 chars)"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "read_mentions",
                "description": "Read recent mentions of the authenticated user",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "max_results": {"type": "integer", "description": "Number of mentions (default: 10, max: 100)"}
                    },
                    "required": []
                }
            }
        ]
    }


def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle JSON-RPC 2.0 request"""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    try:
        if method == "tools/list":
            result = tools_list()
            return {"jsonrpc": "2.0", "id": request_id, "result": result}

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "create_tweet":
                result = create_tweet(
                    text=arguments.get("text")
                )
                return {"jsonrpc": "2.0", "id": request_id, "result": result}

            elif tool_name == "read_mentions":
                result = read_mentions(
                    max_results=arguments.get("max_results", 10)
                )
                return {"jsonrpc": "2.0", "id": request_id, "result": result}

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {tool_name}"}
                }

        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": str(e)}
        }


def main():
    """Main loop: read JSON-RPC requests from stdin, write responses to stdout"""
    for line in sys.stdin:
        if not line.strip():
            continue

        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()
