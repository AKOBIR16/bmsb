"""So'rov parametrlarini o'qish va tekshirish."""

from datetime import timedelta

from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError

from apps.main.models import District, Region, School
from apps.monitoring.constants import CONTENT_TYPES_BY_KEY, STATUS_LABELS
from apps.monitoring.services.querysets import MonitoringFilters

DEFAULT_TIMESERIES_DAYS = 30
MAX_TIMESERIES_DAYS = 366


def _get_bool(request, name, default=False):
    raw = request.query_params.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ('1', 'true', 'yes')


def _get_date(request, name):
    raw = request.query_params.get(name)
    if not raw:
        return None
    value = parse_date(raw.strip())
    if value is None:
        raise ValidationError({name: "Sana YYYY-MM-DD ko'rinishida bo'lishi kerak."})
    return value


def _get_list(request, name):
    raw = request.query_params.get(name)
    if not raw:
        return ()
    return tuple(item.strip() for item in raw.split(',') if item.strip())


def resolve_region(request):
    raw = (request.query_params.get('region') or '').strip()
    if not raw:
        return None
    lookup = {'pk': raw} if raw.isdigit() else {'slug': raw}
    region = Region.objects.filter(**lookup).first()
    if region is None:
        raise ValidationError({'region': f"Viloyat topilmadi: {raw}"})
    return region


def resolve_district(request):
    raw = (request.query_params.get('district') or '').strip()
    if not raw:
        return None
    lookup = {'pk': raw} if raw.isdigit() else {'slug': raw}
    district = District.objects.filter(**lookup).first()
    if district is None:
        raise ValidationError({'district': f"Tuman topilmadi: {raw}"})
    return district


def school_queryset(request):
    """So'rovdagi hudud/maktab filtrlariga mos maktablar."""
    queryset = School.objects.select_related('region', 'district')

    if not _get_bool(request, 'include_inactive'):
        queryset = queryset.filter(is_active=True)

    region = resolve_region(request)
    if region:
        queryset = queryset.filter(region=region)

    district = resolve_district(request)
    if district:
        queryset = queryset.filter(district=district)

    domains = _get_list(request, 'school')
    if domains:
        queryset = queryset.filter(domain__in=[domain.lower() for domain in domains])

    online = request.query_params.get('is_online')
    if online is not None and online.strip() != '':
        queryset = queryset.filter(is_online=_get_bool(request, 'is_online'))

    search = (request.query_params.get('search') or '').strip()
    if search:
        queryset = queryset.filter(name__icontains=search)

    return queryset


def content_filters(request, schools=None, use_search=False):
    """Kontent modellariga qo'llanadigan filtrlar."""
    type_keys = _get_list(request, 'type')
    unknown = [key for key in type_keys if key not in CONTENT_TYPES_BY_KEY]
    if unknown:
        raise ValidationError({'type': f"Noma'lum kontent turi: {', '.join(unknown)}"})

    date_from = _get_date(request, 'date_from')
    date_to = _get_date(request, 'date_to')
    if date_from and date_to and date_from > date_to:
        raise ValidationError({'date_from': "`date_from` `date_to` dan katta bo'lmasligi kerak."})

    school_ids = None
    if schools is not None:
        school_ids = list(schools.values_list('id', flat=True))

    return MonitoringFilters(
        school_ids=school_ids,
        date_from=date_from,
        date_to=date_to,
        type_keys=type_keys,
        search=(request.query_params.get('search') or '').strip() if use_search else '',
        include_inactive=_get_bool(request, 'include_inactive'),
    )


def timeseries_range(request):
    date_to = _get_date(request, 'date_to') or timezone.localdate()
    date_from = _get_date(request, 'date_from') or (date_to - timedelta(days=DEFAULT_TIMESERIES_DAYS - 1))

    if date_from > date_to:
        raise ValidationError({'date_from': "`date_from` `date_to` dan katta bo'lmasligi kerak."})
    if (date_to - date_from).days + 1 > MAX_TIMESERIES_DAYS:
        raise ValidationError({'date_from': f"Oraliq {MAX_TIMESERIES_DAYS} kundan oshmasligi kerak."})

    return date_from, date_to


def resolve_status_filter(request):
    raw = (request.query_params.get('status') or '').strip()
    if not raw:
        return None
    if raw not in STATUS_LABELS:
        raise ValidationError({'status': f"Holat noto'g'ri. Mumkin: {', '.join(STATUS_LABELS)}"})
    return raw
