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
        return subprocess.run(command, capture_output=True)
    return run


class TestCLI:

    def test_no_command(self, run):
        result = run('')
        stderr = result.stderr.decode()
        compare(result.returncode, expected=2, suffix=stderr)
        assert 'error: the following arguments are required: command' in stderr

    def test_pack(self, run):
        # stub for coverage
        result = run('pack')
        assert not result.stdout.decode()
        stderr = result.stderr.decode()
        assert not stderr
        compare(result.returncode, expected=0, suffix=stderr)

    def test_unpack(self, run):
        # stub for coverage
        result = run('pack')
        assert not result.stdout.decode()
        stderr = result.stderr.decode()
        assert not stderr
        compare(result.returncode, expected=0, suffix=stderr)
