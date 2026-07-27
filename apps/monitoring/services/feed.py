"""
Barcha maktablar va barcha kontent turlari bo'ylab yagona postlar lentasi.

Har bir model uchun bir xil ustunlar to'plami yasaladi, keyin ular sana
bo'yicha birlashtiriladi.

Nega SQL UNION emas: Django `.values()` da SELECT ustunlarini har doim ham
berilgan tartibda chiqarmaydi (tartib modelning maydonlariga va JOIN'lariga
qarab o'zgaradi). UNION esa ustunlarni nom bo'yicha emas, o'rni bo'yicha
solishtiradi - natijada ma'lumotlar bir-birining ustuniga tushib qoladi.
Shuning uchun har bir model alohida so'raladi va natijalar Python tomonida
birlashtiriladi: har bir turdan kerakli oynagacha (offset + limit) yozuv
olinadi, so'ng umumiy ro'yxat saralanib kesiladi.
"""

from django.db.models import CharField, F, IntegerField, Value
from django.db.models.functions import Coalesce

from apps.monitoring.constants import POST_TYPES
from apps.monitoring.services.querysets import base_queryset, select_types

FEED_COLUMNS = (
    'mon_type', 'mon_id', 'mon_title', 'mon_slug', 'mon_school', 'mon_views',
    'mon_created', 'mon_updated', 'mon_active',
)

# Chuqur sahifalashda har bir model uchun shuncha yozuv o'qishga to'g'ri keladi,
# shuning uchun oyna cheklangan
MAX_FEED_WINDOW = 5000


def annotated_queryset(content_type, filters=None):
    queryset = base_queryset(content_type, filters)

    if content_type.slug_field:
        slug_expression = Coalesce(F(content_type.slug_field), Value(''), output_field=CharField())
    else:
        slug_expression = Value('', output_field=CharField())

    if content_type.view_count_field:
        views_expression = Coalesce(F(content_type.view_count_field), Value(0), output_field=IntegerField())
    else:
        views_expression = Value(0, output_field=IntegerField())

    return queryset.annotate(
        mon_type=Value(content_type.key, output_field=CharField()),
        mon_id=F('id'),
        mon_title=Coalesce(F(content_type.title_field), Value(''), output_field=CharField()),
        mon_slug=slug_expression,
        mon_school=F(f'{content_type.school_path}__id'),
        mon_views=views_expression,
        mon_created=F('created_at'),
        mon_updated=F('updated_at'),
        mon_active=F('is_active'),
    ).values(*FEED_COLUMNS)


def fetch_feed(filters=None, ordering='-created_at', limit=50, offset=0):
    """
    (jami_soni, yozuvlar) qaytaradi.

    `yozuvlar` - lug'atlar ro'yxati, `FEED_COLUMNS` kalitlari bilan.
    """
    content_types = select_types(POST_TYPES, getattr(filters, 'type_keys', ()))
    if not content_types:
        return 0, []

    descending = ordering.startswith('-')
    sort_field = 'mon_updated' if ordering.lstrip('-') == 'updated_at' else 'mon_created'
    order_by = f"{'-' if descending else ''}{sort_field}"

    window = min(offset + limit, MAX_FEED_WINDOW)

    total = 0
    pool = []
    for content_type in content_types:
        queryset = annotated_queryset(content_type, filters)
        total += queryset.count()
        pool.extend(queryset.order_by(order_by)[:window])

    pool.sort(key=lambda row: row[sort_field], reverse=descending)
    return total, pool[offset:offset + limit]
