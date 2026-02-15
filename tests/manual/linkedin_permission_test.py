#!/usr/bin/env python3
"""
LinkedIn Permission Tester
Tests different API endpoints to diagnose permission issues
"""
from dotenv import load_dotenv
load_dotenv()

import os
import requests
import json

access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
author_urn = os.getenv('LINKEDIN_AUTHOR_URN')

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
    'X-Restli-Protocol-Version': '2.0.0'
}

print('═' * 70)
print('  LINKEDIN API PERMISSION DIAGNOSTICS')
print('═' * 70)
print()

tests = [
    {
        'name': 'Basic Profile (OpenID)',
        'url': 'https://api.linkedin.com/v2/userinfo',
        'method': 'GET',
        'required_scope': 'openid, profile'
    },
    {
        'name': 'Member Profile (Lite Profile)',
        'url': 'https://api.linkedin.com/v2/me',
        'method': 'GET',
        'required_scope': 'r_liteprofile'
    },
    {
        'name': 'Email Address',
        'url': 'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))',
        'method': 'GET',
        'required_scope': 'r_emailaddress'
    },
    {
        'name': 'Create UGC Post',
        'url': 'https://api.linkedin.com/v2/ugcPosts',
        'method': 'POST',
        'required_scope': 'w_member_social',
        'payload': {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": "Test post from API"
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
    }
]

results = []

for test in tests:
    print(f'Testing: {test["name"]}')
    print(f'  Endpoint: {test["url"]}')
    print(f'  Required: {test["required_scope"]}')
    
    try:
        if test['method'] == 'GET':
            response = requests.get(test['url'], headers=headers, timeout=10)
        else:
            response = requests.post(
                test['url'], 
                headers=headers, 
                json=test.get('payload'), 
                timeout=10
            )
        
        if response.status_code in [200, 201]:
            print(f'  ✅ SUCCESS (Status: {response.status_code})')
            results.append((test['name'], 'PASS', test['required_scope']))
        else:
            print(f'  ❌ FAILED (Status: {response.status_code})')
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_msg = error_data.get('message', response.text[:100])
            print(f'     Error: {error_msg}')
            results.append((test['name'], 'FAIL', test['required_scope']))
            
    except Exception as e:
        print(f'  ❌ ERROR: {e}')
        results.append((test['name'], 'ERROR', test['required_scope']))
    
    print()

print('═' * 70)
print('  SUMMARY')
print('═' * 70)
print()
print(f'{"Test":<30} {"Status":<10} {"Required Scope"}')
print('-' * 70)
for name, status, scope in results:
    status_icon = '✅' if status == 'PASS' else '❌'
    print(f'{status_icon} {name:<28} {status:<10} {scope}')

print()
print('═' * 70)
print('  RECOMMENDATIONS')
print('═' * 70)
print()

failed_tests = [r for r in results if r[1] != 'PASS']
if failed_tests:
    print('Your app needs these products/scopes:')
    print()
    for name, _, scope in failed_tests:
        print(f'  • {scope}')
    print()
    print('Add products in LinkedIn Developer Portal:')
    print('  → https://www.linkedin.com/developers/apps')
    print()
else:
    print('✅ All permissions working! LinkedIn posting should work.')

