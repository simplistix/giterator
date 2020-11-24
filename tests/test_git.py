import os
from datetime import datetime

from testfixtures import TempDirectory, compare, ShouldRaise

from giterator import Git, User, GitError


class TestCall:

    def test_bad_command(self, git):
        with ShouldRaise(GitError) as s:
            git('wut')
        message = str(s.raised)
        assert message.startswith('git wut gave:\n\n')
        assert "wut' is not a git command" in message


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

    def test_from_empty(self, tmpdir: TempDirectory, git):
        (git.path / 'a').write_text('content')
        git.commit('a commit')
        compare(git('status', '-s'), expected='')
        compare(git('log', '--pretty=format:%s', '--stat'),
                expected=(
                    'a commit\n'
                    ' a | 1 +\n'
                    ' 1 file changed, 1 insertion(+)\n'
                ))

    def test_add_update_delete(self, tmpdir: TempDirectory, git):
        (git.path / 'a').write_text('unchanged')
        (git.path / 'b').write_text('original content')
        (git.path / 'c').write_text('to delete')
        git.commit('commit 1')
        (git.path / 'b').write_text('new content')
        (git.path / 'c').unlink()
        (git.path / 'd').write_text('new file')
        git.commit('commit 2')
        compare(git('status', '-s'), expected='')
        compare(git('log', '--pretty=format:%s', '--stat'),
                expected=(
                    'commit 2\n'
                    ' b | 2 +-\n'
                    ' c | 1 -\n'
                    ' d | 1 +\n'
                    ' 3 files changed, 2 insertions(+), 2 deletions(-)'
                    '\n\n'
                    'commit 1\n'
                    ' a | 1 +\n'
                    ' b | 1 +\n'
                    ' c | 1 +\n'
                    ' 3 files changed, 3 insertions(+)\n'
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
