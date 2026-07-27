import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.main.models import District, Region


class Command(BaseCommand):
    help = (
        "Tumanlarni CSV fayldan import qiladi.\n"
        "CSV ustunlari: region, name, soato (soato ixtiyoriy).\n"
        "`region` ustuniga viloyatning nomi yoki slugi yoziladi.\n\n"
        "Namuna:\n"
        "  region,name,soato\n"
        "  Toshkent viloyati,Chirchiq,1727401\n"
    )

    def add_arguments(self, parser):
        parser.add_argument('csv_path', help="CSV fayl manzili")
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Bazaga yozmasdan faqat tekshiradi",
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        dry_run = options['dry_run']

        try:
            # utf-8-sig - Excel saqlagan CSV fayllardagi BOM belgisi uchun
            with open(csv_path, encoding='utf-8-sig', newline='') as fp:
                rows = list(csv.DictReader(fp))
        except FileNotFoundError:
            raise CommandError(f"Fayl topilmadi: {csv_path}")

        if not rows:
            raise CommandError("CSV fayl bo'sh.")

        missing_columns = {'region', 'name'} - set(rows[0].keys())
        if missing_columns:
            raise CommandError(f"CSV da ustunlar yetishmayapti: {', '.join(sorted(missing_columns))}")

        regions_by_key = {}
        for region in Region.objects.all():
            regions_by_key[region.slug] = region
            regions_by_key[region.name.strip().lower()] = region

        created_count = 0
        skipped_count = 0
        errors = []

        with transaction.atomic():
            for line_number, row in enumerate(rows, start=2):
                region_key = (row.get('region') or '').strip()
                name = (row.get('name') or '').strip()
                soato = (row.get('soato') or '').strip() or None

                if not region_key or not name:
                    errors.append(f"{line_number}-qator: `region` yoki `name` bo'sh")
                    continue

                region = regions_by_key.get(region_key.lower()) or regions_by_key.get(slugify(region_key))
                if region is None:
                    errors.append(f"{line_number}-qator: viloyat topilmadi - {region_key!r}")
                    continue

                _, created = District.objects.get_or_create(
                    region=region,
                    slug=slugify(name),
                    defaults={'name': name, 'soato': soato},
                )
                if created:
                    created_count += 1
                else:
                    skipped_count += 1

            if dry_run:
                transaction.set_rollback(True)

        for error in errors:
            self.stdout.write(self.style.WARNING(f"  ! {error}"))

        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Tayyor: {created_count} ta tuman qo'shildi, "
            f"{skipped_count} tasi allaqachon mavjud, {len(errors)} ta xato."
        ))
