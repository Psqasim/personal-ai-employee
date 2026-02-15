#!/usr/bin/env python3
"""
Odoo Customer List - Step 2: List All Partners/Customers

Shows all customers/partners in Odoo to choose one for invoice test.

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-15
"""

import sys
import os
from dotenv import load_dotenv
import xmlrpc.client

# Load environment
load_dotenv()

print("=" * 80)
print("STEP 2: LIST EXISTING CUSTOMERS/PARTNERS")
print("=" * 80)
print()

# Get Odoo credentials
ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

# Authenticate
common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})

if not uid:
    print("❌ Authentication failed")
    sys.exit(1)

models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

# List all partners (customers/contacts)
print("📋 Searching for all partners/customers...")
print()

try:
    # Search for all partners (limit to non-company users)
    partner_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'res.partner', 'search',
        [[('is_company', '=', True)]], # Only companies, not individual contacts
        {'limit': 50}  # Limit to 50 for readability
    )

    print(f"Found {len(partner_ids)} company partners")
    print()

    if len(partner_ids) == 0:
        print("⚠️  No customers found in Odoo!")
        print()
        print("📝 Next steps:")
        print("   1. Create a customer manually in Odoo web UI")
        print("   2. OR we can create one via API in STEP 3")
        print()
    else:
        # Get partner details
        partners = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner', 'read',
            [partner_ids],
            {'fields': ['id', 'name', 'email', 'phone', 'is_company', 'customer_rank']}
        )

        print("=" * 80)
        print("EXISTING CUSTOMERS:")
        print("=" * 80)
        print()

        for i, partner in enumerate(partners, 1):
            print(f"{i}. {partner['name']}")
            print(f"   ID: {partner['id']}")
            if partner.get('email'):
                print(f"   Email: {partner['email']}")
            if partner.get('phone'):
                print(f"   Phone: {partner['phone']}")
            print(f"   Is Customer: {partner.get('customer_rank', 0) > 0}")
            print()

        # Also list individual contacts (not companies)
        print("-" * 80)
        print("Looking for individual contacts (non-company)...")
        print("-" * 80)
        print()

        individual_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner', 'search',
            [[('is_company', '=', False), ('type', '=', 'contact')]],
            {'limit': 20}
        )

        if individual_ids:
            individuals = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'res.partner', 'read',
                [individual_ids],
                {'fields': ['id', 'name', 'email', 'parent_id']}
            )

            print(f"Found {len(individuals)} individual contacts:")
            print()

            for i, contact in enumerate(individuals, 1):
                print(f"{i}. {contact['name']}")
                print(f"   ID: {contact['id']}")
                if contact.get('parent_id'):
                    print(f"   Company: {contact['parent_id'][1]}")
                print()

except Exception as e:
    print(f"❌ Error listing partners: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

if len(partner_ids) > 0:
    print(f"✅ Found {len(partner_ids)} customers in Odoo")
    print()
    print("🎯 Ready for STEP 3: Create Draft Invoice")
    print()
    print("Choose a customer from the list above to create an invoice for.")
else:
    print("⚠️  No customers found")
    print()
    print("Options:")
    print("   A) Create customer manually in Odoo web UI:")
    print("      https://personal-ai-employee2.odoo.com")
    print("      Go to: Contacts → Create → Name: 'Test Client A'")
    print()
    print("   B) Create customer via API in STEP 3")
    print()
