dropafile
=========

Drop me a file on a webpage.

.. |build-status|_

.. .. |build-status| image:: https://travis-ci.org/ulif/dropafile.png?branch=master
.. .. _build-status: https://travis-ci.org/ulif/dropafile


`dropafile` provides a page to drop files into a local file.

Install
-------

As a user, run::

  $ pip install dropafile

then, start the local server::

  $ dropafile



Developer Install
-----------------

Developers should install a `virtualenv`_ first::

  $ virtualenv -p /usr/bin/python2.7 py27  # for Python2.7

See `tox.ini` for all Python versions supported.

Activate the virtualenv::

  $ source py27/bin/activate
  (py27) $

Now build the devel environment::

  (py27) $ python setup.py dev

You can run tests like this::

  (py27) $ py.test

Tests for all supported (and locally available) Python vesions can be
run by::

  (py27) $ pip install tox  # neccessary only once per virtualenv
  (py27) $ tox
