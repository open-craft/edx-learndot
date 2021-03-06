#!/usr/bin/env python
""" Setup to allow pip installs of edx-learndot module """

from setuptools import setup, find_packages

setup(
    name='edx-learndot',
    version='0.6.0',
    description="""Django app to integrate edX with LearnDot""",
    author='OpenCraft',
    url='https://github.com/open-craft/edxlearndot',
    license='AGPL',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Framework :: Django',
        'Framework :: Django :: 2.2.13',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
    ],
    packages=find_packages(include=['edxlearndot', 'edxlearndot.*']),
    install_requires=[
        "django>=2.2",
        "edx-opaque-keys",
        "dateparser",
        "requests",
        "retrying>=1.3,<2.0",
    ],
    entry_points={
        "lms.djangoapp": [
            "edxlearndot = edxlearndot.apps:LearndotIntegrationConfig",
        ],
    }
)
