"""
Django admin integration
"""

from django.contrib import admin

from edxlearndot.models import CourseMapping, EnrolmentStatusLog

admin.site.register(CourseMapping)
admin.site.register(EnrolmentStatusLog)
