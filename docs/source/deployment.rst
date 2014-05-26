##########
Deployment
##########

Using Docker images
===================

:notes:

    We use Docker links, available in version 0.11+.


Build the *Daybed* image :

::

    sudo docker build -t daybed .


Run a *CouchDB* instance :

::

    sudo docker run --name couchdb klaemo/couchdb


Run *Daybed* linked to *CouchDB* :

::

    sudo docker run --link couchdb:couchdb daybed


Test it !

::

    curl http://localhost:8000


In order to run the container with a custom configuration file. Just create
a file ``production.ini`` in a custom folder (e.g. ``/myconf``), and mount it this way :

::

    sudo docker run --volume=/myconf:/opt/apps/daybed/conf --link couchdb:couchdb daybed
