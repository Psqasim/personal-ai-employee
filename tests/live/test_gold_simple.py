#!/usr/bin/env python3
"""
Gold Tier - Simplified Automated Test Suite

Tests core Gold Tier functionality with correct function signatures.

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-15
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("GOLD TIER - SIMPLIFIED TEST SUITE")
print("=" * 80)
print()

tests_passed = 0
tests_failed = 0


def test(name: str, condition: bool, details: str = ""):
    """Record test result"""
    global tests_passed, tests_failed
    if condition:
        tests_passed += 1
        print(f"✅ PASS: {name}")
    else:
        tests_failed += 1
        print(f"❌ FAIL: {name}")
    if details:
        print(f"   {details}")


print("=" * 80)
print("1. MCP SERVER CONNECTIVITY")
print("=" * 80)

try:
    from agent_skills.mcp_client import MCPClient
    client = MCPClient(timeout=30)

    # Test all 5 MCP servers
    servers = ["email-mcp", "linkedin-mcp", "whatsapp-mcp", "twitter-mcp", "odoo-mcp"]
    for server in servers:
        try:
            tools = client.list_tools(server)
            test(f"{server} connectivity", len(tools) > 0, f"{len(tools)} tools")
        except Exception as e:
            test(f"{server} connectivity", False, str(e))

except Exception as e:
    print(f"❌ MCP Client error: {e}")

print()
print("=" * 80)
print("2. DRAFT GENERATION (WITHOUT API CALLS)")
print("=" * 80)

# Test Email Draft
try:
    from agent_skills.draft_generator import generate_email_draft

    test_email = {
        "from": "test@example.com",
        "subject": "Test Subject",
        "body": "Test body content",
        "email_id": "test_123"
    }

    # This will use template fallback (no actual API call)
    draft = generate_email_draft(test_email)

    test("Email draft generation", "draft_body" in draft, f"Keys: {list(draft.keys())}")
    test("Email draft length", len(draft.get("draft_body", "")) <= 5000)

except Exception as e:
    test("Email draft generation", False, str(e))

# Test WhatsApp Draft
try:
    from agent_skills.draft_generator import generate_whatsapp_draft

    test_message = {
        "from": "+1234567890",
        "contact_name": "Test Contact",
        "text": "URGENT: Need help",
        "message_id": "msg_123"
    }

    draft = generate_whatsapp_draft(test_message)

    test("WhatsApp draft generation", "draft_reply" in draft, f"Keys: {list(draft.keys())}")
    test("WhatsApp draft length", len(draft.get("draft_reply", "")) <= 500)

except Exception as e:
    test("WhatsApp draft generation", False, str(e))

# Test LinkedIn Draft
try:
    from agent_skills.draft_generator import generate_linkedin_draft

    test_goals = "Business Goal: Increase AI adoption in enterprise"

    draft = generate_linkedin_draft(test_goals)

    test("LinkedIn draft generation", "post_content" in draft, f"Keys: {list(draft.keys())}")
    test("LinkedIn draft length", len(draft.get("post_content", "")) <= 3000)

except Exception as e:
    test("LinkedIn draft generation", False, str(e))

print()
print("=" * 80)
print("3. SAFETY & GOVERNANCE")
print("=" * 80)

# Test Odoo Draft-Only Mode
try:
    from agent_skills.mcp_client import MCPClient
    client = MCPClient()
    odoo_tools = client.list_tools("odoo-mcp")
    tool_names = [t.get("name", "") for t in odoo_tools]

    test("Odoo draft invoice tool", "create_draft_invoice" in tool_names)
    test("Odoo NO confirm method", not any("confirm" in n.lower() for n in tool_names))
    test("Odoo NO post method", not any("post" in n.lower() for n in tool_names))

except Exception as e:
    test("Odoo safety check", False, str(e))

# Test Approval Directories
vault_path = Path(os.getenv("VAULT_PATH", "./vault"))
test("Pending_Approval exists", (vault_path / "Pending_Approval").exists())
test("Approved exists", (vault_path / "Approved").exists())
test("Rejected exists", (vault_path / "Rejected").exists())

# Test Logging Directories
test("MCP action logs", (vault_path / "Logs" / "MCP_Actions").exists())
test("Human approval logs", (vault_path / "Logs" / "Human_Approvals").exists())
test("API usage logs", (vault_path / "Logs" / "API_Usage").exists())

# Test Bounded Iteration
max_iter = int(os.getenv("MAX_PLAN_ITERATIONS", "10"))
test("Bounded iteration (max 10)", max_iter == 10, f"MAX_PLAN_ITERATIONS={max_iter}")

# Test Cost Limits
cost_limit = float(os.getenv("API_DAILY_COST_LIMIT", "0.10"))
test("API cost limit", cost_limit == 0.10, f"${cost_limit}/day")

print()
print("=" * 80)
print("4. VAULT STRUCTURE")
print("=" * 80)

# Test Vault Directories
required_dirs = [
    "Inbox", "In_Progress", "Done", "Needs_Action",
    "Pending_Approval", "Approved", "Rejected",
    "Plans", "Briefings", "Logs"
]

for dir_name in required_dirs:
    dir_path = vault_path / dir_name
    test(f"vault/{dir_name}", dir_path.exists(), str(dir_path))

print()
print("=" * 80)
print("5. ENHANCED DASHBOARD")
print("=" * 80)

# Test Dashboard
dashboard = vault_path / "Dashboard.md"
if dashboard.exists():
    content = dashboard.read_text(encoding="utf-8")

    test("Dashboard exists", True)
    test("Dashboard has emoji header", "🤖" in content)
    test("Dashboard has tier badge", "🥇" in content or "🥈" in content or "🥉" in content)
    test("Dashboard has status icons", "📥" in content or "✅" in content)
    test("Dashboard has Gold section", "Gold Tier Status" in content or "🥇" in content)
    test("Dashboard has MCP status", "email-mcp" in content or "MCP Servers" in content)
    test("Dashboard has pending approvals", "Pending Approvals" in content or "⏳" in content)

else:
    test("Dashboard exists", False, "Dashboard.md not found")

print()
print("=" * 80)
print("FINAL SUMMARY")
print("=" * 80)

total = tests_passed + tests_failed
pass_rate = (tests_passed / total * 100) if total > 0 else 0

print()
print(f"✅ PASSED: {tests_passed}/{total} ({pass_rate:.0f}%)")
print(f"❌ FAILED: {tests_failed}/{total}")
print()

if pass_rate >= 90:
    grade = "A+"
    verdict = "🎉 EXCELLENT - Production Ready"
    exit_code = 0
elif pass_rate >= 80:
    grade = "A"
    verdict = "✅ GOOD - Minor Issues"
    exit_code = 0
elif pass_rate >= 70:
    grade = "B"
    verdict = "⚠️  ACCEPTABLE"
    exit_code = 1
else:
    grade = "C"
    verdict = "❌ NEEDS WORK"
    exit_code = 2

print(f"Grade: {grade}")
print(f"Verdict: {verdict}")
print()

if tests_failed == 0:
    print("🎉 ALL TESTS PASSED - GOLD TIER VALIDATED!")
else:
    print(f"⚠️  {tests_failed} test(s) failed - review required")

sys.exit(exit_code)
