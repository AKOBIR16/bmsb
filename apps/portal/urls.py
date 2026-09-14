from django.urls import path

from apps.portal import views

app_name = 'portal'

urlpatterns = [
    path('stats/', views.StatsView.as_view(), name='stats'),
    path('regions/', views.RegionListView.as_view(), name='regions'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('faqs/', views.FAQListView.as_view(), name='faqs'),
    path('appeals/', views.AppealCreateView.as_view(), name='appeals'),

    path('schools/', views.SchoolListView.as_view(), name='schools'),
    path('schools/<slug:domain>/', views.SchoolDetailView.as_view(), name='school-detail'),

    path('directions/', views.DirectionListView.as_view(), name='directions'),
    path('directions/<slug:slug>/', views.DirectionDetailView.as_view(), name='direction-detail'),

    path('news/', views.NewsListView.as_view(), name='news'),
    path('news/meta/', views.NewsMetaView.as_view(), name='news-meta'),
    path('news/<int:pk>/', views.NewsDetailView.as_view(), name='news-detail'),

    path('rating/', views.RatingView.as_view(), name='rating'),
]
