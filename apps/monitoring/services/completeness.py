"""
Maktab ma'lumotlari qanchalik to'liq to'ldirilganini hisoblaydi.

Qoidalar va og'irliklar `constants.COMPLETENESS_SECTIONS` da - ularni
o'zgartirish uchun migratsiya kerak emas.
"""

from decimal import Decimal

from apps.monitoring.constants import COMPLETENESS_SECTIONS


def _is_filled(school, field_name):
    field = school._meta.get_field(field_name)

    if field.is_relation:
        return getattr(school, f'{field_name}_id', None) is not None

    value = getattr(school, field_name, None)
    if value is None:
        return False
    if hasattr(value, 'name'):          # ImageField / FileField
        return bool(value.name)
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        # Maktab yaratilganda raqamli maydonlar 0 qilib qo'yiladi,
        # shuning uchun 0 "to'ldirilgan" hisoblanmaydi
        return value != 0
    return True


def _fields_section(school, rule):
    fields = rule['fields']
    missing = [name for name in fields if not _is_filled(school, name)]
    percent = round((len(fields) - len(missing)) * 100 / len(fields), 1) if fields else 100.0
    return percent, {'missing': missing}


def _count_section(rule, counts, last_dates, days_since):
    total = sum(counts.get(type_key, 0) for type_key in rule['types'])
    target = rule.get('target', 1)
    count_percent = min(total / target, 1) * 100 if target else 100.0

    details = {'count': total, 'target': target}
    fresh_days = rule.get('fresh_days')

    if not fresh_days:
        return round(count_percent, 1), details

    dates = [last_dates.get(type_key) for type_key in rule['types']]
    dates = [value for value in dates if value]
    last_at = max(dates) if dates else None
    age = days_since(last_at)

    is_fresh = age is not None and age <= fresh_days
    details['last_at'] = last_at
    if not is_fresh:
        details['note'] = (
            f"Oxirgi {fresh_days} kun ichida yangi kontent joylanmagan"
            if last_at else "Umuman kontent joylanmagan"
        )

    # Yarim ball - miqdorga, yarim ball - yangilanib turganiga
    return round(count_percent * 0.5 + (100 if is_fresh else 0) * 0.5, 1), details


def compute(school, counts, last_dates, days_since):
    """
    (umumiy_foiz, bo'limlar_ro'yxati) qaytaradi.

    counts     - {type_key: soni}
    last_dates - {type_key: oxirgi created_at}
    days_since - datetime -> kunlar soni funksiyasi
    """
    counts = counts or {}
    last_dates = last_dates or {}

    sections = []
    weighted_total = 0
    weight_sum = 0

    for rule in COMPLETENESS_SECTIONS:
        if rule['kind'] == 'fields':
            percent, details = _fields_section(school, rule)
        else:
            percent, details = _count_section(rule, counts, last_dates, days_since)

        weight = rule['weight']
        weighted_total += percent * weight
        weight_sum += weight

        sections.append({
            'key': rule['key'],
            'label': rule['label'],
            'weight': weight,
            'percent': percent,
            **details,
        })

    overall = round(weighted_total / weight_sum) if weight_sum else 0
    return overall, sections
