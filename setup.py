#!/usr/bin/env python
""" Setup to allow pip installs of edx-learndot module """

from setuptools import setup

setup(
    name='edx-learndot',
    version='0.0.1',
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
        'Programming Language :: Python :: 2.7',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
    ],
    packages=[
        'edxlearndot',
        'tests'
    ],
    install_requires=[
        "django >= 1.8, < 2.0",
        "edx-opaque-keys",
        "python-dateutil",
        "requests",
    ],
    entry_points={
        "lms.djangoapp": [
            "edxlearndot = edxlearndot.apps:LearndotIntegrationConfig",
        ],
    }
)
