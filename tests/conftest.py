import pytest
from testfixtures import TempDirectory


@pytest.fixture()
def tmpdir():
    with TempDirectory() as _dir:
        yield _dir
