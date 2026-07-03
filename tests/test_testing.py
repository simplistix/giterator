from datetime import datetime
from pathlib import Path

import pytest
from testfixtures import compare, TempDirectory

from giterator import Git, User
from giterator.testing import Repo


def check_config_user(git: Git, name: str, email: str) -> None:
    config = (git.path / '.git' / 'config').read_text()
    assert f'name = {name}' in config
    assert f'email = {email}' in config


class TestRepo:
    def test_commit_with_one_date(self, repo: Repo) -> None:
        (repo.path / 'content.txt').write_text('content')
        repo.commit('commit', datetime(2000, 1, 1))
        compare(repo.git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')
        compare(repo.git('log', '--pretty=format:%cd'), expected='Sat Jan 1 00:00:00 2000 +0000')

    def test_commit_with_both_dates(self, repo: Repo) -> None:
        (repo.path / 'content.txt').write_text('content')
        repo.commit('commit', datetime(2000, 1, 1), datetime(2000, 1, 2))
        compare(repo.git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')
        compare(repo.git('log', '--pretty=format:%cd'), expected='Sun Jan 2 00:00:00 2000 +0000')

    def test_commit_with_both_dates_explicit(self, repo: Repo) -> None:
        (repo.path / 'content.txt').write_text('content')
        repo.commit('commit', author_date=datetime(2000, 1, 1), commit_date=datetime(2000, 1, 2))
        compare(repo.git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')
        compare(repo.git('log', '--pretty=format:%cd'), expected='Sun Jan 2 00:00:00 2000 +0000')

    def test_make_default_branch_ignores_machine_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = tmp_path / 'gitconfig'
        config.write_text('[init]\n\tdefaultBranch = unexpected\n')
        monkeypatch.setenv('GIT_CONFIG_GLOBAL', str(config))
        repo = Repo.make(tmp_path / 'repo')
        repo.commit_content('a')
        compare(repo.branches(), expected=['main'])

    def test_make_with_branch(self, tmp_path: Path) -> None:
        repo = Repo.make(tmp_path / 'repo', branch='trunk')
        repo.commit_content('a')
        compare(repo.branches(), expected=['trunk'])

    def test_clone(self, tmpdir: TempDirectory) -> None:
        root = Path(tmpdir.path)
        upstream = Repo.make(root / 'upstream')
        upstream.commit_content('a')
        clone = Repo.clone(upstream, root / 'clone')
        tmpdir.compare(('clone', 'upstream'), recursive=False)
        check_config_user(clone, 'Giterator', 'giterator@example.com')

    def test_with_user(self, repo: Repo, tmpdir: TempDirectory) -> None:
        repo.commit_content('a')
        clone = Repo.clone(repo, 'clone', User('Foo', 'bar@example.com'))
        tmpdir.compare(('clone', 'repo'), recursive=False)
        check_config_user(clone, 'Foo', 'bar@example.com')

    def test_clone_from_path(self, tmpdir: TempDirectory) -> None:
        root = Path(tmpdir.path)
        upstream = Repo.make(root / 'upstream')
        upstream.commit_content('a')
        clone = Repo.clone(upstream.path, root / 'clone')
        check_config_user(clone, 'Giterator', 'giterator@example.com')
        clone.commit_content('b')  # commits never depend on global git config

    def test_clone_from_str(self, repo: Repo, tmpdir: TempDirectory) -> None:
        repo.commit_content('a')
        clone = Repo.clone(str(repo.path), 'clone')
        check_config_user(clone, 'Giterator', 'giterator@example.com')

    def test_clone_from_path_with_user(self, repo: Repo, tmpdir: TempDirectory) -> None:
        repo.commit_content('a')
        clone = Repo.clone(repo.path, 'clone', User('Foo', 'bar@example.com'))
        check_config_user(clone, 'Foo', 'bar@example.com')

    def test_clone_source_git_without_user(self, repo: Repo, tmpdir: TempDirectory) -> None:
        repo.commit_content('a')
        clone = Repo.clone(Git(repo.path), 'clone')
        check_config_user(clone, 'Giterator', 'giterator@example.com')

    def test_clone_inherits_source_user(self, tmpdir: TempDirectory) -> None:
        root = Path(tmpdir.path)
        upstream = Repo.make(root / 'upstream', User(name='Foo Bar', email='foo@example.com'))
        upstream.commit_content('a')
        clone = Repo.clone(upstream, root / 'clone')
        check_config_user(clone, 'Foo Bar', 'foo@example.com')

    def test_clone_non_testing(self, git: Git) -> None:
        (git.path / 'a').write_text('content')
        git.commit('a commit')
        clone = Repo.clone(git, 'clone')
        assert isinstance(clone, Repo)
        (commit,) = clone.git('log', '--format=%h').split()
        compare(
            clone.git('show', '--pretty=format:%s', '--stat', commit),
            expected=('a commit\n a | 1 +\n 1 file changed, 1 insertion(+)\n'),
        )

    def test_commit_content(self, repo: Repo) -> None:
        compare(repo.commit_content('a', datetime(2001, 1, 1, 10)), expected='5ee580a')

    def test_commit_content_full(self, repo: Repo) -> None:
        compare(
            repo.commit_content('a', datetime(2001, 1, 1, 10), short=False),
            expected='5ee580aba98816af22cfa4e76ddf96bb3994964b',
        )
