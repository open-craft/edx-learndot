############
edx-learndot
############

***********
What is it?
***********

A Django app for integrating `Open edX`_ and `Learndot`_.

********
Features
********

Right now its entire raison d'être is automatically updating Learndot
enrolment records when a learner passes an edX course.

************
Installation
************

Support
-------

.. list-table::
  :widths: 80 20
  :header-rows: 1

  * - edX Platform Release
    - Tag
  * - Juniper
    - v0.2
  * - Ironwood
    - v0.1

Prerequisites
-------------

* A working Open edX installation.

Installing
----------

If you're running a Docker devstack, you can clone the repo into your
``src`` tree and add this to your ``lms`` command in your Docker compose
file::

  pip install -e /edx/src/edx-learndot

Then you'll need to migrate your database to support storing the
mappings between Learndot components and edX courses.

*************
Configuration
*************

Configuring access to the Learndot API
--------------------------------------

This enables your edX installation to interact with the `Learndot v2
API`_.

There are two Django settings you'll need to add:

* Put your Learndot Enterprise base URL (e.g. ``https://your-sandbox.trainingrocket.com/``) in
  ``settings.LEARNDOT_API_BASE_URL``.

* Put your Learndot API key in ``settings.LEARNDOT_API_KEY``.

These can of course be added via common Open edX configuration idioms, for example in
``lms.env.json`` and ``lms.auth.json`` respectively, or in Ansible variables::

    EDXAPP_ENV_EXTRA:
         LEARNDOT_API_BASE_URL: https://your-sandbox.trainingrocket.com/
    EDXAPP_AUTH_EXTRA:
        LEARNDOT_API_KEY: "your-key-here"

************************
Managing the integration
************************

The Django model ``edxlearndot.models.CourseMapping`` links edX
courses to Learndot components. To maintain these records, use the
Django admin.

********************
Updating enrollments
********************

When a learner passes a linked edX course, the signal fired triggers
the automatic update of that learner's Learndot enrollment for the
linked component.

If for some reason this fails, Learndot enrollments can be updated in
bulk at any time with the ``update_learndot_enrolments`` Django management
command, e.g.::

  manage.py lms update_learndot_enrolments

**************************
Running edx-learndot tests
**************************

The test suite uses tox. If you want to test using the master branch of edx-platform, you can just
run ``tox``. To test with another release, or another fork, set one or both of the ``OPENEDX_REPO``
and ``OPENEDX_RELEASE`` environment variables, e.g.::

  OPENEDX_REPO=https://github.com/example/edx-platform OPENEDX_RELEASE=master tox


.. _Open edX: https://open.edx.org/
.. _Learndot: https://www.learndot.com
.. _Learndot v2 API: https://trainingrocket.atlassian.net/wiki/spaces/DOCS/pages/74416315/API+V2
