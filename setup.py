#!/usr/bin/env python
import os
import sys

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
PY2 = sys.version_info[0] == 2

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
REQUIREMENTS = ['setuptools',
                'six',
                'pyramid',
                'cornice',
                'colander',
                'pyramid_persona',
                'pyramid_multiauth',
                'pyramid_mako']
DEPENDENCY_LINKS = []
ENTRY_POINTS = {
    'paste.app_factory': [
        'main = daybed:main',
    ]}

if PY2:
    REQUIREMENTS.append('CouchDB')
else:
    # Python3 version for couchdb
    REQUIREMENTS.append('CouchDB==0.9dev')
    DEPENDENCY_LINKS.append(
        'https://github.com/lilydjwg/couchdb-python3/zipball/master'
        '#egg=CouchDB-0.9dev',
    )


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
