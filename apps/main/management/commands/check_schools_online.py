from concurrent.futures import ThreadPoolExecutor

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.main.models import School


class Command(BaseCommand):
    help = (
        "Har bir maktab saytiga so'rov yuborib, javob berayotganini tekshiradi va "
        "natijani School.is_online / last_checked_at / last_online_at maydonlariga yozadi.\n"
        "Cron orqali ishga tushirish tavsiya etiladi, masalan har 10 daqiqada."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout', type=float, default=10.0,
            help="Bitta sayt uchun kutish vaqti, sekundda (standart: 10)",
        )
        parser.add_argument(
            '--workers', type=int, default=16,
            help="Parallel so'rovlar soni (standart: 16)",
        )
        parser.add_argument(
            '--domain', action='append', dest='domains',
            help="Faqat ko'rsatilgan subdomenni tekshiradi (bir necha marta berilishi mumkin)",
        )

    def handle(self, *args, **options):
        timeout = options['timeout']
        workers = options['workers']
        domains = options['domains']

        schools = School.objects.filter(is_active=True)
        if domains:
            schools = schools.filter(domain__in=[d.lower().strip() for d in domains])
        schools = list(schools)

        if not schools:
            self.stdout.write(self.style.WARNING("Tekshiriladigan maktab topilmadi."))
            return

        checked_at = timezone.now()
        session = requests.Session()

        def check(school):
            url = build_school_url(school.domain)
            try:
                response = session.get(
                    url, timeout=timeout, allow_redirects=True,
                    headers={'User-Agent': 'BMSM-Monitoring/1.0'},
                )
                # 5xx - sayt ishlamayapti; 4xx esa sayt javob berayotganini bildiradi
                return school, response.status_code < 500
            except requests.RequestException:
                return school, False

        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(check, schools))

        online_count = 0
        for school, is_online in results:
            school.is_online = is_online
            school.last_checked_at = checked_at
            if is_online:
                school.last_online_at = checked_at
                online_count += 1

        School.objects.bulk_update(
            [school for school, _ in results],
            ['is_online', 'last_checked_at', 'last_online_at'],
            batch_size=200,
        )

        offline_count = len(results) - online_count
        self.stdout.write(self.style.SUCCESS(
            f"Tekshirildi: {len(results)} ta maktab, "
            f"{online_count} tasi javob berdi, {offline_count} tasi offline."
        ))

        if offline_count:
            for school, is_online in results:
                if not is_online:
                    self.stdout.write(self.style.WARNING(f"  ! offline: {school.domain} - {school.name}"))


def build_school_url(domain):
    scheme = getattr(settings, 'MONITORING_SITE_SCHEME', 'https')
    base_domain = getattr(settings, 'MONITORING_SITE_BASE_DOMAIN', 'e-bmsm.uz')
    return f"{scheme}://{domain}.{base_domain}/"
