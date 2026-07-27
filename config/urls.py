from django.contrib import admin
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import path, include
from django.shortcuts import redirect

from config.swagger.schema import swagger_urlpatterns
from config.swagger.monitoring import monitoring_swagger_urlpatterns


urlpatterns = [
    path('', lambda request: redirect('/admin/', permanent=True)),
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),
    path('tinymce/', include('tinymce.urls')),
]   

urlpatterns += [
    path('api/', include('apps.main.urls')),
    path('api/', include('apps.common.urls')),
    path('api/news/', include('apps.news.urls')),
    path('api/media/', include('apps.media.urls')),
    path('api/resources/', include('apps.resource.urls')),
    path('api/services/', include('apps.service.urls')),
    path('api/monitoring/', include('apps.monitoring.urls')),
]

urlpatterns += swagger_urlpatterns
urlpatterns += monitoring_swagger_urlpatterns


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
                + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
