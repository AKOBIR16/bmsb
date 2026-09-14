"""Portal endpointlari uchun hisob-kitoblar: reyting jadvali va umumiy sanoqlar."""

from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Count, Q, Sum

from apps.main.models import Direction, DirectionSchool, School
from apps.news.models import News
from apps.portal.constants import RATING_FIELDS, UZ_LAT_RANGE, UZ_LNG_RANGE, resolve_level
from apps.portal.models import RatingPeriod, SchoolRating


########################################################
# -------------------- MAKTABLAR --------------------- #
########################################################

def active_schools():
    return School.objects.filter(is_active=True)


def location_q():
    """Koordinatasi O'zbekiston hududiga tushadigan maktablar."""
    return Q(
        latitude__gte=UZ_LAT_RANGE[0], latitude__lte=UZ_LAT_RANGE[1],
        longitude__gte=UZ_LNG_RANGE[0], longitude__lte=UZ_LNG_RANGE[1],
    )


def valid_coordinates(school):
    """(kenglik, uzunlik) yoki (None, None) - noto'g'ri qiymatlar xaritaga chiqmaydi."""
    try:
        lat, lng = float(school.latitude), float(school.longitude)
    except (TypeError, ValueError):
        return None, None
    if UZ_LAT_RANGE[0] <= lat <= UZ_LAT_RANGE[1] and UZ_LNG_RANGE[0] <= lng <= UZ_LNG_RANGE[1]:
        return lat, lng
    return None, None


def positive_or_none(value):
    """Maktab yaratilganda raqamli maydonlar 0 qilib qo'yiladi - bu "kiritilmagan" degani."""
    return value if value else None


def portal_stats():
    schools = active_schools()
    totals = schools.aggregate(
        schools=Count('id'),
        students=Sum('student_count'),
        teachers=Sum('teacher_count'),
        employees=Sum('employee_count'),
        admission_open=Count('id', filter=Q(admission_open=True)),
        located=Count('id', filter=location_q()),
        regions=Count('region', distinct=True),
        districts=Count('district', distinct=True),
    )
    directions = (
        Direction.objects
        .filter(is_active=True, direction_schools__is_active=True, direction_schools__school__is_active=True)
        .distinct()
        .count()
    )
    news = News.objects.filter(is_active=True, school__is_active=True).count()

    return {
        'schools': totals['schools'],
        'regions': totals['regions'],
        'districts': totals['districts'],
        'directions': directions,
        'students': totals['students'] or 0,
        'teachers': totals['teachers'] or 0,
        'employees': totals['employees'] or 0,
        'admission_open': totals['admission_open'],
        'located_schools': totals['located'],
        'news': news,
    }


########################################################
# ------------------- YO'NALISHLAR ------------------- #
########################################################

def active_direction_links():
    return DirectionSchool.objects.filter(
        is_active=True, school__is_active=True, direction__is_active=True,
    )


def direction_totals():
    """{direction_id: {'school_count', 'student_count', 'teacher_count'}}"""
    rows = (
        active_direction_links()
        .order_by()
        .values('direction')
        .annotate(
            school_count=Count('school', distinct=True),
            student_count=Sum('student_count'),
            teacher_count=Sum('teacher_count'),
        )
    )
    return {
        row['direction']: {
            'school_count': row['school_count'],
            'student_count': row['student_count'] or 0,
            'teacher_count': row['teacher_count'] or 0,
        }
        for row in rows
    }


########################################################
# --------------------- REYTING ---------------------- #
########################################################

def published_periods():
    return RatingPeriod.objects.filter(is_active=True, is_published=True).order_by('-year')


def resolve_period(year=None):
    periods = published_periods()
    if year:
        return periods.filter(year=year).first()
    return periods.first()


def _ranked(ratings):
    """
    Umumiy ball bo'yicha o'rin beradi. Bir xil ball - bir xil o'rin, keyingisi
    o'tkazib yuboriladi (1, 2, 2, 4).
    """
    ranks = {}
    previous_score = None
    rank = 0
    for index, rating in enumerate(ratings, start=1):
        if rating.score != previous_score:
            rank = index
            previous_score = rating.score
        ranks[rating.school_id] = rank
    return ranks


def _period_ratings(period):
    return list(
        SchoolRating.objects
        .filter(period=period, is_active=True, score__isnull=False, school__is_active=True)
        .select_related('school', 'school__region', 'school__district')
        .order_by('-score', 'school__name')
    )


def _one_decimal(value):
    if value is None:
        return None
    return float(Decimal(value).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


def rating_table(period):
    """
    Davr reytingi: har bir maktab uchun o'rin, oldingi davrdagi o'rin va ballar.
    Oldingi davr - shu davrdan oldingi eng yaqin e'lon qilingan davr.
    """
    ratings = _period_ratings(period)
    ranks = _ranked(ratings)

    previous_period = published_periods().filter(year__lt=period.year).first()
    previous_ranks = _ranked(_period_ratings(previous_period)) if previous_period else {}

    rows = []
    for rating in ratings:
        rank = ranks[rating.school_id]
        previous_rank = previous_ranks.get(rating.school_id)
        if previous_rank is None:
            trend = 'new'
        elif previous_rank > rank:
            trend = 'up'
        elif previous_rank < rank:
            trend = 'down'
        else:
            trend = 'same'

        level, level_label = resolve_level(rating.score)
        rows.append({
            'rank': rank,
            'previous_rank': previous_rank,
            'trend': trend,
            'rank_change': (previous_rank - rank) if previous_rank else None,
            'score': _one_decimal(rating.score),
            'level': level,
            'level_label': level_label,
            **{key: _one_decimal(getattr(rating, key)) for key in RATING_FIELDS},
            'school': rating.school,
        })
    return rows, previous_period


def rating_summary(rows):
    if not rows:
        return {'count': 0, 'average': None, 'max': None, 'excellent_count': 0, 'improved_count': 0}
    scores = [row['score'] for row in rows]
    return {
        'count': len(rows),
        'average': round(sum(scores) / len(scores), 1),
        'max': max(scores),
        'excellent_count': sum(1 for row in rows if row['level'] == 'excellent'),
        'improved_count': sum(1 for row in rows if row['trend'] == 'up'),
    }


def school_rating(school):
    """Maktab sahifasi uchun: joriy e'lon qilingan davrdagi o'rni va bali."""
    period = resolve_period()
    if period is None:
        return None
    rows, _previous = rating_table(period)
    for row in rows:
        if row['school'].id == school.id:
            return {
                'year': period.year,
                'rank': row['rank'],
                'total': len(rows),
                'score': row['score'],
                'level': row['level'],
                'level_label': row['level_label'],
            }
    return None
