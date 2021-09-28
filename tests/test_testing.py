from datetime import datetime
from pathlib import Path

from testfixtures import compare, TempDirectory

from giterator import Git, User
from giterator.testing import Repo


class TestRepo:

    def test_commit_with_one_date(self, repo: Repo):
        (repo.path / 'content.txt').write_text('content')
        repo.commit('commit', datetime(2000, 1, 1))
        compare(repo.git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')
        compare(repo.git('log', '--pretty=format:%cd'), expected='Sat Jan 1 00:00:00 2000 +0000')

    def test_commit_with_both_dates(self, repo: Repo):
        (repo.path / 'content.txt').write_text('content')
        repo.commit('commit', datetime(2000, 1, 1), datetime(2000, 1, 2))
        compare(repo.git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')
        compare(repo.git('log', '--pretty=format:%cd'), expected='Sun Jan 2 00:00:00 2000 +0000')

    def test_commit_with_both_dates_explicit(self, repo: Repo):
        (repo.path / 'content.txt').write_text('content')
        repo.commit('commit', author_date=datetime(2000, 1, 1), commit_date=datetime(2000, 1, 2))
        compare(repo.git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')
        compare(repo.git('log', '--pretty=format:%cd'), expected='Sun Jan 2 00:00:00 2000 +0000')

    def test_clone(self, tmpdir: TempDirectory):
        root = Path(tmpdir.path)
        upstream = Repo.make(root / 'upstream')
        upstream.commit_content('a')
        clone = Repo.clone(upstream, root / 'clone')
        tmpdir.check('clone', 'upstream')
        config = (clone.path / '.git' / 'config').read_text()
        assert 'name = Giterator' in config
        assert 'email = giterator@example.com' in config

    def test_with_user(self, repo: Repo, tmpdir: TempDirectory):
        repo.commit_content('a')
        clone = Repo.clone(repo, 'clone', User('Foo', 'bar@example.com'))
        tmpdir.check('clone', 'repo')
        config = (clone.path / '.git' / 'config').read_text()
        assert 'name = Foo' in config
        assert 'email = bar@example.com' in config

    def test_clone_non_testing(self, git: Git):
        (git.path / 'a').write_text('content')
        git.commit('a commit')
        clone = Repo.clone(git, 'clone')
        assert isinstance(clone, Repo)
        commit, = clone.git('log', '--format=%h').split()
        compare(clone.git('show', '--pretty=format:%s', '--stat', commit), expected=(
            'a commit\n'
            ' a | 1 +\n'
            ' 1 file changed, 1 insertion(+)\n'
        ))
