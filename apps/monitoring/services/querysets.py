"""
Har xil modellarga bir xil filtrlarni qo'llaydigan yordamchi qatlam.

Hudud bo'yicha filtr bu yerda emas, view qatlamida maktablar ro'yxatiga
aylantiriladi (`school_ids`) - shunda har bir model uchun alohida JOIN
qilish shart bo'lmaydi.
"""

from dataclasses import dataclass, field

from django.apps import apps


@dataclass
class MonitoringFilters:
    school_ids: list | None = None
    date_from: object = None          # datetime.date
    date_to: object = None            # datetime.date
    type_keys: tuple = ()
    search: str = ''
    include_inactive: bool = False
    _extra: dict = field(default_factory=dict)


def get_model(content_type):
    return apps.get_model(content_type.model)


def base_queryset(content_type, filters=None):
    """Kontent turi uchun filtrlangan, lekin hali annotatsiyalanmagan queryset."""
    filters = filters or MonitoringFilters()

    # order_by() - modellarning Meta.ordering qiymatini bekor qiladi. UNION
    # ichidagi so'rovlarda ORDER BY bo'lishi mumkin emas, saralash birlashtirilgan
    # natijaga qo'llanadi.
    queryset = get_model(content_type).objects.all().order_by()

    for lookup, value in content_type.filters:
        queryset = queryset.filter(**{lookup: value})
    for lookup, value in content_type.excludes:
        queryset = queryset.exclude(**{lookup: value})

    if not filters.include_inactive:
        queryset = queryset.filter(is_active=True)

    school_path = content_type.school_path
    if filters.school_ids is not None:
        if school_path is None:
            # Maktabga bog'lanmagan modelni maktab bo'yicha filtrlab bo'lmaydi
            return queryset.none()
        queryset = queryset.filter(**{f'{school_path}__in': filters.school_ids})

    if filters.date_from:
        queryset = queryset.filter(created_at__date__gte=filters.date_from)
    if filters.date_to:
        queryset = queryset.filter(created_at__date__lte=filters.date_to)

    if filters.search:
        queryset = queryset.filter(**{f'{content_type.title_field}__icontains': filters.search})

    return queryset


def select_types(content_types, type_keys):
    """So'rovda `type` parametri berilgan bo'lsa, turlarni shunga qarab qisqartiradi."""
    if not type_keys:
        return tuple(content_types)
    wanted = set(type_keys)
    return tuple(ct for ct in content_types if ct.key in wanted)
