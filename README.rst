Daybed
######

Storage and validation as a service.

**Daybed** exposes a REST API where you can create your own models (definitions),
validate data and store records.

Create your own REST storage API in seconds!

It takes advantage of bullet-proof technologies, such as *CouchDB* and *Pyramid*.

.. image:: https://travis-ci.org/spiral-project/daybed.png
    :target: https://travis-ci.org/spiral-project/daybed

.. image:: https://coveralls.io/repos/spiral-project/daybed/badge.png?branch=master
  :target: https://coveralls.io/r/spiral-project/daybed?branch=master


Use-cases
=========

Since *Daybed* talks REST and JSON, you can basically use it as a remote storage with
any of your favorite technologies (python, Android, iOS, AngularJS, Ember.js, Backbone.js, etc.).

It becomes an abstract storage layer, a Google Forms alternative, a *data pad* or an internal component
in your applications : it's database as a service !

We made some demo applications with *Daybed* :

* `daybed-map <http://leplatrem.github.io/daybed-map/>`_, a *geo-pad* where you can create you own maps with custom fields, using `backbone-forms <https://github.com/powmedia/backbone-forms>`_

* A `TODO list <http://daybed.lolnet.org/>`_ using `jquery-spore <https://github.com/nikopol/jquery-spore>`_ ;

* A generic `CRUD application <http://spiral-project.github.io/backbone-daybed/>`_ using `backbone-daybed <https://github.com/spiral-project/backbone-daybed>`_ ;


Features
========

* Geographical types
* Create and retrieve models definitions
* Validate, store and retrieve data
* List available field types
* SPORE access point
* Pluggable database engine

In the future:

* Access right management
* Relationships between models
* JSON schema compatibility


Resources
=========

* `Full documentation <http://daybed.rtfd.org>`_
* `Roadmap and notes <https://github.com/spiral-project/daybed/wiki>`_
