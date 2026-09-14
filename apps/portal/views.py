import re

from django.db.models import Count, F, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.main.models import (
    DIRECTION_CATEGORIES,
    SCHOOL_TYPES,
    Direction,
    DirectionSchool,
    District,
    MusicalInstrument,
    Region,
    School,
    Subject,
)
from apps.monitoring.serializers import school_site_url
from apps.news.models import PORTAL_CATEGORIES, News
from apps.portal import filters, serializers, services
from apps.portal.constants import CACHE_SECONDS, RATING_CRITERIA, RATING_LEVEL_KEYS, RATING_LEVELS
from apps.portal.models import Appeal, PortalFAQ, PortalSettings
from apps.portal.search import loose_pattern, search_q, to_latin

SCHOOL_TYPE_KEYS = tuple(key for key, _label in SCHOOL_TYPES)
DIRECTION_CATEGORY_KEYS = tuple(key for key, _label in DIRECTION_CATEGORIES)
PORTAL_CATEGORY_KEYS = tuple(key for key, _label in PORTAL_CATEGORIES)

cached = method_decorator(cache_page(CACHE_SECONDS), name='get')


class PortalPagination(LimitOffsetPagination):
    default_limit = 12
    max_limit = 500


class NewsPagination(LimitOffsetPagination):
    default_limit = 12
    max_limit = 60


########################################################
# ----------------- SWAGGER PARAMS ------------------- #
########################################################

def _param(name, description, param_type=openapi.TYPE_STRING):
    return openapi.Parameter(name=name, in_=openapi.IN_QUERY, type=param_type, description=description)


PLACE_PARAMS = [
    _param('region', "Viloyat id yoki slug"),
    _param('district', "Tuman id yoki slug"),
]
PAGE_PARAMS = [
    _param('limit', "Sahifadagi yozuvlar soni", openapi.TYPE_INTEGER),
    _param('offset', "Boshlanish o'rni", openapi.TYPE_INTEGER),
]
SEARCH_PARAM = _param('search', "Qidiruv (o' / o‘ / oʻ farqlanmaydi, kirillcha ham bo'ladi)")

# Katalog va xarita bir xil filtrlarni tushunadi (hudud/tumandan tashqari)
SCHOOL_FILTER_PARAMS = [
    SEARCH_PARAM,
    _param('direction', "Yo'nalish slugi, vergul bilan bir nechta"),
    _param('type', f"Maktab turi: {', '.join(SCHOOL_TYPE_KEYS)}"),
    _param('admission', "Qabul holati: open / closed"),
    _param('students_min', "O'quvchilar soni kamida", openapi.TYPE_INTEGER),
    _param('students_max', "O'quvchilar soni ko'pi bilan", openapi.TYPE_INTEGER),
    _param('has_location', "true - faqat xaritada ko'rsatsa bo'ladiganlar"),
]


def filter_schools(queryset, request):
    """Katalog filtrlari. Hudud va tuman bu yerda emas - xarita ularsiz sanaydi."""
    query = search_q(
        request.query_params.get('search'),
        'name_uz', 'name_ru', 'name_en', 'domain', 'address_uz',
    )
    if query is not None:
        queryset = queryset.filter(query)

    directions = filters.get_list(request, 'direction')
    if directions:
        queryset = queryset.filter(
            directions__direction__slug__in=directions,
            directions__is_active=True,
        ).distinct()

    school_type = filters.get_choice(request, 'type', SCHOOL_TYPE_KEYS)
    if school_type:
        queryset = queryset.filter(school_type=school_type)

    admission = filters.get_choice(request, 'admission', ('open', 'closed'))
    if admission:
        queryset = queryset.filter(admission_open=(admission == 'open'))

    students_min = filters.get_int(request, 'students_min', 0, 100000)
    if students_min is not None:
        queryset = queryset.filter(student_count__gte=students_min)

    students_max = filters.get_int(request, 'students_max', 0, 100000)
    if students_max is not None:
        queryset = queryset.filter(student_count__lte=students_max)

    if filters.get_bool(request, 'has_location'):
        queryset = queryset.filter(services.location_q())

    return queryset


########################################################
# -------------------- UMUMIY ------------------------ #
########################################################

@cached
class StatsView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Portal raqamlari",
        operation_description="Maktablar, hududlar, yo'nalishlar, o'quvchi va o'qituvchilar soni.",
        tags=['portal'],
    )
    def get(self, request):
        return Response(services.portal_stats())


@cached
class RegionListView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Viloyatlar va tumanlar",
        operation_description=(
            "Faol maktablar soni bilan. Filtrlar va xarita uchun. "
            "Katalog filtrlari (hudud va tumandan tashqari) berilsa, faqat mos maktablar sanaladi - "
            "xarita katalog bilan bir xil sonlarni ko'rsatadi."
        ),
        manual_parameters=SCHOOL_FILTER_PARAMS,
        tags=['portal'],
    )
    def get(self, request):
        # Hudud filtri qo'llanmaydi: xarita tanlangan hududdan tashqari
        # hududlarning sonini ham ko'rsatadi
        matching = filter_schools(School.objects.filter(is_active=True), request).values('id')
        counted = School.objects.filter(id__in=matching).order_by()
        per_region = dict(counted.values_list('region_id').annotate(total=Count('id')))
        per_district = dict(counted.values_list('district_id').annotate(total=Count('id')))

        districts = District.objects.filter(is_active=True).order_by('name')
        regions = (
            Region.objects
            .filter(is_active=True)
            .prefetch_related(Prefetch('districts', queryset=districts, to_attr='active_districts'))
        )
        payload = [
            {
                'id': region.id,
                'name': region.name,
                'slug': region.slug,
                'soato': region.soato,
                'school_count': per_region.get(region.id, 0),
                'districts': [
                    {
                        'id': district.id,
                        'name': district.name,
                        'slug': district.slug,
                        'school_count': per_district.get(district.id, 0),
                    }
                    for district in region.active_districts
                ],
            }
            for region in regions
        ]
        return Response(payload)


class SettingsView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Portal aloqa ma'lumotlari",
        operation_description="Manzil, telefon, ish vaqti va ijtimoiy tarmoqlar. Kiritilmagan bo'lsa `null`.",
        tags=['portal'],
    )
    def get(self, request):
        settings_obj = PortalSettings.load()
        if settings_obj is None:
            return Response(None)
        return Response(serializers.PortalSettingsSerializer(settings_obj).data)


class FAQListView(ListAPIView):
    permission_classes = [AllowAny]
    pagination_class = None
    serializer_class = serializers.PortalFAQSerializer

    def get_queryset(self):
        return PortalFAQ.objects.filter(is_active=True)

    @swagger_auto_schema(operation_summary="Savol-javoblar", tags=['portal'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AppealThrottle(AnonRateThrottle):
    scope = 'portal_appeal'
    rate = '5/hour'


class AppealCreateView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.AppealCreateSerializer
    throttle_classes = [AppealThrottle]
    queryset = Appeal.objects.all()

    @swagger_auto_schema(
        operation_summary="Murojaat yuborish",
        operation_description="Bitta IP manzildan soatiga 5 tagacha murojaat qabul qilinadi.",
        tags=['portal'],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appeal = serializer.save()
        return Response(
            {'id': appeal.id, 'message': "Murojaatingiz qabul qilindi"},
            status=status.HTTP_201_CREATED,
        )


########################################################
# -------------------- MAKTABLAR --------------------- #
########################################################

SCHOOL_ORDERING = {
    'name': (F('name_uz').asc(),),
    '-name': (F('name_uz').desc(),),
    '-students': (F('student_count').desc(nulls_last=True), F('name_uz').asc()),
    'students': (F('student_count').asc(nulls_last=True), F('name_uz').asc()),
    '-teachers': (F('teacher_count').desc(nulls_last=True), F('name_uz').asc()),
    '-founded': (F('founded_year').desc(nulls_last=True), F('name_uz').asc()),
    'founded': (F('founded_year').asc(nulls_last=True), F('name_uz').asc()),
}


def school_base_queryset():
    directions = (
        DirectionSchool.objects
        .filter(is_active=True, direction__is_active=True)
        .select_related('direction')
        .order_by('direction__name')
    )
    return (
        School.objects
        .filter(is_active=True)
        .select_related('region', 'district')
        .prefetch_related(Prefetch('directions', queryset=directions, to_attr='active_directions'))
    )


class SchoolListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.SchoolCardSerializer
    pagination_class = PortalPagination

    def get_queryset(self):
        request = self.request
        queryset = filter_schools(school_base_queryset(), request)

        region = filters.resolve_region(request)
        if region:
            queryset = queryset.filter(region=region)

        district = filters.resolve_district(request)
        if district:
            queryset = queryset.filter(district=district)

        ordering = filters.get_choice(request, 'ordering', tuple(SCHOOL_ORDERING)) or 'name'
        return queryset.order_by(*SCHOOL_ORDERING[ordering])

    @swagger_auto_schema(
        operation_summary="Maktablar katalogi",
        operation_description=(
            "Faol maktablar. Xarita uchun `limit=500&has_location=true`. "
            "Koordinatasi O'zbekiston hududiga tushmaganlarda `latitude`/`longitude` = null."
        ),
        manual_parameters=PLACE_PARAMS + SCHOOL_FILTER_PARAMS + [
            _param('ordering', f"Saralash: {', '.join(SCHOOL_ORDERING)}"),
        ] + PAGE_PARAMS,
        tags=['portal'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class SchoolDetailView(RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.SchoolDetailSerializer
    lookup_field = 'domain'

    def get_queryset(self):
        return school_base_queryset()

    @swagger_auto_schema(
        operation_summary="Maktab pasporti",
        operation_description="Maktab ma'lumotlari, yo'nalishlari, joriy reytingi va so'nggi yangiliklari.",
        tags=['portal'],
    )
    def get(self, request, *args, **kwargs):
        self.kwargs['domain'] = self.kwargs['domain'].lower()
        school = self.get_object()
        context = self.get_serializer_context()
        context['rating'] = services.school_rating(school)
        return Response(serializers.SchoolDetailSerializer(school, context=context).data)


########################################################
# ------------------- YO'NALISHLAR ------------------- #
########################################################

DIRECTION_ORDERING = {
    '-schools': lambda item: (-item['school_count'], item['name']),
    '-students': lambda item: (-item['student_count'], item['name']),
    '-teachers': lambda item: (-item['teacher_count'], item['name']),
    'name': lambda item: item['name'].lower(),
}


@cached
class DirectionListView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Ta'lim yo'nalishlari",
        operation_description=(
            "Har bir yo'nalish bo'yicha barcha maktablardagi sanoqlar. "
            "`school_share` - yo'nalish mavjud maktablar ulushi (%)."
        ),
        manual_parameters=[
            _param('category', f"Toifa: {', '.join(DIRECTION_CATEGORY_KEYS)}"),
            SEARCH_PARAM,
            _param('ordering', f"Saralash: {', '.join(DIRECTION_ORDERING)}"),
        ],
        tags=['portal'],
    )
    def get(self, request):
        totals = services.direction_totals()
        total_schools = services.active_schools().count()

        directions = Direction.objects.filter(is_active=True)
        all_directions = list(directions)

        category = filters.get_choice(request, 'category', DIRECTION_CATEGORY_KEYS)
        if category:
            directions = directions.filter(category=category)

        query = search_q(request.query_params.get('search'), 'name_uz', 'name_ru', 'name_en')
        if query is not None:
            directions = directions.filter(query)

        context = {'request': request, 'totals': totals, 'total_schools': total_schools}
        results = serializers.DirectionCardSerializer(list(directions), many=True, context=context).data

        ordering = filters.get_choice(request, 'ordering', tuple(DIRECTION_ORDERING)) or '-schools'
        results = sorted(results, key=DIRECTION_ORDERING[ordering])

        categories = [
            {
                'key': key,
                'label': label,
                'count': sum(1 for item in all_directions if item.category == key),
            }
            for key, label in DIRECTION_CATEGORIES
        ]

        return Response({
            'total_schools': total_schools,
            'categories': categories,
            'count': len(results),
            'results': results,
        })


class DirectionDetailView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Yo'nalish tafsiloti",
        operation_description="Asosiy fanlar, cholg'ular va shu yo'nalishda ta'lim beradigan maktablar.",
        tags=['portal'],
    )
    def get(self, request, slug):
        direction = get_object_or_404(Direction.objects.filter(is_active=True), slug=slug)

        links = list(
            services.active_direction_links()
            .filter(direction=direction)
            .select_related('school', 'school__region', 'school__district')
            .order_by('school__name_uz')
        )
        link_ids = [link.id for link in links]

        def ranked(model):
            rows = (
                model.objects
                .filter(is_active=True, directions__id__in=link_ids)
                .annotate(school_count=Count('directions', distinct=True))
                .order_by('-school_count', 'name')[:10]
            )
            return [{'name': row.name, 'slug': row.slug, 'school_count': row.school_count} for row in rows]

        totals = {
            direction.id: {
                'school_count': len({link.school_id for link in links}),
                'student_count': sum(link.student_count or 0 for link in links),
                'teacher_count': sum(link.teacher_count or 0 for link in links),
            }
        }
        schools = [
            {
                'domain': link.school.domain,
                'name': link.school.name,
                'region': serializers.place_payload(link.school.region),
                'district': serializers.place_payload(link.school.district),
                'student_count': services.positive_or_none(link.student_count),
                'teacher_count': services.positive_or_none(link.teacher_count),
                'site_url': school_site_url(link.school.domain),
            }
            for link in links
        ]

        context = {
            'request': request,
            'totals': totals,
            'total_schools': services.active_schools().count(),
            'subjects': ranked(Subject),
            'instruments': ranked(MusicalInstrument),
            'schools': schools,
        }
        return Response(serializers.DirectionDetailSerializer(direction, context=context).data)


########################################################
# -------------------- YANGILIKLAR ------------------- #
########################################################

NEWS_ORDERING = {
    '-date': ('-created_at',),
    'date': ('created_at',),
    '-views': ('-view_count', '-created_at'),
    'title': ('title_uz',),
    '-title': ('-title_uz',),
}


def news_base_queryset():
    return (
        News.objects
        .filter(is_active=True)
        .filter(Q(school__isnull=True) | Q(school__is_active=True))
        .select_related('school', 'school__region', 'school__district')
    )


class NewsListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.NewsCardSerializer
    pagination_class = NewsPagination

    def get_queryset(self):
        request = self.request
        queryset = news_base_queryset()

        query = search_q(request.query_params.get('search'), 'title_uz', 'title_ru', 'title_en')
        if query is not None:
            queryset = queryset.filter(query)

        region = filters.resolve_region(request)
        if region:
            queryset = queryset.filter(school__region=region)

        district = filters.resolve_district(request)
        if district:
            queryset = queryset.filter(school__district=district)

        domains = filters.get_list(request, 'school')
        if domains:
            queryset = queryset.filter(school__domain__in=domains)

        category = filters.get_choice(request, 'category', PORTAL_CATEGORY_KEYS)
        if category:
            queryset = queryset.filter(portal_category=category)

        important = filters.get_bool(request, 'important')
        if important is not None:
            queryset = queryset.filter(is_important=important)

        year = filters.get_int(request, 'year', 2000, 2100)
        if year:
            queryset = queryset.filter(created_at__year=year)

        month = filters.get_int(request, 'month', 1, 12)
        if month:
            queryset = queryset.filter(created_at__month=month)

        ordering = filters.get_choice(request, 'ordering', tuple(NEWS_ORDERING)) or '-date'
        return queryset.order_by(*NEWS_ORDERING[ordering])

    @swagger_auto_schema(
        operation_summary="Barcha maktablar yangiliklari",
        operation_description="Yagona lenta. Toifa - yangilik qo'shilganda maktab tanlagan portal toifasi.",
        manual_parameters=[SEARCH_PARAM] + PLACE_PARAMS + [
            _param('school', "Maktab subdomeni, vergul bilan bir nechta"),
            _param('category', f"Portal toifasi: {', '.join(PORTAL_CATEGORY_KEYS)}"),
            _param('important', "true - faqat muhim yangiliklar"),
            _param('year', "Yil", openapi.TYPE_INTEGER),
            _param('month', "Oy (1-12)", openapi.TYPE_INTEGER),
            _param('ordering', f"Saralash: {', '.join(NEWS_ORDERING)}"),
        ] + PAGE_PARAMS,
        tags=['portal'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@cached
class NewsMetaView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Yangiliklar filtrlari",
        operation_description="Toifalar (sanog'i bilan), yangiliklar bor yillar va jami soni.",
        tags=['portal'],
    )
    def get(self, request):
        base = news_base_queryset()
        # order_by() - News.Meta.ordering (created_at) GROUP BY ga qo'shilib, har bir
        # yangilikni alohida guruhga ajratib yubormasligi uchun
        counts = dict(
            base.exclude(portal_category=None)
            .order_by()
            .values_list('portal_category')
            .annotate(total=Count('id'))
        )
        years = sorted({date.year for date in base.dates('created_at', 'year')}, reverse=True)
        return Response({
            'total': base.count(),
            'important': base.filter(is_important=True).count(),
            'categories': [
                {'key': key, 'label': label, 'count': counts.get(key, 0)}
                for key, label in PORTAL_CATEGORIES
            ],
            'years': years,
        })


class NewsDetailView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Yangilik",
        operation_description="To'liq matn va shu maktabning boshqa yangiliklari. Ko'rishlar soni oshadi.",
        tags=['portal'],
    )
    def get(self, request, pk):
        news = get_object_or_404(news_base_queryset(), pk=pk)
        News.objects.filter(pk=news.pk).update(view_count=F('view_count') + 1)
        news.view_count += 1

        related = news_base_queryset().exclude(pk=news.pk)
        related = related.filter(school=news.school) if news.school_id else related.filter(school__isnull=True)
        context = {'request': request, 'related': list(related.order_by('-created_at')[:4])}
        return Response(serializers.NewsDetailSerializer(news, context=context).data)


########################################################
# --------------------- REYTING ---------------------- #
########################################################

RATING_ORDERING = {
    'rank': lambda row: (row['rank'], row['school'].name),
    'score': lambda row: (row['score'], row['school'].name),
    'name': lambda row: row['school'].name.lower(),
    '-quality': lambda row: (-row['quality'], row['rank']),
    '-achievement': lambda row: (-row['achievement'], row['rank']),
    '-teachers': lambda row: (-row['teachers'], row['rank']),
    '-infrastructure': lambda row: (-row['infrastructure'], row['rank']),
    '-creative': lambda row: (-row['creative'], row['rank']),
}


class RatingView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Maktablar reytingi",
        operation_description=(
            "E'lon qilingan davr reytingi. O'rin respublika bo'yicha: hudud tanlansa ham "
            "maktab o'z o'rnini saqlaydi. `summary` filtrlardan qat'i nazar butun davr bo'yicha."
        ),
        manual_parameters=[
            _param('period', "Yil. Berilmasa - eng so'nggi e'lon qilingan davr", openapi.TYPE_INTEGER),
            SEARCH_PARAM,
        ] + PLACE_PARAMS + [
            _param('type', f"Maktab turi: {', '.join(SCHOOL_TYPE_KEYS)}"),
            _param('level', f"Daraja: {', '.join(RATING_LEVEL_KEYS)}"),
            _param('trend', "O'rin o'zgarishi: up, down, same, new"),
            _param('ordering', f"Saralash: {', '.join(RATING_ORDERING)}"),
            _param('limit', "Nechta qator (masalan TOP-10)", openapi.TYPE_INTEGER),
        ],
        tags=['portal'],
    )
    def get(self, request):
        periods = services.published_periods()
        period = services.resolve_period(filters.get_int(request, 'period', 2000, 2100))

        payload = {
            'period': None,
            'periods': [{'year': item.year, 'title': item.title} for item in periods],
            'criteria': [
                {'key': key, 'label': label, 'weight': weight}
                for key, label, weight in RATING_CRITERIA
            ],
            'levels': [
                {'key': key, 'label': label, 'min': minimum}
                for minimum, key, label in RATING_LEVELS
            ],
            'summary': None,
            'count': 0,
            'results': [],
        }
        if period is None:
            return Response(payload)

        rows, previous_period = services.rating_table(period)
        payload['period'] = {
            'year': period.year,
            'title': period.title,
            'previous_year': previous_period.year if previous_period else None,
        }
        payload['summary'] = services.rating_summary(rows)

        region = filters.resolve_region(request)
        if region:
            rows = [row for row in rows if row['school'].region_id == region.id]

        district = filters.resolve_district(request)
        if district:
            rows = [row for row in rows if row['school'].district_id == district.id]

        school_type = filters.get_choice(request, 'type', SCHOOL_TYPE_KEYS)
        if school_type:
            rows = [row for row in rows if row['school'].school_type == school_type]

        level = filters.get_choice(request, 'level', RATING_LEVEL_KEYS)
        if level:
            rows = [row for row in rows if row['level'] == level]

        trend = filters.get_choice(request, 'trend', ('up', 'down', 'same', 'new'))
        if trend:
            rows = [row for row in rows if row['trend'] == trend]

        pattern = loose_pattern(request.query_params.get('search'))
        if pattern:
            regex = re.compile(pattern, re.IGNORECASE)
            rows = [
                row for row in rows
                if regex.search(to_latin(row['school'].name)) or regex.search(row['school'].domain)
            ]

        ordering = filters.get_choice(request, 'ordering', tuple(RATING_ORDERING)) or 'rank'
        rows = sorted(rows, key=RATING_ORDERING[ordering])

        payload['count'] = len(rows)
        limit = filters.get_int(request, 'limit', 1, 500)
        if limit:
            rows = rows[:limit]

        payload['results'] = serializers.RatingRowSerializer(rows, many=True, context={'request': request}).data
        return Response(payload)
