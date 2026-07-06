.. py:currentmodule:: giterator

Changes
=======

1.0.0 (6 Jul 2026)
------------------

.. warning:: Breaking changes:

  - The ``prefix`` parameter of
    :meth:`Repo.commit_content <giterator.testing.Repo.commit_content>` has been renamed
    to ``name`` and is now optional.

- Added :func:`read`, which replays the history of a repository as a series of
  :class:`Giteration` snapshots, either one per commit or taken on a schedule such as
  :data:`daily`.

- Added :func:`write`, which turns a series of :class:`Giteration` snapshots into commits,
  useful for turning dated copies of a project, such as backups, into version history.
  Combining it with :func:`read` allows a repository's history to be resampled.

- The ``giterator`` command line tool has grown ``pack`` and ``unpack`` commands for
  moving between files with dates in their names and commits in a repository.

- Added :meth:`Git.log`, which returns the commits in a repository as :class:`Commit`
  instances, giving structured access to the hash, author, committer, dates and full
  message of each commit.

- :meth:`Repo.commit_content <giterator.testing.Repo.commit_content>` no longer needs a
  file name, and the content and commit message can now be given when a test cares
  about them.

- The documentation has been substantially expanded, and every example in it is now
  executed as part of the test suite.

- Fixed a bug where :meth:`Git.clone` failed when the source repository was given as a
  relative path.

- Fixed a bug where calling a :class:`Git` instance with environment variable overrides,
  as :meth:`Git.commit` does when given explicit dates, ran ``git`` with only those
  variables rather than the full process environment.

0.4.0 (4 Jul 2026)
------------------

- Moved to a `uv`__-based, ``pyproject.toml``-driven project layout, with ``main`` replacing
  ``master`` as the default git branch.

  __ https://docs.astral.sh/uv/

- :meth:`Repo.clone <giterator.testing.Repo.clone>` now always ensures a user is configured in
  the clone, whether specified explicitly, inherited from the source repo, or falling back to
  the same default as :meth:`Repo.make <giterator.testing.Repo.make>`, so commits made in
  clones no longer depend on the git config of the machine the tests are running on.

- :meth:`Git.init` can now pin the name of the initial branch, and
  :meth:`Repo.make <giterator.testing.Repo.make>` does so by default, using ``main``, so branch
  names in test repos no longer depend on the git config of the machine the tests are running on.

0.3.0 (4 Feb 2026)
------------------

- General refresh.

- Add ``short`` parameter to methods that return commit hashes,
  allowing the full commit hash to be returned.

0.2.0 (1 Oct 2021)
------------------

- Methods that create commits now return the newly-create commit hash.

0.1.0 (28 Sep 2021)
-------------------

- Initial release
