from django.urls import path

from apps.profiles.views import CompanyProfileListCreate, UserProfileListCreate, UserProfileDestroy, CompanyProfileDestroy, AutocompleteUserList, AutocompleteCompanyList

urlpatterns = [
    path('user_profiles/<uuid:pk>/',
         UserProfileDestroy.as_view(), name='user_profile_destroy'),
    path('user_profiles/', UserProfileListCreate.as_view(),
         name='user_profiles'),
    path('company_profiles/', CompanyProfileListCreate.as_view(),
         name='company_profiles'),
    path('company_profiles/<uuid:pk>/', CompanyProfileDestroy.as_view(), name='company_profile_destroy'),
    path('autocomplete_user/', AutocompleteUserList.as_view(), name='autocomplete_user'),
    path('autocomplete_company/', AutocompleteCompanyList.as_view(), name='autocomplete_company'),
]
