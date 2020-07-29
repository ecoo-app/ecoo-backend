from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import generics, mixins, permissions, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from oauth2_provider.models import Application
from social_django.utils import psa

from apps.custom_auth.serializers import SocialSerializer, UserSerializer, ApplicationSerializer


class CreateUserView(CreateAPIView):

    model = get_user_model()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = UserSerializer


@permission_classes([AllowAny])
def test_view(request):
    print(request)
    print(request.user)
    return JsonResponse({'foo': 'bar'})


@api_view(http_method_names=['POST'])
@permission_classes([AllowAny])
@psa()
def exchange_token(request, backend):
    serializer = SocialSerializer(data=request.data)

    if serializer.is_valid(raise_exception=True):
        # This is the key line of code: with the @psa() decorator above,
        # it engages the PSA machinery to perform whatever social authentication
        # steps are configured in your SOCIAL_AUTH_PIPELINE. At the end, it either
        # hands you a populated User model of whatever type you've configured in
        # your project, or None.
        user = request.backend.do_auth(
            serializer.validated_data['access_token'])

        if user:
            # if using some other token back-end than DRF's built-in TokenAuthentication,
            # you'll need to customize this to get an appropriate token object
            # token, _ = Token.objects.get_or_create(user=user)
            refresh = RefreshToken.for_user(user)
            # return Response({'token': token.key})
            return Response({'refresh': str(refresh), 'access': str(refresh.access_token), })

        else:
            return Response(
                {'errors': {'token': 'Invalid token'}},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserDetail(mixins.RetrieveModelMixin, generics.GenericAPIView):
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        user = self.request.user

        return Response(UserSerializer(user).data)


class ApplicationsView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    queryset = Application.objects.all()
