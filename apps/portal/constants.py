"""
e-bmsm.uz portali uchun qoidalar: reyting mezonlari, darajalar, murojaat mavzulari.

Reyting mezonlari va og'irliklari shu yerda - ularni o'zgartirish uchun
migratsiya kerak emas (ballar `SchoolRating` da mezon bo'yicha alohida saqlanadi,
umumiy ball esa saqlashda qayta hisoblanadi).
"""

# (kalit, nomi, og'irligi %). Og'irliklar yig'indisi 100 bo'lishi kerak.
RATING_CRITERIA = (
    ('quality', "Ta'lim sifati", 30),
    ('achievement', "O'quvchi yutuqlari", 25),
    ('teachers', "Pedagog salohiyati", 20),
    ('infrastructure', "Infratuzilma", 15),
    ('creative', "Ijodiy faollik", 10),
)

RATING_FIELDS = tuple(key for key, _label, _weight in RATING_CRITERIA)

# Umumiy ball bo'yicha daraja: (quyi chegara, kalit, nomi) - yuqoridan pastga
RATING_LEVELS = (
    (90, 'excellent', "A'lo"),
    (85, 'high', "Yuqori"),
    (80, 'good', "Yaxshi"),
    (0, 'stable', "Barqaror"),
)

RATING_LEVEL_KEYS = tuple(key for _min, key, _label in RATING_LEVELS)


def resolve_level(score):
    """Umumiy ball -> (kalit, nomi)."""
    if score is None:
        return None, None
    for minimum, key, label in RATING_LEVELS:
        if score >= minimum:
            return key, label
    return RATING_LEVELS[-1][1], RATING_LEVELS[-1][2]


def level_bounds(level_key):
    """Daraja kaliti -> (quyi chegara, yuqori chegara yoki None)."""
    upper = None
    for minimum, key, _label in RATING_LEVELS:
        if key == level_key:
            return minimum, upper
        upper = minimum
    return None


APPEAL_TOPICS = [
    ('portal', "Portal bo'yicha"),
    ('school', "Maktab haqida"),
    ('admission', "Qabul masalasi"),
    ('education', "Ta'lim yo'nalishi"),
    ('technical', "Texnik muammo"),
    ('suggestion', "Taklif"),
    ('other', "Boshqa masala"),
]

# Maktab koordinatasi faqat O'zbekiston hududiga tushsa xaritada ko'rsatiladi.
# Bazada 0,0 yoki 10,10 kabi "to'ldirib qo'yilgan" qiymatlar ko'p uchraydi.
UZ_LAT_RANGE = (37.0, 46.0)
UZ_LNG_RANGE = (55.0, 74.0)

# Kesh muddati (sekund) - og'ir agregat javoblar uchun
CACHE_SECONDS = 600
