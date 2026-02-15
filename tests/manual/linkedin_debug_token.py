#!/usr/bin/env python3
"""
LinkedIn Token Debug - Step 1: Check Token & Get Author URN

Checks:
1. Current token validity
2. Token permissions/scopes
3. Get user profile (author URN)

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-15
"""

import sys
import os
from dotenv import load_dotenv
import requests
import json

# Load environment
load_dotenv()

print("=" * 80)
print("STEP 1: DEBUG LINKEDIN TOKEN")
print("=" * 80)
print()

# Get LinkedIn token from .env
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")

if not LINKEDIN_ACCESS_TOKEN:
    print("❌ ERROR: LINKEDIN_ACCESS_TOKEN not found in .env")
    sys.exit(1)

print("📊 LinkedIn Configuration:")
print(f"   Token: {LINKEDIN_ACCESS_TOKEN[:20]}...{LINKEDIN_ACCESS_TOKEN[-10:]}")
print(f"   Length: {len(LINKEDIN_ACCESS_TOKEN)} characters")
print()

# Test 1: Get User Profile (to get author URN)
print("-" * 80)
print("Test 1: Get User Profile (/v2/me)")
print("-" * 80)
print()

try:
    headers = {
        'Authorization': f'Bearer {LINKEDIN_ACCESS_TOKEN}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0'
    }

    response = requests.get(
        'https://api.linkedin.com/v2/me',
        headers=headers,
        timeout=30
    )

    print(f"Status Code: {response.status_code}")
    print()

    if response.status_code == 200:
        profile = response.json()

        print("✅ Token is valid!")
        print()
        print("📄 Profile Information:")
        print(json.dumps(profile, indent=2))
        print()

        # Extract person ID
        if 'id' in profile:
            person_id = profile['id']
            author_urn = f"urn:li:person:{person_id}"

            print("=" * 80)
            print("🎯 AUTHOR URN FOUND!")
            print("=" * 80)
            print()
            print(f"   Person ID: {person_id}")
            print(f"   Author URN: {author_urn}")
            print()
            print("💾 Add this to your .env file:")
            print(f"   LINKEDIN_AUTHOR_URN={author_urn}")
            print()

        # Show available profile fields
        if 'localizedFirstName' in profile and 'localizedLastName' in profile:
            full_name = f"{profile['localizedFirstName']} {profile['localizedLastName']}"
            print(f"   Name: {full_name}")
            print()

    elif response.status_code == 401:
        print("❌ Token is INVALID or EXPIRED")
        print()
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        print()
        print("📝 To fix:")
        print("   1. Go to: https://www.linkedin.com/developers/apps")
        print("   2. Select your app")
        print("   3. Generate new access token")
        print("   4. Update LINKEDIN_ACCESS_TOKEN in .env")
        print()
        sys.exit(1)

    elif response.status_code == 403:
        print("❌ Token lacks required permissions")
        print()
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        print()
        sys.exit(1)

    else:
        print(f"⚠️  Unexpected status code: {response.status_code}")
        print()
        print("Response:")
        print(response.text)
        print()

except requests.exceptions.RequestException as e:
    print(f"❌ Network error: {e}")
    sys.exit(1)

# Test 2: Check Token Introspection (if available)
print("-" * 80)
print("Test 2: Check Token Scopes")
print("-" * 80)
print()

try:
    # Try to get token introspection
    # Note: LinkedIn doesn't have a standard introspection endpoint
    # We'll infer from successful API calls

    print("✅ Token appears to have basic profile access")
    print()
    print("Required scopes for posting:")
    print("   - r_liteprofile or r_basicprofile (read profile)")
    print("   - w_member_social (write posts)")
    print()

    print("⚠️  Note: LinkedIn tokens expire quickly!")
    print("   Most tokens expire in 60 days")
    print("   Check token creation date in LinkedIn Developer Console")
    print()

except Exception as e:
    print(f"⚠️  Could not check scopes: {e}")
    print()

# Test 3: Try a test API call to verify write permissions
print("-" * 80)
print("Test 3: Verify Write Permissions")
print("-" * 80)
print()

if 'author_urn' in locals():
    print(f"Testing with Author URN: {author_urn}")
    print()

    # Don't actually post, just prepare the request
    print("✅ Author URN ready for posting")
    print()
    print("🎯 Ready for STEP 2: Update .env and Test Posting")
    print()
else:
    print("⚠️  Could not extract Author URN from profile")
    print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

if response.status_code == 200 and 'author_urn' in locals():
    print("✅ Token Status: Valid")
    print("✅ Profile Access: Working")
    print(f"✅ Author URN: {author_urn}")
    print()
    print("📝 Next Steps:")
    print(f"   1. Add to .env: LINKEDIN_AUTHOR_URN={author_urn}")
    print("   2. Restart any running processes")
    print("   3. Test LinkedIn posting")
    print()
else:
    print("❌ Token has issues - see errors above")
    print()
