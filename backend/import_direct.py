#!/usr/bin/env python
"""Direct SQL import for Limitless data - much faster."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

import csv
from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.utils import timezone
from django.db import connection
from apps.limitless.models import LimitlessUser, LimitlessPurchase, LimitlessEarning

def parse_datetime(value):
    if not value or value.strip() == '':
        return None
    formats = [
        '%Y-%m-%dT%H:%M:%S.%f%z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%d %H:%M:%S.%f %z',
        '%Y-%m-%d %H:%M:%S %z',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None

def parse_decimal(value, default='0'):
    if not value or value.strip() == '':
        return default
    return value.strip()

def parse_bool(value):
    if not value:
        return False
    return str(value).lower() in ('true', '1', 'yes', 't')

def parse_int(value, default=None):
    if not value or str(value).strip() == '':
        return default
    try:
        return int(str(value).strip())
    except ValueError:
        return default

def read_csv(filepath):
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

print("Clearing existing Limitless data...")
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM limitless_limitlessearning")
    cursor.execute("DELETE FROM limitless_limitlesspurchase")
    cursor.execute("DELETE FROM limitless_limitlessuser")
print("Done clearing.")

# Import users
print("Importing users...")
users_data = read_csv('./limitless_new_data/jggl_users_202512131646.csv')
print(f"Found {len(users_data)} users")

user_map = {}
parent_map = {}

with connection.cursor() as cursor:
    for idx, row in enumerate(users_data):
        original_id = parse_int(row.get('id'))
        if not original_id:
            continue
        
        parent_id = parse_int(row.get('parent_id'))
        if parent_id:
            parent_map[original_id] = parent_id
        
        email = row.get('email', '').strip() or None
        date_joined = parse_datetime(row.get('date_joined'))
        parent_changed_at = parse_datetime(row.get('parent_changed_at'))
        
        cursor.execute("""
            INSERT INTO limitless_limitlessuser 
            (created_at, updated_at, original_id, username, email, password_hash, referral_code, 
             referral_code_confirmed, wallet, is_superuser, is_staff, is_active, is_deleted, is_blocked,
             date_joined, parent_changed_at, original_lft, original_rght, original_tree_id, original_level,
             lft, rght, tree_id, level, parent_id)
            VALUES (NOW(), NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)
            RETURNING id
        """, [
            original_id,
            row.get('username', '').strip(),
            email,
            row.get('password', '').strip(),
            row.get('referral_code', '').strip(),
            parse_bool(row.get('referral_code_confirmed')),
            row.get('wallet', '').strip(),
            parse_bool(row.get('is_superuser')),
            parse_bool(row.get('is_staff')),
            parse_bool(row.get('is_active')),
            parse_bool(row.get('is_deleted')),
            parse_bool(row.get('is_blocked')),
            date_joined,
            parent_changed_at,
            parse_int(row.get('lft')),
            parse_int(row.get('rght')),
            parse_int(row.get('tree_id')),
            parse_int(row.get('level')),
            # MPTT fields - temporary values
            idx * 2 + 1,  # lft
            idx * 2 + 2,  # rght
            idx + 1,      # tree_id
            0,            # level
        ])
        db_id = cursor.fetchone()[0]
        user_map[original_id] = db_id
        
        if (idx + 1) % 500 == 0:
            print(f"  Imported {idx + 1} users...")

print(f"Created {len(user_map)} users")

# Set parent relationships
print("Setting parent relationships...")
with connection.cursor() as cursor:
    for original_id, parent_original_id in parent_map.items():
        if original_id in user_map and parent_original_id in user_map:
            cursor.execute(
                "UPDATE limitless_limitlessuser SET parent_id = %s WHERE id = %s",
                [user_map[parent_original_id], user_map[original_id]]
            )

print("Rebuilding MPTT tree...")
LimitlessUser.objects.rebuild()
print("Done with users.")

# Import purchases
print("Importing purchases...")
purchases_data = read_csv('./limitless_new_data/jggl_purchases_202512131646.csv')
print(f"Found {len(purchases_data)} purchases")

purchase_map = {}
with connection.cursor() as cursor:
    for idx, row in enumerate(purchases_data):
        original_id = parse_int(row.get('id'))
        if not original_id:
            continue
        
        buyer_original_id = parse_int(row.get('buyer_id'))
        buyer_db_id = user_map.get(buyer_original_id)
        created_at = parse_datetime(row.get('created_at')) or timezone.now()
        
        metadata = row.get('metadata', '{}').strip()
        if not metadata:
            metadata = '{}'
        # Convert Python dict repr to JSON (single quotes to double quotes)
        import json as json_module
        try:
            # Try to eval as Python dict and convert to JSON
            metadata_dict = eval(metadata) if metadata.startswith('{') else {}
            metadata = json_module.dumps(metadata_dict)
        except:
            metadata = '{}'
        
        cursor.execute("""
            INSERT INTO limitless_limitlesspurchase
            (created_at, updated_at, original_id, buyer_id, buyer_original_id, amount_usdt, 
             tx_hash, block_number, contract_address, metadata, payment_status, referral_system_status, pack_id)
            VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, [
            created_at,
            original_id,
            buyer_db_id,
            buyer_original_id,
            parse_decimal(row.get('amount_usdt')),
            row.get('tx_hash', '').strip(),
            parse_int(row.get('block_number')),
            row.get('contract_address', '').strip(),
            metadata,
            row.get('payment_status', 'PENDING').strip(),
            parse_int(row.get('referral_system_status')),
            parse_int(row.get('pack_id')),
        ])
        db_id = cursor.fetchone()[0]
        purchase_map[original_id] = db_id

print(f"Created {len(purchase_map)} purchases")

# Import earnings
print("Importing earnings...")
earnings_data = read_csv('./limitless_new_data/jggl_ref_earnings_202512131646.csv')
print(f"Found {len(earnings_data)} earnings")

earnings_count = 0
with connection.cursor() as cursor:
    for idx, row in enumerate(earnings_data):
        original_id = parse_int(row.get('id'))
        if not original_id:
            continue
        
        recipient_original_id = parse_int(row.get('recipient_id'))
        buyer_original_id = parse_int(row.get('buyer_id'))
        purchase_original_id = parse_int(row.get('purchase_id'))
        created_at = parse_datetime(row.get('created_at')) or timezone.now()
        
        cursor.execute("""
            INSERT INTO limitless_limitlessearning
            (created_at, updated_at, original_id, recipient_id, recipient_original_id, buyer_id, buyer_original_id,
             purchase_id, purchase_original_id, earning_type, level, percentage, amount_usdt, status,
             is_grace_period, recipient_was_active, compression_applied, original_level, shares_count, distribution_id)
            VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, [
            created_at,
            original_id,
            user_map.get(recipient_original_id),
            recipient_original_id,
            user_map.get(buyer_original_id),
            buyer_original_id,
            purchase_map.get(purchase_original_id),
            purchase_original_id,
            row.get('earning_type', 'NETWORK').strip(),
            parse_int(row.get('level')),
            parse_decimal(row.get('percentage')) if row.get('percentage') else None,
            parse_decimal(row.get('amount_usdt')),
            row.get('status', 'PENDING').strip(),
            parse_bool(row.get('is_grace_period')),
            parse_bool(row.get('recipient_was_active')),
            parse_bool(row.get('compression_applied')),
            parse_int(row.get('original_level')),
            parse_int(row.get('shares_count')),
            parse_int(row.get('distribution_id')),
        ])
        earnings_count += 1
        
        if (idx + 1) % 1000 == 0:
            print(f"  Imported {idx + 1} earnings...")

print(f"Created {earnings_count} earnings")

print("\n=== Import completed! ===")
print(f"Users: {LimitlessUser.objects.count()}")
print(f"Purchases: {LimitlessPurchase.objects.count()}")
print(f"Earnings: {LimitlessEarning.objects.count()}")

