from pathlib import Path
from typing import Union

from .git import Git, User


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
