from collections.abc import Generator
from datetime import datetime, time, timedelta, timezone
from itertools import islice
from pathlib import Path

from testfixtures import ShouldRaise, TempDirectory, compare

from giterator import Every, Git, Giteration, User, daily, read, write
from giterator.testing import Repo


def utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


class TestEvery:
    def test_unanchored(self) -> None:
        compare(
            list(islice(Every(timedelta(hours=2)).ticks(datetime(2001, 1, 1, 10)), 3)),
            expected=[
                datetime(2001, 1, 1, 10),
                datetime(2001, 1, 1, 12),
                datetime(2001, 1, 1, 14),
            ],
        )

    def test_anchor_later_in_day(self) -> None:
        compare(
            list(islice(daily.at(16).ticks(datetime(2001, 1, 1, 10)), 2)),
            expected=[datetime(2001, 1, 1, 16), datetime(2001, 1, 2, 16)],
        )

    def test_anchor_earlier_in_day(self) -> None:
        compare(
            list(islice(daily.at(16).ticks(datetime(2001, 1, 1, 17)), 2)),
            expected=[datetime(2001, 1, 2, 16), datetime(2001, 1, 3, 16)],
        )

    def test_anchor_exactly_at_start(self) -> None:
        compare(
            list(islice(daily.at(16).ticks(datetime(2001, 1, 1, 16)), 2)),
            expected=[datetime(2001, 1, 1, 16), datetime(2001, 1, 2, 16)],
        )

    def test_anchor_with_minutes(self) -> None:
        compare(
            list(islice(daily.at(9, 30).ticks(datetime(2001, 1, 1, 10)), 2)),
            expected=[datetime(2001, 1, 2, 9, 30), datetime(2001, 1, 3, 9, 30)],
        )

    def test_at_returns_new_schedule(self) -> None:
        anchored = daily.at(16)
        compare(anchored.anchor, expected=time(16))
        compare(anchored.period, expected=timedelta(days=1))
        compare(daily.anchor, expected=None)

    def test_bad_period(self) -> None:
        with ShouldRaise(ValueError('period must be positive')):
            Every(timedelta(0))


class TestGiteration:
    def test_minimal(self) -> None:
        giteration = Giteration('some/path')
        compare(giteration.path, expected=Path('some/path'))
        compare(giteration.at, expected=None)
        compare(giteration.rev, expected=None)
        compare(giteration.message, expected=None)

    def test_maximal(self) -> None:
        giteration = Giteration(
            Path('some/path'), at=utc(2001, 1, 1), rev='abc1234', message='a message'
        )
        compare(giteration.path, expected=Path('some/path'))
        compare(giteration.at, expected=utc(2001, 1, 1))
        compare(giteration.rev, expected='abc1234')
        compare(giteration.message, expected='a message')


class TestRead:
    def test_empty_repo(self, repo: Repo) -> None:
        compare(list(read(repo, daily)), expected=[])

    def test_daily(self, repo: Repo) -> None:
        repo.commit_content('a', utc(2001, 1, 1, 10))
        rev_b = repo.commit_content('b', utc(2001, 1, 1, 12))
        rev_c = repo.commit_content('c', utc(2001, 1, 3, 9))
        results = []
        for giteration in read(repo, daily.at(16)):
            files = sorted(p.name for p in giteration.path.iterdir() if p.name != '.git')
            results.append((giteration.rev, giteration.at, files))
        compare(
            results,
            expected=[
                (rev_b, utc(2001, 1, 1, 16), ['a', 'b']),
                (rev_c, utc(2001, 1, 3, 16), ['a', 'b', 'c']),
            ],
        )

    def test_path_removed_when_iteration_finishes(self, repo: Repo) -> None:
        repo.commit_content('a', utc(2001, 1, 1, 10))
        paths = []
        contents = []
        for giteration in read(repo, daily):
            paths.append(giteration.path)
            contents.append((giteration.path / 'a').read_text())
        compare(contents, expected=['a content'])
        (path,) = paths
        assert not path.exists()

    def test_path_removed_when_iteration_abandoned(self, repo: Repo) -> None:
        repo.commit_content('a', utc(2001, 1, 1, 10))
        repo.commit_content('b', utc(2001, 1, 5, 10))
        iterator = read(repo, daily)
        assert isinstance(iterator, Generator)
        giteration = next(iterator)
        assert giteration.path.exists()
        iterator.close()
        assert not giteration.path.exists()

    def test_start_specified(self, repo: Repo) -> None:
        repo.commit_content('a', utc(2001, 1, 1, 10))
        repo.commit_content('b', utc(2001, 1, 1, 12))
        rev_c = repo.commit_content('c', utc(2001, 1, 3, 9))
        compare(
            [(g.rev, g.at) for g in read(repo, daily.at(16), start=utc(2001, 1, 3))],
            expected=[(rev_c, utc(2001, 1, 3, 16))],
        )

    def test_start_before_first_commit(self, repo: Repo) -> None:
        rev_a = repo.commit_content('a', utc(2001, 1, 2, 10))
        rev_b = repo.commit_content('b', utc(2001, 1, 4, 10))
        compare(
            [(g.rev, g.at) for g in read(repo, daily, start=utc(2001, 1, 1))],
            expected=[(rev_a, utc(2001, 1, 3)), (rev_b, utc(2001, 1, 5))],
        )

    def test_naive_start(self, repo: Repo) -> None:
        rev_a = repo.commit_content('a', utc(2001, 1, 1, 12))
        rev_b = repo.commit_content('b', utc(2001, 2, 1, 12))
        rev_c = repo.commit_content('c', utc(2001, 3, 1, 12))
        compare(
            [g.rev for g in read(repo, daily, start=datetime(2000, 12, 25))],
            expected=[rev_a, rev_b, rev_c],
        )

    def test_timedelta_schedule(self, repo: Repo) -> None:
        rev_a = repo.commit_content('a', utc(2001, 1, 1, 10))
        rev_b = repo.commit_content('b', utc(2001, 1, 1, 22))
        compare(
            [(g.rev, g.at) for g in read(repo, timedelta(hours=6))],
            expected=[(rev_a, utc(2001, 1, 1, 10)), (rev_b, utc(2001, 1, 1, 22))],
        )

    def test_repo_as_path(self, repo: Repo) -> None:
        rev_a = repo.commit_content('a', utc(2001, 1, 1, 10))
        compare(
            [(g.rev, g.at) for g in read(repo.path, daily)],
            expected=[(rev_a, utc(2001, 1, 1, 10))],
        )


class TestWrite:
    def test_new_repo(self, tmpdir: TempDirectory) -> None:
        tmpdir.write('snap1/a.txt', b'a content')
        tmpdir.write('snap1/sub/b.txt', b'b content')
        tmpdir.write('snap2/a.txt', b'new a content')
        git = write(
            tmpdir.getpath('repo'),
            [
                Giteration(tmpdir.getpath('snap1'), utc(2001, 1, 1, 16)),
                Giteration(tmpdir.getpath('snap2'), utc(2001, 1, 2, 16)),
            ],
            user=User(name='Foo Bar', email='foo@example.com'),
        )
        compare(
            git('log', '--reverse', '--format=%an %aI %cI %s').replace('Z ', '+00:00 '),
            expected=(
                'Foo Bar 2001-01-01T16:00:00+00:00 2001-01-01T16:00:00+00:00'
                ' 2001-01-01T16:00:00+00:00\n'
                'Foo Bar 2001-01-02T16:00:00+00:00 2001-01-02T16:00:00+00:00'
                ' 2001-01-02T16:00:00+00:00\n'
            ),
        )
        compare(git('status', '-s'), expected='')
        compare((git.path / 'a.txt').read_text(), expected='new a content')
        assert not (git.path / 'sub').exists()

    def test_existing_repo(self, git: Git, tmpdir: TempDirectory) -> None:
        (git.path / 'a.txt').write_text('existing content')
        git.commit('existing', utc(2001, 1, 1, 10))
        tmpdir.write('snap/b.txt', b'b content')
        write(git, [Giteration(tmpdir.getpath('snap'), utc(2001, 1, 2, 16))])
        compare(
            git('log', '--reverse', '--format=%s'),
            expected='existing\n2001-01-02T16:00:00+00:00\n',
        )
        compare((git.path / 'b.txt').read_text(), expected='b content')
        assert not (git.path / 'a.txt').exists()

    def test_no_at_no_message(self, git: Git, tmpdir: TempDirectory) -> None:
        tmpdir.write('snap/a.txt', b'content')
        write(git, [Giteration(tmpdir.getpath('snap'))])
        compare(git('log', '--format=%s'), expected='giterator commit\n')

    def test_message_specified(self, git: Git, tmpdir: TempDirectory) -> None:
        tmpdir.write('snap/a.txt', b'content')
        write(git, [Giteration(tmpdir.getpath('snap'), utc(2001, 1, 1), message='a message')])
        compare(git('log', '--format=%s'), expected='a message\n')

    def test_identical_snapshots(self, git: Git, tmpdir: TempDirectory) -> None:
        tmpdir.write('snap/a.txt', b'content')
        write(
            git,
            [
                Giteration(tmpdir.getpath('snap'), utc(2001, 1, 1, 16)),
                Giteration(tmpdir.getpath('snap'), utc(2001, 1, 2, 16)),
            ],
        )
        compare(
            git('log', '--reverse', '--format=%s'),
            expected='2001-01-01T16:00:00+00:00\n2001-01-02T16:00:00+00:00\n',
        )

    def test_snapshot_containing_git_dir(self, git: Git, tmpdir: TempDirectory) -> None:
        tmpdir.write('snap/a.txt', b'content')
        tmpdir.write('snap/.git/marker', b'should not be copied')
        write(git, [Giteration(tmpdir.getpath('snap'), utc(2001, 1, 1))])
        compare(git('ls-files'), expected='a.txt\n')
        assert not (git.path / '.git' / 'marker').exists()

    def test_round_trip(self, repo: Repo, tmpdir: TempDirectory) -> None:
        repo.commit_content('a', utc(2001, 1, 1, 10))
        repo.commit_content('b', utc(2001, 1, 1, 12))
        repo.commit_content('c', utc(2001, 1, 3, 9))
        resampled = write(
            tmpdir.getpath('resampled'),
            read(repo, daily.at(16)),
            user=User(name='Giterator', email='giterator@example.com'),
        )
        compare(
            resampled('log', '--reverse', '--format=%cI %s').replace('Z ', '+00:00 '),
            expected=(
                '2001-01-01T16:00:00+00:00 2001-01-01T16:00:00+00:00\n'
                '2001-01-03T16:00:00+00:00 2001-01-03T16:00:00+00:00\n'
            ),
        )
        compare(
            resampled('ls-files').split(),
            expected=['a', 'b', 'c'],
        )
        compare((resampled.path / 'c').read_text(), expected='c content')
