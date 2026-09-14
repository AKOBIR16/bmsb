"""Maktab adminlari kiritgan HTML ni portalda xavfsiz ko'rsatish.

Portal 266 ta maktabning matnini bitta asosiy domenda chiqaradi, shuning uchun
TinyMCE matnidan faqat oddiy teglar qoladi: script/style, on* atributlar,
javascript: havolalar, inline stillar va Word'dan qolgan data-* atributlar
olib tashlanadi.
"""

import nh3

ALLOWED_ATTRIBUTES = {
    'a': {'href', 'title'},
    'img': {'src', 'alt', 'width', 'height', 'title'},
    'ol': {'start'},
    'td': {'colspan', 'rowspan'},
    'th': {'colspan', 'rowspan'},
}


def clean_html(value):
    if not value:
        return value
    return nh3.clean(value, attributes=ALLOWED_ATTRIBUTES, link_rel='noopener noreferrer')
