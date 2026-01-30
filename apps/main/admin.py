from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.common.mixins import DescriptionMixin, SchoolAdminMixin, AdminTranslation
from mptt.admin import DraggableMPTTAdmin
from modeltranslation.admin import TranslationTabularInline, TranslationStackedInline
from modeltranslation import settings as mt_settings
from django.utils.translation import gettext_lazy as _
from . import models
from django.utils.safestring import mark_safe
from django import forms


@admin.register(models.Menu)
class MenuAdmin(SchoolAdminMixin, AdminTranslation, DraggableMPTTAdmin):
    class Media:
        css = {
            'screen': ('css/admin_menu.css',),
        }
        
    def has_module_permission(self, request):
        return not request.user.is_superuser


class SiteSettingsInline(TranslationStackedInline):
    model = models.SiteSettings
    extra = 0
    max_num = 1  # Only one SiteSettings per school
    can_delete = False
    
    fieldsets = (
        ('Sahifa tavsiflar 📝', {
            'fields': (
                'school_life', 'directions', 'numbers', 'teachers', 'honors', 
                'news', 'gallery', 'contact', 'comments', 'faqs'
            )
        }),
        ('Boshqaruv bo\'limlari 🏢', {
            'fields': ('leaders', 'vacancies', 'documents', 'timetables', 'edu_infos', 'events', 'resources')
        }),
        ('Xizmatlar 🎨', {
            'fields': ('culture_services', 'culture_arts', 'fine_arts')
        }),
    )
    
    class Media:
        js = (
            "admin/js/jquery.init.js",
            "modeltranslation/js/force_jquery.js",
            mt_settings.JQUERY_UI_URL,
            "modeltranslation/js/tabbed_translation_fields.js",
        )
        css = {
            "all": ("modeltranslation/css/tabbed_translation_fields.css", "css/admin_translation.css",),
        }


@admin.register(models.School)
class SchoolAdmin(DescriptionMixin, SchoolAdminMixin, AdminTranslation):
    list_display = ('name', 'domain', 'is_active')
    search_fields = ('name', 'domain')
    list_filter = ('is_active',)
    inlines = [SiteSettingsInline]
    fieldsets = (
        ('Asosiy 📌',
            {'fields': ('is_active', 'domain', 'name', 'slug', 'description', 'short_description')}
        ),
        ('Raqamlar 📊', {'fields': ('founded_year', 'capacity', 'student_count', 'teacher_count', 'direction_count', 'class_count')}),
        ('Kontaktlar 📞', {'fields': ('email', 'phone_number', 'address', 'latitude', 'longitude')}),
        ('Ijtimoiy tarmoqlar 🔗', {'fields': ('instagram_link', 'telegram_link', 'facebook_link', 'youtube_link')}),
        ('Boshqa sozlamalar ⚙️', {'fields': ('logo',)}),
    )
    prepopulated_fields = {
        'slug': ('name',),
    }
    
    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            ro += ['domain', 'is_active']
        return ro

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    

@admin.register(models.Banner)
class BannerAdmin(SchoolAdminMixin, AdminTranslation):
    list_display = ('image_tag', 'title', 'is_active')
    search_fields = ('title',)
    list_filter = ('is_active',)
    list_display_links = ('image_tag', 'title')
    
    def has_module_permission(self, request):
        return not request.user.is_superuser


@admin.register(models.SchoolLife)
class SchoolLifeAdmin(DescriptionMixin, SchoolAdminMixin, AdminTranslation):
    list_display = ('image_tag', 'title', 'is_active')
    search_fields = ('title',)
    list_filter = ('is_active',)
    list_display_links = ('image_tag', 'title')
    
    def has_module_permission(self, request):
        return not request.user.is_superuser


@admin.register(models.Direction)
class DirectionAdmin(DescriptionMixin, AdminTranslation):
    list_display = ('name', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)
    list_display_links = ('name',)
    prepopulated_fields = {
        'slug': ('name',),
    }


@admin.register(models.Subject)
class SubjectAdmin(DescriptionMixin, AdminTranslation):
    list_display = ('name', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)
    list_display_links = ('name',)
    prepopulated_fields = {
        'slug': ('name',),
    }


@admin.register(models.MusicalInstrument)
class MusicalInstrumentAdmin(DescriptionMixin, AdminTranslation):
    list_display = ('name', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)
    list_display_links = ('name',)
    prepopulated_fields = {
        'slug': ('name',),
    }


class TeacherExperienceInline(TranslationTabularInline):
    model = models.TeacherExperience
    extra = 0
    class Media:
        js = (
            "admin/js/jquery.init.js",
            "modeltranslation/js/force_jquery.js",
            mt_settings.JQUERY_UI_URL,
            "modeltranslation/js/tabbed_translation_fields.js",
        )
        css = {
            "all": ("modeltranslation/css/tabbed_translation_fields.css", "css/admin_translation.css",),
        }
            

@admin.register(models.Teacher)
class TeacherAdmin(DescriptionMixin, SchoolAdminMixin, admin.ModelAdmin):
    list_display = ('full_name', 'is_active')
    search_fields = ('full_name',)
    list_filter = ('is_active',)
    list_display_links = ('full_name',)
    inlines = [TeacherExperienceInline]
    prepopulated_fields = {
        'slug': ('full_name',),
    }
    
    def has_module_permission(self, request):
        return not request.user.is_superuser
    

class DirectionSchoolForm(forms.ModelForm):
    class Meta:
        model  = models.DirectionSchool
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)    # Make request optional
        super().__init__(*args, **kwargs)

        if request and hasattr(request, 'user') and request.user.is_authenticated and not request.user.is_superuser:
            school = getattr(request.user, 'school', None)
            if school:
                # Start with a base query for directions taken by the current school.
                taken_qs = models.DirectionSchool.objects.filter(school=school)

                # If editing an existing instance, exclude it from the "taken" list.
                # This ensures the current direction remains in the dropdown.
                if self.instance and self.instance.pk:
                    taken_qs = taken_qs.exclude(pk=self.instance.pk)

                taken_ids = taken_qs.values_list("direction_id", flat=True)


                # Offer only directions that are *not* taken
                if "direction" in self.fields:
                    self.fields["direction"].queryset = models.Direction.objects.exclude(id__in=taken_ids)

                # School is implicit – hide the field and fix its value (if field exists)
                if "school" in self.fields:
                    self.fields["school"].initial = school
                    self.fields["school"].widget = forms.HiddenInput()
            
            
class DirectionImageInline(admin.TabularInline):
    model = models.DirectionImage
    extra = 0
    

class DirectionVideoInline(admin.TabularInline):
    model = models.DirectionVideo
    extra = 0


@admin.register(models.DirectionSchool)
class DirectionSchoolAdmin(DescriptionMixin, SchoolAdminMixin, AdminTranslation):
    form = DirectionSchoolForm
    list_display = ("direction", "founded_year", "student_count", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("direction__name", "description")
    inlines = [DirectionImageInline, DirectionVideoInline]
    # inject `request` into the form so we can filter choices
    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)
        
        class RequestForm(form_class):
            def __init__(self, *args, **kwargs):
                kwargs['request'] = request
                super().__init__(*args, **kwargs)
        
        return RequestForm

    # hide module from super-admins if you really want to
    def has_module_permission(self, request):
        return not request.user.is_superuser

    # always set / lock the school to the current user's school
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.school = request.user.school
        super().save_model(request, obj, form, change)
    

@admin.register(models.FAQ)
class FAQAdmin(SchoolAdminMixin, AdminTranslation):
    list_display = ('title', 'is_active',)
    list_filter = ('is_active',)
    search_fields = ('title', 'description',)

    def has_module_permission(self, request):
        return not request.user.is_superuser


@admin.register(models.Vacancy)
class VacancyAdmin(SchoolAdminMixin, AdminTranslation):
    list_display = ('title', 'type', 'salary', 'location', 'is_active', 'created_at')
    list_filter = ('is_active', 'type', 'created_at')
    search_fields = ('title', 'description', 'requirements', 'location')
    prepopulated_fields = {'slug': ('title',)}
    
    def get_form(self, request, obj=None, **kwargs):
        """Override form to show choice labels in admin"""
        form = super().get_form(request, obj, **kwargs)
        return form
    
    def has_module_permission(self, request):
        return not request.user.is_superuser


@admin.register(models.Document)
class DocumentAdmin(SchoolAdminMixin, AdminTranslation):
    list_display = ('title', 'category', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('title',)

    def has_module_permission(self, request):
        return not request.user.is_superuser


@admin.register(models.TimeTable)
class TimeTableAdmin(SchoolAdminMixin, AdminTranslation):
    list_display = ('title', 'file', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title',)
    
    def has_module_permission(self, request):
        return not request.user.is_superuser
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(models.DocumentCategory)
class DocumentCategoryAdmin(SchoolAdminMixin, AdminTranslation):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {
        'slug': ('name',),
    }
    
    def has_module_permission(self, request):
        return not request.user.is_superuser


@admin.register(models.Staff)
class StaffAdmin(SchoolAdminMixin, AdminTranslation):
    list_display = ('full_name', 'position', 'experience_years', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('full_name', 'position')
    prepopulated_fields = {'slug': ('full_name',)}

    def has_module_permission(self, request):
        return not request.user.is_superuser


@admin.register(models.Leader)
class LeaderAdmin(SchoolAdminMixin, AdminTranslation):
    list_display = ('full_name', 'position', 'working_days', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('full_name', 'position', 'description')
    prepopulated_fields = {'slug': ('full_name',)}

    def has_module_permission(self, request):
        return not request.user.is_superuser


class HonorAchievementsInline(TranslationTabularInline):
    model = models.HonorAchievements
    extra = 0
    fields = ('year', 'description', 'address', 'is_active')
    
    class Media:
        js = (
            "admin/js/jquery.init.js",
            "modeltranslation/js/force_jquery.js",
            mt_settings.JQUERY_UI_URL,
            "modeltranslation/js/tabbed_translation_fields.js",
        )
        css = {
            "all": ("modeltranslation/css/tabbed_translation_fields.css", "css/admin_translation.css",),
        }
    
    def has_module_permission(self, request):
        return not request.user.is_superuser


@admin.register(models.Honors)
class HonorsAdmin(DescriptionMixin, SchoolAdminMixin, AdminTranslation):
    list_display = ('full_name', 'type', 'image_preview', 'is_active', 'created_at')
    list_filter = ('is_active', 'type', 'created_at')
    search_fields = ('full_name', 'description')
    prepopulated_fields = {'slug': ('full_name',)}
    inlines = [HonorAchievementsInline]
    
    def has_module_permission(self, request):
        return not request.user.is_superuser
    
    def image_preview(self, obj):
        """Display image thumbnail in list view"""
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="height: 50px; width: 50px; object-fit: cover; border-radius: 4px;" />')
        return ""
    image_preview.short_description = "Rasm"


@admin.register(models.EduInfo)
class EduInfoAdmin(SchoolAdminMixin, AdminTranslation):
    list_display = ('title', 'is_active')
    search_fields = ('title', 'description')

    def has_module_permission(self, request):
        return not request.user.is_superuser


@admin.register(models.SiteSettings)
class SiteSettingsAdmin(SchoolAdminMixin, AdminTranslation):
    exclude = ('is_active',)
    list_display = ('school', 'created_at')
    
    # Hide this from the admin menu since it's managed through SchoolAdmin inline
    def has_module_permission(self, request):
        return False  # Hide from admin menu - managed through School inline
    
    def has_add_permission(self, request):
        return False  # Managed through School inline only
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete
        
    def has_change_permission(self, request, obj=None):
        # Allow school admins to change their own school's settings
        if request.user.is_superuser:
            return True
        if obj and hasattr(request.user, 'school') and request.user.school:
            return obj.school == request.user.school
        return False


@admin.register(models.ContactForm)
class ContactFormAdmin(SchoolAdminMixin, admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('full_name', 'phone_number', 'message')
    readonly_fields = ('full_name', 'phone_number', 'message', 'created_at', 'updated_at')
    
    def has_module_permission(self, request):
        return not request.user.is_superuser
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(models.Comments)
class CommentsAdmin(SchoolAdminMixin, AdminTranslation):
    list_display = ('full_name', 'rating', 'image_preview', 'is_active', 'created_at')
    list_filter = ('is_active', 'rating', 'created_at')
    search_fields = ('full_name', 'comment')
    
    def has_module_permission(self, request):
        return not request.user.is_superuser
    
    def image_preview(self, obj):
        """Display image thumbnail in list view"""
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="height: 50px; width: 50px; object-fit: cover; border-radius: 4px;" />')
        return ""
    image_preview.short_description = "Rasm"


@admin.register(models.EmailSubscription)
class EmailSubscriptionAdmin(SchoolAdminMixin, admin.ModelAdmin):
    def has_module_permission(self, request):
        return not request.user.is_superuser
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser