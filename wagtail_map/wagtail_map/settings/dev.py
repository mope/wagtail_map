from .base import *


DEBUG = True
TEMPLATE_DEBUG = True

SECRET_KEY = '6@^i3r(f$_7z9yo%0f_iu@wn_5^kqg!=)be_n#p@&2(-2n!%ug'
DATABASES['default']['PASSWORD'] = ''

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Process all tasks synchronously.
# Helpful for local development and running tests
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_ALWAYS_EAGER = True

try:
    from .local import *
except ImportError:
    pass
