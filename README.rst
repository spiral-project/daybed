Daybed
######

Daybed is a form-validation and data-storage API.

It is a way to create definitions (models) and to do validation on some
incoming data using these definitions.

Why ?
=====

You can do a lot of things with this kind of service, so these use-cases are
only some of the possibilities we would like to offer.

Maybe do you know Google forms? That's a service letting you design a form and
exposing it to end users, so then you can access the results.

That's working pretty well but nothing there is done in the open. Google now
has all your data ;) In addition to that, the APIs to access this data are not
that funny, you can't interact with them without dealing with rows and cells…
which probably isn't what you want.

As a data geek and librist, I don't think that google forms is a reasonable
choice.

**Daybed** tries to solve this very problem by providing a REST API able to do
validation for you, depending on some rules you defined. Oh, and of course it
is a free software, so you can modify it if you want / need.

Let's go!
=========

Go on http://daybed.rtfd.org for more documentation.

.. image:: https://travis-ci.org/spiral-project/daybed.png
    :target: https://travis-ci.org/spiral-project/daybed

.. image:: https://coveralls.io/repos/spiral-project/daybed/badge.png
    :target: https://coveralls.io/r/spiral-project/daybed
