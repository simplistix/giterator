from datetime import datetime
from pathlib import Path
from typing import Union

from .clock import Clock
from .git import Git, User
from .typing import Date


class Repo(Git):
    """
    A repo for use in automated tests.
    """

    def __init__(self, path: Union[Path, str]):
        super().__init__(path)
        self._clock = Clock()

    @classmethod
    def make(cls, path: Union[Path, str], user: User = None):
        """
        Make a repo at the path specified and ensure a user is configured
        in the repo. The user can be specified.
        """
        repo = cls(path)
        repo.init(user or User(name='Giterator', email='giterator@example.com'))
        return repo

    def commit(self, msg: str, author_date: Date = None, commit_date: Date = None) -> str:
        return super().commit(msg, author_date, commit_date or author_date)

    def commit_content(
        self,
        prefix: str,
        dt: datetime = None,
        *,
        tag: str = None,
        branch: str = None,
    ) -> str:
        """
        Write new context based on the prefix and then commit it
        at the specified datetime, or using at a sequence of increasing
        datetimes if not specified.
        """
        if branch:
            self.branch(branch)
        (self.path / prefix).write_text(f'{prefix} content')
        commit = self.commit('a commit', dt or self._clock.now())
        if tag:
            self.tag(tag)
        return commit
