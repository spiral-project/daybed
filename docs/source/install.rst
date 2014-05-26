Installing daybed
=================

Daybed has the following requirements:

- A Python_ 2.6, 2.7, 3.x or PyPy_ installation
- A CouchDB_ server instance running

Daybed comes with a Makefile to simplify your life when developing. To install
daybed in your current virtualenv and get started, just run::

    $ make install

Then, running the test suite is a good way to check that everything is going
well, and is well installed. You can run them with::

    $ make tests

The test suite will run all the available tests for every supported Python
environment. You can check the current build status
`on Travis <https://travis-ci.org/spiral-project/daybed>`_.

Installation on *n*x systems
----------------------------

Standard installation
~~~~~~~~~~~~~~~~~~~~~

First, ensure having CouchDB_ installed on your system.

.. note::

   If you're running OSX, you can use Homebrew_ to install
   daybed required dependencies::

       $ brew install python couchdb

   Take care of following any supplementary setup instruction provided by brew
   for these packages.

It's highly recommended to create & use a Python virtualenv_ local to the
project::

    $ virtualenv `pwd`/.venv
    $ source .venv/bin/activate

Now, install daybed's Python dependencies in this venv::

    $ make install

Don't forget to start your CouchDB_ server instance::

    $ couchdb

Then start the daybed server::

    $ make serve

Development installation
~~~~~~~~~~~~~~~~~~~~~~~~

If you start hacking on daybed, a good practice is to ensure the tests keep
passing for all supported Python environments::

    $ make tests

.. note::

    OSX users can install all supported Python platforms using this brew
    command::

       $ brew install python python3 pypy couchdb

Once you're all set, keep on reading for :doc:`using daybed <usage>`.

.. _CouchDB: http://couchdb.apache.org/
.. _Homebrew: http://brew.sh/
.. _Python: http://python.org/
.. _PyPy: http://pypy.org/
.. _Mono: http://www.mono-project.com/
.. _virtualenv: http://virtualenv.readthedocs.org/
