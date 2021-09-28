from datetime import datetime
from pathlib import Path
from typing import Union

from .clock import Clock
from .git import Git, User
from .typing import Date


class Repo(Git):
    """
    A repo for use in automated tests.

    :param container: The directory in which to place test repos.
    :param name: The name for this test repo within `container`.
    """

    def __init__(self, container: Union[Path, str], name: str = 'local'):
        if not isinstance(container, Path):
            container = Path(container)
        super().__init__(container / name)
        self.init(User(name='Giterator', email='giterator@example.com'))
        self._clock = Clock()

    def commit(self, msg: str, author_date: Date = None, commit_date: Date = None):
        super().commit(msg, author_date, commit_date or author_date)

    def commit_content(
        self,
        prefix: str,
        dt: datetime = None,
        *,
        tag: str = None,
        branch: str = None,
    ) -> None:
        """
        Write new context based on the prefix and then commit it
        at the specified datetime, or using at a sequence of increasing
        datetimes if not specified.
        """
        if branch:
            self.branch(branch)
        (self.path / prefix).write_text(f'{prefix} content')
        self.commit('a commit', dt or self._clock.now())
        if tag:
            self.tag(tag)
