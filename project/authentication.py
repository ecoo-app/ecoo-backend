from oauth2_provider.contrib.rest_framework import OAuth2Authentication


class ImprovedOAuth2Authentication(OAuth2Authentication):
    """
    OAuth 2 authentication backend using `django-oauth-toolkit`
    """

    def authenticate(self, request):
        """
        Returns two-tuple of (user, token) if authentication succeeds,
        or None otherwise.
        """

        response = super().authenticate(request)

        if response is None:
            request.oauth2_error = None
            return None

        return response
