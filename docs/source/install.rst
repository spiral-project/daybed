Installing Daybed
=================

Daybed has the following requirements:

- A Python_ 2.6, 2.7, 3.x or PyPy_ installation
- A CouchDB_ or Redis_ server instance running

Daybed comes with a Makefile to simplify your life when developing. To install
daybed in your current virtualenv and get started, just run::

    $ make install

Then, running the test suite is a good way to check that everything is going
well, and is correctly installed. You can run them with::

    $ make tests

The test suite will run all the available tests for every supported Python
environment. You can check the current build status
`on Travis <https://travis-ci.org/spiral-project/daybed>`_.

Installation on \*nix systems
-----------------------------

Standard installation
~~~~~~~~~~~~~~~~~~~~~

First, make sure you have CouchDB_ installed on your system.

.. note::

   If you're running OSX, you can use Homebrew_ to install
   Daybed required dependencies::

       $ brew install python couchdb

   Make sure you follow any extra setup instruction provided by Homebrew
   for these packages.

It's highly recommended to create and use a Python virtualenv_ local to the
project::

    $ virtualenv `pwd`/.venv
    $ source .venv/bin/activate

Now, install Daybed's Python dependencies in this venv::

    $ make install

Don't forget to start your CouchDB_ server instance::

    $ couchdb

Then start the Daybed server::

    $ make serve

Development installation
~~~~~~~~~~~~~~~~~~~~~~~~

If you start hacking on Daybed, a good practice is to ensure the tests keep
passing for all supported Python environments::

    $ make tests

.. note::

    OSX users can install all supported Python platforms using this Homebrew
    command::

       $ brew install python python3 pypy couchdb

Once you're all set, keep on reading for :doc:`using daybed <usage>`.


Using Docker images
-------------------

Docker_ allows you to easily run a Daybed instance, locally or in
production.

Two steps setup
~~~~~~~~~~~~~~~

.. note::

    We use Docker links, available in version 0.11+.

Run a CouchDB_ instance::

    $ sudo docker run --name couchdb klaemo/couchdb

Run a *Daybed* container linked to the previous one::

    $ sudo docker run --link=couchdb:couchdb --publish=8000:8000 makinacorpus/daybed

Test it !::

    $ curl http://localhost:8000

Runtime parameters
~~~~~~~~~~~~~~~~~~

A number of environment variables can be set at runtime, to control the backend
connection for instance::

    $ sudo docker run ... --env BACKEND_DB_NAME=mydb ...

See the ``Dockerfile`` file for a complete list of variables, and their default
value.

Custom configuration
~~~~~~~~~~~~~~~~~~~~

In order to run the container with a custom configuration file. Just create
a file ``production.ini`` in a custom folder (e.g. ``/myconf``), and mount it
this way::

    $ sudo docker run ... --volume=/myconf:/opt/apps/daybed/conf ...


Build the image from sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

From the repository folder::

    $ make clean
    $ sudo docker build -t daybed .


.. _CouchDB: http://couchdb.apache.org/
.. _Redis: http://redis.io
.. _Homebrew: http://brew.sh/
.. _Python: http://python.org/
.. _PyPy: http://pypy.org/
.. _Mono: http://www.mono-project.com/
.. _virtualenv: http://virtualenv.readthedocs.org/
.. _Docker: http://docker.io
