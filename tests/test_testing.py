from datetime import datetime

from testfixtures import compare

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
