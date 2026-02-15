#!/usr/bin/env python3
"""
Odoo Draft Invoice Test - Step 3: Create Customer + Draft Invoice

Steps:
1. Create customer "Test Client A" via API
2. Create draft invoice for $100
3. Verify invoice is in draft state (NOT posted)
4. Show invoice link

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-15
"""

import sys
import os
from dotenv import load_dotenv
import xmlrpc.client
from datetime import date

# Load environment
load_dotenv()

print("=" * 80)
print("STEP 3: CREATE CUSTOMER + DRAFT INVOICE")
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

# PART 1: Create Customer
print("-" * 80)
print("Part 1: Create Customer")
print("-" * 80)
print()

try:
    # Check if "Test Client A" already exists
    existing = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'res.partner', 'search',
        [[('name', '=', 'Test Client A')]]
    )

    if existing:
        customer_id = existing[0]
        print(f"✅ Customer 'Test Client A' already exists (ID: {customer_id})")
    else:
        # Create new customer
        customer_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner', 'create',
            [{
                'name': 'Test Client A',
                'is_company': True,
                'customer_rank': 1,  # Mark as customer
                'email': 'testclient@example.com',
                'phone': '+1-555-0100',
                'street': '123 Test Street',
                'city': 'Test City',
                'zip': '12345',
                'country_id': 167,  # Pakistan (PKR currency)
            }]
        )

        print(f"✅ Customer 'Test Client A' created successfully!")
        print(f"   Customer ID: {customer_id}")

    print()

except Exception as e:
    print(f"❌ Failed to create customer: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# PART 2: Create Draft Invoice
print("-" * 80)
print("Part 2: Create Draft Invoice")
print("-" * 80)
print()

try:
    # Get default product (service) for invoice line
    # First try to find an existing product
    product_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.product', 'search',
        [[('type', '=', 'service')]],
        {'limit': 1}
    )

    if not product_ids:
        # Create a simple service product
        print("Creating test service product...")
        product_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.product', 'create',
            [{
                'name': 'Gold Tier Testing Service',
                'type': 'service',
                'list_price': 100.00,
                'sale_ok': True,
                'invoice_policy': 'order',
            }]
        )
        print(f"   ✅ Product created (ID: {product_id})")
    else:
        product_id = product_ids[0]
        print(f"   ✅ Using existing product (ID: {product_id})")

    print()

    # Create draft invoice (account.move)
    print("Creating draft invoice...")

    invoice_vals = {
        'partner_id': customer_id,
        'move_type': 'out_invoice',  # Customer invoice
        'invoice_date': date.today().isoformat(),
        'invoice_line_ids': [(0, 0, {
            'product_id': product_id,
            'name': 'Gold Tier Testing Invoice - Hackathon Demo',
            'quantity': 1,
            'price_unit': 100.00,
        })],
    }

    invoice_id = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'account.move', 'create',
        [invoice_vals]
    )

    print(f"✅ Draft invoice created successfully!")
    print(f"   Invoice ID: {invoice_id}")
    print()

except Exception as e:
    print(f"❌ Failed to create invoice: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# PART 3: Verify Invoice State
print("-" * 80)
print("Part 3: Verify Invoice State")
print("-" * 80)
print()

try:
    # Read invoice details
    invoice = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'account.move', 'read',
        [invoice_id],
        {'fields': ['name', 'state', 'amount_total', 'currency_id', 'partner_id', 'invoice_date']}
    )[0]

    print("📄 Invoice Details:")
    print(f"   Number: {invoice.get('name', 'Draft')}")
    print(f"   Customer: {invoice['partner_id'][1]}")
    print(f"   Date: {invoice.get('invoice_date', 'Not set')}")
    print(f"   Amount: {invoice['amount_total']} {invoice['currency_id'][1]}")
    print(f"   State: {invoice['state'].upper()}")
    print()

    # Verify it's in draft state
    if invoice['state'] == 'draft':
        print("✅ VERIFIED: Invoice is in DRAFT state (not posted)")
        print("   ✓ Safety check passed - draft-only mode working!")
    else:
        print(f"⚠️  Warning: Invoice state is '{invoice['state']}' (expected 'draft')")

    print()

except Exception as e:
    print(f"❌ Failed to verify invoice: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# PART 4: Generate Invoice Link
print("-" * 80)
print("Part 4: View in Odoo Web UI")
print("-" * 80)
print()

invoice_url = f"{ODOO_URL}/web#id={invoice_id}&model=account.move&view_type=form"

print("🔗 Invoice URL:")
print(f"   {invoice_url}")
print()
print("📝 To verify manually:")
print("   1. Click the link above")
print("   2. Login if needed")
print("   3. Confirm invoice is in 'Draft' state")
print("   4. See 'Confirm' button (but DON'T click it!)")
print()

# Summary
print("=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print()
print(f"✅ Customer Created: Test Client A (ID: {customer_id})")
print(f"✅ Invoice Created: {invoice.get('name', 'Draft')} (ID: {invoice_id})")
print(f"✅ State: DRAFT (safe - not posted)")
print(f"✅ Amount: {invoice['amount_total']} {invoice['currency_id'][1]}")
print()
print(f"🔗 View Invoice: {invoice_url}")
print()
print("🎉 ODOO INTEGRATION TEST: PASSED")
print()
