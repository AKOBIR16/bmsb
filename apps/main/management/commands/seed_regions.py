from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.main.models import Region


# O'zbekiston Respublikasining ma'muriy-hududiy birliklari (SOATO kodlari bilan).
# Kodlar noto'g'ri bo'lsa admin panelda tahrirlash mumkin - ular faqat ma'lumot uchun.
REGIONS = [
    ("Qoraqalpog'iston Respublikasi", "1703"),
    ("Andijon viloyati", "1706"),
    ("Buxoro viloyati", "1708"),
    ("Jizzax viloyati", "1710"),
    ("Qashqadaryo viloyati", "1712"),
    ("Navoiy viloyati", "1714"),
    ("Namangan viloyati", "1718"),
    ("Samarqand viloyati", "1722"),
    ("Surxondaryo viloyati", "1724"),
    ("Sirdaryo viloyati", "1726"),
    ("Toshkent shahri", "1727"),
    ("Toshkent viloyati", "1728"),
    ("Farg'ona viloyati", "1730"),
    ("Xorazm viloyati", "1733"),
]


class Command(BaseCommand):
    help = "Viloyatlar ro'yxatini bazaga yozadi (mavjudlari o'zgarmaydi)."

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0

        for name, soato in REGIONS:
            _, created = Region.objects.get_or_create(
                slug=slugify(name),
                defaults={'name': name, 'soato': soato},
            )
            if created:
                created_count += 1
                self.stdout.write(f"  + {name}")

        self.stdout.write(self.style.SUCCESS(
            f"Tayyor: {created_count} ta viloyat qo'shildi, "
            f"jami {Region.objects.count()} ta."
        ))
