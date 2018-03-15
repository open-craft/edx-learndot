"""
Django app configuration
"""

from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig
from openedx.core.djangoapps.plugins.constants import (
    ProjectType, SettingsType, PluginSettings, PluginSignals
)


class LearndotIntegrationConfig(AppConfig):
    """
    Configures edxlearndot as a Django app plugin
    """
    name = 'edxlearndot'
    verbose_name = "edX Learndot Integration"

    plugin_app = {
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.AWS: {
                    PluginSettings.RELATIVE_PATH: u'settings',
                },
                SettingsType.COMMON: {
                    PluginSettings.RELATIVE_PATH: u'settings',
                },
                SettingsType.DEVSTACK: {
                    PluginSettings.RELATIVE_PATH: u'settings',
                }
            }
        },

        PluginSignals.CONFIG: {
            ProjectType.LMS: {
                PluginSignals.RELATIVE_PATH: u'signals',
                PluginSignals.RECEIVERS: [{
                    PluginSignals.RECEIVER_FUNC_NAME: u'listen_for_passing_grade',
                    PluginSignals.SIGNAL_PATH: u'openedx.core.djangoapps.signals.signals.COURSE_GRADE_NOW_PASSED',
                }],
            }
        }
    }
