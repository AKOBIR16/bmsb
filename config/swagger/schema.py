from django.urls import include, path, re_path
from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from drf_yasg.generators import OpenAPISchemaGenerator


# Sayt API'si. Monitoring endpointlari bu ro'yxatga kirmaydi - ular
# `config/swagger/monitoring.py` dagi alohida sxemada hujjatlashtirilgan.
site_api_patterns = [
    path('api/', include('apps.main.urls')),
    path('api/', include('apps.common.urls')),
    path('api/news/', include('apps.news.urls')),
    path('api/media/', include('apps.media.urls')),
    path('api/resources/', include('apps.resource.urls')),
    path('api/services/', include('apps.service.urls')),
]


class BothHttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ['https', 'http']
        
        # Define School header parameter (OpenAPI Parameter object)
        school_param = openapi.Parameter(
            name='School',
            in_=openapi.IN_HEADER,
            type=openapi.TYPE_STRING,
            description='Maktab subdomain (toshken1, mk1)',
            required=False,
            default='mk1'
        )
        
        # Iterate over all paths and operations
        if schema.paths:
            for path_name, path_item in schema.paths.items():
                # path_item is a dict-like object with HTTP method keys (get, post, etc.)
                for method_name, operation in list(path_item.items()):
                    # Skip if not an Operation object
                    if not isinstance(operation, openapi.Operation):
                        continue
                    
                    # Ensure 'parameters' key exists and is a list
                    params = list(operation.get('parameters', []))
                    
                    # Check if School header already included
                    exists = any(
                        isinstance(p, openapi.Parameter) and p.name == 'School' and p.in_ == openapi.IN_HEADER
                        for p in params
                    )
                    if not exists:
                        params.insert(0, school_param)
                        operation['parameters'] = params
        
        return schema


schema_view = get_schema_view(
    openapi.Info(
        title='Musiqa Maktablari API',
        default_version='v1',
        description='Musiqa Maktablari'
    ),
    public=True,
    patterns=site_api_patterns,
    generator_class=BothHttpAndHttpsSchemaGenerator,
    permission_classes=(permissions.AllowAny,),
)

swagger_urlpatterns = [
    re_path(
        r'^api/swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json',
    ),
    re_path(
        r'^api/swagger/$',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui',
    ),
    re_path(
        r'^api/redoc/$',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc',
    ),
]
