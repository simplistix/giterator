import subprocess
import sys

import pytest
from testfixtures import compare


@pytest.fixture()
def run():
    def run(options):
        command = [sys.executable, '-m', 'giterator']
        if options:
            command.extend(options.split())
        return subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, errors='replace'
        )
    return run


class TestCLI:

    def test_no_command(self, run):
        result = run('')
        compare(result.returncode, expected=2, suffix=result.stdout)
        assert 'error: the following arguments are required: command' in result.stdout

    def test_pack(self, run):
        # stub for coverage
        result = run('pack')
        compare(result.returncode, expected=0, suffix=result.stdout)
        assert not result.stdout

    def test_unpack(self, run):
        # stub for coverage
        result = run('pack')
        compare(result.returncode, expected=0, suffix=result.stdout)
        assert not result.stdout
