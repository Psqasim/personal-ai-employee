#!/usr/bin/env python3
"""
Odoo Connection Test - Step 1: Verify Connection & Access

Tests:
1. Connection to Odoo server
2. Authentication with credentials
3. User access and permissions
4. Available modules

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-15
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import xmlrpc.client

# Load environment
load_dotenv()

print("=" * 80)
print("STEP 1: ODOO CONNECTION TEST")
print("=" * 80)
print()

# Get Odoo credentials from .env
ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

print("📊 Odoo Configuration:")
print(f"   URL: {ODOO_URL}")
print(f"   Database: {ODOO_DB}")
print(f"   Username: {ODOO_USER}")
print(f"   Password: {'*' * len(ODOO_PASSWORD) if ODOO_PASSWORD else 'NOT SET'}")
print()

if not all([ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD]):
    print("❌ ERROR: Missing Odoo credentials in .env")
    sys.exit(1)

# Test 1: Server Connection
print("-" * 80)
print("Test 1: Server Connection")
print("-" * 80)

try:
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    version = common.version()

    print("✅ Server reachable!")
    print(f"   Odoo Version: {version.get('server_version', 'Unknown')}")
    print(f"   Server Series: {version.get('server_serie', 'Unknown')}")
    print(f"   Protocol: {version.get('protocol_version', 'Unknown')}")
    print()

except Exception as e:
    print(f"❌ Server connection failed: {e}")
    sys.exit(1)

# Test 2: Authentication
print("-" * 80)
print("Test 2: Authentication")
print("-" * 80)

try:
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})

    if uid:
        print(f"✅ Authentication successful!")
        print(f"   User ID: {uid}")
        print()
    else:
        print("❌ Authentication failed - Invalid credentials")
        sys.exit(1)

except Exception as e:
    print(f"❌ Authentication error: {e}")
    sys.exit(1)

# Test 3: Access Check
print("-" * 80)
print("Test 3: User Access & Permissions")
print("-" * 80)

try:
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

    # Check access rights for key models
    models_to_check = [
        'res.partner',      # Customers/Contacts
        'account.move',     # Invoices
        'product.product',  # Products
    ]

    print("Checking access rights:")
    for model in models_to_check:
        try:
            can_read = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                model, 'check_access_rights',
                ['read'], {'raise_exception': False}
            )

            can_create = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                model, 'check_access_rights',
                ['create'], {'raise_exception': False}
            )

            icon = "✅" if (can_read and can_create) else "⚠️"
            print(f"   {icon} {model}")
            print(f"      Read: {'✓' if can_read else '✗'}")
            print(f"      Create: {'✓' if can_create else '✗'}")

        except Exception as e:
            print(f"   ❌ {model}: {e}")

    print()

except Exception as e:
    print(f"❌ Access check failed: {e}")
    sys.exit(1)

# Test 4: Available Modules
print("-" * 80)
print("Test 4: Installed Modules")
print("-" * 80)

try:
    # Get installed modules
    module_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'ir.module.module', 'search',
        [[('state', '=', 'installed')]]
    )

    modules = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'ir.module.module', 'read',
        [module_ids], {'fields': ['name', 'shortdesc']}
    )

    # Filter key modules
    key_modules = ['account', 'sale', 'contacts', 'product']
    installed_key = [m for m in modules if any(k in m['name'] for k in key_modules)]

    print(f"Total installed modules: {len(modules)}")
    print()
    print("Key modules for invoicing:")
    for mod in installed_key[:10]:  # Limit to 10
        print(f"   ✓ {mod['name']}: {mod['shortdesc']}")

    print()

except Exception as e:
    print(f"⚠️  Could not list modules: {e}")
    print()

# Test 5: Company Info
print("-" * 80)
print("Test 5: Company Information")
print("-" * 80)

try:
    # Get company info
    company_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'res.company', 'search',
        [[]]
    )

    companies = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'res.company', 'read',
        [company_ids], {'fields': ['name', 'currency_id']}
    )

    print(f"Companies in database: {len(companies)}")
    for company in companies:
        print(f"   - {company['name']}")
        if company.get('currency_id'):
            print(f"     Currency: {company['currency_id'][1]}")

    print()

except Exception as e:
    print(f"⚠️  Could not get company info: {e}")
    print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print("✅ Connection: Working")
print(f"✅ Authentication: User ID {uid}")
print("✅ Database: Accessible")
print()
print("🎯 Ready for STEP 2: List Existing Customers")
print()
