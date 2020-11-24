import pytest
from testfixtures import TempDirectory

from giterator.testing import Repo


@pytest.fixture()
def tmpdir():
    with TempDirectory() as _dir:
        yield _dir


@pytest.fixture()
def git(tmpdir: TempDirectory):
    return Repo(tmpdir.path)
