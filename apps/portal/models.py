from datetime import time
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import BaseModel
from apps.main.models import School
from apps.news.models import News
from apps.portal.constants import APPEAL_TOPICS, RATING_CRITERIA, RATING_FIELDS


########################################################
# -------------------- SOZLAMALAR -------------------- #
########################################################

class PortalSettings(BaseModel):
    """Portalning aloqa ma'lumotlari. Bitta yozuv bo'ladi - `PortalSettings.load()`."""

    address = models.CharField(max_length=255, verbose_name="Manzil")
    phone_number = models.CharField(max_length=50, verbose_name="Telefon raqami")
    email = models.EmailField(null=True, blank=True, verbose_name="Email")
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, verbose_name="Kenglik")
    longitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, verbose_name="Uzunlik")

    work_start = models.TimeField(default=time(9, 0), verbose_name="Ish boshlanishi")
    work_end = models.TimeField(default=time(18, 0), verbose_name="Ish tugashi")
    work_days = models.CharField(
        max_length=20, default='1,2,3,4,5',
        verbose_name="Ish kunlari",
        help_text="Hafta kunlari raqamlari vergul bilan: 1 - Dushanba ... 7 - Yakshanba",
    )

    telegram_link = models.URLField(null=True, blank=True, verbose_name="Telegram havola")
    instagram_link = models.URLField(null=True, blank=True, verbose_name="Instagram havola")
    facebook_link = models.URLField(null=True, blank=True, verbose_name="Facebook havola")
    youtube_link = models.URLField(null=True, blank=True, verbose_name="Youtube havola")

    def __str__(self):
        return "Portal sozlamalari"

    @classmethod
    def load(cls):
        return cls.objects.filter(is_active=True).order_by('id').first()

    @property
    def work_day_numbers(self):
        return sorted({int(day) for day in self.work_days.split(',') if day.strip().isdigit()})

    def clean(self):
        days = [day.strip() for day in (self.work_days or '').split(',') if day.strip()]
        if not days or any(not day.isdigit() or not 1 <= int(day) <= 7 for day in days):
            raise ValidationError({'work_days': "1 dan 7 gacha raqamlarni vergul bilan yozing, masalan: 1,2,3,4,5"})
        if self.work_start and self.work_end and self.work_start >= self.work_end:
            raise ValidationError({'work_end': "Ish tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak."})

    class Meta:
        verbose_name = "Portal sozlamalari"
        verbose_name_plural = "Portal sozlamalari"


class PortalFAQ(BaseModel):
    question = models.CharField(max_length=255, verbose_name="Savol")
    answer = models.TextField(verbose_name="Javob")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Tartib raqami")

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "Savol-javob "
        verbose_name_plural = "Savol-javoblar"
        ordering = ['order', 'id']


class Appeal(BaseModel):
    """Portaldagi "Aloqa" sahifasidan yuborilgan murojaat."""

    full_name = models.CharField(max_length=255, verbose_name="F.I.Sh.")
    phone_number = models.CharField(max_length=20, verbose_name="Telefon raqami")
    email = models.EmailField(null=True, blank=True, verbose_name="Email")
    topic = models.CharField(max_length=20, choices=APPEAL_TOPICS, verbose_name="Mavzu")
    message = models.TextField(verbose_name="Murojaat matni")
    is_processed = models.BooleanField(default=False, verbose_name="Ko'rib chiqildi")

    def __str__(self):
        return f"{self.full_name} - {self.get_topic_display()}"

    class Meta:
        verbose_name = "Murojaat "
        verbose_name_plural = "Murojaatlar"
        ordering = ['-created_at']


########################################################
# --------------------- REYTING ---------------------- #
########################################################

class RatingPeriod(BaseModel):
    year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
        verbose_name="Yil",
    )
    title = models.CharField(
        max_length=255, null=True, blank=True,
        verbose_name="Nomi", help_text="Masalan: 2026-yil yakunlari bo'yicha reyting",
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="E'lon qilingan",
        help_text="Portalda faqat e'lon qilingan davrlar ko'rinadi",
    )

    def __str__(self):
        return self.title or f"{self.year}-yil"

    class Meta:
        verbose_name = "Reyting davri "
        verbose_name_plural = "Reyting davrlari"
        ordering = ['-year']
        constraints = [
            models.UniqueConstraint(
                fields=['year'],
                name='unique_ratingperiod_year',
            )
        ]


def _score_field(label):
    return models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=label,
    )


class SchoolRating(BaseModel):
    """
    Maktabning bitta davrdagi reyting ballari (0-100).

    Umumiy ball mezonlarning og'irlik bo'yicha yig'indisi va saqlashda
    hisoblanadi. Birorta mezon bo'sh bo'lsa, umumiy ball ham bo'sh qoladi va
    maktab portaldagi reytingga tushmaydi - ballarni bosqichma-bosqich kiritish
    mumkin.
    """

    period = models.ForeignKey(
        RatingPeriod, on_delete=models.CASCADE,
        verbose_name="Davr",
        related_name="ratings",
    )
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        verbose_name="Maktab",
        related_name="ratings",
    )

    quality = _score_field("Ta'lim sifati")
    achievement = _score_field("O'quvchi yutuqlari")
    teachers = _score_field("Pedagog salohiyati")
    infrastructure = _score_field("Infratuzilma")
    creative = _score_field("Ijodiy faollik")

    score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True, editable=False,
        verbose_name="Umumiy ball",
    )
    note = models.TextField(null=True, blank=True, verbose_name="Izoh")

    def compute_score(self):
        values = [getattr(self, key) for key in RATING_FIELDS]
        if any(value is None for value in values):
            return None
        total = sum(
            Decimal(value) * weight
            for value, (_key, _label, weight) in zip(values, RATING_CRITERIA)
        ) / Decimal(100)
        return total.quantize(Decimal('0.01'))

    def save(self, *args, **kwargs):
        self.score = self.compute_score()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.school} - {self.period}"

    class Meta:
        verbose_name = "Maktab reytingi "
        verbose_name_plural = "Maktablar reytingi"
        ordering = ['-score']
        constraints = [
            models.UniqueConstraint(
                fields=['period', 'school'],
                name='unique_schoolrating_period_school',
            )
        ]


########################################################
# -------------------- YANGILIKLAR ------------------- #
########################################################

class PortalNews(News):
    """
    Barcha maktablar yangiliklari - vazirlik portal toifasini tuzatishi va
    "Muhim" belgisini qo'yishi uchun. Alohida jadval emas, `News` ning o'zi.
    """

    class Meta:
        proxy = True
        verbose_name = "Portal yangiligi "
        verbose_name_plural = "Portal yangiliklari"
