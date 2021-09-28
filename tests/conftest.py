from pathlib import Path

import pytest
from testfixtures import TempDirectory

from giterator import Git, User
from giterator.testing import Repo


@pytest.fixture()
def tmpdir():
    with TempDirectory() as _dir:
        yield _dir


@pytest.fixture()
def git(tmpdir: TempDirectory):
    git_ = Git(Path(tmpdir.path) / 'git')
    git_.init(User(name='Giterator', email='giterator@example.com'))
    return git_


@pytest.fixture()
def repo(tmpdir: TempDirectory):
    return Repo.make(Path(tmpdir.path) / 'repo')
