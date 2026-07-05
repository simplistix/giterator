API Reference
=============

Everything documented here is importable directly from ``giterator``, except
for :class:`~giterator.testing.Repo`, which lives in ``giterator.testing`` so
that test-only code is never pulled in by normal use.

giterator
~~~~~~~~~

.. automodule:: giterator
    :members:
    :special-members: __call__
    :member-order: bysource

.. data:: daily
    :type: Every

    A daily schedule, for use with :func:`read`.


giterator.testing
~~~~~~~~~~~~~~~~~~

.. automodule:: giterator.testing
    :members:
    :member-order: bysource
