import re
from html import unescape

from django.utils.html import strip_tags
from rest_framework import serializers

from apps.main.models import Direction, School
from apps.monitoring.serializers import school_site_url
from apps.news.models import News
from apps.portal.constants import APPEAL_TOPICS
from apps.portal.html import clean_html
from apps.portal.models import Appeal, PortalFAQ, PortalSettings
from apps.portal.services import positive_or_none, valid_coordinates


def place_payload(place):
    """Viloyat yoki tuman: {id, name, slug} yoki None."""
    if place is None:
        return None
    return {'id': place.id, 'name': place.name, 'slug': place.slug}


def excerpt(html, length=220):
    # TinyMCE apostroflarni &rsquo; kabi entity qilib saqlaydi
    text = unescape(strip_tags(html or '')).replace('\xa0', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0].rstrip(',.;:') + '…'


def absolute_file_url(field, request):
    if not field:
        return None
    url = field.url
    return request.build_absolute_uri(url) if request else url


########################################################
# -------------------- MAKTABLAR --------------------- #
########################################################

class SchoolShortSerializer(serializers.ModelSerializer):
    """Yangilik va reyting ichidagi maktab."""

    logo = serializers.SerializerMethodField()
    region = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    site_url = serializers.SerializerMethodField()

    class Meta:
        model = School
        fields = ['id', 'domain', 'name', 'school_type', 'logo', 'region', 'district', 'site_url']
        # Faqat o'qish uchun. Busiz DRF modeldagi UniqueConstraint maydonlarini
        # (masalan News.school) HiddenField bilan almashtirib, javobdan tushirib qoldiradi.
        validators = []

    def get_logo(self, obj):
        return absolute_file_url(obj.logo, self.context.get('request'))

    def get_region(self, obj):
        return place_payload(obj.region)

    def get_district(self, obj):
        return place_payload(obj.district)

    def get_site_url(self, obj):
        return school_site_url(obj.domain)


class SchoolCardSerializer(SchoolShortSerializer):
    """Katalog, xarita va bosh sahifa kartalari."""

    school_type_label = serializers.CharField(source='get_school_type_display', read_only=True)
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    teacher_count = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()
    capacity = serializers.SerializerMethodField()
    directions = serializers.SerializerMethodField()

    class Meta(SchoolShortSerializer.Meta):
        fields = SchoolShortSerializer.Meta.fields + [
            'school_type_label', 'admission_open', 'address', 'latitude', 'longitude',
            'student_count', 'teacher_count', 'employee_count', 'capacity', 'founded_year',
            'directions',
        ]

    def get_latitude(self, obj):
        return valid_coordinates(obj)[0]

    def get_longitude(self, obj):
        return valid_coordinates(obj)[1]

    def get_student_count(self, obj):
        return positive_or_none(obj.student_count)

    def get_teacher_count(self, obj):
        return positive_or_none(obj.teacher_count)

    def get_employee_count(self, obj):
        return positive_or_none(obj.employee_count)

    def get_capacity(self, obj):
        return positive_or_none(obj.capacity)

    def _links(self, obj):
        # `active_directions` - view'dagi Prefetch; boshqa joyda ishlatilsa so'rab olinadi
        links = getattr(obj, 'active_directions', None)
        if links is None:
            links = (
                obj.directions
                .filter(is_active=True, direction__is_active=True)
                .select_related('direction')
            )
        return links

    def get_directions(self, obj):
        return [
            {'slug': link.direction.slug, 'name': link.direction.name}
            for link in self._links(obj)
        ]


class SchoolDetailSerializer(SchoolCardSerializer):
    description = serializers.SerializerMethodField()
    short_description = serializers.SerializerMethodField()
    class_count = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    latest_news = serializers.SerializerMethodField()
    news_count = serializers.SerializerMethodField()

    class Meta(SchoolCardSerializer.Meta):
        fields = SchoolCardSerializer.Meta.fields + [
            'description', 'short_description', 'phone_number', 'email',
            'instagram_link', 'telegram_link', 'facebook_link', 'youtube_link',
            'class_count', 'rating', 'news_count', 'latest_news',
        ]

    def get_description(self, obj):
        return clean_html(obj.description) or None

    def get_short_description(self, obj):
        return excerpt(obj.short_description, length=600) or None

    def get_class_count(self, obj):
        return positive_or_none(obj.class_count)

    def get_directions(self, obj):
        request = self.context.get('request')
        return [
            {
                'slug': link.direction.slug,
                'name': link.direction.name,
                'icon': absolute_file_url(link.direction.icon, request),
                'student_count': positive_or_none(link.student_count),
                'teacher_count': positive_or_none(link.teacher_count),
            }
            for link in self._links(obj)
        ]

    def get_rating(self, obj):
        return self.context.get('rating')

    def get_news_count(self, obj):
        return obj.news.filter(is_active=True).count()

    def get_latest_news(self, obj):
        items = obj.news.filter(is_active=True).order_by('-created_at')[:4]
        return NewsCardSerializer(items, many=True, context={**self.context, 'embed_school': False}).data


########################################################
# ------------------- YO'NALISHLAR ------------------- #
########################################################

class DirectionCardSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source='get_category_display', read_only=True)
    school_count = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    teacher_count = serializers.SerializerMethodField()
    school_share = serializers.SerializerMethodField()

    class Meta:
        model = Direction
        fields = [
            'id', 'slug', 'name', 'category', 'category_label', 'short_description',
            'duration_years', 'icon', 'background_image',
            'school_count', 'student_count', 'teacher_count', 'school_share',
        ]
        validators = []

    def _totals(self, obj):
        return self.context.get('totals', {}).get(obj.id, {})

    def get_school_count(self, obj):
        return self._totals(obj).get('school_count', 0)

    def get_student_count(self, obj):
        return self._totals(obj).get('student_count', 0)

    def get_teacher_count(self, obj):
        return self._totals(obj).get('teacher_count', 0)

    def get_school_share(self, obj):
        total = self.context.get('total_schools') or 0
        if not total:
            return 0
        return round(self.get_school_count(obj) * 100 / total, 1)


class DirectionDetailSerializer(DirectionCardSerializer):
    subjects = serializers.SerializerMethodField()
    instruments = serializers.SerializerMethodField()
    schools = serializers.SerializerMethodField()

    class Meta(DirectionCardSerializer.Meta):
        fields = DirectionCardSerializer.Meta.fields + ['description', 'subjects', 'instruments', 'schools']

    def get_subjects(self, obj):
        return self.context.get('subjects', [])

    def get_instruments(self, obj):
        return self.context.get('instruments', [])

    def get_schools(self, obj):
        return self.context.get('schools', [])


########################################################
# -------------------- YANGILIKLAR ------------------- #
########################################################

class NewsCardSerializer(serializers.ModelSerializer):
    excerpt = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    school = serializers.SerializerMethodField()
    site_url = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = [
            'id', 'title', 'slug', 'image', 'excerpt', 'category', 'is_important',
            'view_count', 'created_at', 'school', 'site_url',
        ]
        validators = []

    def get_excerpt(self, obj):
        return excerpt(obj.content)

    def get_category(self, obj):
        if not obj.portal_category:
            return None
        return {'key': obj.portal_category, 'label': obj.get_portal_category_display()}

    def get_school(self, obj):
        if not self.context.get('embed_school', True) or obj.school is None:
            return None
        return SchoolShortSerializer(obj.school, context=self.context).data

    def get_site_url(self, obj):
        if obj.school is None:
            return None
        return school_site_url(obj.school.domain, f'/news/{obj.slug}')


class NewsDetailSerializer(NewsCardSerializer):
    content = serializers.SerializerMethodField()
    related = serializers.SerializerMethodField()

    class Meta(NewsCardSerializer.Meta):
        fields = NewsCardSerializer.Meta.fields + ['content', 'updated_at', 'related']

    def get_content(self, obj):
        return clean_html(obj.content)

    def get_related(self, obj):
        return NewsCardSerializer(self.context.get('related', []), many=True, context=self.context).data


########################################################
# --------------------- REYTING ---------------------- #
########################################################

class RatingRowSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    previous_rank = serializers.IntegerField(allow_null=True)
    rank_change = serializers.IntegerField(allow_null=True)
    trend = serializers.CharField()
    score = serializers.FloatField()
    level = serializers.CharField()
    level_label = serializers.CharField()
    quality = serializers.FloatField()
    achievement = serializers.FloatField()
    teachers = serializers.FloatField()
    infrastructure = serializers.FloatField()
    creative = serializers.FloatField()
    school = serializers.SerializerMethodField()

    def get_school(self, row):
        school = row['school']
        data = SchoolShortSerializer(school, context=self.context).data
        data['student_count'] = positive_or_none(school.student_count)
        return data


########################################################
# --------------- SOZLAMALAR VA ALOQA ---------------- #
########################################################

class PortalSettingsSerializer(serializers.ModelSerializer):
    work_days = serializers.ListField(source='work_day_numbers', child=serializers.IntegerField())
    work_start = serializers.TimeField(format='%H:%M')
    work_end = serializers.TimeField(format='%H:%M')

    class Meta:
        model = PortalSettings
        fields = [
            'address', 'phone_number', 'email', 'latitude', 'longitude',
            'work_start', 'work_end', 'work_days',
            'telegram_link', 'instagram_link', 'facebook_link', 'youtube_link',
        ]


class PortalFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalFAQ
        fields = ['id', 'question', 'answer']


class AppealCreateSerializer(serializers.ModelSerializer):
    agreement = serializers.BooleanField(write_only=True)

    class Meta:
        model = Appeal
        fields = ['full_name', 'phone_number', 'email', 'topic', 'message', 'agreement']
        extra_kwargs = {'topic': {'choices': APPEAL_TOPICS}}

    def validate_full_name(self, value):
        value = ' '.join(value.split())
        if len(value) < 3:
            raise serializers.ValidationError("F.I.Sh. kamida 3 ta belgidan iborat bo'lishi kerak.")
        return value

    def validate_phone_number(self, value):
        digits = re.sub(r'\D', '', value)
        if len(digits) == 9:
            digits = '998' + digits
        if len(digits) != 12 or not digits.startswith('998'):
            raise serializers.ValidationError("To'liq O'zbekiston telefon raqamini kiriting.")
        return f"+{digits[:3]} {digits[3:5]} {digits[5:8]} {digits[8:10]} {digits[10:]}"

    def validate_message(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError("Murojaat matni kamida 10 ta belgidan iborat bo'lishi kerak.")
        if len(value) > 1000:
            raise serializers.ValidationError("Murojaat matni 1000 ta belgidan oshmasligi kerak.")
        return value

    def validate_agreement(self, value):
        if not value:
            raise serializers.ValidationError("Ma'lumotlarni qayta ishlashga rozilik bering.")
        return value

    def create(self, validated_data):
        validated_data.pop('agreement', None)
        return super().create(validated_data)
