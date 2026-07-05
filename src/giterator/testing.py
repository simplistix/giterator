from datetime import datetime
from pathlib import Path
from typing import Self

from .clock import Clock
from .git import Git, User
from .typing import Date


DEFAULT_USER = User(name='Giterator', email='giterator@example.com')
DEFAULT_BRANCH = 'main'


class Repo(Git):
    """
    A repo for making sample repositories in automated tests.
    """

    def __init__(self, path: Path | str) -> None:
        super().__init__(path)
        self._clock = Clock()

    @classmethod
    def make(cls, path: Path | str, user: User | None = None, branch: str = DEFAULT_BRANCH) -> Self:
        """
        Make a repo at the path specified and ensure a user and initial branch
        name are configured in the repo, so neither depends on the git config
        of the machine the tests are running on. Both can be specified.
        """
        repo = cls(path)
        repo.init(user or DEFAULT_USER, branch)
        return repo

    @classmethod
    def clone(cls, source: str | Path | Git, path: str | Path, user: User | None = None) -> Self:
        """
        As :meth:`Git.clone <giterator.Git.clone>`, but always ensures a user
        is configured in the clone, so commits made in it never depend on the
        machine's global git config. The user can be specified, and is
        otherwise inherited from a :class:`Git <giterator.Git>` ``source``;
        failing both, the same default as :meth:`make` is used.
        """
        repo = super().clone(source, path, user)
        if repo._user is None:
            repo._set_user(DEFAULT_USER)
        return repo

    def commit(
        self,
        msg: str,
        author_date: Date | None = None,
        commit_date: Date | None = None,
        short: bool = True,
        allow_empty: bool = False,
    ) -> str:
        """
        As :meth:`Git.commit <giterator.Git.commit>`, but ``commit_date``
        defaults to ``author_date`` when not given, so a single date is
        enough to pin both of a commit's timestamps.
        """
        return super().commit(
            msg, author_date, commit_date or author_date, short=short, allow_empty=allow_empty
        )

    def commit_content(
        self,
        prefix: str,
        dt: datetime | None = None,
        *,
        tag: str | None = None,
        branch: str | None = None,
        short: bool = True,
    ) -> str:
        """
        Make a commit in a single call: write a file named after ``prefix``,
        containing content derived from it, and commit it with the message
        ``'a commit'``.

        :param prefix: The name of the file to write, and the basis of its content.
        :param dt: The datetime to use for both the author and commit dates.
            When not given, each commit uses the next point in a deterministic
            sequence of increasing datetimes, so tests never depend on the
            current time.
        :param tag: A tag to create at the new commit.
        :param branch: A branch to create and check out before committing.
        :param short: Return the short commit hash instead of the full 40-character hash.
        """
        if branch:
            self.branch(branch)
        (self.path / prefix).write_text(f'{prefix} content')
        commit = self.commit('a commit', dt or self._clock.now(), short=short)
        if tag:
            self.tag(tag)
        return commit
