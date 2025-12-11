"""
Management command to import CSV data into PostgreSQL.
"""
import csv
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = 'Import CSV data from sheets folder into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            choices=['limitless', 'boostyfi', 'all'],
            default='all',
            help='Which app data to import (default: all)'
        )
        parser.add_argument(
            '--sheets-dir',
            type=str,
            default='../sheets',
            help='Path to sheets directory (default: ../sheets)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import'
        )

    def handle(self, *args, **options):
        sheets_dir = Path(options['sheets_dir'])
        
        if not sheets_dir.exists():
            raise CommandError(f"Sheets directory not found: {sheets_dir}")
        
        app = options['app']
        clear = options['clear']
        
        if app in ['limitless', 'all']:
            self.import_limitless(sheets_dir / 'limitless', clear)
        
        if app in ['boostyfi', 'all']:
            self.import_boostyfi(sheets_dir / 'boostyfi', clear)
        
        self.stdout.write(self.style.SUCCESS('Import completed successfully!'))

    def parse_datetime(self, value):
        """Parse datetime from various formats."""
        if not value or value.strip() == '':
            return None
        
        formats = [
            '%Y-%m-%d %H:%M:%S.%f %z',
            '%Y-%m-%d %H:%M:%S %z',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%dT%H:%M:%S%z',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(value.strip(), fmt)
                if dt.tzinfo is None:
                    dt = timezone.make_aware(dt)
                return dt
            except ValueError:
                continue
        
        self.stdout.write(self.style.WARNING(f"Could not parse datetime: {value}"))
        return None

    def parse_decimal(self, value, default=Decimal('0')):
        """Parse decimal from string."""
        if not value or value.strip() == '':
            return default
        try:
            return Decimal(value.strip())
        except (InvalidOperation, ValueError):
            return default

    def parse_bool(self, value):
        """Parse boolean from string."""
        if not value:
            return False
        return value.lower() in ('true', '1', 'yes', 't')

    def parse_int(self, value, default=None):
        """Parse integer from string."""
        if not value or value.strip() == '':
            return default
        try:
            return int(value.strip())
        except ValueError:
            return default

    def parse_json(self, value):
        """Parse JSON from string."""
        if not value or value.strip() == '':
            return {}
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}

    def read_csv(self, filepath):
        """Read CSV file and return list of dicts."""
        if not filepath.exists():
            self.stdout.write(self.style.WARNING(f"File not found: {filepath}"))
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)

    @transaction.atomic
    def import_limitless(self, data_dir, clear=False):
        """Import Limitless data."""
        from apps.limitless.models import LimitlessUser, LimitlessPurchase, LimitlessEarning
        
        self.stdout.write('Importing Limitless data...')
        
        if clear:
            self.stdout.write('Clearing existing Limitless data...')
            LimitlessEarning.objects.all().delete()
            LimitlessPurchase.objects.all().delete()
            LimitlessUser.objects.all().delete()
        
        # Import users first
        users_data = self.read_csv(data_dir / 'limitless_users.csv')
        self.stdout.write(f'Found {len(users_data)} users to import')
        
        user_map = {}  # original_id -> instance
        parent_map = {}  # original_id -> parent_original_id
        
        # First pass: create all users without parents
        for row in users_data:
            original_id = self.parse_int(row.get('id'))
            if not original_id:
                continue
            
            parent_id = self.parse_int(row.get('parent_id'))
            if parent_id:
                parent_map[original_id] = parent_id
            
            user, created = LimitlessUser.objects.update_or_create(
                original_id=original_id,
                defaults={
                    'username': row.get('username', '').strip(),
                    'email': row.get('email', '').strip() or None,
                    'password_hash': row.get('password', '').strip(),
                    'referral_code': row.get('referral_code', '').strip(),
                    'referral_code_confirmed': self.parse_bool(row.get('referral_code_confirmed')),
                    'wallet': row.get('wallet', '').strip(),
                    'is_superuser': self.parse_bool(row.get('is_superuser')),
                    'is_staff': self.parse_bool(row.get('is_staff')),
                    'is_active': self.parse_bool(row.get('is_active')),
                    'is_deleted': self.parse_bool(row.get('is_deleted')),
                    'is_blocked': self.parse_bool(row.get('is_blocked')),
                    'date_joined': self.parse_datetime(row.get('date_joined')),
                    'parent_changed_at': self.parse_datetime(row.get('parent_changed_at')),
                    'original_lft': self.parse_int(row.get('lft')),
                    'original_rght': self.parse_int(row.get('rght')),
                    'original_tree_id': self.parse_int(row.get('tree_id')),
                    'original_level': self.parse_int(row.get('level')),
                }
            )
            user_map[original_id] = user
        
        self.stdout.write(f'Created/updated {len(user_map)} users')
        
        # Second pass: set parent relationships
        for original_id, parent_original_id in parent_map.items():
            if original_id in user_map and parent_original_id in user_map:
                user = user_map[original_id]
                user.parent = user_map[parent_original_id]
                user.save(update_fields=['parent'])
        
        self.stdout.write('Set parent relationships')
        
        # Rebuild MPTT tree
        LimitlessUser.objects.rebuild()
        self.stdout.write('Rebuilt MPTT tree')
        
        # Import purchases
        purchases_data = self.read_csv(data_dir / 'limitless_purchases.csv')
        self.stdout.write(f'Found {len(purchases_data)} purchases to import')
        
        purchase_map = {}  # original_id -> instance
        for row in purchases_data:
            original_id = self.parse_int(row.get('id'))
            if not original_id:
                continue
            
            buyer_original_id = self.parse_int(row.get('buyer_id'))
            buyer = user_map.get(buyer_original_id)
            
            purchase, created = LimitlessPurchase.objects.update_or_create(
                original_id=original_id,
                defaults={
                    'buyer': buyer,
                    'buyer_original_id': buyer_original_id,
                    'amount_usdt': self.parse_decimal(row.get('amount_usdt')),
                    'tx_hash': row.get('tx_hash', '').strip(),
                    'block_number': self.parse_int(row.get('block_number')),
                    'contract_address': row.get('contract_address', '').strip(),
                    'metadata': self.parse_json(row.get('metadata')),
                    'payment_status': row.get('payment_status', 'PENDING').strip(),
                    'referral_system_status': self.parse_int(row.get('referral_system_status')),
                    'pack_id': self.parse_int(row.get('pack_id')),
                }
            )
            
            # Set created_at from CSV
            created_at = self.parse_datetime(row.get('created_at'))
            if created_at:
                purchase.created_at = created_at
                purchase.save(update_fields=['created_at'])
            
            purchase_map[original_id] = purchase
        
        self.stdout.write(f'Created/updated {len(purchase_map)} purchases')
        
        # Import earnings
        earnings_data = self.read_csv(data_dir / 'limitless_referral_earnings.csv')
        self.stdout.write(f'Found {len(earnings_data)} earnings to import')
        
        for row in earnings_data:
            original_id = self.parse_int(row.get('id'))
            if not original_id:
                continue
            
            recipient_original_id = self.parse_int(row.get('recipient_id'))
            buyer_original_id = self.parse_int(row.get('buyer_id'))
            purchase_original_id = self.parse_int(row.get('purchase_id'))
            
            earning, created = LimitlessEarning.objects.update_or_create(
                original_id=original_id,
                defaults={
                    'recipient': user_map.get(recipient_original_id),
                    'recipient_original_id': recipient_original_id,
                    'buyer': user_map.get(buyer_original_id),
                    'buyer_original_id': buyer_original_id,
                    'purchase': purchase_map.get(purchase_original_id),
                    'purchase_original_id': purchase_original_id,
                    'earning_type': row.get('earning_type', 'NETWORK').strip(),
                    'level': self.parse_int(row.get('level')),
                    'percentage': self.parse_decimal(row.get('percentage')),
                    'amount_usdt': self.parse_decimal(row.get('amount_usdt')),
                    'status': row.get('status', 'PENDING').strip(),
                    'is_grace_period': self.parse_bool(row.get('is_grace_period')),
                    'recipient_was_active': self.parse_bool(row.get('recipient_was_active')),
                    'compression_applied': self.parse_bool(row.get('compression_applied')),
                    'original_level': self.parse_int(row.get('original_level')),
                    'shares_count': self.parse_int(row.get('shares_count')),
                    'distribution_id': self.parse_int(row.get('distribution_id')),
                }
            )
            
            # Set created_at from CSV
            created_at = self.parse_datetime(row.get('created_at'))
            if created_at:
                earning.created_at = created_at
                earning.save(update_fields=['created_at'])
        
        self.stdout.write(self.style.SUCCESS(f'Limitless import completed'))

    @transaction.atomic
    def import_boostyfi(self, data_dir, clear=False):
        """Import BoostyFi data."""
        from apps.boostyfi.models import BoostyFiUser, BoostyFiPurchase, BoostyFiEarning
        
        self.stdout.write('Importing BoostyFi data...')
        
        if clear:
            self.stdout.write('Clearing existing BoostyFi data...')
            BoostyFiEarning.objects.all().delete()
            BoostyFiPurchase.objects.all().delete()
            BoostyFiUser.objects.all().delete()
        
        # Import users first
        users_data = self.read_csv(data_dir / 'boostyfi_users.csv')
        self.stdout.write(f'Found {len(users_data)} users to import')
        
        user_map = {}  # original_id -> instance
        parent_map = {}  # original_id -> parent_original_id
        
        # First pass: create all users without parents
        for row in users_data:
            original_id = self.parse_int(row.get('id'))
            if not original_id:
                continue
            
            parent_id = self.parse_int(row.get('parent_id'))
            if parent_id:
                parent_map[original_id] = parent_id
            
            user, created = BoostyFiUser.objects.update_or_create(
                original_id=original_id,
                defaults={
                    'username': row.get('username', '').strip(),
                    'email': row.get('email', '').strip() or None,
                    'password_hash': row.get('password', '').strip(),
                    'referral_code': row.get('referral_code', '').strip(),
                    'referral_code_confirmed': self.parse_bool(row.get('referral_code_confirmed')),
                    'referral_type': row.get('referral_type', '').strip(),
                    'wallet': row.get('wallet', '').strip(),
                    'evm_address': row.get('evm_address', '').strip(),
                    'tron_address': row.get('tron_address', '').strip(),
                    'locked_atla_balance': self.parse_decimal(row.get('locked_atla_balance')),
                    'unlocked_atla_balance': self.parse_decimal(row.get('unlocked_atla_balance')),
                    'is_superuser': self.parse_bool(row.get('is_superuser')),
                    'is_staff': self.parse_bool(row.get('is_staff')),
                    'is_active': self.parse_bool(row.get('is_active')),
                    'is_deleted': self.parse_bool(row.get('is_deleted')),
                    'is_blocked': self.parse_bool(row.get('is_blocked')),
                    'date_joined': self.parse_datetime(row.get('date_joined')),
                    'parent_changed_at': self.parse_datetime(row.get('parent_changed_at')),
                    'original_lft': self.parse_int(row.get('lft')),
                    'original_rght': self.parse_int(row.get('rght')),
                    'original_tree_id': self.parse_int(row.get('tree_id')),
                    'original_level': self.parse_int(row.get('level')),
                }
            )
            user_map[original_id] = user
        
        self.stdout.write(f'Created/updated {len(user_map)} users')
        
        # Second pass: set parent relationships
        for original_id, parent_original_id in parent_map.items():
            if original_id in user_map and parent_original_id in user_map:
                user = user_map[original_id]
                user.parent = user_map[parent_original_id]
                user.save(update_fields=['parent'])
        
        self.stdout.write('Set parent relationships')
        
        # Rebuild MPTT tree
        BoostyFiUser.objects.rebuild()
        self.stdout.write('Rebuilt MPTT tree')
        
        # Import purchases
        purchases_data = self.read_csv(data_dir / 'boostyfi_purchases.csv')
        self.stdout.write(f'Found {len(purchases_data)} purchases to import')
        
        purchase_map = {}  # original_id -> instance
        for row in purchases_data:
            original_id = self.parse_int(row.get('id'))
            if not original_id:
                continue
            
            buyer_original_id = self.parse_int(row.get('buyer_id'))
            buyer = user_map.get(buyer_original_id)
            
            purchase, created = BoostyFiPurchase.objects.update_or_create(
                original_id=original_id,
                defaults={
                    'buyer': buyer,
                    'buyer_original_id': buyer_original_id,
                    'amount': self.parse_decimal(row.get('amount')),
                    'full_amount': self.parse_decimal(row.get('full_amount')),
                    'discount_rate': self.parse_decimal(row.get('discount_rate')),
                    'tx_hash': row.get('tx_hash', '').strip(),
                    'block_number': self.parse_int(row.get('block_number')),
                    'contract_address': row.get('contract_address', '').strip(),
                    'metadata': self.parse_json(row.get('metadata')),
                    'payment_status': row.get('payment_status', 'PENDING').strip(),
                    'payment_type': row.get('payment_type', 'CRYPTO').strip(),
                    'referral_system_status': self.parse_int(row.get('referral_system_status')),
                    'jggl_pack_id': self.parse_int(row.get('jggl_pack_id')),
                    'atla_pack_id': self.parse_int(row.get('atla_pack_id')),
                    'paylink_invoice_id': row.get('paylink_invoice_id', '').strip(),
                    'paylink_reference_id': row.get('paylink_reference_id', '').strip(),
                }
            )
            
            # Set created_at from CSV
            created_at = self.parse_datetime(row.get('created_at'))
            if created_at:
                purchase.created_at = created_at
                purchase.save(update_fields=['created_at'])
            
            purchase_map[original_id] = purchase
        
        self.stdout.write(f'Created/updated {len(purchase_map)} purchases')
        
        # Import earnings
        earnings_data = self.read_csv(data_dir / 'boostyfi_referral_earnings.csv')
        self.stdout.write(f'Found {len(earnings_data)} earnings to import')
        
        for row in earnings_data:
            original_id = self.parse_int(row.get('id'))
            if not original_id:
                continue
            
            user_original_id = self.parse_int(row.get('user_id'))
            buyer_original_id = self.parse_int(row.get('buyer_id'))
            purchase_original_id = self.parse_int(row.get('purchase_id'))
            
            earning, created = BoostyFiEarning.objects.update_or_create(
                original_id=original_id,
                defaults={
                    'user': user_map.get(user_original_id),
                    'user_original_id': user_original_id,
                    'buyer': user_map.get(buyer_original_id),
                    'buyer_original_id': buyer_original_id,
                    'purchase': purchase_map.get(purchase_original_id),
                    'purchase_original_id': purchase_original_id,
                    'earning_type': row.get('earning_type', 'NETWORK').strip(),
                    'generation_level': self.parse_int(row.get('generation_level')),
                    'percentage': self.parse_decimal(row.get('percentage')),
                    'amount': self.parse_decimal(row.get('amount')),
                    'referral_pool': self.parse_decimal(row.get('referral_pool')),
                    'referral_system_type': self.parse_int(row.get('referral_system_type')),
                    'status': row.get('status', 'PENDING').strip(),
                    'ppv': self.parse_decimal(row.get('ppv')),
                    'tv': self.parse_decimal(row.get('tv')),
                    'tier': self.parse_int(row.get('tier')),
                    'qualification_reason': row.get('qualification_reason', '').strip(),
                    'tx_amount': self.parse_decimal(row.get('tx_amount')),
                    'rpr': self.parse_decimal(row.get('rpr')),
                    'calculated_at': self.parse_datetime(row.get('calculated_at')),
                    'is_sponsor_earning': self.parse_bool(row.get('is_sponsor_earning')),
                    'sponsor_withhold_amount': self.parse_decimal(row.get('sponsor_withhold_amount')),
                }
            )
            
            # Set created_at from CSV
            created_at = self.parse_datetime(row.get('created_at'))
            if created_at:
                earning.created_at = created_at
                earning.save(update_fields=['created_at'])
        
        self.stdout.write(self.style.SUCCESS(f'BoostyFi import completed'))
