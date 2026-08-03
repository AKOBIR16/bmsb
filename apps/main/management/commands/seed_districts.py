from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.main.models import District, Region


# Tumanlar va viloyat bo'ysunuvidagi shaharlar, viloyat slugi bo'yicha guruhlangan.
#
# DIQQAT: hududiy bo'linish o'zgarib turadi - yangi tumanlar tashkil etiladi,
# nomlar almashadi. Ro'yxatni rasmiy ma'lumotnoma bilan solishtirib chiqing.
# O'zgartirish oson: kerakli qatorni shu yerda tahrirlab, komandani qayta
# ishga tushirasiz (mavjudlariga tegilmaydi), yoki admin panelda tuzatasiz.
DISTRICTS = {
    'qoraqalpogiston-respublikasi': [
        "Amudaryo", "Beruniy", "Bo'zatov", "Chimboy", "Ellikqal'a", "Kegeyli",
        "Mo'ynoq", "Nukus", "Qanliko'l", "Qorao'zak", "Qo'ng'irot", "Shumanay",
        "Taxiatosh", "Taxtako'pir", "To'rtko'l", "Xo'jayli",
        "Nukus shahri",
    ],
    'andijon-viloyati': [
        "Andijon", "Asaka", "Baliqchi", "Bo'z", "Buloqboshi", "Izboskan",
        "Jalaquduq", "Marhamat", "Oltinko'l", "Paxtaobod", "Qo'rg'ontepa",
        "Shahrixon", "Ulug'nor", "Xo'jaobod",
        "Andijon shahri", "Asaka shahri", "Xonobod shahri",
    ],
    'buxoro-viloyati': [
        "Buxoro", "G'ijduvon", "Jondor", "Kogon", "Olot", "Peshku", "Qorako'l",
        "Qorovulbozor", "Romitan", "Shofirkon", "Vobkent",
        "Buxoro shahri", "Kogon shahri",
    ],
    'jizzax-viloyati': [
        "Arnasoy", "Baxmal", "Do'stlik", "Forish", "G'allaorol", "Mirzacho'l",
        "Paxtakor", "Sharof Rashidov", "Yangiobod", "Zafarobod", "Zarbdor", "Zomin",
        "Jizzax shahri",
    ],
    'qashqadaryo-viloyati': [
        "Chiroqchi", "Dehqonobod", "G'uzor", "Kasbi", "Kitob", "Koson",
        "Ko'kdala", "Mirishkor", "Muborak", "Nishon", "Qamashi", "Qarshi",
        "Shahrisabz", "Yakkabog'",
        "Qarshi shahri", "Shahrisabz shahri",
    ],
    'navoiy-viloyati': [
        "Karmana", "Konimex", "Navbahor", "Nurota", "Qiziltepa", "Tomdi",
        "Uchquduq", "Xatirchi",
        "Navoiy shahri", "Zarafshon shahri",
    ],
    'namangan-viloyati': [
        "Chortoq", "Chust", "Davlatobod", "Kosonsoy", "Mingbuloq", "Namangan",
        "Norin", "Pop", "To'raqo'rg'on", "Uchqo'rg'on", "Uychi", "Yangiqo'rg'on",
        "Namangan shahri",
    ],
    'samarqand-viloyati': [
        "Bulung'ur", "Ishtixon", "Jomboy", "Kattaqo'rg'on", "Narpay", "Nurobod",
        "Oqdaryo", "Past darg'om", "Paxtachi", "Payariq", "Qo'shrabot",
        "Samarqand", "Toyloq", "Urgut",
        "Samarqand shahri", "Kattaqo'rg'on shahri",
    ],
    'surxondaryo-viloyati': [
        "Angor", "Bandixon", "Boysun", "Denov", "Jarqo'rg'on", "Muzrabot",
        "Oltinsoy", "Qiziriq", "Qumqo'rg'on", "Sariosiyo", "Sherobod",
        "Sho'rchi", "Termiz", "Uzun",
        "Termiz shahri",
    ],
    'sirdaryo-viloyati': [
        "Boyovut", "Guliston", "Mirzaobod", "Oqoltin", "Sardoba", "Sayxunobod",
        "Sirdaryo", "Xovos",
        "Guliston shahri", "Shirin shahri", "Yangiyer shahri",
    ],
    'toshkent-viloyati': [
        "Bekobod", "Bo'ka", "Bo'stonliq", "Chinoz", "Ohangaron", "Oqqo'rg'on",
        "Parkent", "Piskent", "Qibray", "Quyichirchiq", "O'rtachirchiq",
        "Toshkent", "Yangiyo'l", "Yuqorichirchiq", "Zangiota",
        "Angren shahri", "Bekobod shahri", "Chirchiq shahri", "Nurafshon shahri",
        "Ohangaron shahri", "Olmaliq shahri", "Yangiyo'l shahri",
    ],
    'fargona-viloyati': [
        "Bag'dod", "Beshariq", "Buvayda", "Dang'ara", "Farg'ona", "Furqat",
        "Oltiariq", "O'zbekiston", "Qo'shtepa", "Quva", "Rishton", "So'x",
        "Toshloq", "Uchko'prik", "Yozyovon",
        "Farg'ona shahri", "Marg'ilon shahri", "Qo'qon shahri", "Quvasoy shahri",
    ],
    'xorazm-viloyati': [
        "Bog'ot", "Gurlan", "Qo'shko'pir", "Shovot", "Tuproqqal'a", "Urganch",
        "Xazorasp", "Xiva", "Xonqa", "Yangiariq", "Yangibozor",
        "Urganch shahri", "Xiva shahri",
    ],
    'toshkent-shahri': [
        "Bektemir", "Chilonzor", "Mirobod", "Mirzo Ulug'bek", "Olmazor",
        "Sergeli", "Shayxontohur", "Uchtepa", "Yakkasaroy", "Yangihayot",
        "Yashnobod", "Yunusobod",
    ],
}


class Command(BaseCommand):
    help = (
        "Barcha tumanlar va viloyat bo'ysunuvidagi shaharlarni tegishli "
        "viloyatlarga biriktirib bazaga yozadi.\n"
        "Avval `seed_regions` ishga tushirilgan bo'lishi kerak.\n"
        "Qayta-qayta ishga tushirish xavfsiz - mavjudlariga tegilmaydi."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Bazaga yozmasdan faqat nima qo'shilishini ko'rsatadi",
        )
        parser.add_argument(
            '--region', dest='region_slug',
            help="Faqat bitta viloyat uchun, masalan: --region toshkent-viloyati",
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        only_region = options['region_slug']

        regions = {region.slug: region for region in Region.objects.all()}
        if not regions:
            self.stdout.write(self.style.ERROR(
                "Viloyatlar topilmadi. Avval `python manage.py seed_regions` ni ishga tushiring."
            ))
            return

        created_total = 0
        existing_total = 0
        missing_regions = []

        with transaction.atomic():
            for region_slug, names in DISTRICTS.items():
                if only_region and region_slug != only_region:
                    continue

                region = regions.get(region_slug)
                if region is None:
                    missing_regions.append(region_slug)
                    continue

                created_here = 0
                for name in names:
                    _, created = District.objects.get_or_create(
                        region=region,
                        slug=slugify(name),
                        defaults={'name': name},
                    )
                    if created:
                        created_here += 1
                    else:
                        existing_total += 1

                created_total += created_here
                self.stdout.write(
                    f"  {region.name}: {len(names)} ta "
                    f"({created_here} ta yangi)"
                )

            if dry_run:
                transaction.set_rollback(True)

        for region_slug in missing_regions:
            self.stdout.write(self.style.WARNING(
                f"  ! Viloyat bazada yo'q, o'tkazib yuborildi: {region_slug}"
            ))

        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Tayyor: {created_total} ta yangi qo'shildi, "
            f"{existing_total} tasi allaqachon mavjud edi. "
            f"Bazada jami {District.objects.count()} ta tuman/shahar."
        ))
