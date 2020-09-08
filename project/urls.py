""" URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static  # new
from django.contrib import admin
from django.contrib.auth import views
from django.urls import path
from django.views.generic import RedirectView, TemplateView
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)
import apps.wallet.urls as wallet_url
from two_factor.urls import urlpatterns as tf_urls
from project.mixins import AdminSiteOTPRequiredMixinRedirSetup

if not settings.DEBUG:
    admin.site.__class__ = AdminSiteOTPRequiredMixinRedirSetup


admin.site.site_header = 'ecoo-admin'
admin.site.site_title = 'ecoo-admin'

router = DefaultRouter()

router.register('', FCMDeviceAuthorizedViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/wallet/', include('apps.wallet.urls')),
    path('api/auth/', include('apps.custom_auth.urls')),
    path('api/currency/', include('apps.currency.urls')),
    path('api/profiles/', include('apps.profiles.urls')),
    path('api/verification/', include('apps.verification.urls')),
    path('api/oauth/', include('rest_framework_social_oauth2.urls')),
    path('', include(tf_urls)),
    # path('social/', include('social_django.urls', namespace='social')),
    path('api/devices/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
