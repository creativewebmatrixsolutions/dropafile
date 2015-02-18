dropafile
=========

Drop me a file, securely.

|build-status|_

.. |build-status| image:: https://travis-ci.org/ulif/dropafile.png?branch=master
.. _build-status: https://travis-ci.org/ulif/dropafile


`dropafile` provides a webapp where users can drop files.

Install
-------

As a user, run::

  $ pip install dropafile

then, start the local server::

  $ dropafile
  Creating temporary self-signed SSL certificate...
  Done.
  Certificate in: /tmp/tmp1y2bgh/cert.pem
  Key in:         /tmp/tmp1y2bgh/cert.key
  Password is: H93rqnsrdEXD2ad3rQwdWqZ
   * Running on https://localhost:8443/ (Press CTRL+C to quit)

The server will provide SSL. Users can access `dropafile` sevice
pointing their browsers to the location given. They will have to
provide the password displayed (which changes with restart).

`dropafile` is meant as a channel to deliver documents in a not too
unsecure manner. For instance as a quickly installable workaround if
people are not able or willing to use GnuPG or similar, although they
have sensible documents to send.


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


.. _virtualenv: https://virtualenv.pypa.io/
