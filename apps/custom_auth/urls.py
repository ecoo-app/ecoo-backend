from django.urls import path

from apps.custom_auth.views import (CreateUserView, UserDetail, exchange_token,
                                    test_view)

urlpatterns = [
    path('signup/', CreateUserView.as_view(), name='signup'),
    # path('loggedin/', UserDetail.as_view(), name='loggedin')
    # path('loggedin/', exchange_token, name='loggedin'),
    path('loggedin/', test_view, name='test'),
]
