from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.permissions import AllowAny
from apps.common.mixins import IsActiveFilterMixin
from apps.main.serializers.school import SchoolSerializer, SchoolSubdomainSerializer
from apps.main.models import School
from django.http import Http404


class CheckSchoolView(APIView):
    def get(self, request):
        res = False
        school_header = request.META.get('HTTP_SCHOOL', None)
        if school_header and school_header.strip():
            # Use the header value as subdomain
            subdomain = school_header.lower().strip()
            request.subdomain = subdomain
            
            
            try:
                school = School.objects.get(domain=subdomain)
                if school.is_active:
                    res = True
                else:
                    res = False
            except School.DoesNotExist:
                res = False
            except Http404:
                # Re-raise Http404 exceptions to properly display 404 pages
                res = False
            except Exception as e:
                # Only catch other exceptions, not Http404
                print(f"Unexpected error in CheckSchoolView: {e}")
                res = False
        return Response({'school': res})


class SchoolView(IsActiveFilterMixin, RetrieveAPIView):
    serializer_class = SchoolSerializer
    permission_classes = []
    
    def get(self, request):
        if not request.school and not request.subdomain:
            return Response({'detail': None})
        
        serializer = SchoolSerializer(request.school)
        return Response(serializer.data)


class SchoolSubdomainListView(IsActiveFilterMixin, ListAPIView):
    queryset = School.objects.all()
    serializer_class = SchoolSubdomainSerializer
    permission_classes = [AllowAny]