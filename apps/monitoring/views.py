from django.contrib.auth import get_user_model
from django.db.models import Count, Max, Prefetch, Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.main.models import District, Region
from apps.monitoring import filters as monitoring_filters
from apps.monitoring import serializers as monitoring_serializers
from apps.monitoring.constants import CONTENT_TYPES, STATUS_LABELS, resolve_status
from apps.monitoring.services import completeness, stats
from apps.monitoring.services.feed import MAX_FEED_WINDOW, fetch_feed
from apps.monitoring.services.querysets import MonitoringFilters

User = get_user_model()

EMPTY_ACTIVITY = {'today': 0, 'week': 0, 'month': 0, 'last_post_at': None, 'by_type': {}}

ORDERING_KEYS = {
    'name': lambda row: row['name'].lower(),
    'completeness_percent': lambda row: row['completeness_percent'],
    'posts_month': lambda row: row['activity']['posts_month'],
    'last_post_at': lambda row: (row['activity']['last_post_at'] is not None,
                                 row['activity']['last_post_at']),
    'days_since_last_post': lambda row: (
        row['activity']['days_since_last_post']
        if row['activity']['days_since_last_post'] is not None else 10 ** 6
    ),
}


class MonitoringPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 500


########################################################
# ----------------- SWAGGER PARAMS ------------------- #
########################################################

def _param(name, description, param_type=openapi.TYPE_STRING, **kwargs):
    return openapi.Parameter(
        name=name, in_=openapi.IN_QUERY, type=param_type, description=description, **kwargs
    )


SCOPE_PARAMS = [
    _param('region', "Viloyat id yoki slug"),
    _param('district', "Tuman id yoki slug"),
    _param('school', "Maktab subdomeni. Vergul bilan bir nechta: mk1,mk2"),
    _param('is_online', "Sayt holati bo'yicha filtr: true / false"),
    _param('include_inactive', "Faol bo'lmagan yozuvlarni ham qo'shish: true / false"),
]

DATE_PARAMS = [
    _param('date_from', "Boshlanish sanasi, YYYY-MM-DD"),
    _param('date_to', "Tugash sanasi, YYYY-MM-DD"),
]

TYPE_PARAM = _param('type', "Kontent turlari, vergul bilan. Ro'yxat: /api/monitoring/content-types/")


########################################################
# --------------------- YORDAMCHI -------------------- #
########################################################

def _last_login_map(school_ids):
    rows = (
        User.objects
        .filter(school_id__in=school_ids, last_login__isnull=False)
        .values('school_id')
        .annotate(last_login_at=Max('last_login'))
    )
    return {row['school_id']: row['last_login_at'] for row in rows}


def _region_payload(region):
    if region is None:
        return None
    return {'id': region.id, 'name': region.name, 'slug': region.slug}


def build_school_rows(schools, with_sections=False):
    """
    Maktablar ro'yxatini monitoring ko'rsatkichlari bilan to'ldiradi.

    Sanoqlar va faollik butun ro'yxat uchun bir nechta GROUP BY so'rovida
    olinadi - maktablar soni ortganda so'rovlar soni ortmaydi.
    """
    schools = list(schools)
    school_ids = [school.id for school in schools]
    scope = MonitoringFilters(school_ids=school_ids)

    counts = stats.content_counts(scope)
    activity = stats.activity_map(scope)
    last_logins = _last_login_map(school_ids)

    rows = []
    for school in schools:
        entry = activity.get(school.id, EMPTY_ACTIVITY)
        school_counts = counts.get(school.id, {})
        days = stats.days_since(entry['last_post_at'])
        status = resolve_status(days)

        percent, sections = completeness.compute(
            school, school_counts, entry['by_type'], stats.days_since,
        )

        row = {
            'id': school.id,
            'domain': school.domain,
            'name': school.name,
            'is_active': school.is_active,
            'is_online': school.is_online,
            'last_checked_at': school.last_checked_at,
            'site_url': monitoring_serializers.school_site_url(school.domain),
            'region': _region_payload(school.region),
            'district': _region_payload(school.district),
            'status': status,
            'status_label': STATUS_LABELS[status],
            'completeness_percent': percent,
            'activity': {
                'posts_today': entry['today'],
                'posts_week': entry['week'],
                'posts_month': entry['month'],
                'last_post_at': entry['last_post_at'],
                'last_news_at': entry['by_type'].get('news'),
                'days_since_last_post': days,
                'last_login_at': last_logins.get(school.id),
            },
            'content_counts': school_counts,
        }
        if with_sections:
            row['completeness_sections'] = sections
        rows.append(row)

    return rows


########################################################
# ---------------------- VIEWLAR --------------------- #
########################################################

class ContentTypeListView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Kontent turlari",
        operation_description="Filtrlarda ishlatiladigan `type` qiymatlari ro'yxati.",
        responses={200: monitoring_serializers.ContentTypeSerializer(many=True)},
        tags=['monitoring'],
    )
    def get(self, request):
        payload = [
            {'key': content_type.key, 'label': content_type.label, 'is_post': content_type.is_post}
            for content_type in CONTENT_TYPES
            if content_type.is_school_scoped
        ]
        return Response(payload)


class RegionListView(ListAPIView):
    permission_classes = [AllowAny]
    pagination_class = None
    serializer_class = monitoring_serializers.RegionSerializer

    def get_queryset(self):
        active_schools = Q(schools__is_active=True)
        districts = (
            District.objects
            .filter(is_active=True)
            .annotate(school_count=Count('schools', filter=active_schools, distinct=True))
        )
        return (
            Region.objects
            .filter(is_active=True)
            .annotate(school_count=Count('schools', filter=active_schools, distinct=True))
            .prefetch_related(Prefetch('districts', queryset=districts, to_attr='active_districts'))
        )

    @swagger_auto_schema(
        operation_summary="Viloyatlar va tumanlar",
        operation_description="Kaskadli filtr uchun to'liq ma'lumotnoma, maktablar soni bilan.",
        tags=['monitoring'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class OverviewView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Umumiy ko'rsatkichlar",
        operation_description=(
            "Dashboard yuqorisidagi plitkalar: jami maktablar, bugun post joylaganlar, "
            "7 va 30 kun yangilanmaganlar, offline maktablar va faollik ulushi."
        ),
        manual_parameters=SCOPE_PARAMS,
        responses={200: monitoring_serializers.OverviewSerializer()},
        tags=['monitoring'],
    )
    def get(self, request):
        schools = monitoring_filters.school_queryset(request)
        content = monitoring_filters.content_filters(request, schools=schools)
        payload = stats.overview(schools, content)
        return Response(monitoring_serializers.OverviewSerializer(payload).data)


class TimeseriesView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Kunlik postlar dinamikasi",
        operation_description=(
            "Sana kesimida joylangan postlar soni va o'sha kuni post joylagan "
            "maktablar soni. Sana berilmasa - oxirgi 30 kun."
        ),
        manual_parameters=SCOPE_PARAMS + DATE_PARAMS + [TYPE_PARAM],
        responses={200: monitoring_serializers.TimeseriesPointSerializer(many=True)},
        tags=['monitoring'],
    )
    def get(self, request):
        date_from, date_to = monitoring_filters.timeseries_range(request)
        schools = monitoring_filters.school_queryset(request)
        content = monitoring_filters.content_filters(request, schools=schools)
        points = stats.timeseries(date_from, date_to, content)
        return Response(monitoring_serializers.TimeseriesPointSerializer(points, many=True).data)


class SchoolListView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Maktablar monitoringi",
        operation_description=(
            "Har bir maktab bo'yicha kontent sanoqlari, faollik ko'rsatkichlari, "
            "holati va ma'lumotlar to'ldirilganligi foizi."
        ),
        manual_parameters=SCOPE_PARAMS + [
            _param('search', "Maktab nomi bo'yicha qidiruv"),
            _param('status', f"Holat bo'yicha filtr: {', '.join(STATUS_LABELS)}"),
            _param('ordering', f"Saralash: {', '.join(ORDERING_KEYS)} (oldiga `-` qo'yilsa teskari)"),
            _param('limit', "Sahifadagi yozuvlar soni", openapi.TYPE_INTEGER),
            _param('offset', "Boshlanish o'rni", openapi.TYPE_INTEGER),
        ],
        responses={200: monitoring_serializers.SchoolRowSerializer(many=True)},
        tags=['monitoring'],
    )
    def get(self, request):
        schools = monitoring_filters.school_queryset(request).order_by('name')
        rows = build_school_rows(schools)

        status_filter = monitoring_filters.resolve_status_filter(request)
        if status_filter:
            rows = [row for row in rows if row['status'] == status_filter]

        ordering = (request.query_params.get('ordering') or 'name').strip()
        reverse = ordering.startswith('-')
        key_name = ordering.lstrip('-')
        if key_name in ORDERING_KEYS:
            rows.sort(key=ORDERING_KEYS[key_name], reverse=reverse)

        paginator = MonitoringPagination()
        page = paginator.paginate_queryset(rows, request, view=self)
        serializer = monitoring_serializers.SchoolRowSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SchoolDetailView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Bitta maktab kartasi",
        operation_description=(
            "Maktabning kontent sanoqlari, faollik ko'rsatkichlari va "
            "to'ldirilganlikning bo'limlar bo'yicha yoyilmasi."
        ),
        responses={200: monitoring_serializers.SchoolDetailSerializer()},
        tags=['monitoring'],
    )
    def get(self, request, domain):
        schools = monitoring_filters.school_queryset(request).filter(domain=domain.lower())
        rows = build_school_rows(schools, with_sections=True)
        if not rows:
            return Response({'detail': "Maktab topilmadi."}, status=404)
        return Response(monitoring_serializers.SchoolDetailSerializer(rows[0]).data)


class PostListView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Barcha postlar lentasi",
        operation_description=(
            "Barcha maktablar va barcha kontent turlari bo'ylab yagona lenta. "
            "Viloyat, tuman yoki maktab tanlanganda faqat o'shanga tegishli postlar qaytadi."
        ),
        manual_parameters=SCOPE_PARAMS + DATE_PARAMS + [
            TYPE_PARAM,
            _param('search', "Sarlavha bo'yicha qidiruv"),
            _param('ordering', "created_at yoki -created_at (standart: -created_at)"),
            _param('limit', "Sahifadagi yozuvlar soni", openapi.TYPE_INTEGER),
            _param('offset', "Boshlanish o'rni", openapi.TYPE_INTEGER),
        ],
        responses={200: monitoring_serializers.PostSerializer(many=True)},
        tags=['monitoring'],
    )
    def get(self, request):
        schools = list(monitoring_filters.school_queryset(request))
        content = monitoring_filters.content_filters(request, schools=None, use_search=True)
        content.school_ids = [school.id for school in schools]

        paginator = MonitoringPagination()
        limit = paginator.get_limit(request)
        offset = paginator.get_offset(request)
        if offset + limit > MAX_FEED_WINDOW:
            raise ValidationError({
                'offset': f"Lentaning eng chuqur nuqtasi {MAX_FEED_WINDOW} ta yozuv. "
                          f"Natijani sana yoki hudud bo'yicha toraytiring."
            })

        ordering = (request.query_params.get('ordering') or '-created_at').strip()
        total, rows = fetch_feed(content, ordering=ordering, limit=limit, offset=offset)

        serializer = monitoring_serializers.PostSerializer(
            rows, many=True, context={'schools': {school.id: school for school in schools}},
        )

        # Sahifalash lentaning o'zida bajarilgani uchun paginator faqat
        # javob shaklini (count / next / previous) yasash uchun ishlatiladi
        paginator.count = total
        paginator.limit = limit
        paginator.offset = offset
        paginator.request = request
        return paginator.get_paginated_response(serializer.data)
