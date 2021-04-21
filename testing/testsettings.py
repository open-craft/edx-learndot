"""
Settings for unit tests
"""

from __future__ import absolute_import, unicode_literals

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "default.db",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
}

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "edxlearndot"
)

USE_TZ = True

SECRET_KEY = "insecure-secret-key"

LEARNDOT_API_BASE_URL = 'http://learndot/'
LEARNDOT_API_KEY = 'abc'
LEARNDOT_RETRY_WAIT_SECONDS=1
LEARNDOT_RETRY_MAX_ATTEMPTS=2
