#!/usr/bin/env python3
"""
Instagram MCP Server - Instagram Basic Display API via JSON-RPC 2.0

Implements Model Context Protocol for Instagram post creation using Instagram Basic Display API.
Requires Instagram Business Account and Facebook App with instagram_basic and instagram_content_publish permissions.

Tools:
- create_post: Create Instagram post with image
- create_story: Create Instagram story with image

Author: Personal AI Employee (Gold Tier - Phase 2B)
Created: 2026-02-14
"""

import sys
import json
import os
from datetime import datetime
from typing import Dict, Any
import requests


def create_post(caption: str, image_url: str, user_id: str = None) -> Dict[str, Any]:
    """
    Create Instagram post with image via Basic Display API.

    Args:
        caption: Post caption text (max 2,200 chars)
        image_url: Publicly accessible URL of image to post
        user_id: Instagram Business Account ID (optional, uses env var if not provided)

    Returns:
        Dict with post_id and post_url
    """
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    if not access_token:
        raise Exception("AUTH_FAILED: INSTAGRAM_ACCESS_TOKEN not configured")

    if not user_id:
        user_id = os.getenv("INSTAGRAM_USER_ID")
        if not user_id:
            raise Exception("AUTH_FAILED: INSTAGRAM_USER_ID not configured")

    # Validate caption length
    if len(caption) > 2200:
        raise Exception("INVALID_INPUT: Caption exceeds 2,200 characters")

    if not image_url:
        raise Exception("INVALID_INPUT: image_url is required for Instagram posts")

    # Step 1: Create media container
    container_url = f"https://graph.facebook.com/v18.0/{user_id}/media"

    container_payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token
    }

    try:
        # Create media container
        response = requests.post(container_url, data=container_payload, timeout=30)

        # Handle auth errors
        if response.status_code == 401 or response.status_code == 403:
            raise Exception("AUTH_FAILED: Instagram access token expired or insufficient permissions")

        # Handle other errors
        if response.status_code >= 400:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_message = error_data.get('error', {}).get('message', response.text)
            raise Exception(f"API_ERROR: {response.status_code} - {error_message}")

        # Extract container ID
        container_data = response.json()
        container_id = container_data.get("id")

        if not container_id:
            raise Exception("API_ERROR: Failed to create media container")

        # Step 2: Publish media container
        publish_url = f"https://graph.facebook.com/v18.0/{user_id}/media_publish"

        publish_payload = {
            "creation_id": container_id,
            "access_token": access_token
        }

        response = requests.post(publish_url, data=publish_payload, timeout=30)

        # Handle rate limiting
        if response.status_code == 429:
            raise Exception("RATE_LIMITED: Instagram API rate limit exceeded. Retry after 60 minutes")

        # Handle errors
        if response.status_code >= 400:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_message = error_data.get('error', {}).get('message', response.text)
            raise Exception(f"API_ERROR: {response.status_code} - {error_message}")

        # Extract post ID
        response_data = response.json()
        post_id = response_data.get("id", "unknown")

        # Construct post URL (simplified - actual permalink requires additional API call)
        post_url = f"https://www.instagram.com/p/{post_id}"

        return {
            "post_id": post_id,
            "post_url": post_url,
            "posted_at": datetime.now().isoformat()
        }

    except requests.exceptions.Timeout:
        raise Exception("NETWORK_ERROR: Request timed out")
    except requests.exceptions.RequestException as e:
        raise Exception(f"NETWORK_ERROR: {e}")


def create_story(image_url: str, user_id: str = None) -> Dict[str, Any]:
    """
    Create Instagram story with image.

    Args:
        image_url: Publicly accessible URL of image for story
        user_id: Instagram Business Account ID (optional, uses env var if not provided)

    Returns:
        Dict with story_id
    """
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    if not access_token:
        raise Exception("AUTH_FAILED: INSTAGRAM_ACCESS_TOKEN not configured")

    if not user_id:
        user_id = os.getenv("INSTAGRAM_USER_ID")
        if not user_id:
            raise Exception("AUTH_FAILED: INSTAGRAM_USER_ID not configured")

    if not image_url:
        raise Exception("INVALID_INPUT: image_url is required for Instagram stories")

    # Create story media container
    container_url = f"https://graph.facebook.com/v18.0/{user_id}/media"

    container_payload = {
        "image_url": image_url,
        "media_type": "STORIES",
        "access_token": access_token
    }

    try:
        # Create media container for story
        response = requests.post(container_url, data=container_payload, timeout=30)

        # Handle auth errors
        if response.status_code == 401 or response.status_code == 403:
            raise Exception("AUTH_FAILED: Instagram access token expired or insufficient permissions")

        # Handle other errors
        if response.status_code >= 400:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_message = error_data.get('error', {}).get('message', response.text)
            raise Exception(f"API_ERROR: {response.status_code} - {error_message}")

        # Extract container ID
        container_data = response.json()
        container_id = container_data.get("id")

        # Publish story
        publish_url = f"https://graph.facebook.com/v18.0/{user_id}/media_publish"

        publish_payload = {
            "creation_id": container_id,
            "access_token": access_token
        }

        response = requests.post(publish_url, data=publish_payload, timeout=30)

        # Handle errors
        if response.status_code >= 400:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_message = error_data.get('error', {}).get('message', response.text)
            raise Exception(f"API_ERROR: {response.status_code} - {error_message}")

        # Extract story ID
        response_data = response.json()
        story_id = response_data.get("id", "unknown")

        return {
            "story_id": story_id,
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
                "description": "Create an Instagram post with image via Basic Display API",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "caption": {"type": "string", "description": "Post caption (max 2,200 chars)"},
                        "image_url": {"type": "string", "description": "Publicly accessible URL of image"},
                        "user_id": {"type": "string", "description": "Instagram Business Account ID (optional)"}
                    },
                    "required": ["caption", "image_url"]
                }
            },
            {
                "name": "create_story",
                "description": "Create an Instagram story with image",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_url": {"type": "string", "description": "Publicly accessible URL of image for story"},
                        "user_id": {"type": "string", "description": "Instagram Business Account ID (optional)"}
                    },
                    "required": ["image_url"]
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
                    caption=arguments.get("caption"),
                    image_url=arguments.get("image_url"),
                    user_id=arguments.get("user_id")
                )
                return {"jsonrpc": "2.0", "id": request_id, "result": result}

            elif tool_name == "create_story":
                result = create_story(
                    image_url=arguments.get("image_url"),
                    user_id=arguments.get("user_id")
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
