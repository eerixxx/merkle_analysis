#!/usr/bin/env python
"""Quick CSV import script using bulk operations."""
import os
import sys
import csv
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
os.environ.setdefault('DEBUG', 'true')
os.environ.setdefault('SECRET_KEY', 'dev-secret-key')
os.environ.setdefault('POSTGRES_HOST', 'localhost')
os.environ.setdefault('POSTGRES_PORT', '5432')
os.environ.setdefault('POSTGRES_DB', 'hierarchy_db')
os.environ.setdefault('POSTGRES_USER', 'postgres')
os.environ.setdefault('POSTGRES_PASSWORD', 'postgres')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')

django.setup()

from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from apps.limitless.models import LimitlessUser, LimitlessPurchase, LimitlessEarning
from apps.boostyfi.models import BoostyFiUser, BoostyFiPurchase, BoostyFiEarning


def parse_datetime(value):
    if not value or value.strip() == '':
        return None
    formats = [
        '%Y-%m-%d %H:%M:%S.%f %z',
        '%Y-%m-%d %H:%M:%S %z',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(value.strip(), fmt)
            if dt.tzinfo is None:
                dt = timezone.make_aware(dt)
            return dt
        except ValueError:
            continue
    return None


def parse_decimal(value, default=Decimal('0')):
    if not value or value.strip() == '':
        return default
    try:
        return Decimal(value.strip())
    except (InvalidOperation, ValueError):
        return default


def parse_bool(value):
    if not value:
        return False
    return value.lower() in ('true', '1', 'yes', 't')


def parse_int(value, default=None):
    if not value or value.strip() == '':
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def read_csv(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def import_limitless():
    print("=== Importing Limitless ===")
    base_dir = '../sheets/limitless'
    
    # Clear existing data
    print("Clearing existing data...")
    LimitlessEarning.objects.all().delete()
    LimitlessPurchase.objects.all().delete()
    LimitlessUser.objects.all().delete()
    
    # Import users
    print("Reading users CSV...")
    users_data = read_csv(f'{base_dir}/limitless_users.csv')
    print(f"Found {len(users_data)} users")
    
    users = []
    parent_map = {}
    
    for row in users_data:
        original_id = parse_int(row.get('id'))
        if not original_id:
            continue
        
        parent_id = parse_int(row.get('parent_id'))
        if parent_id:
            parent_map[original_id] = parent_id
        
        users.append(LimitlessUser(
            original_id=original_id,
            username=row.get('username', '').strip(),
            email=row.get('email', '').strip() or None,
            password_hash=row.get('password', '').strip(),
            referral_code=row.get('referral_code', '').strip(),
            referral_code_confirmed=parse_bool(row.get('referral_code_confirmed')),
            wallet=row.get('wallet', '').strip(),
            is_superuser=parse_bool(row.get('is_superuser')),
            is_staff=parse_bool(row.get('is_staff')),
            is_active=parse_bool(row.get('is_active')),
            is_deleted=parse_bool(row.get('is_deleted')),
            is_blocked=parse_bool(row.get('is_blocked')),
            date_joined=parse_datetime(row.get('date_joined')),
            parent_changed_at=parse_datetime(row.get('parent_changed_at')),
            original_lft=parse_int(row.get('lft')),
            original_rght=parse_int(row.get('rght')),
            original_tree_id=parse_int(row.get('tree_id')),
            original_level=parse_int(row.get('level')),
            # Temp MPTT values - will be rebuilt
            lft=0,
            rght=0,
            tree_id=original_id,
            level=0,
        ))
    
    print("Bulk creating users...")
    LimitlessUser.objects.bulk_create(users, batch_size=500)
    print(f"Created {LimitlessUser.objects.count()} users")
    
    # Build user map
    user_map = {u.original_id: u for u in LimitlessUser.objects.all()}
    
    # Set parent relationships
    print("Setting parent relationships...")
    to_update = []
    for original_id, parent_original_id in parent_map.items():
        if original_id in user_map and parent_original_id in user_map:
            user = user_map[original_id]
            user.parent = user_map[parent_original_id]
            to_update.append(user)
    
    LimitlessUser.objects.bulk_update(to_update, ['parent_id'], batch_size=500)
    print(f"Updated {len(to_update)} parent relationships")
    
    # Rebuild MPTT tree
    print("Rebuilding MPTT tree...")
    LimitlessUser.objects.rebuild()
    print("Tree rebuilt")
    
    # Import purchases
    print("Reading purchases CSV...")
    purchases_data = read_csv(f'{base_dir}/limitless_purchases.csv')
    print(f"Found {len(purchases_data)} purchases")
    
    purchases = []
    for row in purchases_data:
        original_id = parse_int(row.get('id'))
        if not original_id:
            continue
        
        buyer_original_id = parse_int(row.get('buyer_id'))
        buyer = user_map.get(buyer_original_id)
        
        purchases.append(LimitlessPurchase(
            original_id=original_id,
            buyer=buyer,
            buyer_original_id=buyer_original_id,
            amount_usdt=parse_decimal(row.get('amount_usdt')),
            tx_hash=row.get('tx_hash', '').strip(),
            block_number=parse_int(row.get('block_number')),
            contract_address=row.get('contract_address', '').strip(),
            payment_status=row.get('payment_status', 'PENDING').strip(),
            referral_system_status=parse_int(row.get('referral_system_status')),
            pack_id=parse_int(row.get('pack_id')),
            created_at=parse_datetime(row.get('created_at')) or timezone.now(),
        ))
    
    print("Bulk creating purchases...")
    LimitlessPurchase.objects.bulk_create(purchases, batch_size=500)
    print(f"Created {LimitlessPurchase.objects.count()} purchases")
    
    # Build purchase map
    purchase_map = {p.original_id: p for p in LimitlessPurchase.objects.all()}
    
    # Import earnings
    print("Reading earnings CSV...")
    earnings_data = read_csv(f'{base_dir}/limitless_referral_earnings.csv')
    print(f"Found {len(earnings_data)} earnings")
    
    earnings = []
    for row in earnings_data:
        original_id = parse_int(row.get('id'))
        if not original_id:
            continue
        
        recipient_original_id = parse_int(row.get('recipient_id'))
        buyer_original_id = parse_int(row.get('buyer_id'))
        purchase_original_id = parse_int(row.get('purchase_id'))
        
        earnings.append(LimitlessEarning(
            original_id=original_id,
            recipient=user_map.get(recipient_original_id),
            recipient_original_id=recipient_original_id,
            buyer=user_map.get(buyer_original_id),
            buyer_original_id=buyer_original_id,
            purchase=purchase_map.get(purchase_original_id),
            purchase_original_id=purchase_original_id,
            earning_type=row.get('earning_type', 'NETWORK').strip(),
            level=parse_int(row.get('level')),
            percentage=parse_decimal(row.get('percentage')),
            amount_usdt=parse_decimal(row.get('amount_usdt')),
            status=row.get('status', 'PENDING').strip(),
            is_grace_period=parse_bool(row.get('is_grace_period')),
            recipient_was_active=parse_bool(row.get('recipient_was_active')),
            compression_applied=parse_bool(row.get('compression_applied')),
            original_level=parse_int(row.get('original_level')),
            shares_count=parse_int(row.get('shares_count')),
            distribution_id=parse_int(row.get('distribution_id')),
            created_at=parse_datetime(row.get('created_at')) or timezone.now(),
        ))
    
    print("Bulk creating earnings...")
    LimitlessEarning.objects.bulk_create(earnings, batch_size=500)
    print(f"Created {LimitlessEarning.objects.count()} earnings")
    print("=== Limitless import complete ===\n")


def import_boostyfi():
    print("=== Importing BoostyFi ===")
    base_dir = '../sheets/boostyfi'
    
    # Clear existing data
    print("Clearing existing data...")
    BoostyFiEarning.objects.all().delete()
    BoostyFiPurchase.objects.all().delete()
    BoostyFiUser.objects.all().delete()
    
    # Import users
    print("Reading users CSV...")
    users_data = read_csv(f'{base_dir}/boostyfi_users.csv')
    print(f"Found {len(users_data)} users")
    
    users = []
    parent_map = {}
    
    for row in users_data:
        original_id = parse_int(row.get('id'))
        if not original_id:
            continue
        
        parent_id = parse_int(row.get('parent_id'))
        if parent_id:
            parent_map[original_id] = parent_id
        
        users.append(BoostyFiUser(
            original_id=original_id,
            username=row.get('username', '').strip(),
            email=row.get('email', '').strip() or None,
            password_hash=row.get('password', '').strip(),
            referral_code=row.get('referral_code', '').strip(),
            referral_code_confirmed=parse_bool(row.get('referral_code_confirmed')),
            referral_type=row.get('referral_type', '').strip(),
            wallet=row.get('wallet', '').strip(),
            evm_address=row.get('evm_address', '').strip(),
            tron_address=row.get('tron_address', '').strip(),
            locked_atla_balance=parse_decimal(row.get('locked_atla_balance')),
            unlocked_atla_balance=parse_decimal(row.get('unlocked_atla_balance')),
            is_superuser=parse_bool(row.get('is_superuser')),
            is_staff=parse_bool(row.get('is_staff')),
            is_active=parse_bool(row.get('is_active')),
            is_deleted=parse_bool(row.get('is_deleted')),
            is_blocked=parse_bool(row.get('is_blocked')),
            date_joined=parse_datetime(row.get('date_joined')),
            parent_changed_at=parse_datetime(row.get('parent_changed_at')),
            original_lft=parse_int(row.get('lft')),
            original_rght=parse_int(row.get('rght')),
            original_tree_id=parse_int(row.get('tree_id')),
            original_level=parse_int(row.get('level')),
            # Temp MPTT values - will be rebuilt
            lft=0,
            rght=0,
            tree_id=original_id,
            level=0,
        ))
    
    print("Bulk creating users...")
    BoostyFiUser.objects.bulk_create(users, batch_size=500)
    print(f"Created {BoostyFiUser.objects.count()} users")
    
    # Build user map
    user_map = {u.original_id: u for u in BoostyFiUser.objects.all()}
    
    # Set parent relationships
    print("Setting parent relationships...")
    to_update = []
    for original_id, parent_original_id in parent_map.items():
        if original_id in user_map and parent_original_id in user_map:
            user = user_map[original_id]
            user.parent = user_map[parent_original_id]
            to_update.append(user)
    
    BoostyFiUser.objects.bulk_update(to_update, ['parent_id'], batch_size=500)
    print(f"Updated {len(to_update)} parent relationships")
    
    # Rebuild MPTT tree
    print("Rebuilding MPTT tree...")
    BoostyFiUser.objects.rebuild()
    print("Tree rebuilt")
    
    # Import purchases
    print("Reading purchases CSV...")
    purchases_data = read_csv(f'{base_dir}/boostyfi_purchases.csv')
    print(f"Found {len(purchases_data)} purchases")
    
    purchases = []
    for row in purchases_data:
        original_id = parse_int(row.get('id'))
        if not original_id:
            continue
        
        buyer_original_id = parse_int(row.get('buyer_id'))
        buyer = user_map.get(buyer_original_id)
        
        purchases.append(BoostyFiPurchase(
            original_id=original_id,
            buyer=buyer,
            buyer_original_id=buyer_original_id,
            amount=parse_decimal(row.get('amount')),
            full_amount=parse_decimal(row.get('full_amount')),
            discount_rate=parse_decimal(row.get('discount_rate')),
            tx_hash=row.get('tx_hash', '').strip(),
            block_number=parse_int(row.get('block_number')),
            contract_address=row.get('contract_address', '').strip(),
            payment_status=row.get('payment_status', 'PENDING').strip(),
            payment_type=row.get('payment_type', 'CRYPTO').strip(),
            referral_system_status=parse_int(row.get('referral_system_status')),
            jggl_pack_id=parse_int(row.get('jggl_pack_id')),
            atla_pack_id=parse_int(row.get('atla_pack_id')),
            paylink_invoice_id=row.get('paylink_invoice_id', '').strip(),
            paylink_reference_id=row.get('paylink_reference_id', '').strip(),
            created_at=parse_datetime(row.get('created_at')) or timezone.now(),
        ))
    
    print("Bulk creating purchases...")
    BoostyFiPurchase.objects.bulk_create(purchases, batch_size=500)
    print(f"Created {BoostyFiPurchase.objects.count()} purchases")
    
    # Build purchase map
    purchase_map = {p.original_id: p for p in BoostyFiPurchase.objects.all()}
    
    # Import earnings
    print("Reading earnings CSV...")
    earnings_data = read_csv(f'{base_dir}/boostyfi_referral_earnings.csv')
    print(f"Found {len(earnings_data)} earnings")
    
    earnings = []
    for row in earnings_data:
        original_id = parse_int(row.get('id'))
        if not original_id:
            continue
        
        user_original_id = parse_int(row.get('user_id'))
        buyer_original_id = parse_int(row.get('buyer_id'))
        purchase_original_id = parse_int(row.get('purchase_id'))
        
        earnings.append(BoostyFiEarning(
            original_id=original_id,
            user=user_map.get(user_original_id),
            user_original_id=user_original_id,
            buyer=user_map.get(buyer_original_id),
            buyer_original_id=buyer_original_id,
            purchase=purchase_map.get(purchase_original_id),
            purchase_original_id=purchase_original_id,
            earning_type=row.get('earning_type', 'NETWORK').strip(),
            generation_level=parse_int(row.get('generation_level')),
            percentage=parse_decimal(row.get('percentage')),
            amount=parse_decimal(row.get('amount')),
            referral_pool=parse_decimal(row.get('referral_pool')),
            referral_system_type=parse_int(row.get('referral_system_type')),
            status=row.get('status', 'PENDING').strip(),
            ppv=parse_decimal(row.get('ppv')),
            tv=parse_decimal(row.get('tv')),
            tier=parse_int(row.get('tier')),
            qualification_reason=row.get('qualification_reason', '').strip(),
            tx_amount=parse_decimal(row.get('tx_amount')),
            rpr=parse_decimal(row.get('rpr')),
            calculated_at=parse_datetime(row.get('calculated_at')),
            is_sponsor_earning=parse_bool(row.get('is_sponsor_earning')),
            sponsor_withhold_amount=parse_decimal(row.get('sponsor_withhold_amount')),
            created_at=parse_datetime(row.get('created_at')) or timezone.now(),
        ))
    
    print("Bulk creating earnings...")
    BoostyFiEarning.objects.bulk_create(earnings, batch_size=500)
    print(f"Created {BoostyFiEarning.objects.count()} earnings")
    print("=== BoostyFi import complete ===\n")


if __name__ == '__main__':
    print("Starting fast CSV import...\n")
    import_limitless()
    import_boostyfi()
    print("\n✅ All data imported successfully!")
