from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from os import makedirs
from pathlib import Path
from subprocess import check_output, STDOUT, CalledProcessError
from typing import Self

from .typing import Date


@dataclass
class User:
    """
    Represents a git user, for configuring a repo.
    """

    #: The name of the user.
    name: str
    #: The email address of the user.
    email: str


@dataclass
class Commit:
    """
    A commit from the log of a repo.
    """

    #: The short hash of the commit.
    rev: str
    #: The author of the commit.
    author: User
    #: The author date of the commit.
    author_date: datetime
    #: The committer of the commit.
    committer: User
    #: The committer date of the commit.
    committer_date: datetime
    #: The full commit message, without any trailing newlines.
    message: str


LOG_FORMAT = '%x00'.join(('%h', '%an', '%ae', '%aI', '%cn', '%ce', '%cI', '%B')) + '%x00'


class GitError(Exception):
    """
    Something went wrong while running a git command.
    """


class Git:
    """
    Represents a local work tree and repo.

    :param path: The path to an existing work tree or local repo.
    """

    _user: User | None = None

    def __init__(self, path: Path | str):
        if not isinstance(path, Path):
            path = Path(path)
        #: The path where this instance is located.
        self.path: Path = path

    def __call__(
        self, *command: str, env: dict[str, str] | None = None, cwd: Path | None = None
    ) -> str:
        """
        Run a git command in this repo. For example:

        .. code-block:: python

            Git(...)('log', '-1')

        ``env`` supplies additional environment variables, or overrides for
        existing ones; it is merged with the current process's environment
        rather than replacing it.
        """
        full_env = None if env is None else {**os.environ, **env}
        try:
            output = check_output(
                ('git',) + command, cwd=cwd or self.path, stderr=STDOUT, env=full_env
            )
        except CalledProcessError as e:
            raise GitError(
                f"{' '.join(e.cmd)!r} gave return code {e.returncode}:\n\n{e.output.decode()}\n\n"
            ) from None
        return output.decode()

    git = __call__

    def _set_user(self, user: User | None) -> None:
        if user:
            self._user = user
            self('config', 'user.name', user.name)
            self('config', 'user.email', user.email)

    def init(self, user: User | None = None, branch: str | None = None) -> None:
        """
        Create an empty Git repository or reinitialize an existing one.
        If the path doesn't exist, it will be created. This includes any missing
        parent directories.

        :param user: The user to configure in the local repo.
        :param branch: The name to use for the initial branch. If not specified,
            the machine's git default is used.
        """
        makedirs(self.path, exist_ok=True)
        command = ['init']
        if branch:
            command.extend(['-b', branch])
        self(*command)
        self._set_user(user)

    @classmethod
    def clone(
        cls,
        source: str | Path | Git,
        path: str | Path,
        user: User | None = None,
    ) -> Self:
        """
        Clone the ``source`` repo to the ``path`` specified.

        :param source: The repo to clone, either as a path or a :class:`Git` instance.
        :param path: Where to clone to. Relative paths are resolved relative to the
            parent of ``source``.
        :param user: The user to configure in the local clone. If not specified and
            ``source`` is a :class:`Git` instance, the user from ``source``, if any,
            is configured. Otherwise, no user is configured and commits in the clone
            will depend on git's normal identity discovery.
        """
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
    def _coerce_date(dt: Date) -> str:
        return dt if isinstance(dt, str) else dt.isoformat()

    def commit(
        self,
        msg: str,
        author_date: Date | None = None,
        commit_date: Date | None = None,
        short: bool = True,
        allow_empty: bool = False,
    ) -> str:
        """
        Commit changes in this repo, including and new or deleted files.

        :param msg: The commit message.
        :param author_date: The author date.
        :param commit_date: The commit date. If not specified, git's own default
            is used, which is the current time rather than ``author_date``.
        :param short: Return the short commit hash instead of the full 40-character hash.
        :param allow_empty: Allow a commit to be made even when there are no changes.
        """
        self('add', '.')
        command = ['commit', '-m', msg]
        if allow_empty:
            command.append('--allow-empty')
        if author_date:
            command.extend(['--date', self._coerce_date(author_date)])
        env: dict[str, str] = {}
        if commit_date:
            env['GIT_COMMITTER_DATE'] = self._coerce_date(commit_date)
        self(*command, env=env)
        return self.rev_parse('HEAD', short)

    def rev_parse(self, label: str, short: bool = True) -> str:
        """
        Return the commit hash that ``label`` refers to.

        :param label: A branch, tag, or other revision that ``git rev-parse`` accepts.
        :param short: Return the short commit hash instead of the full 40-character hash.
        """
        command = ['rev-parse', '--verify', '-q']
        if short:
            command.append('--short')
        command.append(label)
        return self(*command).strip()

    def log(self, *options: str) -> list[Commit]:
        """
        Return the commits in this repo as a list of :class:`Commit`
        instances, most recent first.

        :param options: Any options, revision ranges or paths that
            ``git log`` accepts.
        """
        commits = []
        for record in self('log', '--format=' + LOG_FORMAT, *options).split('\x00\n'):
            if not record:
                continue
            (
                rev,
                author_name,
                author_email,
                author_date,
                committer_name,
                committer_email,
                committer_date,
                message,
            ) = record.split('\x00')
            commits.append(
                Commit(
                    rev=rev,
                    author=User(author_name, author_email),
                    author_date=datetime.fromisoformat(author_date),
                    committer=User(committer_name, committer_email),
                    committer_date=datetime.fromisoformat(committer_date),
                    message=message.rstrip('\n'),
                )
            )
        return commits

    def tag(self, name: str) -> None:
        """
        Create a tag with the specified name.
        """
        self('tag', name)

    def tags(self) -> list[str]:
        """
        Return a list of tags in this repo.
        """
        return self('tag').split()

    def tag_hashes(self) -> dict[str, str]:
        """
        Return a mapping of tag name to commit hash.
        """
        return {tag: self.rev_parse(tag) for tag in self.tags()}

    def branch(self, name: str) -> None:
        """
        Create and checkout a branch with the specified name.
        """
        self('checkout', '-b', name)

    def branches(self) -> list[str]:
        """
        Return a list of branches in this repo.
        """
        return self('for-each-ref', '--format', '%(refname:short)', 'refs/heads/').split()

    def branch_hashes(self) -> dict[str, str]:
        """
        Return a mapping of branch name to commit hash.
        """
        return {branch: self.rev_parse(branch) for branch in self.branches()}
