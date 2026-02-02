from django.urls import path
from .views.menu import MenuView
from .views.school import SchoolView, CheckSchoolView, SchoolSubdomainListView
from .views.school_life import SchoolLifeView
from .views.banner import BannerListView
from .views.direction import DirectionListView, DirectionDetailView
from .views.teacher import TeacherListView, TeacherDetailView
from .views.faq import FAQListView
from .views.vacancy import VacancyListView
from .views.document import DocumentListView, DocumentCategoryListView
from .views.timetable import TimeTableListView
from .views.staff import StaffListView
from .views.leader import LeaderListView, LeaderDetailView
from .views.honor import HonorsListView, HonorsDetailView
from .views.contact_form import ContactFormCreateView
from .views.comments import CommentsListView, CommentsDetailView
from .views.edu_info import EduInfoListView
from .views.site_settings import SiteSettingsView
from .views.email_subscription import EmailSubscriptionCreateView

urlpatterns = [
    path('menus/', MenuView.as_view(), name='menu'),
    path('banners/', BannerListView.as_view(), name='banner'),
    path('school/', SchoolView.as_view(), name='school'),
    path('school-lifes/', SchoolLifeView.as_view(), name='school-life'),
    
    # Direction endpoints
    path('directions/', DirectionListView.as_view(), name='direction-list'),
    path('directions/<slug:slug>/', DirectionDetailView.as_view(), name='direction-detail'),
    
    # Teacher endpoints
    path('teachers/', TeacherListView.as_view(), name='teacher-list'),
    path('teachers/<slug:slug>/', TeacherDetailView.as_view(), name='teacher-detail'),
    
    # FAQ endpoints
    path('faqs/', FAQListView.as_view(), name='faq-list'),
    
    # Vacancy endpoints
    path('vacancies/', VacancyListView.as_view(), name='vacancy-list'),
    
    # TimeTable endpoints
    path('timetables/', TimeTableListView.as_view(), name='timetable-list'),
    
    # Document endpoints
    path('documents/', DocumentListView.as_view(), name='document-list'),
    path('documents/categories/', DocumentCategoryListView.as_view(), name='document-category-list'),
    
    # Staff endpoints
    path('staffs/', StaffListView.as_view(), name='staff-list'),
    
    # Leader endpoints
    path('leaders/', LeaderListView.as_view(), name='leader-list'),
    path('leaders/<slug:slug>/', LeaderDetailView.as_view(), name='leader-detail'),
    
    # Honor endpoints
    path('honors/', HonorsListView.as_view(), name='honors-list'),
    path('honors/<slug:slug>/', HonorsDetailView.as_view(), name='honors-detail'),
    
    # ContactForm endpoints
    path('contact-forms/', ContactFormCreateView.as_view(), name='contact-form-create'),
    
    # Email subscription endpoints
    path('email-subscription/', EmailSubscriptionCreateView.as_view(), name='email-subscription-create'),
    
    # Comments endpoints
    path('comments/', CommentsListView.as_view(), name='comments-list'),
    path('comments/<int:id>/', CommentsDetailView.as_view(), name='comments-detail'),
    
    # EduInfo endpoint
    path('edu-infos/', EduInfoListView.as_view(), name='edu-info-list'),
    
    # SiteSettings endpoint
    path('site-text/', SiteSettingsView.as_view(), name='site-text'),
    
    # School check endpoint
    path('check-school/', CheckSchoolView.as_view(), name='check-school'),
    path('schools/list/', SchoolSubdomainListView.as_view(), name='school-list'),
]

