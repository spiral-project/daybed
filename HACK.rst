Daybed
######

Setup
=====

::

    virtualenv --no-site-packages env
    source env/bin/activate
    python setup.py develop

Run tests
=========

Unit tests :

::

    python setup.py test -q

Functional tests :

* Install Lettuce (should be in ``requires`` ?)

::

    pip install lettuce
  

* Run !

::

    lettuce daybed/tests/features


Run server
==========

::

    pserve development.ini --reload
