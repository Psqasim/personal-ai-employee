#!/usr/bin/env python3
"""
Gold Tier - MCP Server Validation Script
Tests connectivity and health of all 5 MCP servers

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-15
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent_skills.mcp_client import MCPClient

def test_mcp_servers():
    """Test all 5 MCP servers for connectivity"""

    print("=" * 80)
    print("GOLD TIER - MCP SERVER VALIDATION")
    print("=" * 80)
    print()

    # MCP servers to test
    servers = [
        ("email-mcp", "Email MCP (SMTP Send)"),
        ("linkedin-mcp", "LinkedIn MCP (API v2 Posting)"),
        ("whatsapp-mcp", "WhatsApp MCP (Playwright Automation)"),
        ("twitter-mcp", "Twitter MCP (API v2 Tweeting)"),
        ("odoo-mcp", "Odoo MCP (Accounting Drafts)")
    ]

    client = MCPClient(timeout=30)  # 30s timeout for testing

    results = {
        "passed": [],
        "failed": []
    }

    # Test each server
    for server_name, description in servers:
        print(f"Testing {description}...")
        print(f"Server: {server_name}")

        try:
            # Test 1: List tools (health check)
            tools = client.list_tools(server_name)

            if len(tools) > 0:
                print(f"  ✅ Connected - {len(tools)} tools available:")
                for tool in tools:
                    print(f"     - {tool.get('name', 'unknown')}")
                results["passed"].append((server_name, description))
            else:
                print(f"  ⚠️  Connected but no tools found")
                results["failed"].append((server_name, description, "No tools available"))

        except Exception as e:
            print(f"  ❌ FAILED: {str(e)}")
            results["failed"].append((server_name, description, str(e)))

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    print(f"✅ PASSED: {len(results['passed'])}/{len(servers)}")
    for server_name, description in results["passed"]:
        print(f"   - {description}")
    print()

    if results["failed"]:
        print(f"❌ FAILED: {len(results['failed'])}/{len(servers)}")
        for server_name, description, error in results["failed"]:
            print(f"   - {description}")
            print(f"     Error: {error}")
        print()

    # Final verdict
    if len(results["passed"]) == len(servers):
        print("🎉 ALL MCP SERVERS OPERATIONAL")
        return 0
    elif len(results["passed"]) >= 3:
        print("⚠️  PARTIAL SUCCESS - Some servers need attention")
        return 1
    else:
        print("🚨 CRITICAL - Most servers failing")
        return 2


if __name__ == "__main__":
    exit_code = test_mcp_servers()
    sys.exit(exit_code)
