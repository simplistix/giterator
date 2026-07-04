.. py:currentmodule:: giterator

Changes
=======

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
