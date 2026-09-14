"""
Portal (e-bmsm.uz) API uchun alohida Swagger sxemasi.

Portal endpointlari `School` headeriga muhtoj emas va barcha maktablar
kesimida ishlaydi, shuning uchun ular sayt API'sidan alohida hujjatlanadi.
"""

from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from rest_framework import permissions


class PortalSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ['https', 'http']
        return schema


portal_patterns = [
    path('api/portal/', include('apps.portal.urls')),
]


portal_schema_view = get_schema_view(
    openapi.Info(
        title='BMSM Portal API',
        default_version='v1',
        description=(
            "e-bmsm.uz bosh sayti uchun API: barcha maktablar, yo'nalishlar, "
            "yangiliklar va reyting.\n\n"
            "`School` headeri talab qilinmaydi. Til `Accept-Language` orqali: uz, ru, en."
        ),
    ),
    public=True,
    patterns=portal_patterns,
    generator_class=PortalSchemaGenerator,
    permission_classes=(permissions.AllowAny,),
)


portal_swagger_urlpatterns = [
    re_path(
        r'^api/portal/swagger(?P<format>\.json|\.yaml)$',
        portal_schema_view.without_ui(cache_timeout=0),
        name='portal-schema-json',
    ),
    re_path(
        r'^api/portal/swagger/$',
        portal_schema_view.with_ui('swagger', cache_timeout=0),
        name='portal-schema-swagger-ui',
    ),
    re_path(
        r'^api/portal/redoc/$',
        portal_schema_view.with_ui('redoc', cache_timeout=0),
        name='portal-schema-redoc',
    ),
]
