from os import makedirs
from pathlib import Path
from subprocess import check_output, STDOUT, CalledProcessError
from typing import Union, Dict, List, Optional

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

    _user: User = None

    def __init__(self, path: Union[Path, str]):
        if not isinstance(path, Path):
            path = Path(path)
        #: The path where this instance is located.
        self.path: Path = path

    def __call__(self, *command, env: dict = None, cwd: Path = None) -> str:
        """
        Run a git command in this repo. For example:

        .. code-block:: python

            Git(...)('log', '-1')
        """
        try:
            output = check_output(
                ('git',) + command, cwd=cwd or self.path, stderr=STDOUT, env=env
            )
        except CalledProcessError as e:
            raise GitError(
                f"{' '.join(e.cmd)!r} gave return code {e.returncode}:\n\n"
                f"{e.output.decode()}\n\n"
            ) from None
        return output.decode()

    git = __call__

    def _set_user(self, user: Optional[User]):
        if user:
            self._user = user
            self('config', 'user.name', user.name)
            self('config', 'user.email', user.email)

    def init(self, user: User = None) -> None:
        """
        Create an empty Git repository or reinitialize an existing one.
        If the path doesn't exist, it will be created. This includes any missing
        parent directories.

        :param user: The user to configure in the local repo.
        """
        makedirs(self.path, exist_ok=True)
        self('init')
        self._set_user(user)

    @classmethod
    def clone(cls, source: Union[str, Path, 'Git'], path: Union[str, Path], user: User = None):
        if isinstance(source, Git):
            user = user or source._user
            source = source.path
        source = Path(source)
        dest = source.parent.joinpath(Path(path)).absolute()
        git = cls(dest)
        git('clone', str(source), str(git.path), cwd=source.parent)
        git._set_user(user)
        return git

    @staticmethod
    def _coerce_date(dt):
        return dt if isinstance(dt, str) else dt.isoformat()

    def commit(self, msg: str, author_date: Date = None, commit_date: Date = None) -> str:
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
        return self.rev_parse('HEAD')

    def rev_parse(self, label: str):
        return self('rev-parse', '--verify', '-q', '--short', label).strip()

    def tag(self, name: str) -> None:
        """
        Create a tag with the specified name.
        """
        self('tag', name)

    def tags(self) -> List[str]:
        """
        Return a list of tags in this repo.
        """
        return self('tag').split()

    def tag_hashes(self) -> Dict[str, str]:
        """
        Return a mapping of tag name to commit hash.
        """
        return {tag: self.rev_parse(tag) for tag in self.tags()}

    def branch(self, name: str) -> None:
        """
        Create and checkout a branch with the specified name.
        """
        self('checkout', '-b', name)

    def branches(self) -> List[str]:
        """
        Return a list of branches in this repo.
        """
        return self('for-each-ref', '--format', '%(refname:short)', 'refs/heads/').split()

    def branch_hashes(self) -> Dict[str, str]:
        """
        Return a mapping of branch name to commit hash.
        """
        return {branch: self.rev_parse(branch) for branch in self.branches()}
