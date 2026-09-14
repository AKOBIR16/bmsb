"""
Portal bo'limi faqat vazirlik (superadmin) uchun.

Bu yerdagi admin'lar `SchoolAdminMixin` ishlatmaydi: reyting va yangiliklar
barcha maktablar kesimida boshqariladi, shuning uchun maktab ustuni ataylab
ko'rsatiladi. "Maktab Admin" guruhiga huquq berib yuborilsa ham maktab
adminlari bu bo'limni ko'rmasligi uchun ruxsatlar qo'lda cheklangan.
"""

from django.contrib import admin, messages
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from apps.common.mixins import AdminTranslation
from apps.main.models import School
from apps.portal.models import Appeal, PortalFAQ, PortalNews, PortalSettings, RatingPeriod, SchoolRating


class SuperuserOnlyMixin:
    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser


########################################################
# --------------- SOZLAMALAR VA ALOQA ---------------- #
########################################################

@admin.register(PortalSettings)
class PortalSettingsAdmin(SuperuserOnlyMixin, AdminTranslation):
    list_display = ('__str__', 'phone_number', 'email', 'updated_at')
    fieldsets = (
        ('Kontaktlar 📞', {'fields': ('address', 'phone_number', 'email', 'latitude', 'longitude')}),
        ('Ish vaqti 🕘', {'fields': ('work_days', 'work_start', 'work_end')}),
        ('Ijtimoiy tarmoqlar 🔗', {'fields': ('telegram_link', 'instagram_link', 'facebook_link', 'youtube_link')}),
    )

    def has_add_permission(self, request):
        # Bitta yozuv yetarli
        return super().has_add_permission(request) and not PortalSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PortalFAQ)
class PortalFAQAdmin(SuperuserOnlyMixin, AdminTranslation):
    list_display = ('question', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('question', 'answer')


@admin.register(Appeal)
class AppealAdmin(SuperuserOnlyMixin, admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'topic', 'is_processed', 'created_at')
    list_editable = ('is_processed',)
    list_filter = ('is_processed', 'topic', 'created_at')
    search_fields = ('full_name', 'phone_number', 'email', 'message')
    readonly_fields = ('full_name', 'phone_number', 'email', 'topic', 'message', 'created_at')
    fields = ('full_name', 'phone_number', 'email', 'topic', 'message', 'created_at', 'is_processed')
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False


########################################################
# --------------------- REYTING ---------------------- #
########################################################

@admin.register(RatingPeriod)
class RatingPeriodAdmin(SuperuserOnlyMixin, AdminTranslation):
    list_display = ('__str__', 'year', 'is_published', 'rated_schools')
    list_editable = ('is_published',)
    list_filter = ('is_published',)
    actions = ['create_school_rows']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(rating_count=Count('ratings'))

    @admin.display(description="Baholangan maktablar")
    def rated_schools(self, obj):
        url = reverse('admin:portal_schoolrating_changelist') + f'?period__id__exact={obj.id}'
        return format_html('<a href="{}">{} ta - ballarni kiritish</a>', url, obj.rating_count)

    @admin.action(description="Barcha faol maktablar uchun bo'sh qatorlar yaratish")
    def create_school_rows(self, request, queryset):
        created = 0
        for period in queryset:
            existing = set(period.ratings.values_list('school_id', flat=True))
            rows = [
                SchoolRating(period=period, school=school)
                for school in School.objects.filter(is_active=True).exclude(id__in=existing)
            ]
            SchoolRating.objects.bulk_create(rows)
            created += len(rows)
        self.message_user(
            request,
            f"{created} ta qator yaratildi. Endi ballarni ro'yxatning o'zida kiritishingiz mumkin.",
            messages.SUCCESS,
        )


@admin.register(SchoolRating)
class SchoolRatingAdmin(SuperuserOnlyMixin, admin.ModelAdmin):
    list_display = (
        'school', 'region', 'quality', 'achievement', 'teachers', 'infrastructure', 'creative',
        'score', 'period',
    )
    list_editable = ('quality', 'achievement', 'teachers', 'infrastructure', 'creative')
    list_filter = ('period', 'school__region', 'school__school_type')
    list_select_related = ('school', 'school__region', 'period')
    search_fields = ('school__name', 'school__domain')
    autocomplete_fields = ('school',)
    readonly_fields = ('score',)
    fields = ('period', 'school', 'quality', 'achievement', 'teachers', 'infrastructure', 'creative', 'score', 'note', 'is_active')
    ordering = ('period', '-score', 'school__name')
    # Bitta viloyat yoki butun davrni bir sahifada to'ldirish uchun
    list_per_page = 300

    @admin.display(description="Viloyat", ordering='school__region__name')
    def region(self, obj):
        return obj.school.region or '-'


########################################################
# -------------------- YANGILIKLAR ------------------- #
########################################################

@admin.register(PortalNews)
class PortalNewsAdmin(SuperuserOnlyMixin, admin.ModelAdmin):
    list_display = ('title', 'school', 'portal_category', 'is_important', 'view_count', 'created_at')
    list_editable = ('portal_category', 'is_important')
    list_display_links = ('title',)
    list_filter = ('is_important', 'portal_category', 'school__region', 'created_at')
    list_select_related = ('school',)
    search_fields = ('title', 'school__name', 'school__domain')
    date_hierarchy = 'created_at'
    fields = ('school', 'category', 'title', 'image', 'portal_category', 'is_important', 'view_count', 'created_at')
    readonly_fields = ('school', 'category', 'title', 'image', 'view_count', 'created_at')
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_active=True)

    def has_add_permission(self, request):
        # Yangiliklarni maktablar o'z saytida qo'shadi
        return False

    def has_delete_permission(self, request, obj=None):
        return False
