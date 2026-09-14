import environ
from pathlib import Path

env = environ.Env()
env.read_env('.env')

#######################################################
# --------------------- GENERAL --------------------- #
#######################################################

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = env.str('SECRET_KEY')

DEBUG = True

ALLOWED_HOSTS = ['*']


#######################################################
# --------------------- APPS --------------------- #
#######################################################

PRIORITY_APPS = [
    'jazzmin',
    'modeltranslation',
    'apps.main',
]


DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]


MY_APPS = [
    'apps.common',
    'apps.media',
    'apps.resource',
    'apps.user',
    'apps.news',
    'apps.service',
    'apps.monitoring',
    'apps.portal',
]


THIRD_APPS = [
    'mptt',
    'rest_framework',
    'drf_yasg',
    'corsheaders',
    'django_filters',
    'tinymce',
    
    
    'django_cleanup.apps.CleanupConfig',
]


INSTALLED_APPS = PRIORITY_APPS + DJANGO_APPS + MY_APPS + THIRD_APPS


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    
    'corsheaders.middleware.CorsMiddleware',
    'apps.main.middleware.SubdomainMiddleware',
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


########################################################
# --------------------- DATABASE --------------------- #
########################################################

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


##############################################################
# --------------------- REST FRAMEWORK --------------------- #
##############################################################

from .rest_framework import *


#######################################################
# --------------------- JAZZMIN --------------------- #
#######################################################

from .jazzmin import *


#######################################################
# --------------------- TINYMCE --------------------- #
#######################################################

from .tinymce import *

    
####################################################
# --------------------- I18N --------------------- #
####################################################

MODELTRANSLATION_DEFAULT_LANGUAGE = 'uz'
MODELTRANSLATION_LANGUAGES = ('uz', 'ru', 'en')
MODELTRANSLATION_FALLBACK_LANGUAGES = ('uz', 'ru', 'en')

MODELTRANSLATION_TRANSLATION_FILES = (    
    'apps.common.translation',
    'apps.main.translation',
    'apps.news.translation',
    'apps.media.translation',
    'apps.resource.translation',
    'apps.service.translation',
    'apps.portal.translation',
)


LANGUAGE_CODE = 'uz'


LANGUAGES = [
    ('uz', 'Uzbek'),
    ('en', 'English'),
    ('ru', 'Russian'),
]


LOCALE_PATHS = [
    BASE_DIR / 'locale/',
]


#########################################################
# --------------------- TIME ZONE --------------------- #
#########################################################

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True


#############################################################
# --------------------- STATIC & MEDIA -------------------- #
#############################################################

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIRS = (BASE_DIR / 'assets',)

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'


#################################################################
# --------------------- IMPORTANT SETTINGS -------------------- #
#################################################################

AUTH_USER_MODEL = 'user.User'

AUTH_GROUP_MODEL = 'auth.Group'


#############################################################
# --------------------- OTHER SETTINGS -------------------- #
#############################################################

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

NOT_ALLOWED_SUBDOMAINS = ['www', '', 'cdn', 'api', 'admin']


##########################################################
# --------------------- MONITORING -------------------- #
##########################################################

# Maktab saytlarining manzili: {domain}.{MONITORING_SITE_BASE_DOMAIN}
# `check_schools_online` komandasi va API dagi site_url shu sozlamadan foydalanadi
MONITORING_SITE_BASE_DOMAIN = env.str('MONITORING_SITE_BASE_DOMAIN', default='e-bmsm.uz')
MONITORING_SITE_SCHEME = env.str('MONITORING_SITE_SCHEME', default='https')


#######################################################
# --------------------- CELERY ---------------------- #
#######################################################

# Celery Configuration Options
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


#######################################################
# --------------------- EMAIL ----------------------- #
#######################################################

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env.str('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', 587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', True)
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL', 'noreply@bmsb.uz')

# For development, you can use console backend
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

#######################################################
# --------------------- IMGPROXY -------------------- #
#######################################################

# Imgproxy Configuration (Simple Setup)
# The imgproxy service runs in insecure mode and frontend constructs URLs directly
IMGPROXY_BASE_URL = env.str('IMGPROXY_BASE_URL', 'http://localhost:8080')