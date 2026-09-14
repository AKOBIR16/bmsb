"""
O'zbekcha matn bo'yicha qidiruv.

Bazadagi nomlarda bir xil harf turlicha yozilgan: "Farg'ona", "Farg‘ona",
"Fargʻona", ba'zan umuman tutuq belgisisiz "Fargona". Oddiy `icontains` ularni
bir-biriga moslamaydi, shuning uchun so'rovdan har bir harf orasida ixtiyoriy
tutuq belgisini qabul qiladigan regex yasaladi. Kirill harflarida yozilgan
so'rov avval lotinchaga o'giriladi.
"""

import re
from functools import reduce
from operator import or_

from django.db.models import Q

APOSTROPHES = "'`ʻʼ‘’´"
_APOSTROPHE_CLASS = "[" + re.escape(APOSTROPHES) + "]?"

_CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'j', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'x', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh', 'ъ': "'",
    'ы': 'i', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya', 'ў': "o'", 'қ': 'q',
    'ғ': "g'", 'ҳ': 'h',
}

MAX_QUERY_LENGTH = 100


def to_latin(text):
    return ''.join(_CYRILLIC_TO_LATIN.get(char, char) for char in text.lower())


def loose_pattern(query):
    """So'rovdan tutuq belgilariga befarq regex yasaydi. Bo'sh so'rov uchun None."""
    text = to_latin((query or '').strip()[:MAX_QUERY_LENGTH])
    text = ''.join(char for char in text if char not in APOSTROPHES)
    words = text.split()
    if not words:
        return None
    return r'\s+'.join(
        _APOSTROPHE_CLASS.join(re.escape(char) for char in word)
        for word in words
    )


def search_q(query, *fields):
    """Berilgan maydonlarning birortasida so'rov uchrasa mos keladigan Q."""
    pattern = loose_pattern(query)
    if pattern is None:
        return None
    return reduce(or_, (Q(**{f'{field}__iregex': pattern}) for field in fields))
