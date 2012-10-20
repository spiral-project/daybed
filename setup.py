import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [
    'pyramid',
    'cornice',
    'colander',
    'couchdb',
    ]

test_requires = requires + ['lettuce', ]

setup(name='daybed',
      version='0.0',
      description='daybed',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web pyramid pylons',
      packages=find_packages(),
      dependency_links = [
        "https://github.com/mozilla-services/cornice/tarball/spore-support#egg=cornice"
      ],
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=test_requires,
      test_suite="daybed.tests",
      entry_points="""\
      [paste.app_factory]
      main = daybed:main
      """,
      )
