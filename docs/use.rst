.. py:currentmodule:: giterator

Using giterator
===============


Installation
~~~~~~~~~~~~

giterator is available on the `Python Package Index`__ and can be installed
with any tools for managing Python environments.

__ https://pypi.org


Examining history
~~~~~~~~~~~~~~~~~

The :meth:`Git.log` method returns the commits in a repository as
:class:`Commit` instances, giving structured access to the hash, author,
committer, dates and full message of each commit:

.. code-block:: python

    from giterator import Git

    for commit in Git('path/to/repo').log('--reverse'):
        print(commit.committer_date, commit.rev, commit.message)

Any options, revision ranges or paths accepted by ``git log`` can be passed
as strings, as with ``--reverse`` above.


Iterating over history
~~~~~~~~~~~~~~~~~~~~~~

The :func:`read` function replays the history of a repository as a series of
snapshots taken on a schedule. Each snapshot is a :class:`Giteration` giving
the path to a checkout of the repository as it was at that point in time,
along with the revision checked out and the time of the snapshot:

.. code-block:: python

    from giterator import daily, read

    for giteration in read('path/to/repo', daily.at(16, 0)):
        print(giteration.at, giteration.rev)
        process(giteration.path)

Snapshots are made by cloning the repository into a temporary location, so
the repository itself is never modified. Each checkout is only valid until
the next snapshot is requested, and is removed when iteration finishes.

The schedule can be :data:`daily`, anchored to a time of day with
:meth:`Every.at` as above, or any :class:`~datetime.timedelta` giving the gap
between snapshots. Points on the schedule where the repository had not
changed since the previous snapshot are skipped, and iteration stops once the
most recent commit has been seen. The schedule starts at the date of the
first commit, but ``start`` can be used to begin somewhere else.


Writing snapshots as commits
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`write` function does the reverse, turning a series of snapshots
into commits in a repository. This is useful when you have dated copies of a
project, such as backups, that you would like to turn into version history:

.. code-block:: python

    from datetime import datetime
    from giterator import Giteration, write

    write('path/to/new/repo', [
        Giteration('backups/2001-01-01', datetime(2001, 1, 1)),
        Giteration('backups/2001-02-01', datetime(2001, 2, 1)),
    ])

If the target repository does not already exist, it is created. The content
of each :class:`Giteration` replaces the content of the repository's work
tree and is committed using its ``at`` date for both the author and committer
dates.

Since :func:`read` yields :class:`Giteration` instances and :func:`write`
accepts them, the two can be combined to resample a repository's history,
here as it stood at 4pm each day:

.. code-block:: python

    from giterator import daily, read, write

    write('path/to/resampled', read('path/to/repo', daily.at(16, 0)))
