import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.main.models import District, Region, School


class Command(BaseCommand):
    help = (
        "Maktablarga viloyat va tumanni CSV fayldan biriktiradi.\n"
        "CSV ustunlari: domain, region, district (district ixtiyoriy).\n"
        "`region` va `district` ustunlariga nom yoki slug yozilishi mumkin.\n\n"
        "Namuna:\n"
        "  domain,region,district\n"
        "  mk1,Toshkent viloyati,Chirchiq\n"
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
            with open(csv_path, encoding='utf-8-sig', newline='') as fp:
                rows = list(csv.DictReader(fp))
        except FileNotFoundError:
            raise CommandError(f"Fayl topilmadi: {csv_path}")

        if not rows:
            raise CommandError("CSV fayl bo'sh.")

        missing_columns = {'domain', 'region'} - set(rows[0].keys())
        if missing_columns:
            raise CommandError(f"CSV da ustunlar yetishmayapti: {', '.join(sorted(missing_columns))}")

        regions_by_key = {}
        for region in Region.objects.all():
            regions_by_key[region.slug] = region
            regions_by_key[region.name.strip().lower()] = region

        districts_by_key = {}
        for district in District.objects.select_related('region'):
            districts_by_key[(district.region_id, district.slug)] = district
            districts_by_key[(district.region_id, district.name.strip().lower())] = district

        updated_count = 0
        errors = []

        with transaction.atomic():
            for line_number, row in enumerate(rows, start=2):
                domain = (row.get('domain') or '').strip().lower()
                region_key = (row.get('region') or '').strip()
                district_key = (row.get('district') or '').strip()

                if not domain:
                    errors.append(f"{line_number}-qator: `domain` bo'sh")
                    continue

                school = School.objects.filter(domain=domain).first()
                if school is None:
                    errors.append(f"{line_number}-qator: maktab topilmadi - {domain!r}")
                    continue

                region = regions_by_key.get(region_key.lower()) or regions_by_key.get(slugify(region_key))
                if region is None:
                    errors.append(f"{line_number}-qator: viloyat topilmadi - {region_key!r}")
                    continue

                district = None
                if district_key:
                    district = (
                        districts_by_key.get((region.id, district_key.lower()))
                        or districts_by_key.get((region.id, slugify(district_key)))
                    )
                    if district is None:
                        errors.append(
                            f"{line_number}-qator: {region.name} tarkibida tuman topilmadi - {district_key!r}"
                        )
                        continue

                school.region = region
                school.district = district
                school.save(update_fields=['region', 'district', 'updated_at'])
                updated_count += 1

            if dry_run:
                transaction.set_rollback(True)

        for error in errors:
            self.stdout.write(self.style.WARNING(f"  ! {error}"))

        without_region = School.objects.filter(region__isnull=True).count()
        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Tayyor: {updated_count} ta maktab yangilandi, {len(errors)} ta xato. "
            f"Hududi belgilanmagan maktablar: {without_region} ta."
        ))
