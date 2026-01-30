from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from mptt.models import MPTTModel, TreeForeignKey
from apps.common.mixins import SlugifyMixin
from tinymce.models import HTMLField
from django.utils.safestring import mark_safe
from django.core.validators import FileExtensionValidator
from apps.common.models import BaseModel
from apps.common.utils import generate_upload_path
from apps.common.validators import file_size, file_size_50, validate_subdomain, validate_youtube_link
    
    
class School(SlugifyMixin, BaseModel):
    domain = models.SlugField(verbose_name="Subdomen", validators=[validate_subdomain])
    name = models.CharField(max_length=255, verbose_name="Nomi")
    slug = models.SlugField(verbose_name="Slug")
    description = HTMLField(null=True, blank=True, verbose_name="Tafsilot")
    short_description = HTMLField(null=True, blank=True, verbose_name="Qisqacha tafsilot")
    founded_year = models.SmallIntegerField(null=True, blank=True, verbose_name="Ishga tushgan yili")
    capacity = models.PositiveIntegerField(null=True, blank=True, verbose_name="O'quvchilar sig'imi")
    student_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="O'quvchilar soni")
    teacher_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="O'qituvchilar soni")
    direction_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="Yo'nalishlar soni")
    class_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="Sinflar soni")
    email = models.EmailField(null=True, blank=True, verbose_name="Email")
    phone_number = models.CharField(max_length=255, null=True, blank=True, verbose_name="Telefon raqami")
    address = models.CharField(max_length=255, null=True, blank=True, verbose_name="Manzil")
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, verbose_name="Kenglik")
    longitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, verbose_name="Uzunlik")
    instagram_link = models.URLField(null=True, blank=True, verbose_name="Instagram havola")
    telegram_link = models.URLField(null=True, blank=True, verbose_name="Telegram havola")
    facebook_link = models.URLField(null=True, blank=True, verbose_name="Facebook havola")
    youtube_link = models.URLField(null=True, blank=True, verbose_name="Youtube havola")
    logo = models.ImageField(
        upload_to=generate_upload_path,
        verbose_name="Maktab logosi",
        validators=[file_size],
        null=True, blank=True,
        help_text="Maktab logosi. Rasm 5 MB dan katta bo'lishi mumkin emas."
    )
    
    def __str__(self):
        return self.name
    
    
    class Meta:
        verbose_name = "Maktab "
        verbose_name_plural = "Maktablar"
        constraints = [
            models.UniqueConstraint(
                fields=['domain'],
                name='unique_school_domain',
            ),
            models.UniqueConstraint(
                fields=['slug'],
                name='unique_school_slug',
            )
        ]


class SchoolLife(BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="school_lives",
    )
    
    image = models.ImageField(upload_to=generate_upload_path, verbose_name="Rasm", validators=[file_size], 
                              help_text="Rasm 5 MB dan katta bo'lishi mumkin emas.")
    title = models.CharField(max_length=255, verbose_name="Sarlavha")
    description = models.TextField(null=True, blank=True, verbose_name="Tafsilot")
    
    def image_tag(self):
        return mark_safe(f'<img src="{self.image.url}" style="height: 50px; object-fit: cover;" />')
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Maktab hayoti "
        verbose_name_plural = "Maktab hayoti"


class Menu(MPTTModel):
    school = models.ForeignKey(
        'School', on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="menus",
    )
    
    title = models.CharField(max_length=120)
    parent = TreeForeignKey(
        "self",
        null=True, blank=True,
        related_name="children",
        on_delete=models.CASCADE,
    )
    url = models.CharField(max_length=255, null=True, blank=True)
    
    class MPTTMeta:
        order_insertion_by = ("id",)

    def get_absolute_url(self):
        return self.url

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Menu "
        verbose_name_plural = "Menu"


class Banner(BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="banners",
    )
    
    image = models.ImageField(upload_to=generate_upload_path, verbose_name="Rasm", validators=[file_size], 
                              help_text="Rasm 5 MB dan katta bo'lishi mumkin emas.")
    title = models.CharField(max_length=255, verbose_name="Sarlavha")
    button_text = models.CharField(max_length=255, null=True, blank=True, verbose_name="Tugma matni")
    link = models.URLField(null=True, blank=True, verbose_name="Havola")
    
    
    def __str__(self):
        return self.title
    
    def image_tag(self):
        return mark_safe(f'<img src="{self.image.url}" style="height: 50px; object-fit: cover;" />')
    
    class Meta:
        verbose_name = "Banner "
        verbose_name_plural = "Bannerlar"


class Subject(SlugifyMixin, BaseModel):
    name = models.CharField(max_length=255, verbose_name="Nomi")
    slug = models.SlugField(verbose_name="Slug")
    
    description = models.TextField(null=True, blank=True, verbose_name="Tafsilot")
    background_image = models.ImageField(
        upload_to=generate_upload_path, 
        verbose_name="Fon rasmi", 
        validators=[file_size],
        null=True, blank=True,
        help_text="Rasm 5 MB dan katta bo'lishi mumkin emas."
    )
    icon = models.ImageField(
        upload_to=generate_upload_path, 
        verbose_name="Ikonka", 
        validators=[file_size],
        null=True, blank=True,
        help_text="Rasm 5 MB dan katta bo'lishi mumkin emas."
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Fan "
        verbose_name_plural = "Fanlar"
        constraints = [
            models.UniqueConstraint(
                fields=['slug'],
                name='unique_subject_slug',
            )
        ]


class MusicalInstrument(SlugifyMixin, BaseModel):
    name = models.CharField(max_length=255, verbose_name="Nomi")
    slug = models.SlugField(verbose_name="Slug")
    
    description = models.TextField(null=True, blank=True, verbose_name="Tafsilot")
    background_image = models.ImageField(
        upload_to=generate_upload_path, 
        verbose_name="Fon rasmi", 
        validators=[file_size],
        null=True, blank=True,
        help_text="Rasm 5 MB dan katta bo'lishi mumkin emas."
    )
    icon = models.ImageField(
        upload_to=generate_upload_path, 
        verbose_name="Ikonka", 
        validators=[file_size],
        null=True, blank=True,
        help_text="Rasm 5 MB dan katta bo'lishi mumkin emas."
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Musiqa asbobi "
        verbose_name_plural = "Musiqa asboblari"
        constraints = [
            models.UniqueConstraint(
                fields=['slug'],
                name='unique_musicalinstrument_slug',
            )
        ]


class Direction(SlugifyMixin, BaseModel):
    name = models.CharField(max_length=255, verbose_name="Nomi")
    slug = models.SlugField(verbose_name="Slug")
    slug_source = "name"
    
    
    icon = models.ImageField(
        upload_to=generate_upload_path, 
        verbose_name="Ikonka", 
        validators=[file_size],
        null=True, blank=True,
        help_text="Rasm 5 MB dan katta bo'lishi mumkin emas."
    )
    background_image = models.ImageField(
        upload_to=generate_upload_path, 
        verbose_name="Fon rasmi", 
        validators=[file_size],
        null=True, blank=True,
        help_text="Rasm 5 MB dan katta bo'lishi mumkin emas."
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Yo'nalish "
        verbose_name_plural = "Yo'nalishlar"
        constraints = [
            models.UniqueConstraint(
                fields=['slug'],
                name='unique_direction_slug',
            )
        ]


class DirectionImage(BaseModel):
    direction = models.ForeignKey(
        'DirectionSchool', on_delete=models.CASCADE,
        verbose_name="Yo'nalish",
        related_name="direction_images",
    )
    image = models.ImageField(upload_to=generate_upload_path, verbose_name="Rasm", validators=[file_size], 
                              help_text="Rasm 5 MB dan katta bo'lishi mumkin emas.")

    class Meta:
        verbose_name = "Yo'nalish galereya "
        verbose_name_plural = "Yo'nalish galereyalari"


class DirectionVideo(BaseModel):
    direction = models.ForeignKey(
        'DirectionSchool', on_delete=models.CASCADE,
        verbose_name="Yo'nalish",
        related_name="direction_videos",
    )
    video = models.URLField(verbose_name="Youtube video havola", validators=[validate_youtube_link])

    class Meta:
        verbose_name = "Yo'nalish video "
        verbose_name_plural = "Yo'nalish videolar"


class DirectionSchool(BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        verbose_name="Maktab",
        related_name="directions",
        null=True, blank=True,
    )
    direction = models.ForeignKey(
        Direction,
        verbose_name="Yo'nalish",
        related_name="direction_schools",
        on_delete=models.CASCADE,
    )
    
    direction_image = models.ImageField(
        upload_to=generate_upload_path,
        verbose_name="Yo'nalish rasmi",
        validators=[file_size],
        help_text="Rasm 5 MB dan katta bo'lishi mumkin emas.",
        null=True, blank=True,
    )
    
    description = HTMLField(null=True, blank=True, verbose_name="Tafsilot")
    founded_year = models.SmallIntegerField(null=True, blank=True, verbose_name="Ishga tushgan yili")
    student_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="O'quvchilar soni")
    teacher_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="O'qituvchilar soni")
    
    subjects = models.ManyToManyField(
        Subject,
        verbose_name="Fanlar",
        related_name="directions",
        blank=True
    )
    musical_instruments = models.ManyToManyField(
        MusicalInstrument,
        verbose_name="Musiqa asboblari",
        related_name="directions",
        blank=True
    )
    
    def __str__(self):
        return self.direction.name
    
    class Meta:
        verbose_name_plural = "Maktab yo‘nalishlari"
        constraints = [
            models.UniqueConstraint(
                fields=("school", "direction"),
                name="unique_school_direction",
            )
        ]
    
    class Meta:
        verbose_name = "Maktab yo'nalishlari "
        verbose_name_plural = "Maktab yo'nalishlari"


class Teacher(SlugifyMixin, BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="teachers",
    )
    full_name = models.CharField(max_length=500, verbose_name="F.I.O")
    slug = models.SlugField(verbose_name="Slug")
    slug_source = "full_name"
    image = models.ImageField(upload_to=generate_upload_path, verbose_name="Rasm", validators=[file_size], 
                              help_text="Rasm 5 MB dan katta bo'lishi mumkin emas.")
    
    directions = models.ManyToManyField(
        Direction,
        verbose_name="Yo'nalishlar",
        related_name="teachers",
        blank=True,
    )
    subject = models.ForeignKey(
        Subject,
        verbose_name="Dars o'tadigan Fan",
        related_name="teachers",
        on_delete=models.CASCADE,
        null=True, blank=True,
    )
    experience_years = models.PositiveIntegerField(null=True, blank=True, verbose_name="Tajribasi", help_text="Yil")
    
    def __str__(self):
        return self.full_name
    
    class Meta:
        verbose_name = "O'qituvchi "
        verbose_name_plural = "O'qituvchilar"
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'slug'],
                name='unique_teacher_school_slug',
            )
        ]


class TeacherExperience(BaseModel):
    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE,
        verbose_name="O'qituvchi",
        related_name="experiences",
    )
    
    title = models.CharField(max_length=255, verbose_name="Lavozimi")
    start_date = models.DateField(verbose_name="Boshlanish sanasi", null=True, blank=True)
    end_date = models.DateField(verbose_name="Tugash sanasi", null=True, blank=True)
    
    def __str__(self):
        return f"{self.teacher.full_name} - {self.title}"
    
    class Meta:
        verbose_name = "O'qituvchi tajribasi "
        verbose_name_plural = "O'qituvchi tajribalari"


class FAQ(BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="faqs",
    )
    
    title = models.CharField(max_length=255, verbose_name="Savol")
    description = models.TextField(verbose_name="Javob")
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "FAQ "
        verbose_name_plural = "FAQ"


class Vacancy(SlugifyMixin, BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="vacancies",
    )
    
    title = models.CharField(max_length=255, verbose_name="Lavozim nomi")
    slug = models.SlugField(verbose_name="Slug")
    description = models.TextField(verbose_name="Tafsilot")
    salary = models.CharField(max_length=255, verbose_name="Maosh", null=True, blank=True)
    requirements = models.CharField(max_length=255, verbose_name="Talablar", null=True, blank=True)
    location = models.CharField(max_length=255, verbose_name="Joylashuv", null=True, blank=True)
    
    VACANCY_TYPES = [
        ('full_time', "To'la ish kuni"),
        ('part_time', "Yarim ish kuni"),
        ('contract', "Shartnoma asosida"),
        ('internship', "Amaliyot"),
        ('remote', "Masofaviy ish"),
    ]
    
    type = models.CharField(
        max_length=50,
        choices=VACANCY_TYPES,
        default='full_time',
        verbose_name="Ish turi"
    )
    
    # SlugifyMixin configuration
    slug_field = 'slug'
    slug_source = 'title'
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Vakansiya "
        verbose_name_plural = "Vakansiyalar"
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'slug'],
                name='unique_vacancy_school_slug',
            )
        ]


class Staff(SlugifyMixin, BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="staffs",
    )
    
    full_name = models.CharField(max_length=500, verbose_name="F.I.O")
    slug = models.SlugField(verbose_name="Slug")
    position = models.CharField(max_length=255, verbose_name="Lavozimi")
    image = models.ImageField(
        upload_to=generate_upload_path, 
        verbose_name="Rasm", 
        validators=[file_size], 
        help_text="Rasm 5 MB dan katta bo'lishi mumkin emas."
    )
    
    # Social media links
    instagram_link = models.URLField(null=True, blank=True, verbose_name="Instagram havola")
    telegram_link = models.URLField(null=True, blank=True, verbose_name="Telegram havola")
    facebook_link = models.URLField(null=True, blank=True, verbose_name="Facebook havola")
    linkedin_link = models.URLField(null=True, blank=True, verbose_name="LinkedIn havola")
    
    experience_years = models.PositiveIntegerField(null=True, blank=True, verbose_name="Tajribasi", help_text="Yil")
    
    # SlugifyMixin configuration
    slug_field = 'slug'
    slug_source = 'full_name'
    
    def __str__(self):
        return f"{self.full_name} - {self.position}"
    
    class Meta:
        verbose_name = "Xodim "
        verbose_name_plural = "Xodimlar"
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'slug'],
                name='unique_staff_school_slug',
            )
        ]


class Leader(SlugifyMixin, BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="leaders",
    )
    
    full_name = models.CharField(max_length=500, verbose_name="F.I.O")
    slug = models.SlugField(verbose_name="Slug")
    slug_source = "full_name"
    position = models.CharField(max_length=255, verbose_name="Lavozimi")
    image = models.ImageField(
        upload_to=generate_upload_path, 
        verbose_name="Rasm", 
        validators=[file_size], 
        help_text="Rasm 5 MB dan katta bo'lishi mumkin emas."
    )
    description = HTMLField(null=True, blank=True, verbose_name="Tafsilot")
    
    # Social media links
    phone_number = models.CharField(max_length=255, null=True, blank=True, verbose_name="Telefon raqami")
    email = models.EmailField(null=True, blank=True, verbose_name="Email")
    instagram_link = models.URLField(null=True, blank=True, verbose_name="Instagram havola")
    telegram_link = models.URLField(null=True, blank=True, verbose_name="Telegram havola")
    facebook_link = models.URLField(null=True, blank=True, verbose_name="Facebook havola")
    linkedin_link = models.URLField(null=True, blank=True, verbose_name="LinkedIn havola")
    
    working_days = models.CharField(max_length=255, null=True, blank=True, verbose_name="Ish kunlari")
    
    # SlugifyMixin configuration
    slug_field = 'slug'
    slug_source = 'full_name'
    
    def __str__(self):
        return f"{self.full_name} - {self.position}"
    
    class Meta:
        verbose_name = "Rahbar "
        verbose_name_plural = "Rahbarlar"
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'slug'],
                name='unique_leader_school_slug',
            )
        ]

        

class TimeTable(BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="time_tables",
    )
    
    title = models.CharField(max_length=255, verbose_name="Sinf")
    file = models.FileField(
        upload_to=generate_upload_path,
        verbose_name="O'quv reja",
        null=True, blank=True,
        validators=[file_size_50, FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="Fayl 50 MB dan katta bo'lishi mumkin emas. Fayl PDF formatida bo'lishi kerak."
    )
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "O'quv reja "
        verbose_name_plural = "O'quv reja"
        ordering = ['title']


class DocumentCategory(SlugifyMixin, BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="document_categories",
    )
    name = models.CharField(max_length=255, verbose_name="Kategoriya nomi")
    slug = models.SlugField(verbose_name="Slug")
    
    slug_source = "name"
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Hujjat kategoriyasi "
        verbose_name_plural = "Hujjat kategoriyalari"
        
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'slug'],
                name='unique_document_category_school_slug',
            )
        ]


class Document(BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="documents",
    )
    category = models.ForeignKey(
        DocumentCategory, on_delete=models.CASCADE,
        verbose_name="Kategoriya",
        related_name="documents"
    )
    title = models.CharField(max_length=255, verbose_name="Hujjat nomi")
    file = models.FileField(
        upload_to=generate_upload_path,
        verbose_name="Fayl",
        validators=[file_size_50],
        help_text="Fayl 50 MB dan katta bo'lishi mumkin emas."
    )
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Hujjat "
        verbose_name_plural = "Hujjatlar"
        

HONOR_TYPES = [
    ('student', 'Talaba'),
    ('teacher', 'O\'qituvchi'),
    ('staff', 'Xodim'),
    ('leader', 'Rahbar'),
]


class Honors(SlugifyMixin, BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="honors",
    )
    
    image = models.ImageField(
        upload_to=generate_upload_path,
        verbose_name="Rasm",
        validators=[file_size],
        help_text="Rasm 5 MB dan katta bo'lishi mumkin emas."
    )
    full_name = models.CharField(max_length=255, verbose_name="F.I.O")
    slug = models.SlugField(verbose_name="Slug")
    slug_source = "full_name"
    
    type = models.CharField(
        max_length=50,
        choices=HONOR_TYPES,
        default='student', 
        verbose_name="Kim?"
    )
    description = HTMLField(verbose_name="Tafsilot")
     
    email = models.EmailField(null=True, blank=True, verbose_name="Email")
    phone_number = models.CharField(max_length=255, null=True, blank=True, verbose_name="Telefon raqami")
    
    def __str__(self):
        return self.full_name
    
    class Meta:
        verbose_name = "Faxrimiz "
        verbose_name_plural = "Faxrlarimiz"
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'slug'],
                name='unique_honors_school_slug',
            )
        ]


class HonorAchievements(BaseModel):
    honor = models.ForeignKey(
        Honors, on_delete=models.CASCADE,
        verbose_name="Hojat",
        related_name="achievements",
    )
    year = models.PositiveIntegerField(verbose_name="Yil")
    description = models.TextField(verbose_name="Tafsilot")
    address = models.CharField(max_length=255, verbose_name="Manzil")
    
    def __str__(self):
        return f"{self.honor.full_name} - {self.year}"
    
    class Meta:
        verbose_name = "Yutuq "
        verbose_name_plural = "Yutuqlar"


class ContactForm(BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="contact_forms",
    )
    full_name = models.CharField(max_length=255, verbose_name="F.I.O")
    phone_number = models.CharField(max_length=255, verbose_name="Telefon raqami")
    message = models.TextField(verbose_name="Xabar")
    
    def __str__(self):
        return f"{self.full_name} - {self.created_at}"
    
    class Meta:
        verbose_name = "Aloqa so'rovi "
        verbose_name_plural = "Aloqa so'rovlari"
        ordering = ['-created_at']
    

class Comments(BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="comments",
    )
    image = models.ImageField(
        upload_to=generate_upload_path,
        verbose_name="Rasm",
        validators=[file_size],
        help_text="Rasm 5 MB dan katta bo'lishi mumkin emas."
    )
    full_name = models.CharField(max_length=255, verbose_name="F.I.O")
    rating = models.PositiveIntegerField(verbose_name="Reyting")
    comment = models.TextField(verbose_name="Izoh")
    
    def __str__(self):
        return self.full_name
    
    class Meta:
        verbose_name = "Izoh "
        verbose_name_plural = "Izohlar"
        ordering = ['-created_at']
    

class EduInfo(BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="edu_infos",
    )
    title = models.CharField(max_length=255, verbose_name="Sarlavha")
    description = HTMLField(verbose_name="Tafsilot")
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Ta'limga oid ma'lumotlar "
        verbose_name_plural = "Ta'limga oid ma'lumotlar"


class EmailSubscription(BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="email_subscriptions",
    )
    email = models.EmailField(verbose_name="Email")
    
    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = "Email obunachilar "
        verbose_name_plural = "Email obunachilar"


class SiteSettings(BaseModel):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Maktab",
        related_name="site_settings",
    )
    school_life = models.CharField(max_length=500, verbose_name="Maktabimiz hayoti", null=True, blank=True)
    directions = models.CharField(max_length=500, verbose_name="Bizning yo'nalishlar", null=True, blank=True)
    numbers = models.CharField(max_length=500, verbose_name="Biz raqamlarda", null=True, blank=True)
    teachers = models.CharField(max_length=500, verbose_name="Maktabimiz o'qituvchilari", null=True, blank=True)
    honors = models.CharField(max_length=500, verbose_name="Maktabimiz faxrlari", null=True, blank=True)
    news = models.CharField(max_length=500, verbose_name="Yangiliklar", null=True, blank=True)
    gallery = models.CharField(max_length=500, verbose_name="Galereya", null=True, blank=True)
    contact = models.CharField(max_length=500, verbose_name="Bog'lanish", null=True, blank=True)
    comments = models.CharField(max_length=500, verbose_name="Mashxurlar biz haqimizda", null=True, blank=True)
    faqs = models.CharField(max_length=500, verbose_name="Ko'p beriladigan savollar", null=True, blank=True)
    leaders = models.CharField(max_length=500, verbose_name="Rahbariyat/Xodimlar/O'qituvchilar", null=True, blank=True)
    vacancies = models.CharField(max_length=500, verbose_name="Bo'sh ish o'rinlari", null=True, blank=True)
    documents = models.CharField(max_length=500, verbose_name="Hujjatlar", null=True, blank=True)
    timetables = models.CharField(max_length=500, verbose_name="O'quv reja", null=True, blank=True)
    edu_infos = models.CharField(max_length=500, verbose_name="Ta'limga oid ma'lumotlar", null=True, blank=True) 
    events = models.CharField(max_length=500, verbose_name="Tadbirlar", null=True, blank=True)
    resources = models.CharField(max_length=500, verbose_name="Resurslar", null=True, blank=True)
    culture_services = models.CharField(max_length=500, verbose_name="Madaniy xizmatlar tavsifi", null=True, blank=True)
    culture_arts = models.CharField(max_length=500, verbose_name="Madaniy san'at tavsifi", null=True, blank=True)
    fine_arts = models.CharField(max_length=500, verbose_name="Tasviriy san'at tavsifi", null=True, blank=True)

    def __str__(self):
        return "Maktab text tavsilotlar"
    
    class Meta:
        verbose_name = "Maktab text tavsilotlar"
        verbose_name_plural = "Maktab text tavsilotlar"

# Signal to create default instances when a new School is created
@receiver(post_save, sender=School)
def create_school_defaults(sender, instance, created, **kwargs):
    """
    Create default instances and set default values when a new School is created.
    """
    if created:
        # Set default values for the school if not provided
        if not instance.capacity:
            instance.capacity = 0
        if not instance.student_count:
            instance.student_count = 0
        if not instance.teacher_count:
            instance.teacher_count = 0
        if not instance.direction_count:
            instance.direction_count = 0
        if not instance.class_count:
            instance.class_count = 0
        
        # Save the instance with default values
        instance.save()
        
        # Create hierarchical menu structure in correct order
        # Using ordered list instead of dictionary to maintain order
        menu_structure = [
            {
                "title": "Maktab",
                "url": "#",
                "children": [
                    {"title": "Maktab haqida", "url": "#"},
                    {"title": "Rahbariyat va o'qituvchilar xodimlar", "url": "#"},
                    {"title": "Bo'sh ish o'rinlari", "url": "#"},
                ]
            },
            {
                "title": "Faoliyat",
                "url": "#",
                "children": [
                    {"title": "Yo'nalishlar", "url": "#"},
                    {"title": "Tadbirlar", "url": "#"},
                    {"title": "Tanlov va festivallar", "url": "#"},
                    {"title": "Maktabimiz faxrlariz", "url": "#"},
                    {"title": "Mahorat darslari", "url": "#"},
                ]
            },
            {
                "title": "Ta'lim jarayoni",
                "url": "#",
                "children": [
                    {"title": "O'quv reja va dastur", "url": "#"},
                    {"title": "Ta'limga oid ma'lumotlar", "url": "#"},
                    {"title": "Resurslar (🔗 YouTube, PDF darsliklar)", "url": "#"},
                ]
            },
            {
                "title": "Matbuot",
                "url": "#",
                "children": [
                    {"title": "Yangiliklar va e'lonlar", "url": "#"},
                    {"title": "Media (rasm va videolar)", "url": "#"},
                ]
            },
            {
                "title": "Hujjatlar",
                "url": "#",
                "children": [
                    {"title": "Rasmiy hujjatlar", "url": "#"},
                    {"title": "Ochiq ma'lumotlar", "url": "#"},
                ]
            },
            {
                "title": "Tijoriy bo'lim",
                "url": "#",
                "children": [
                    {"title": "Madaniy xizmatlar", "url": "#"},
                    {"title": "Amaliy san'at", "url": "#"},
                    {"title": "Tasviriy san'at", "url": "#"},
                ]
            },
            {
                "title": "Bog'lanish",
                "url": "#",
                "children": []
            }
        ]
        
        # Create menu items in correct order
        for menu_data in menu_structure:
            # Create parent menu item
            parent_menu = Menu.objects.create(
                school=instance,
                title=menu_data["title"],
                url=menu_data["url"],
                parent=None
            )
            
            # Create child menu items
            for child_data in menu_data["children"]:
                Menu.objects.create(
                    school=instance,
                    title=child_data["title"],
                    url=child_data["url"],
                    parent=parent_menu
                )
        
        # Create TimeTable instances for the new school with translations
        
        time_tables = [
            {'uz': '1-sinflar', 'ru': '1-классы', 'en': '1-classes'},
            {'uz': '2-sinflar', 'ru': '2-классы', 'en': '2-classes'},
            {'uz': '3-sinflar', 'ru': '3-классы', 'en': '3-classes'},
            {'uz': '4-sinflar', 'ru': '4-классы', 'en': '4-classes'},
            {'uz': '5-sinflar', 'ru': '5-классы', 'en': '5-classes'},
            {'uz': '6-sinflar', 'ru': '6-классы', 'en': '6-classes'},
            {'uz': '7-sinflar', 'ru': '7-классы', 'en': '7-classes'},
            {'uz': '8-sinflar', 'ru': '8-классы', 'en': '8-classes'},
            {'uz': '9-sinflar', 'ru': '9-классы', 'en': '9-classes'},
        ]
        
        for time_table in time_tables:
            TimeTable.objects.create(
                school=instance,
                title=time_table['uz'],
                title_uz=time_table['uz'],
                title_ru=time_table['ru'],
                title_en=time_table['en']
            )
        
        # Create default SiteSettings instance for the new school
        SiteSettings.objects.create(
            school=instance,
            school_life="Maktabimiz hayoti haqida ma'lumot",
            directions="Bizning yo'nalishlar haqida ma'lumot",
            numbers="Maktab raqamlari haqida ma'lumot",
            teachers="O'qituvchilarimiz haqida ma'lumot",
            honors="Maktabimiz faxrlari haqida ma'lumot",
            news="Yangiliklar bo'limi haqida ma'lumot",
            gallery="Galereya bo'limi haqida ma'lumot",
            contact="Bog'lanish bo'limi haqida ma'lumot",
            comments="Izohlar bo'limi haqida ma'lumot",
            faqs="Ko'p beriladigan savollar haqida ma'lumot",
            leaders="Rahbariyat bo'limi haqida ma'lumot",
            vacancies="Vakansiyalar bo'limi haqida ma'lumot",
            documents="Hujjatlar bo'limi haqida ma'lumot",
            timetables="O'quv reja bo'limi haqida ma'lumot",
            edu_infos="Ta'lim ma'lumotlari bo'limi haqida ma'lumot",
            events="Tadbirlar bo'limi haqida ma'lumot",
            resources="Resurslar bo'limi haqida ma'lumot",
            culture_services="Madaniy xizmatlar haqida ma'lumot",
            culture_arts="Madaniy san'at haqida ma'lumot",
            fine_arts="Tasviriy san'at haqida ma'lumot"
        )