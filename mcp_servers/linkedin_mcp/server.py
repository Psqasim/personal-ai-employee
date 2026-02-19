#!/usr/bin/env python3
"""
LinkedIn MCP Server - LinkedIn REST API (new, 2024+)

Uses /rest/posts endpoint with LinkedIn-Version: 202601 header.
Author URN resolved from userinfo (urn:li:person:XXX).

Tools:
- create_post: Create LinkedIn text or image post
"""

import sys
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import requests


def _headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": "202601",           # YYYYMM — 6 digits required
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }


def _get_credentials():
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not token:
        raise Exception("AUTH_FAILED: LINKEDIN_ACCESS_TOKEN not set")
    urn = os.getenv("LINKEDIN_AUTHOR_URN")
    if not urn:
        raise Exception("AUTH_FAILED: LINKEDIN_AUTHOR_URN not set")
    return token, urn


def _upload_image(access_token: str, author_urn: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Upload image to LinkedIn and return image URN."""
    # Step 1: Initialize upload
    init_url = "https://api.linkedin.com/rest/images?action=initializeUpload"
    init_payload = {"initializeUploadRequest": {"owner": author_urn}}
    r = requests.post(init_url, json=init_payload, headers=_headers(access_token), timeout=30)
    if r.status_code >= 400:
        raise Exception(f"IMAGE_UPLOAD_INIT_FAILED: {r.status_code} {r.text}")
    data = r.json()["value"]
    upload_url = data["uploadUrl"]
    image_urn = data["image"]

    # Step 2: Upload the bytes
    upload_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": mime_type,
        "LinkedIn-Version": "202601",
    }
    r2 = requests.put(upload_url, data=image_bytes, headers=upload_headers, timeout=60)
    if r2.status_code not in (200, 201):
        raise Exception(f"IMAGE_UPLOAD_FAILED: {r2.status_code} {r2.text}")

    return image_urn  # e.g. "urn:li:image:C5600AQF..."


def create_post(text: str, image_url: str = None, image_path: str = None) -> Dict[str, Any]:
    """
    Create LinkedIn post via REST API.

    Args:
        text: Post content (max 3000 chars)
        image_url: Optional public image URL to attach
        image_path: Optional local file path to attach

    Returns:
        Dict with post_id and post_url
    """
    if len(text) > 3000:
        raise Exception("INVALID_INPUT: Post text exceeds 3000 characters")

    access_token, author_urn = _get_credentials()

    # Build base payload (new /rest/posts schema)
    payload: Dict[str, Any] = {
        "author": author_urn,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    # Attach image if provided
    image_urn = None
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        mime = "image/png" if image_path.endswith(".png") else "image/jpeg"
        image_urn = _upload_image(access_token, author_urn, image_bytes, mime)
    elif image_url:
        # Download then upload
        r = requests.get(image_url, timeout=30)
        if r.status_code == 200:
            mime = "image/png" if "png" in r.headers.get("Content-Type", "") else "image/jpeg"
            image_urn = _upload_image(access_token, author_urn, r.content, mime)

    if image_urn:
        payload["content"] = {
            "media": {
                "id": image_urn,
                "title": "Post image",
            }
        }

    url = "https://api.linkedin.com/rest/posts"
    try:
        response = requests.post(url, json=payload, headers=_headers(access_token), timeout=30)

        if response.status_code == 429:
            raise Exception("RATE_LIMITED: LinkedIn API rate limit. Retry after 60 minutes")
        if response.status_code == 401:
            raise Exception("AUTH_FAILED: LinkedIn access token expired or invalid")
        if response.status_code >= 400:
            raise Exception(f"API_ERROR: {response.status_code} - {response.text}")

        # New API returns 201 with post ID in X-RestLi-Id header
        post_id = response.headers.get("X-RestLi-Id") or response.headers.get("x-restli-id", "")
        if not post_id:
            try:
                post_id = response.json().get("id", "")
            except Exception:
                post_id = ""

        post_url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id else "https://www.linkedin.com/feed/"

        return {
            "post_id": post_id,
            "post_url": post_url,
            "posted_at": datetime.now().isoformat(),
            "has_image": image_urn is not None,
        }

    except requests.exceptions.Timeout:
        raise Exception("NETWORK_ERROR: Request timed out")
    except requests.exceptions.RequestException as e:
        raise Exception(f"NETWORK_ERROR: {e}")


def tools_list() -> Dict[str, Any]:
    return {
        "tools": [
            {
                "name": "create_post",
                "description": "Create a LinkedIn post (text + optional image)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Post content (max 3000 chars)"},
                        "image_url": {"type": "string", "description": "Optional public image URL"},
                        "image_path": {"type": "string", "description": "Optional local image file path"},
                    },
                    "required": ["text"]
                }
            }
        ]
    }


def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    try:
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": request_id, "result": tools_list()}

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "create_post":
                result = create_post(
                    text=arguments.get("text"),
                    image_url=arguments.get("image_url"),
                    image_path=arguments.get("image_path"),
                )
                return {"jsonrpc": "2.0", "id": request_id, "result": result}

            return {
                "jsonrpc": "2.0", "id": request_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
            }

        return {
            "jsonrpc": "2.0", "id": request_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"}
        }

    except Exception as e:
        return {
            "jsonrpc": "2.0", "id": request_id,
            "error": {"code": -32000, "message": str(e)}
        }


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            print(json.dumps({
                "jsonrpc": "2.0", "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            }), flush=True)


if __name__ == "__main__":
    main()
