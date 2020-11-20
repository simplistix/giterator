import os

import pytest
from testfixtures import TempDirectory, compare, ShouldRaise

from giterator import Git, User, GitError
from giterator.testing import Repo


@pytest.fixture()
def repo(tmpdir: TempDirectory):
    return Repo(tmpdir.path)


class TestCall:

    def test_bad_command(self, repo: Repo):
        with ShouldRaise(GitError) as s:
            repo('wut')
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
