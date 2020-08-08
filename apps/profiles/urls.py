from django.urls import path

from apps.profiles.views import CompanyProfileListCreate, UserProfileListCreate

urlpatterns = [
    path('user_profiles/', UserProfileListCreate.as_view(),
         name='user_profiles'),
    path('company_profiles/', CompanyProfileListCreate.as_view(),
         name='company_profiles'),
]
