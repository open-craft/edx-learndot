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

SECRET_KEY = "insecure-secret-key"
