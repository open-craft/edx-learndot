"""
Django app configuration
"""

from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig
from django.conf import settings


class LearndotIntegrationConfig(AppConfig):
    """
    Configures edxlearndot as a Django app
    """
    name = 'edxlearndot'
    verbose_name = "edX Learndot Integration"

    def ready(self):
        import edxlearndot.signals  # pylint: disable=unused-variable

        from edxlearndot.settings import plugin_settings
        plugin_settings(settings)
