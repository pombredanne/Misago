from django.conf import settings
from theme import Theme

class ThemeMiddleware(object):
    def process_request(self, request):
        if not settings.INSTALLED_THEMES:
            raise ValueError('There are no themes installed!')
        request.theme = Theme(settings.INSTALLED_THEMES[0])