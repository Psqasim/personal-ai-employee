#!/usr/bin/env python3
"""
Facebook MCP Server - Facebook Graph API via JSON-RPC 2.0

Implements Model Context Protocol for Facebook post creation using Facebook Graph API.
Requires Facebook App credentials and Page access token with pages_manage_posts permission.

Tools:
- create_post: Create Facebook page post
- read_feed: Read recent posts from Facebook page (summary)

Author: Personal AI Employee (Gold Tier - Phase 2B)
Created: 2026-02-14
"""

import sys
import json
import os
from datetime import datetime
from typing import Dict, Any
import requests


def create_post(message: str, page_id: str = None) -> Dict[str, Any]:
    """
    Create Facebook page post via Graph API.

    Args:
        message: Post content (max 63,206 chars for Facebook)
        page_id: Facebook Page ID (optional, uses env var if not provided)

    Returns:
        Dict with post_id and post_url
    """
    access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
    if not access_token:
        raise Exception("AUTH_FAILED: FACEBOOK_ACCESS_TOKEN not configured")

    if not page_id:
        page_id = os.getenv("FACEBOOK_PAGE_ID")
        if not page_id:
            raise Exception("AUTH_FAILED: FACEBOOK_PAGE_ID not configured")

    # Validate message length
    if len(message) > 63206:
        raise Exception("INVALID_INPUT: Post message exceeds 63,206 characters")

    # Facebook Graph API endpoint
    url = f"https://graph.facebook.com/v18.0/{page_id}/feed"

    # Build request payload
    payload = {
        "message": message,
        "access_token": access_token
    }

    try:
        # Make API request
        response = requests.post(url, data=payload, timeout=30)

        # Handle rate limiting
        if response.status_code == 429:
            raise Exception("RATE_LIMITED: Facebook API rate limit exceeded. Retry after 60 minutes")

        # Handle auth errors
        if response.status_code == 401 or response.status_code == 403:
            raise Exception("AUTH_FAILED: Facebook access token expired or insufficient permissions")

        # Handle other errors
        if response.status_code >= 400:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_message = error_data.get('error', {}).get('message', response.text)
            raise Exception(f"API_ERROR: {response.status_code} - {error_message}")

        # Extract post ID from response
        response_data = response.json()
        post_id = response_data.get("id", "unknown")

        # Construct post URL
        post_url = f"https://www.facebook.com/{post_id}"

        return {
            "post_id": post_id,
            "post_url": post_url,
            "posted_at": datetime.now().isoformat()
        }

    except requests.exceptions.Timeout:
        raise Exception("NETWORK_ERROR: Request timed out")
    except requests.exceptions.RequestException as e:
        raise Exception(f"NETWORK_ERROR: {e}")


def read_feed(page_id: str = None, limit: int = 10) -> Dict[str, Any]:
    """
    Read recent posts from Facebook page feed.

    Args:
        page_id: Facebook Page ID (optional, uses env var if not provided)
        limit: Number of posts to retrieve (default: 10, max: 100)

    Returns:
        Dict with posts array containing message and created_time
    """
    access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
    if not access_token:
        raise Exception("AUTH_FAILED: FACEBOOK_ACCESS_TOKEN not configured")

    if not page_id:
        page_id = os.getenv("FACEBOOK_PAGE_ID")
        if not page_id:
            raise Exception("AUTH_FAILED: FACEBOOK_PAGE_ID not configured")

    # Validate limit
    if limit > 100:
        limit = 100

    # Facebook Graph API endpoint
    url = f"https://graph.facebook.com/v18.0/{page_id}/feed"

    params = {
        "access_token": access_token,
        "limit": limit,
        "fields": "id,message,created_time,permalink_url"
    }

    try:
        # Make API request
        response = requests.get(url, params=params, timeout=30)

        # Handle auth errors
        if response.status_code == 401 or response.status_code == 403:
            raise Exception("AUTH_FAILED: Facebook access token expired or insufficient permissions")

        # Handle other errors
        if response.status_code >= 400:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_message = error_data.get('error', {}).get('message', response.text)
            raise Exception(f"API_ERROR: {response.status_code} - {error_message}")

        # Extract posts from response
        response_data = response.json()
        posts = response_data.get("data", [])

        return {
            "posts": posts,
            "count": len(posts)
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
                "description": "Create a Facebook page post via Graph API",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Post content (max 63,206 chars)"},
                        "page_id": {"type": "string", "description": "Facebook Page ID (optional)"}
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "read_feed",
                "description": "Read recent posts from Facebook page feed",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string", "description": "Facebook Page ID (optional)"},
                        "limit": {"type": "integer", "description": "Number of posts (default: 10, max: 100)"}
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

            if tool_name == "create_post":
                result = create_post(
                    message=arguments.get("message"),
                    page_id=arguments.get("page_id")
                )
                return {"jsonrpc": "2.0", "id": request_id, "result": result}

            elif tool_name == "read_feed":
                result = read_feed(
                    page_id=arguments.get("page_id"),
                    limit=arguments.get("limit", 10)
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
