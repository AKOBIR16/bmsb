"""Sanoqlar, faollik ko'rsatkichlari va vaqt bo'yicha dinamika."""

from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, Max, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.monitoring.constants import (
    COUNTED_TYPES,
    POST_TYPES,
    STATUS_ACTIVE,
    STATUS_CRITICAL,
    STATUS_LABELS,
    STATUS_PASSIVE,
    resolve_status,
)
from apps.monitoring.services.querysets import MonitoringFilters, base_queryset


def _scope_only(filters):
    """
    Sana filtrlarini olib tashlaydi.

    Umumiy sanoqlar va "bugungi/haftalik/oylik" ko'rsatkichlari doim to'liq
    tarix bo'yicha hisoblanishi kerak - aks holda sana oralig'i tanlanganda
    ular buzilib ketadi.
    """
    if filters is None:
        return MonitoringFilters()
    return MonitoringFilters(
        school_ids=filters.school_ids,
        include_inactive=filters.include_inactive,
    )


def content_counts(filters=None):
    """{school_id: {type_key: soni}} - maktab kartasidagi "sayt tarkibi" bloki uchun."""
    scope = _scope_only(filters)
    counts = defaultdict(dict)

    for content_type in COUNTED_TYPES:
        rows = (
            base_queryset(content_type, scope)
            .values(content_type.school_path)
            .annotate(total=Count('id'))
        )
        for row in rows:
            school_id = row[content_type.school_path]
            if school_id is not None:
                counts[school_id][content_type.key] = row['total']

    return counts


def activity_map(filters=None):
    """
    {school_id: {'today', 'week', 'month', 'last_post_at', 'by_type'}}

    `by_type` har bir kontent turi bo'yicha oxirgi sanani saqlaydi - u
    to'ldirilganlikdagi "yangilik qachon joylangan" mezoni uchun kerak.
    """
    scope = _scope_only(filters)
    today = timezone.localdate()
    week_start = today - timedelta(days=6)
    month_start = today - timedelta(days=29)

    activity = defaultdict(lambda: {
        'today': 0, 'week': 0, 'month': 0, 'last_post_at': None, 'by_type': {},
    })

    for content_type in POST_TYPES:
        rows = (
            base_queryset(content_type, scope)
            .values(content_type.school_path)
            .annotate(
                last_at=Max('created_at'),
                today_count=Count('id', filter=Q(created_at__date=today)),
                week_count=Count('id', filter=Q(created_at__date__gte=week_start)),
                month_count=Count('id', filter=Q(created_at__date__gte=month_start)),
            )
        )
        for row in rows:
            school_id = row[content_type.school_path]
            if school_id is None:
                continue

            entry = activity[school_id]
            entry['today'] += row['today_count']
            entry['week'] += row['week_count']
            entry['month'] += row['month_count']
            entry['by_type'][content_type.key] = row['last_at']

            if row['last_at'] and (entry['last_post_at'] is None or row['last_at'] > entry['last_post_at']):
                entry['last_post_at'] = row['last_at']

    return activity


def days_since(moment):
    if moment is None:
        return None
    return (timezone.localdate() - timezone.localtime(moment).date()).days


def timeseries(date_from, date_to, filters=None):
    """Kunlar kesimida postlar soni va post joylagan maktablar soni."""
    scope = MonitoringFilters(
        school_ids=filters.school_ids if filters else None,
        type_keys=filters.type_keys if filters else (),
        include_inactive=filters.include_inactive if filters else False,
        date_from=date_from,
        date_to=date_to,
    )

    posts_per_day = defaultdict(int)
    schools_per_day = defaultdict(set)

    content_types = POST_TYPES
    if scope.type_keys:
        wanted = set(scope.type_keys)
        content_types = tuple(ct for ct in POST_TYPES if ct.key in wanted)

    for content_type in content_types:
        rows = (
            base_queryset(content_type, scope)
            .annotate(day=TruncDate('created_at'))
            .values('day', content_type.school_path)
            .annotate(total=Count('id'))
        )
        for row in rows:
            day = row['day']
            if day is None:
                continue
            posts_per_day[day] += row['total']
            school_id = row[content_type.school_path]
            if school_id is not None:
                schools_per_day[day].add(school_id)

    result = []
    current = date_from
    while current <= date_to:
        result.append({
            'date': current,
            'posts': posts_per_day.get(current, 0),
            'active_schools': len(schools_per_day.get(current, ())),
        })
        current += timedelta(days=1)

    return result


def overview(schools, filters=None):
    """Dashboard yuqorisidagi plitkalar va faollik ulushi."""
    school_rows = list(schools.values('id', 'is_online'))
    activity = activity_map(filters)

    total = len(school_rows)
    posted_today = 0
    offline_count = 0
    covered_count = 0
    status_counts = {STATUS_ACTIVE: 0, STATUS_PASSIVE: 0, STATUS_CRITICAL: 0}

    for row in school_rows:
        entry = activity.get(row['id'])
        last_post_at = entry['last_post_at'] if entry else None

        if entry and entry['today']:
            posted_today += 1
        if last_post_at:
            covered_count += 1
        if not row['is_online']:
            offline_count += 1

        status_counts[resolve_status(days_since(last_post_at))] += 1

    def percent(part):
        return round(part * 100 / total, 1) if total else 0.0

    return {
        'total_schools': total,
        'coverage_percent': percent(covered_count),
        'posted_today': posted_today,
        'posted_today_percent': percent(posted_today),
        'not_posted_today': total - posted_today,
        'stale_7_days': status_counts[STATUS_PASSIVE],
        'stale_30_days': status_counts[STATUS_CRITICAL],
        'offline_schools': offline_count,
        'active_percent': percent(status_counts[STATUS_ACTIVE]),
        'statuses': [
            {'status': status, 'label': STATUS_LABELS[status], 'count': status_counts[status]}
            for status in (STATUS_ACTIVE, STATUS_PASSIVE, STATUS_CRITICAL)
        ],
    }
