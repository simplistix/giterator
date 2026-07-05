from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import datetime, time, timedelta
from pathlib import Path
from shutil import copy2, copytree, rmtree
from tempfile import TemporaryDirectory

from .git import Git, GitError, User


class Every:
    """
    A schedule of evenly spaced points in time.

    :param period: The gap between points on the schedule.
    :param anchor: An optional time of day to anchor points to.
    """

    def __init__(self, period: timedelta, anchor: time | None = None):
        if period <= timedelta(0):
            raise ValueError('period must be positive')
        self.period = period
        self.anchor = anchor

    def at(self, hour: int, minute: int = 0) -> Every:
        """
        Return a copy of this schedule anchored at the time of day specified.
        """
        return Every(self.period, time(hour, minute))

    def ticks(self, start: datetime) -> Iterator[datetime]:
        """
        Yield an unbounded sequence of points on this schedule,
        beginning with the first point at or after ``start``.
        """
        tick = start
        if self.anchor is not None:
            tick = start.replace(
                hour=self.anchor.hour, minute=self.anchor.minute, second=0, microsecond=0
            )
            if tick < start:
                tick += self.period
        while True:
            yield tick
            tick += self.period


#: A daily schedule, for use with :func:`read`.
daily: Every = Every(timedelta(days=1))


class Giteration:
    """
    The content of a repo at a point in time.

    :param path: The path of a directory containing the content.
    :param at: When the content was current.
    :param rev: The revision the content came from, filled in by :func:`read`.
    :param message: The commit message for :func:`write` to use,
        filled in from the source commit by :func:`read`.
    """

    def __init__(
        self,
        path: Path | str,
        at: datetime | None = None,
        rev: str | None = None,
        message: str | None = None,
    ):
        if not isinstance(path, Path):
            path = Path(path)
        #: The path of a directory containing the content.
        self.path: Path = path
        #: When the content was current.
        self.at: datetime | None = at
        #: The revision the content came from.
        self.rev: str | None = rev
        #: The commit message for :func:`write` to use.
        #: :func:`read` fills this in from the source commit.
        self.message: str | None = message


def read(
    repo: Git | Path | str,
    schedule: Every | timedelta,
    start: datetime | None = None,
) -> Iterator[Giteration]:
    """
    Iterate over the history of ``repo``, yielding a :class:`Giteration`
    for each point on ``schedule`` at which the repo had changed since the
    previous point. Iteration stops once the most recent commit has been
    yielded.

    The repo is cloned into a temporary location and each revision is checked
    out there, so the repo itself is never modified. The path of each
    :class:`Giteration` yielded is only valid until the next one is requested,
    and is removed when iteration finishes.

    :param repo: The repo to read, either as a path or a :class:`Git` instance.
    :param schedule: The points in time at which to sample the repo's history,
        either an :class:`Every` instance such as :data:`daily` or a
        :class:`~datetime.timedelta` giving the gap between points.
    :param start: Where the schedule starts. Defaults to the date of the
        repo's first commit.
    """
    if isinstance(schedule, timedelta):
        schedule = Every(schedule)
    if not isinstance(repo, Git):
        repo = Git(repo)
    with TemporaryDirectory() as checkout_dir:
        clone = Git.clone(repo, Path(checkout_dir) / 'clone')
        try:
            history = clone.log('--first-parent', '--reverse')
        except GitError:
            return
        if start is None:
            begin = history[0].committer_date
        elif start.tzinfo is None:
            begin = start.astimezone()
        else:
            begin = start
        index = -1
        yielded = None
        for tick in schedule.ticks(begin):
            while index + 1 < len(history) and history[index + 1].committer_date <= tick:
                index += 1
            if index < 0:
                continue
            commit = history[index]
            if commit.rev != yielded:
                clone('checkout', '--detach', commit.rev)
                yielded = commit.rev
                yield Giteration(clone.path, at=tick, rev=commit.rev, message=commit.message)
            if index == len(history) - 1:
                return


def write(
    repo: Git | Path | str,
    revs: Iterable[Giteration],
    user: User | None = None,
) -> Git:
    """
    Write each :class:`Giteration` in ``revs`` as a commit in ``repo``,
    in the order given. The content of each one replaces the content of the
    repo's work tree and is committed using its ``at`` date for both the
    author and committer dates.

    :param repo: The repo to write to, either as a path or a :class:`Git`
        instance. If the path is not already a repo, one is created.
    :param revs: The :class:`Giteration` instances to write.
    :param user: The user to configure if a repo is created.
    """
    if not isinstance(repo, Git):
        repo = Git(repo)
    if not (repo.path / '.git').exists():
        repo.init(user)
    for giteration in revs:
        for existing in repo.path.iterdir():
            if existing.name == '.git':
                continue
            if existing.is_dir():
                rmtree(existing)
            else:
                existing.unlink()
        for item in giteration.path.iterdir():
            if item.name == '.git':
                continue
            if item.is_dir():
                copytree(item, repo.path / item.name)
            else:
                copy2(item, repo.path / item.name)
        message = giteration.message
        if message is None:
            message = giteration.at.isoformat() if giteration.at else 'giterator commit'
        repo.commit(message, author_date=giteration.at, commit_date=giteration.at, allow_empty=True)
    return repo
