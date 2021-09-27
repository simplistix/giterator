from os import makedirs
from pathlib import Path
from subprocess import check_output, STDOUT, CalledProcessError
from typing import Union

from .typing import Date


class User:
    """
    Represents a git user, for configuring a repo.
    """

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email


class GitError(Exception):
    """
    Something went wrong while running a git command.
    """


class Git:
    """
    Represents a local work tree and repo.

    :param path: The path to an existing work tree or local repo.
    """

    def __init__(self, path: Union[Path, str]):
        if not isinstance(path, Path):
            path = Path(path)
        #: The path where this instance is located.
        self.path: Path = path

    def __call__(self, *command, env: dict = None) -> str:
        """
        Run a git command in this repo. For example:

        .. code-block:: python

            Git(...)('log', '-1')
        """
        try:
            output = check_output(
                ('git',) + command, cwd=self.path, stderr=STDOUT, env=env
            )
        except CalledProcessError as e:
            raise GitError(
                f"{' '.join(e.cmd)!r} gave:\n\n{e.output.decode()}\n\n"
            ) from None
        return output.decode()

    git = __call__

    def init(self, user: User = None) -> None:
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

    @staticmethod
    def _coerce_date(dt):
        return dt if isinstance(dt, str) else dt.isoformat()

    def commit(self, msg: str, author_date: Date = None, commit_date: Date = None):
        """
        Commit changes in this repo, including and new or deleted files.

        :param msg: The commit message.
        :param author_date: The author date.
        :param commit_date: The commit date. Defaults to author date if not specified.
        """
        self('add', '.')
        command = ['commit', '-m', msg]
        if author_date:
            command.extend(['--date', self._coerce_date(author_date)])
        env = {}
        if commit_date:
            env['GIT_COMMITTER_DATE'] = self._coerce_date(commit_date)
        self(*command, env=env)
