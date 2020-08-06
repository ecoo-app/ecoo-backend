from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin

class RemoveNextMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if 'next' in request.GET:
            print('redirect')
            return HttpResponseRedirect('/account/login')

