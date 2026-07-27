"""
Monitoring API uchun alohida Swagger sxemasi.

Asosiy sayt API'sidan ajratilgan: monitoring endpointlari `School` headeriga
muhtoj emas va barcha maktablar kesimida ishlaydi, shuning uchun ular alohida
hujjatda ko'rsatiladi.
"""

from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from rest_framework import permissions


class MonitoringSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ['https', 'http']
        return schema


# Sxemaga faqat shu patternlar kiradi
monitoring_patterns = [
    path('api/monitoring/', include('apps.monitoring.urls')),
]


monitoring_schema_view = get_schema_view(
    openapi.Info(
        title='BMSM Monitoring API',
        default_version='v1',
        description=(
            "Barcha bolalar musiqa va san'at maktablari bo'yicha monitoring API.\n\n"
            "Sayt API'sidan farqli o'laroq `School` headeri talab qilinmaydi - "
            "hududiy qamrov `region`, `district` va `school` parametrlari orqali "
            "boshqariladi."
        ),
    ),
    public=True,
    patterns=monitoring_patterns,
    generator_class=MonitoringSchemaGenerator,
    permission_classes=(permissions.AllowAny,),
)


monitoring_swagger_urlpatterns = [
    re_path(
        r'^api/monitoring/swagger(?P<format>\.json|\.yaml)$',
        monitoring_schema_view.without_ui(cache_timeout=0),
        name='monitoring-schema-json',
    ),
    re_path(
        r'^api/monitoring/swagger/$',
        monitoring_schema_view.with_ui('swagger', cache_timeout=0),
        name='monitoring-schema-swagger-ui',
    ),
    re_path(
        r'^api/monitoring/redoc/$',
        monitoring_schema_view.with_ui('redoc', cache_timeout=0),
        name='monitoring-schema-redoc',
    ),
]
