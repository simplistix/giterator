giterator
=========

|Docs|_ |PyPI|_ |Git|_

.. |Docs| image:: https://readthedocs.org/projects/giterator/badge/?version=latest
.. _Docs: http://giterator.readthedocs.org/en/latest/

.. |PyPI| image:: https://badge.fury.io/py/giterator.svg
.. _PyPI: https://pypi.org/project/giterator/

.. |Git| image:: https://github.com/simplistix/giterator/actions/workflows/ci.yml/badge.svg
.. _Git: https://github.com/simplistix/giterator

Python tools for doing git things:

- ``Git`` wraps command-line git for scripting everyday repository operations,
  with structured access to the log.

- ``read`` and ``write`` replay a repository's history as a series of dated
  snapshots and turn dated snapshots, such as backups, back into history.
  The ``giterator`` command line tool packs and unpacks dated files in the
  same way.

- ``giterator.testing.Repo`` makes sample repositories for automated tests,
  with machine-independent configuration and single-call commits.

Full documentation is available at http://giterator.readthedocs.org/en/latest/
