from django.conf import settings
from rest_framework import serializers

from apps.main.models import District, Region
from apps.monitoring.constants import CONTENT_TYPES_BY_KEY, STATUS_LABELS


def school_site_url(domain, path=''):
    scheme = getattr(settings, 'MONITORING_SITE_SCHEME', 'https')
    base_domain = getattr(settings, 'MONITORING_SITE_BASE_DOMAIN', 'e-bmsm.uz')
    return f"{scheme}://{domain}.{base_domain}{path}"


########################################################
# ---------------- MA'LUMOTNOMALAR ------------------- #
########################################################

class DistrictSerializer(serializers.ModelSerializer):
    school_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = District
        fields = ('id', 'name', 'slug', 'soato', 'school_count')


class RegionSerializer(serializers.ModelSerializer):
    school_count = serializers.IntegerField(read_only=True)
    districts = serializers.SerializerMethodField()

    class Meta:
        model = Region
        fields = ('id', 'name', 'slug', 'soato', 'school_count', 'districts')

    def get_districts(self, obj):
        return DistrictSerializer(obj.active_districts, many=True).data


class SchoolShortSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    domain = serializers.CharField()
    name = serializers.CharField()


########################################################
# --------------------- POSTLAR ---------------------- #
########################################################

class PostSerializer(serializers.Serializer):
    """Union lentasidan kelgan lug'atlarni JSON ga aylantiradi."""

    type = serializers.CharField(source='mon_type')
    type_label = serializers.SerializerMethodField()
    id = serializers.IntegerField(source='mon_id')
    title = serializers.CharField(source='mon_title')
    slug = serializers.CharField(source='mon_slug')
    view_count = serializers.IntegerField(source='mon_views')
    created_at = serializers.DateTimeField(source='mon_created')
    updated_at = serializers.DateTimeField(source='mon_updated')
    is_active = serializers.BooleanField(source='mon_active')
    school = serializers.SerializerMethodField()
    region = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    site_url = serializers.SerializerMethodField()

    def _school(self, obj):
        return self.context.get('schools', {}).get(obj['mon_school'])

    def get_type_label(self, obj):
        content_type = CONTENT_TYPES_BY_KEY.get(obj['mon_type'])
        return content_type.label if content_type else obj['mon_type']

    def get_school(self, obj):
        school = self._school(obj)
        return SchoolShortSerializer(school).data if school else None

    def get_region(self, obj):
        school = self._school(obj)
        if school is None or school.region is None:
            return None
        return {'id': school.region_id, 'name': school.region.name, 'slug': school.region.slug}

    def get_district(self, obj):
        school = self._school(obj)
        if school is None or school.district is None:
            return None
        return {'id': school.district_id, 'name': school.district.name, 'slug': school.district.slug}

    def get_site_url(self, obj):
        school = self._school(obj)
        content_type = CONTENT_TYPES_BY_KEY.get(obj['mon_type'])
        if school is None or content_type is None or not content_type.site_path:
            return None
        path = content_type.site_path.format(slug=obj['mon_slug'] or '')
        return school_site_url(school.domain, path)


########################################################
# -------------------- MAKTABLAR --------------------- #
########################################################

class SchoolActivitySerializer(serializers.Serializer):
    posts_today = serializers.IntegerField()
    posts_week = serializers.IntegerField()
    posts_month = serializers.IntegerField()
    last_post_at = serializers.DateTimeField(allow_null=True)
    last_news_at = serializers.DateTimeField(allow_null=True)
    days_since_last_post = serializers.IntegerField(allow_null=True)
    last_login_at = serializers.DateTimeField(allow_null=True)


class SchoolRowSerializer(serializers.Serializer):
    """Monitoring jadvalidagi bitta qator."""

    id = serializers.IntegerField()
    domain = serializers.CharField()
    name = serializers.CharField()
    is_active = serializers.BooleanField()
    is_online = serializers.BooleanField()
    last_checked_at = serializers.DateTimeField(allow_null=True)
    site_url = serializers.CharField()
    region = serializers.DictField(allow_null=True)
    district = serializers.DictField(allow_null=True)
    status = serializers.CharField()
    status_label = serializers.CharField()
    completeness_percent = serializers.IntegerField()
    activity = SchoolActivitySerializer()
    content_counts = serializers.DictField(child=serializers.IntegerField())


class CompletenessSectionSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    weight = serializers.IntegerField()
    percent = serializers.FloatField()
    count = serializers.IntegerField(required=False)
    target = serializers.IntegerField(required=False)
    last_at = serializers.DateTimeField(required=False)
    missing = serializers.ListField(child=serializers.CharField(), required=False)
    note = serializers.CharField(required=False)


class SchoolDetailSerializer(SchoolRowSerializer):
    completeness_sections = CompletenessSectionSerializer(many=True)


########################################################
# -------------------- DASHBOARD --------------------- #
########################################################

class StatusCountSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=sorted(STATUS_LABELS))
    label = serializers.CharField()
    count = serializers.IntegerField()


class OverviewSerializer(serializers.Serializer):
    total_schools = serializers.IntegerField()
    coverage_percent = serializers.FloatField()
    posted_today = serializers.IntegerField()
    posted_today_percent = serializers.FloatField()
    not_posted_today = serializers.IntegerField()
    stale_7_days = serializers.IntegerField()
    stale_30_days = serializers.IntegerField()
    offline_schools = serializers.IntegerField()
    active_percent = serializers.FloatField()
    statuses = StatusCountSerializer(many=True)


class TimeseriesPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    posts = serializers.IntegerField()
    active_schools = serializers.IntegerField()


class ContentTypeSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    is_post = serializers.BooleanField()
