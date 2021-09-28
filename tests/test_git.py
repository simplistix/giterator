import os
from datetime import datetime, timezone

import pytest
from testfixtures import TempDirectory, compare, ShouldRaise

from giterator import Git, User
from giterator.git import GitError
from giterator.testing import Repo


@pytest.fixture()
def repo(tmpdir: TempDirectory):
    return Repo(tmpdir.path)


class TestCall:

    def test_bad_command(self, repo: Repo):
        with ShouldRaise(GitError) as s:
            repo('wut')
        assert str(s.raised).startswith("'git wut' gave return code 1:")
        assert "git: 'wut' is not a git command" in str(s.raised)


class TestInit:

    def test_init(self, tmpdir: TempDirectory):
        tmpdir.makedir('foo')
        Git(tmpdir.getpath('foo')).init()
        assert os.path.exists(tmpdir.getpath('foo/.git'))

    def test_init_make_path(self, tmpdir):
        Git(tmpdir.getpath('foo/bar')).init()
        assert os.path.exists(tmpdir.getpath('foo/bar/.git'))

    def test_init_with_user(self, tmpdir: TempDirectory):
        Git(tmpdir.getpath('foo')).init(User(name='Foo Bar', email='foo@example.com'))
        config = tmpdir.read('foo/.git/config')
        assert b'name = Foo Bar' in config
        assert b'email = foo@example.com' in config


class TestCommit:

    def test_from_empty(self, repo: Repo):
        (repo.path / 'a').write_text('content')
        repo.commit('a commit')
        compare(repo.git('status', '-s'), expected='')
        commit, = repo.git('log', '--format=%h').split()
        compare(repo.git('show', '--pretty=format:%s', '--stat', commit), expected=(
            'a commit\n'
            ' a | 1 +\n'
            ' 1 file changed, 1 insertion(+)\n'
        ))

    def test_from_one_commit(self, repo: Repo):
        (repo.path / 'a').write_text('a content')
        (repo.path / 'b').write_text('b content')
        (repo.path / 'c').write_text('c content')
        repo.commit('commit 1')
        (repo.path / 'b').write_text('new content')
        (repo.path / 'c').unlink()
        (repo.path / 'd').write_text('d content')
        repo.commit('commit 2')
        compare(repo.git('status', '-s'), expected='')
        commit2, commit1 = repo.git('log', '--format=%h').split()
        compare(repo.git('show', '--pretty=format:%s', '--stat', commit1), expected=(
            'commit 1\n'
            ' a | 1 +\n'
            ' b | 1 +\n'
            ' c | 1 +\n'
            ' 3 files changed, 3 insertions(+)\n'
        ))
        compare(repo.git('show', '--pretty=format:%s', '--stat', commit2), expected=(
            'commit 2\n'
            ' b | 2 +-\n'
            ' c | 1 -\n'
            ' d | 1 +\n'
            ' 3 files changed, 2 insertions(+), 2 deletions(-)\n'
        ))

    def test_with_author_date(self, tmpdir: TempDirectory, git):
        (git.path / 'content.txt').write_text('content')
        repo = Git(git.path)
        repo.commit('commit', author_date=datetime(2000, 1, 1))
        compare(git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')

    def test_with_committer_date(self, tmpdir: TempDirectory, git):
        (git.path / 'content.txt').write_text('content')
        repo = Git(git.path)
        repo.commit('commit', commit_date=datetime(2000, 1, 1))
        compare(git('log', '--pretty=format:%cd'), expected='Sat Jan 1 00:00:00 2000 +0000')

    def test_with_dates_as_strings(self, tmpdir: TempDirectory, git):
        (git.path / 'content.txt').write_text('content')
        repo = Git(git.path)
        repo.commit('commit',
                    author_date='format:iso8601:'+datetime(2000, 1, 1).isoformat(),
                    commit_date='format:iso8601:'+datetime(2000, 1, 2).isoformat())
        compare(git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')
        compare(git('log', '--pretty=format:%cd'), expected='Sun Jan 2 00:00:00 2000 +0000')

    def test_with_naive_datetime(self, repo: Repo):
        (repo.path / 'a').write_text('content')
        repo.commit('a commit', datetime(2001, 1, 1, 10))
        compare(repo.git('log', '--format=%aI %cI'),
                expected='2001-01-01T10:00:00+00:00 2001-01-01T10:00:00+00:00\n')

    def test_with_tz_datetime(self, repo: Repo):
        (repo.path / 'a').write_text('content')
        repo.commit('a commit', datetime(2001, 1, 1, 10).astimezone(timezone.utc))
        compare(repo.git('log', '--format=%aI %cI'),
                expected='2001-01-01T10:00:00+00:00 2001-01-01T10:00:00+00:00\n')
