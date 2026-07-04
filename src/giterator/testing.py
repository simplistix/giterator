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
    A repo for use in automated tests.
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
        As :meth:`Git.clone`, but always ensures a user is configured in the
        clone, so commits made in it never depend on the machine's global git
        config. The user can be specified, and is otherwise inherited from a
        :class:`Git` ``source``; failing both, the same default as :meth:`make`
        is used.
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
        Write new context based on the prefix and then commit it
        at the specified datetime, or using at a sequence of increasing
        datetimes if not specified.
        """
        if branch:
            self.branch(branch)
        (self.path / prefix).write_text(f'{prefix} content')
        commit = self.commit('a commit', dt or self._clock.now(), short=short)
        if tag:
            self.tag(tag)
        return commit
