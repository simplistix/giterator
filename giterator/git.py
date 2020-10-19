from os import makedirs
from pathlib import Path
from subprocess import check_output, STDOUT
from typing import Union


class User:
    """
    Represents a git user, for configuring a repo.
    """

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email


class Git:
    """
    Represents a local work tree and repo.
    """

    def __init__(self, path: Union[Path, str]):
        """
        :param path: The path to an existing work tree or local repo.
        """
        if not isinstance(path, Path):
            path = Path(path)
        self.path: Path = path

    def __call__(self, *command):
        """
        Run a git command in this repo. For example:

        .. code-block:: python

            Git(...)('log', '-1')
        """
        return check_output(('git',) + command, cwd=self.path, stderr=STDOUT)

    def init(self, user: User = None):
        """
        Create an empty Git repository or reinitialize an existing one.
        If the path doesn't exist, it will be created. This includes any missing
        parent directories.

        :param user: The user to configure in the local repo.
        """
        makedirs(self.path, exist_ok=True)
        self('init')
        if user:
            self('config', 'user.name', user.name)
            self('config', 'user.email', user.email)
