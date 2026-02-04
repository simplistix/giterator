import os
from pathlib import Path

import pytest
from testfixtures import TempDirectory

from giterator import Git, User
from giterator.testing import Repo


# Enable coverage for subprocesses (CLI tests)
os.environ.setdefault('COVERAGE_PROCESS_START', str(Path(__file__).parent.parent / '.coveragerc'))


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
