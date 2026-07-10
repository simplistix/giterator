.. py:currentmodule:: giterator

Using giterator
===============


Installation
~~~~~~~~~~~~

giterator is available on the `Python Package Index`__ and can be installed
with any tools for managing Python environments.

__ https://pypi.org


Normal use
~~~~~~~~~~

:class:`Git` wraps the command-line ``git`` tool, giving common repository
operations a typed Python method instead of a shell command assembled by
hand. Point it at an existing work tree, or create one with :meth:`Git.init`:

.. code-block:: python

    from giterator import Git, User

    repo = Git('path/to/repo')
    repo.init(User('Alice', 'alice@example.com'))

Any git subcommand that doesn't have a dedicated method can still be run
directly; calling a :class:`Git` instance (or its :meth:`~Git.git` alias)
runs ``git`` in the work tree and returns its output as a string:

.. code-block:: python

    repo.git('remote', 'add', 'origin', 'git@example.com:some/repo.git')

If the command fails, a :class:`GitError` is raised carrying git's own
output:

>>> repo.git('merge', 'no-such-branch')
Traceback (most recent call last):
...
giterator.git.GitError: 'git merge no-such-branch' gave return code 1:
<BLANKLINE>
merge: no-such-branch - not something we can merge
...

:meth:`Git.commit` stages everything in the work tree, including new and
deleted files, and commits it, optionally backdating the author and
committer:

.. code-block:: python

    from datetime import datetime, timezone

    (repo.path / 'README.rst').write_text('hello')
    repo.commit('add readme', author_date=datetime(2020, 1, 1, tzinfo=timezone.utc))

:meth:`Git.clone` clones a repo. When the source is a :class:`Git` instance
with a user configured, that user is carried over to the clone unless a
different one is given:

.. code-block:: python

    clone = Git.clone(repo, 'path/to/clone')

Branches and tags are created and listed with :meth:`Git.branch`,
:meth:`Git.branches`, :meth:`Git.tag` and :meth:`Git.tags`, and their commit
hashes looked up with :meth:`Git.branch_hashes` and :meth:`Git.tag_hashes`:

>>> repo.branch('feature')
>>> repo.tag('v1.0')
>>> repo.branches()
['feature', 'main']
>>> repo.tags()
['v1.0']

Passing ``bare=True`` to :meth:`Git.init` creates a bare repository instead.
A worktree of a bare repo shares its config, so configuring a ``user`` there
means commits made in those worktrees don't depend on the git configuration
of the machine running the tests:

.. code-block:: python

    bare = Git('path/to/bare.git')
    bare.init(User('Alice', 'alice@example.com'), branch='main', bare=True)
    bare.git('worktree', 'add', '--orphan', '-b', 'main', '../worktree')

.. invisible-code-block: python

    from pathlib import Path

    (Path('path/to/worktree') / 'greeting.txt').write_text('hello')

>>> worktree = Git('path/to/worktree')
>>> worktree.commit('add greeting')
'...'
>>> worktree.log()[0].author
User(name='Alice', email='alice@example.com')


Examining history
~~~~~~~~~~~~~~~~~~

:meth:`Git.log` returns the commits in a repository as :class:`Commit`
instances, giving structured access to the hash, author, committer, dates
and full message of each commit. Here, after committing some docs to go
with the readme:

.. code-block:: python

    (repo.path / 'docs').mkdir()
    (repo.path / 'docs' / 'index.rst').write_text('welcome')
    repo.commit('add docs', author_date=datetime(2020, 2, 1, tzinfo=timezone.utc))

>>> for commit in repo.log():
...     print(commit.author_date, commit.author.name, commit.message)
2020-02-01 00:00:00+00:00 Alice add docs
2020-01-01 00:00:00+00:00 Alice add readme

Any options, revision ranges or paths accepted by ``git log`` can be passed
as strings, here reversing the order and restricting to commits that touch
``docs/``:

>>> for commit in repo.log('--reverse', 'docs/'):
...     print(commit.author_date, commit.message)
2020-02-01 00:00:00+00:00 add docs


Iterating over history
~~~~~~~~~~~~~~~~~~~~~~

The :func:`read` function replays the history of a repository as a series of
snapshots taken on a schedule. Each snapshot is a :class:`Giteration` giving
the path to a checkout of the repository as it was at that point in time,
along with the revision checked out and the time of the snapshot. The
examples below read a repository with commits at 10:00 on 1 January, 11:00
on 2 January and 12:00 on 5 January 2001, all UTC:

.. invisible-code-block: python

    from giterator.testing import Repo

    project = Repo.make('path/to/project')
    for prefix, day, hour in [('a', 1, 10), ('b', 2, 11), ('c', 5, 12)]:
        project.commit_content(prefix, datetime(2001, 1, day, hour, tzinfo=timezone.utc))

>>> from giterator import daily, read
>>> for giteration in read('path/to/project', daily.at(16, 0)):
...     print(giteration.at, giteration.rev)
2001-01-01 16:00:00+00:00 5ee580a
2001-01-02 16:00:00+00:00 e3a9fbb
2001-01-05 16:00:00+00:00 4f0b0f3

Snapshots are made by cloning the repository into a temporary location, so
the repository itself is never modified. Each checkout is only valid until
the next snapshot is requested, and is removed when iteration finishes.

The schedule can be :data:`daily`, anchored to a time of day with
:meth:`Every.at` as above, or any :class:`~datetime.timedelta` giving the gap
between snapshots. Without an anchor, the schedule ticks from the date of
the repository's first commit:

>>> from datetime import timedelta
>>> for giteration in read('path/to/project', timedelta(days=2)):
...     print(giteration.at, giteration.rev)
2001-01-01 10:00:00+00:00 5ee580a
2001-01-03 10:00:00+00:00 e3a9fbb
2001-01-07 10:00:00+00:00 4f0b0f3

``start`` begins the schedule somewhere else, with the first snapshot giving
the repository as it stood at that point:

>>> start = datetime(2001, 1, 4, tzinfo=timezone.utc)
>>> for giteration in read('path/to/project', daily.at(16, 0), start=start):
...     print(giteration.at, giteration.rev)
2001-01-04 16:00:00+00:00 e3a9fbb
2001-01-05 16:00:00+00:00 4f0b0f3

As the examples above show, points on the schedule where the repository had
not changed since the previous snapshot are skipped, and iteration stops
once the most recent commit has been seen. Pass ``skip_unchanged=False`` to
get exactly one snapshot per point instead, useful when whatever consumes
them expects evenly spaced samples:

>>> snapshots = read('path/to/project', daily.at(16, 0), skip_unchanged=False)
>>> for giteration in snapshots:
...     print(giteration.at, giteration.rev)
2001-01-01 16:00:00+00:00 5ee580a
2001-01-02 16:00:00+00:00 e3a9fbb
2001-01-03 16:00:00+00:00 e3a9fbb
2001-01-04 16:00:00+00:00 e3a9fbb
2001-01-05 16:00:00+00:00 4f0b0f3

When no schedule is given, a snapshot is yielded for every commit, with the
time of each snapshot being the date of its commit:

>>> for giteration in read('path/to/project'):
...     print(giteration.at, giteration.rev)
2001-01-01 10:00:00+00:00 5ee580a
2001-01-02 11:00:00+00:00 e3a9fbb
2001-01-05 12:00:00+00:00 4f0b0f3

The :func:`write` function does the reverse, turning a series of snapshots
into commits in a repository, which is useful when you have dated copies of
a project, such as backups, that you would like to turn into version
history:

.. invisible-code-block: python

    from pathlib import Path

    for day in '2001-01-01', '2001-02-01':
        backup = Path('backups') / day
        backup.mkdir(parents=True)
        (backup / 'notes.txt').write_text(day)

.. code-block:: python

    from datetime import datetime
    from giterator import Giteration, write

    write('path/to/new/repo', [
        Giteration('backups/2001-01-01', datetime(2001, 1, 1)),
        Giteration('backups/2001-02-01', datetime(2001, 2, 1)),
    ])

If the target repository does not already exist, it is created. The content
of each :class:`Giteration` replaces the content of the repository's work
tree and is committed using its ``at`` date for both the author and
committer dates, with the ``at`` date as the message when none is given:

>>> [commit.message for commit in Git('path/to/new/repo').log()]
['2001-02-01T00:00:00', '2001-01-01T00:00:00']

Since :func:`read` yields :class:`Giteration` instances and :func:`write`
accepts them, the two can be combined to resample a repository's history,
here as it stood at 4pm each day. Commit messages are preserved, as
:func:`read` fills in the message of each snapshot's source commit:

>>> from giterator import write
>>> resampled = write('path/to/resampled', read('path/to/project', daily.at(16, 0)))
>>> for commit in resampled.log('--reverse'):
...     print(commit.author_date, commit.message)
2001-01-01 16:00:00+00:00 a commit
2001-01-02 16:00:00+00:00 a commit
2001-01-05 16:00:00+00:00 a commit

The ``giterator`` command line tool builds on the same read/write model to
move between dated files and commits. ``pack`` looks for files matching a
:meth:`~datetime.datetime.strftime` pattern, parses the date out of each
file's name, and commits them oldest first under the name on the right of
the mapping:

.. code-block:: bash

    giterator pack --repo path/to/repo 'downloads/foo-%Y-%m-%d.csv:foo.csv'

``unpack`` does the reverse, copying files matching the glob pattern on the
left of the mapping to the path produced by formatting each commit's date
with the pattern on the right:

.. code-block:: bash

    giterator unpack --repo path/to/repo '*.csv:downloads/foo-%Y-%m-%d.csv'

If any of the paths involved contain a colon, ``--sep`` changes the
separator used in the mapping.


Testing
~~~~~~~

:class:`~giterator.testing.Repo` is a :class:`Git` subclass built for use in
automated tests. It configures a user and initial branch name that don't
depend on the git configuration of the machine running the tests, so the
same test behaves the same way in every environment, including CI.

The usual pattern is a pytest fixture that makes a fresh repo in a temporary
directory for each test:

.. code-block:: python

    from pathlib import Path

    import pytest
    from giterator.testing import Repo


    @pytest.fixture()
    def repo(tmp_path: Path) -> Repo:
        return Repo.make(tmp_path / 'repo')


    def test_something(repo: Repo) -> None:
        repo.commit_content('data')
        commit = repo.log()[0]
        assert commit.message == 'a commit'

.. invisible-code-block: python

    from sybil.testing import run_pytest

    run_pytest(test_something, fixtures=[repo])

    repo = Repo.make(tmp_path / 'sample')

As ``test_something`` shows, :meth:`~giterator.testing.Repo.commit_content`
makes a commit in a single call: it writes a file, defaulting to
``sample.txt`` with content derived from its name, and commits with an
automatically increasing timestamp, so a test can create a string of
commits without inventing a file name, content, or dates by hand. When a
test does care about those, or about the commit message, they can all be
given, and the commit can be placed on a new branch or tagged:

.. code-block:: python

    from datetime import datetime

    repo.commit_content('a')
    repo.commit_content('b', datetime(2021, 6, 1))
    repo.commit_content('c', content='some specific content')
    repo.commit_content('d', message='a specific message')
    repo.commit_content('e', tag='v1.0')
    repo.commit_content('f', branch='feature')

That leaves the work tree with one file per call:

>>> sorted(path.name for path in repo.path.iterdir())
['.git', 'a', 'b', 'c', 'd', 'e', 'f']

:meth:`~giterator.testing.Repo.make` is the usual way to create a
:class:`~giterator.testing.Repo`.
A :class:`User` and branch name can be given if the defaults, ``Giterator
<giterator@example.com>`` and ``main``, don't suit a particular test:

.. code-block:: python

    from giterator import User

    repo = Repo.make(
        tmp_path / 'repo', user=User('Alice', 'alice@example.com'), branch='trunk'
    )

:meth:`~giterator.testing.Repo.clone` works like :meth:`Git.clone`, but
ensures the clone always has a user configured, even when the source has
none, falling back to the same default as
:meth:`~giterator.testing.Repo.make`:

.. code-block:: python

    clone = Repo.clone(repo, tmp_path / 'clone')

When a test needs full control over the files in a commit, write them and
use :meth:`~giterator.testing.Repo.commit`. It works like
:meth:`Git.commit`, except that when ``commit_date`` is omitted it defaults
to ``author_date``, so one date is enough to pin both of a commit's
timestamps:

.. code-block:: python

    (repo.path / 'content.txt').write_text('content')
    repo.commit('a commit', datetime(2020, 1, 1))
