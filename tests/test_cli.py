import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Protocol

import pytest
from testfixtures import TempDirectory, compare, StringComparison

from giterator import Git
from giterator.testing import Repo


class RunCLI(Protocol):
    def __call__(
        self, options: str, env: dict[str, str] | None = None
    ) -> 'subprocess.CompletedProcess[str]': ...


GIT_IDENTITY = {
    'GIT_AUTHOR_NAME': 'Giterator',
    'GIT_AUTHOR_EMAIL': 'giterator@example.com',
    'GIT_COMMITTER_NAME': 'Giterator',
    'GIT_COMMITTER_EMAIL': 'giterator@example.com',
}


@pytest.fixture()
def run() -> RunCLI:
    def run(options: str, env: dict[str, str] | None = None) -> 'subprocess.CompletedProcess[str]':
        command = [sys.executable, '-m', 'giterator']
        if options:
            command.extend(options.split())
        if env:
            env = {**os.environ, **env}
        return subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, errors='replace', env=env
        )

    return run


class TestCLI:
    def test_no_command(self, run: RunCLI) -> None:
        result = run('')
        compare(result.returncode, expected=2, suffix=result.stdout)
        compare(
            result.stdout,
            expected=StringComparison(
                r'(?s).*error: the following arguments are required: command.*'
            ),
        )

    def test_missing_sep(self, run: RunCLI, tmpdir: TempDirectory) -> None:
        result = run(f'pack --repo {tmpdir.getpath("repo")} no-separator-here')
        compare(result.returncode, expected=1, suffix=result.stdout)
        compare(result.stdout, expected="mapping must contain ':'\n")


class TestPack:
    def test_new_repo(self, run: RunCLI, tmpdir: TempDirectory) -> None:
        tmpdir.write('downloads/foo-2001-01-03.csv', b'second')
        tmpdir.write('downloads/foo-2001-01-02.csv', b'first')
        tmpdir.write('downloads/foo-aa-bb-cc.csv', b'not dated')
        repo_path = tmpdir.getpath('repo')
        pattern = tmpdir.getpath('downloads/foo-%Y-%m-%d.csv')
        result = run(f'pack --repo {repo_path} {pattern}:foo.csv', env=GIT_IDENTITY)
        compare(result.returncode, expected=0, suffix=result.stdout)
        compare(
            result.stdout,
            expected=StringComparison(
                r'[0-9a-f]+ \S+foo-2001-01-02\.csv\n[0-9a-f]+ \S+foo-2001-01-03\.csv\n'
            ),
        )
        git = Git(repo_path)
        compare(
            git('log', '--reverse', '--date=short', '--format=%ad %s'),
            expected='2001-01-02 foo-2001-01-02.csv\n2001-01-03 foo-2001-01-03.csv\n',
        )
        compare(git('status', '-s'), expected='')
        compare((git.path / 'foo.csv').read_text(), expected='second')

    def test_existing_repo(self, run: RunCLI, repo: Repo, tmpdir: TempDirectory) -> None:
        tmpdir.write('bar-2001.csv', b'bar content')
        rev = repo.commit_content('a', datetime(2000, 1, 1, tzinfo=timezone.utc))
        pattern = tmpdir.getpath('bar-%Y.csv')
        result = run(f'pack --repo {repo.path} {pattern}:bar.csv')
        compare(result.returncode, expected=0, suffix=result.stdout)
        compare(
            repo('log', '--reverse', '--format=%s'),
            expected='a commit\nbar-2001.csv\n',
        )
        compare(repo.rev_parse('HEAD~1'), expected=rev)
        compare((repo.path / 'a').read_text(), expected='a content')
        compare((repo.path / 'bar.csv').read_text(), expected='bar content')

    def test_custom_sep(self, run: RunCLI, repo: Repo, tmpdir: TempDirectory) -> None:
        tmpdir.write('bar-2001.csv', b'bar content')
        pattern = tmpdir.getpath('bar-%Y.csv')
        result = run(f'pack --repo {repo.path} --sep | {pattern}|bar.csv')
        compare(result.returncode, expected=0, suffix=result.stdout)
        compare(repo('log', '--format=%s'), expected='bar-2001.csv\n')


class TestUnpack:
    def test_unpack(self, run: RunCLI, repo: Repo, tmpdir: TempDirectory) -> None:
        (repo.path / 'foo.csv').write_text('first')
        repo.commit('one', datetime(2001, 1, 2, 12, tzinfo=timezone.utc))
        (repo.path / 'foo.csv').write_text('second')
        repo.commit('two', datetime(2001, 1, 3, 12, tzinfo=timezone.utc))
        pattern = tmpdir.getpath('out/foo-%Y-%m-%d.csv')
        result = run(f'unpack --repo {repo.path} *.csv:{pattern}')
        compare(result.returncode, expected=0, suffix=result.stdout)
        compare(
            result.stdout,
            expected=(
                f'{tmpdir.getpath("out/foo-2001-01-02.csv")}\n'
                f'{tmpdir.getpath("out/foo-2001-01-03.csv")}\n'
            ),
        )
        compare(tmpdir.read('out/foo-2001-01-02.csv'), expected=b'first')
        compare(tmpdir.read('out/foo-2001-01-03.csv'), expected=b'second')

    def test_ignores_git_internals(self, run: RunCLI, repo: Repo, tmpdir: TempDirectory) -> None:
        (repo.path / 'config.txt').write_text('content')
        repo.commit('one', datetime(2001, 1, 2, 12, tzinfo=timezone.utc))
        pattern = tmpdir.getpath('out/%Y-%m-%d.txt')
        result = run(f'unpack --repo {repo.path} **/config*:{pattern}')
        compare(result.returncode, expected=0, suffix=result.stdout)
        compare(result.stdout, expected=f'{tmpdir.getpath("out/2001-01-02.txt")}\n')
        compare(tmpdir.read('out/2001-01-02.txt'), expected=b'content')
