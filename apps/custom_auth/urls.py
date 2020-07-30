from django.urls import path

from apps.custom_auth.views import (CreateUserView, UserDetail, exchange_token,
                                    test_view, ApplicationsView)

urlpatterns = [
    path('signup/', CreateUserView.as_view(), name='signup'),
    # path('loggedin/', UserDetail.as_view(), name='loggedin')
    # path('loggedin/', exchange_token, name='loggedin'),
    path('loggedin/', test_view, name='test'),
    path('applications/', ApplicationsView.as_view(), name='applications')
]
