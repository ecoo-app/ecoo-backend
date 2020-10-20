from django.urls import path

from apps.custom_auth.views import (CreateUserView, UserDetail, exchange_token, ApplicationsView)

urlpatterns = [
    path('signup/', CreateUserView.as_view(), name='signup'),
    # path('loggedin/', UserDetail.as_view(), name='loggedin')
    # path('loggedin/', exchange_token, name='loggedin'),
    path('applications/', ApplicationsView.as_view(), name='applications')
]
