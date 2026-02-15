#!/usr/bin/env python3
"""
LinkedIn MCP Server - LinkedIn API v2 via JSON-RPC 2.0

Implements Model Context Protocol for LinkedIn post creation using LinkedIn API v2.
Requires OAuth2 access token with w_member_social scope.

Tools:
- create_post: Create LinkedIn post

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
"""

import sys
import json
import os
from datetime import datetime
from typing import Dict, Any
import requests


def create_post(text: str, author_urn: str = None) -> Dict[str, Any]:
    """
    Create LinkedIn post via API v2.

    Args:
        text: Post content (max 3000 chars)
        author_urn: LinkedIn person URN (optional, uses env var if not provided)

    Returns:
        Dict with post_id and post_url
    """
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not access_token:
        raise Exception("AUTH_FAILED: LINKEDIN_ACCESS_TOKEN not configured")

    if not author_urn:
        author_urn = os.getenv("LINKEDIN_AUTHOR_URN")
        if not author_urn:
            raise Exception("AUTH_FAILED: LINKEDIN_AUTHOR_URN not configured")

    # Validate text length
    if len(text) > 3000:
        raise Exception("INVALID_INPUT: Post text exceeds 3000 characters")

    # LinkedIn API v2 endpoint
    url = "https://api.linkedin.com/v2/ugcPosts"

    # Build request payload
    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": text
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    try:
        # Make API request
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        # Handle rate limiting
        if response.status_code == 429:
            raise Exception("RATE_LIMITED: LinkedIn API rate limit exceeded. Retry after 60 minutes")

        # Handle auth errors
        if response.status_code == 401:
            raise Exception("AUTH_FAILED: LinkedIn access token expired or invalid")

        # Handle other errors
        if response.status_code >= 400:
            raise Exception(f"API_ERROR: {response.status_code} - {response.text}")

        # Extract post ID from response
        response_data = response.json()
        post_id = response_data.get("id", "unknown")

        # Construct post URL (simplified)
        post_url = f"https://www.linkedin.com/feed/update/{post_id}"

        return {
            "post_id": post_id,
            "post_url": post_url,
            "posted_at": datetime.now().isoformat()
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
                "name": "create_post",
                "description": "Create a LinkedIn post via API v2",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Post content (max 3000 chars)"},
                        "author_urn": {"type": "string", "description": "LinkedIn person URN (optional)"}
                    },
                    "required": ["text"]
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

            if tool_name == "create_post":
                result = create_post(
                    text=arguments.get("text"),
                    author_urn=arguments.get("author_urn")
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
