"""
Management command to import wallet profiles from rank_users export CSV.
"""
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.limitless.models import WalletProfile


class Command(BaseCommand):
    help = 'Import wallet profiles from rank_users export CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file to import'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing wallet profiles before import'
        )

    def parse_decimal(self, value, default=Decimal('0')):
        """Parse decimal from string."""
        if not value or value.strip() == '':
            return default
        try:
            return Decimal(value.strip().replace(',', ''))
        except (InvalidOperation, ValueError):
            return default

    def parse_bool(self, value):
        """Parse boolean from string."""
        if not value:
            return False
        return value.lower() in ('true', '1', 'yes', 't')

    def parse_int(self, value, default=0):
        """Parse integer from string."""
        if not value or value.strip() == '':
            return default
        try:
            return int(value.strip())
        except ValueError:
            return default

    @transaction.atomic
    def handle(self, *args, **options):
        csv_path = Path(options['csv_file'])
        
        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")
        
        if options['clear']:
            self.stdout.write('Clearing existing wallet profiles...')
            WalletProfile.objects.all().delete()
        
        self.stdout.write(f'Reading CSV from {csv_path}...')
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.stdout.write(f'Found {len(rows)} rows to import')
        
        created_count = 0
        updated_count = 0
        
        for row in rows:
            export_id = self.parse_int(row.get('ID'))
            if not export_id:
                continue
            
            main_wallet = row.get('Main Wallet', '').strip()
            if not main_wallet:
                continue
            
            # Parse all fields
            data = {
                'main_wallet': main_wallet,
                'subwallets': row.get('Subwallets', '').strip(),
                'email': row.get('Email', '').strip() or None,
                'email_verified': self.parse_bool(row.get('Email Verified')),
                'is_seller': self.parse_bool(row.get('Seller')),
                'preferred_language': row.get('Preferred Language', '').strip(),
                'can_communicate_english': self.parse_bool(row.get('Can Communicate in English')),
                'community_count': self.parse_int(row.get('Community Count')),
                'atla_balance': self.parse_decimal(row.get('ATLA Balance')),
                'rank': row.get('Rank', '').strip(),
                'has_lp': self.parse_bool(row.get('LP')),
                'lp_shares': self.parse_decimal(row.get('LP Shares')),
                'has_chs': self.parse_bool(row.get('CHS')),
                'ch_share': self.parse_decimal(row.get('CH Share')),
                'has_dsy': self.parse_bool(row.get('DSY')),
                'dsy_bonus': self.parse_decimal(row.get('DSY Bonus')),
                'bfi_atla': self.parse_decimal(row.get('BFI ATLA')),
                'bfi_jggl': self.parse_decimal(row.get('BFI JGGL')),
                'jggl': self.parse_decimal(row.get('JGGL')),
                'need_private_zoom_call': self.parse_bool(row.get('Need Private Zoom Call')),
                'want_business_dev_access': self.parse_bool(row.get('Want Business Dev Access')),
                'want_ceo_access': self.parse_bool(row.get('Want CEO Access')),
                'telegram': row.get('Telegram', '').strip(),
                'facebook': row.get('Facebook', '').strip(),
                'whatsapp': row.get('WhatsApp', '').strip(),
                'viber': row.get('Viber', '').strip(),
                'line': row.get('Line', '').strip(),
                'other_contact': row.get('Other', '').strip(),
            }
            
            profile, created = WalletProfile.objects.update_or_create(
                export_id=export_id,
                defaults=data
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Import completed: {created_count} created, {updated_count} updated'
            )
        )
