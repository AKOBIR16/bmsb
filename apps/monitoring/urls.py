from django.urls import path

from apps.monitoring import views

app_name = 'monitoring'

urlpatterns = [
    path('overview/', views.OverviewView.as_view(), name='overview'),
    path('timeseries/', views.TimeseriesView.as_view(), name='timeseries'),
    path('regions/', views.RegionListView.as_view(), name='regions'),
    path('content-types/', views.ContentTypeListView.as_view(), name='content-types'),
    path('posts/', views.PostListView.as_view(), name='posts'),
    path('schools/', views.SchoolListView.as_view(), name='schools'),
    path('schools/<str:domain>/', views.SchoolDetailView.as_view(), name='school-detail'),
]
