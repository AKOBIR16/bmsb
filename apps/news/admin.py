from django.contrib import admin
from apps.common.mixins import SchoolAdminMixin, AdminTranslation, DescriptionMixin
from apps.news.models import News, Category


@admin.register(Category)
class CategoryAdmin(SchoolAdminMixin, AdminTranslation):
    list_display = ['name', 'is_active']
    
    prepopulated_fields = {
        'slug': ('name',),
    }
    
    def has_module_permission(self, request):
        return not request.user.is_superuser


@admin.register(News)
class NewsAdmin(SchoolAdminMixin, DescriptionMixin, AdminTranslation):
    list_display = ['image_tag', 'title', 'category', 'portal_category', 'view_count', 'is_active', 'created_at']
    list_filter = ['category', 'portal_category', 'is_active', 'created_at']
    list_display_links = ['image_tag', 'title']
    prepopulated_fields = {
        'slug': ('title',),
    }

    def has_module_permission(self, request):
        return not request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        # "Muhim" belgisini portal bo'limida faqat vazirlik qo'yadi
        if not request.user.is_superuser:
            ro.append('is_important')
        return ro
    
    # search_fields = ['title', 'description']
    #    readonly_fields = ['view_count']
    
    # fieldsets = (
    #     (None, {
    #         'fields': ('school', 'category', 'title', 'slug', 'image')
    #     }),
    #     ('Kontent', {
    #         'fields': ('description',)
    #     }),
    # )
    
    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     return qs.select_related('school', 'category')
