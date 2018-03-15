"""
Django admin integration
"""

from django.contrib import admin

from edxlearndot.models import CourseMapping

admin.site.register(CourseMapping)
