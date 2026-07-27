"""
Monitoring uchun kontent turlari reyestri va hisoblash qoidalari.

Bu yerdagi ro'yxat monitoringning yagona manbai: yangi model qo'shilganda
faqat shu faylga bitta qator yoziladi, qolgan hamma joyda (lenta, sanoqlar,
to'ldirilganlik, statistika) avtomatik hisobga olinadi.
"""

from dataclasses import dataclass


# "E'lonlar" uchun alohida model yo'q - ular News modelining kategoriyasi orqali
# ajratiladi. Maktablar boshqa nom ishlatgan bo'lsa, shu ro'yxatga qo'shiladi.
ANNOUNCEMENT_CATEGORY_SLUGS = ('elonlar', 'e-lonlar', 'elon', 'announcements')


@dataclass(frozen=True)
class ContentType:
    key: str
    label: str
    model: str                      # "app_label.ModelName"
    title_field: str
    school_path: str | None = 'school'   # None - model maktabga bog'lanmagan
    slug_field: str | None = None
    view_count_field: str | None = None
    site_path: str | None = None    # frontend manzili, "{slug}" o'rin egallovchisi bilan
    is_post: bool = True            # postlar lentasiga tushadimi
    filters: tuple = ()             # ((lookup, value), ...)
    excludes: tuple = ()

    @property
    def is_school_scoped(self):
        return self.school_path is not None


CONTENT_TYPES = (
    # ------------------------- Postlar -------------------------
    ContentType(
        key='news', label="Yangilik", model='news.News', title_field='title',
        slug_field='slug', view_count_field='view_count', site_path='/news/{slug}',
        excludes=(('category__slug__in', ANNOUNCEMENT_CATEGORY_SLUGS),),
    ),
    ContentType(
        key='announcement', label="E'lon", model='news.News', title_field='title',
        slug_field='slug', view_count_field='view_count', site_path='/news/{slug}',
        filters=(('category__slug__in', ANNOUNCEMENT_CATEGORY_SLUGS),),
    ),
    ContentType(
        key='school-life', label="Maktab hayoti", model='main.SchoolLife',
        title_field='title', site_path='/about',
    ),
    ContentType(
        key='honor', label="Maktab faxri", model='main.Honors', title_field='full_name',
        slug_field='slug', site_path='/top-students/{slug}',
    ),
    ContentType(
        key='media-image', label="Galereya rasmi", model='media.MediaImage',
        title_field='collection__title', school_path='collection__school',
        site_path='/media',
    ),
    # DIQQAT: MediaVideo modelida maktab bilan bog'lanish (FK) yo'q - videolar
    # barcha maktablar uchun umumiy. Shu sababli u maktab kesimidagi hisob-kitobga
    # qo'shilmaydi. Modelga `school` FK qo'shilgach, bu yerda school_path='school'
    # deb yozilsa, monitoring uni avtomatik hisobga oladi.
    ContentType(
        key='media-video', label="Galereya videosi", model='media.MediaVideo',
        title_field='title', school_path=None, site_path='/media',
    ),
    ContentType(
        key='document', label="Hujjat", model='main.Document', title_field='title',
        site_path='/official-documents',
    ),
    ContentType(
        key='vacancy', label="Bo'sh ish o'rni", model='main.Vacancy', title_field='title',
        slug_field='slug', site_path='/vacancy',
    ),
    ContentType(
        key='resource-file', label="Resurs fayl", model='resource.ResourceFile',
        title_field='title', site_path='/resources',
    ),
    ContentType(
        key='resource-video', label="Resurs video", model='resource.ResourceVideo',
        title_field='title', view_count_field='view_count', site_path='/resources',
    ),
    ContentType(
        key='culture-service', label="Madaniy xizmat", model='service.CultureService',
        title_field='name', slug_field='slug', site_path='/cultural-services/{slug}',
    ),
    ContentType(
        key='culture-art', label="Amaliy san'at", model='service.CultureArt',
        title_field='name', slug_field='slug', site_path='/applied-arts/{slug}',
    ),
    ContentType(
        key='fine-art', label="Tasviriy san'at", model='service.FineArt',
        title_field='name', slug_field='slug', site_path='/visual-arts/{slug}',
    ),

    # ------------- Profil ma'lumotlari (lentaga tushmaydi) -------------
    ContentType(
        key='teacher', label="Pedagog", model='main.Teacher', title_field='full_name',
        slug_field='slug', site_path='/teachers/{slug}', is_post=False,
    ),
    ContentType(
        key='staff', label="Xodim", model='main.Staff', title_field='full_name',
        slug_field='slug', is_post=False,
    ),
    ContentType(
        key='leader', label="Rahbar", model='main.Leader', title_field='full_name',
        slug_field='slug', is_post=False,
    ),
    ContentType(
        key='direction', label="Yo'nalish", model='main.DirectionSchool',
        title_field='direction__name', is_post=False,
    ),
    ContentType(
        key='media-collection', label="Rasmlar to'plami", model='media.MediaCollection',
        title_field='title', slug_field='slug', is_post=False,
    ),
    # Maktab yaratilganda 9 ta bo'sh o'quv reja avtomatik hosil bo'ladi
    # (1-9 sinflar, faylsiz). Ular kontent hisoblanmaydi - faqat fayl
    # yuklanganlari sanaladi.
    ContentType(
        key='timetable', label="O'quv reja", model='main.TimeTable', title_field='title',
        is_post=False, excludes=(('file', ''), ('file__isnull', True)),
    ),
    ContentType(
        key='edu-info', label="Ta'limga oid ma'lumot", model='main.EduInfo',
        title_field='title', is_post=False,
    ),
    ContentType(
        key='faq', label="Savol-javob", model='main.FAQ', title_field='title',
        is_post=False,
    ),
    ContentType(
        key='banner', label="Banner", model='main.Banner', title_field='title',
        is_post=False,
    ),
)

CONTENT_TYPES_BY_KEY = {content_type.key: content_type for content_type in CONTENT_TYPES}

# Lentaga tushadigan va maktabga bog'langan turlar
POST_TYPES = tuple(ct for ct in CONTENT_TYPES if ct.is_post and ct.is_school_scoped)

# Maktab kartasidagi sanoqlar uchun (skrinshotdagi "SAYT TARKIBI" bloki)
COUNTED_TYPES = tuple(ct for ct in CONTENT_TYPES if ct.is_school_scoped)


########################################################
# ------------------ FAOLLIK HOLATI ------------------ #
########################################################

STATUS_ACTIVE = 'active'
STATUS_PASSIVE = 'passive'
STATUS_CRITICAL = 'critical'

STATUS_LABELS = {
    STATUS_ACTIVE: "Faol",
    STATUS_PASSIVE: "Passiv",
    STATUS_CRITICAL: "Kritik",
}

# Oxirgi postdan beri o'tgan kunlar bo'yicha holat chegaralari
ACTIVE_MAX_DAYS = 7      # <= 7 kun  -> faol
PASSIVE_MAX_DAYS = 30    # 8-30 kun  -> passiv, undan keyin kritik


def resolve_status(days_since_last_post):
    if days_since_last_post is None or days_since_last_post > PASSIVE_MAX_DAYS:
        return STATUS_CRITICAL
    if days_since_last_post > ACTIVE_MAX_DAYS:
        return STATUS_PASSIVE
    return STATUS_ACTIVE


########################################################
# --------------- TO'LDIRILGANLIK QOIDA -------------- #
########################################################

# Maktab profilida to'ldirilgan bo'lishi kutilayotgan maydonlar
PROFILE_FIELDS = (
    'description', 'short_description', 'founded_year', 'capacity',
    'student_count', 'teacher_count', 'address', 'phone_number', 'email',
    'latitude', 'longitude', 'logo', 'region', 'district',
)

# kind='fields'  - School modelidagi maydonlar to'ldirilganligi
# kind='count'   - kontent turi bo'yicha yozuvlar soni `target` ga yetganligi
# `fresh_days` berilgan bo'lsa, ballning yarmi kontentning yangiligiga beriladi
COMPLETENESS_SECTIONS = (
    {'key': 'profile', 'label': "Maktab profili", 'weight': 20, 'kind': 'fields',
     'fields': PROFILE_FIELDS},
    {'key': 'news', 'label': "Yangiliklar", 'weight': 15, 'kind': 'count',
     'types': ('news', 'announcement'), 'target': 5, 'fresh_days': 30},
    {'key': 'leaders', 'label': "Rahbariyat", 'weight': 10, 'kind': 'count',
     'types': ('leader',), 'target': 1},
    {'key': 'teachers', 'label': "Pedagoglar", 'weight': 10, 'kind': 'count',
     'types': ('teacher',), 'target': 3},
    {'key': 'directions', 'label': "Yo'nalishlar", 'weight': 10, 'kind': 'count',
     'types': ('direction',), 'target': 1},
    {'key': 'media', 'label': "Galereya", 'weight': 10, 'kind': 'count',
     'types': ('media-image',), 'target': 10},
    {'key': 'documents', 'label': "Hujjatlar", 'weight': 5, 'kind': 'count',
     'types': ('document',), 'target': 1},
    {'key': 'timetables', 'label': "O'quv reja", 'weight': 5, 'kind': 'count',
     'types': ('timetable',), 'target': 1},
    {'key': 'services', 'label': "Xizmatlar", 'weight': 5, 'kind': 'count',
     'types': ('culture-service', 'culture-art', 'fine-art'), 'target': 1},
    {'key': 'resources', 'label': "Resurslar", 'weight': 5, 'kind': 'count',
     'types': ('resource-file', 'resource-video'), 'target': 1},
    {'key': 'school-life', 'label': "Maktab hayoti", 'weight': 5, 'kind': 'count',
     'types': ('school-life',), 'target': 1},
)
