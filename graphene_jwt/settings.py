from django.conf import settings
from rest_framework.settings import APISettings


USER_SETTINGS = getattr(settings, 'JWT_GRAPHENE', None)

DEFAULTS = {
    'JWT_GRAPHENE_USER_ONLY_FIELDS': None,
    'JWT_GRAPHENE_USER_EXCLUDE_FIELDS': None,
}

IMPORT_STRINGS = (
)

api_settings = APISettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS)
