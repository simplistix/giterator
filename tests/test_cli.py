import subprocess
import sys
from collections.abc import Callable

import pytest
from testfixtures import compare

RunCLI = Callable[[str], 'subprocess.CompletedProcess[str]']


@pytest.fixture()
def run() -> RunCLI:
    def run(options: str) -> 'subprocess.CompletedProcess[str]':
        command = [sys.executable, '-m', 'giterator']
        if options:
            command.extend(options.split())
        return subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, errors='replace'
        )
    return run


class TestCLI:

    def test_no_command(self, run: RunCLI) -> None:
        result = run('')
        compare(result.returncode, expected=2, suffix=result.stdout)
        assert 'error: the following arguments are required: command' in result.stdout

    def test_pack(self, run: RunCLI) -> None:
        # stub for coverage
        result = run('pack')
        compare(result.returncode, expected=0, suffix=result.stdout)
        assert not result.stdout

    def test_unpack(self, run: RunCLI) -> None:
        # stub for coverage
        result = run('pack')
        compare(result.returncode, expected=0, suffix=result.stdout)
        assert not result.stdout
