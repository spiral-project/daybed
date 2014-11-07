#!/usr/bin/env python
import os
import sys

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
PY2 = sys.version_info[0] == 2
PY26 = sys.version_info[:2] == (2, 6)

NAME = 'daybed'
DESCRIPTION = 'Form validation and data storage API.'
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()
VERSION = open(os.path.join(here, 'VERSION')).read().strip()
AUTHOR = u'Spiral Project'
EMAIL = u'spiral-project@lolnet.org'
URL = 'https://{name}.readthedocs.org/'.format(name=NAME)
CLASSIFIERS = ['Development Status :: 4 - Beta',
               'License :: OSI Approved :: BSD License',
               'Programming Language :: Python :: 2.7',
               'Programming Language :: Python :: 2.6',
               'Topic :: Internet :: WWW/HTTP',
               'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
               'Framework :: Pyramid']
KEYWORDS = ['web',
            'cornice',
            'couchdb',
            'colander',
            'pyramid',
            'pylons',
            'api',
            'form',
            'angular',
            'backbone',
            'storage']
PACKAGES = [NAME.replace('-', '_')]
REQUIREMENTS = [
    'CouchDB',
    'colander',
    'cornice',
    'elasticsearch',
    'hiredis',
    'koremutake',
    'pyramid',
    'pyramid_hawkauth',
    'pyramid_multiauth',
    'redis',
    'setuptools',
    'six',
]
DEPENDENCY_LINKS = [
    'https://github.com/Natim/couchdb-python/tarball/'
    'authorization_header_py26#egg=CouchDB-0.10.1dev',
    'https://github.com/ametaireau/koremutake/tarball/'
    'py3k#egg=koremutake-1.1.0',
]
ENTRY_POINTS = {
    'paste.app_factory': [
        'main = daybed:main',
    ]}


if PY26:
    REQUIREMENTS.append('ordereddict')

if __name__ == '__main__':  # Don't run setup() when we import this module.
    setup(name=NAME,
          version=VERSION,
          description=DESCRIPTION,
          long_description=README,
          classifiers=CLASSIFIERS,
          keywords=' '.join(KEYWORDS),
          author=AUTHOR,
          author_email=EMAIL,
          url=URL,
          license='BSD',
          packages=PACKAGES,
          include_package_data=True,
          zip_safe=False,
          install_requires=REQUIREMENTS,
          dependency_links=DEPENDENCY_LINKS,
          entry_points=ENTRY_POINTS)
