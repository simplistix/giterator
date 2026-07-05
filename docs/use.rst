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

When no schedule is given, a snapshot is yielded for every commit, with the
time of each snapshot being the date of its commit.


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
here as it stood at 4pm each day. Commit messages are preserved, as
:func:`read` fills in the message of each snapshot's source commit:

.. code-block:: python

    from giterator import daily, read, write

    write('path/to/resampled', read('path/to/repo', daily.at(16, 0)))


Command line use
~~~~~~~~~~~~~~~~

The ``giterator`` command line tool packs dated files into a repository and
unpacks a repository into dated files. Both commands take a mapping of a
source to a target, separated by a colon.

``pack`` looks for files matching a :meth:`~datetime.datetime.strftime`
pattern, parses the date out of each file's name, and commits them to the
repository, oldest first, under the name on the right of the mapping:

.. code-block:: bash

    giterator pack --repo path/to/repo 'downloads/foo-%Y-%m-%d.csv:foo.csv'

If the repository does not already exist, it is created. Files that match
the shape of the pattern but do not contain a valid date are ignored, and
any other content already in the repository is left alone.

``unpack`` does the reverse. For each commit in the repository, files
matching the glob pattern on the left of the mapping are copied to the path
produced by formatting the commit's date with the pattern on the right:

.. code-block:: bash

    giterator unpack --repo path/to/repo '*.csv:downloads/foo-%Y-%m-%d.csv'

Any directories needed for the target files are created, and existing files
are overwritten.

If any of the paths involved contain a colon, ``--sep`` can be used to
change the separator used in the mapping.
