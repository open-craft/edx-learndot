"""
Django settings required for Learndot integration
"""

from __future__ import absolute_import, unicode_literals

import os


def plugin_settings(settings):
    """
    The integration requires two settings: an API key and a base URL.
    """

    if hasattr(settings, "ENV_TOKENS"):
        settings.LEARNDOT_API_BASE_URL = settings.ENV_TOKENS.get(
            "LEARNDOT_API_BASE_URL",
            os.environ.get("LEARNDOT_API_BASE_URL", "")
        )

        settings.LEARNDOT_API_KEY = settings.AUTH_TOKENS.get(
            "LEARNDOT_API_KEY",
            os.environ.get("LEARNDOT_API_BASE_URL", "")
        )
    else:
        settings.LEARNDOT_API_BASE_URL = os.environ.get("LEARNDOT_API_BASE_URL", "")
        settings.LEARNDOT_API_KEY = os.environ.get("LEARNDOT_API_KEY", "")
