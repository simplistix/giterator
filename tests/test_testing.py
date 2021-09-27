from datetime import datetime

from testfixtures import TempDirectory, compare


class TestGit:

    def test_commit_with_one_date(self, tmpdir: TempDirectory, git):
        (git.path / 'content.txt').write_text('content')
        git.commit('commit', datetime(2000, 1, 1))
        compare(git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')
        compare(git('log', '--pretty=format:%cd'), expected='Sat Jan 1 00:00:00 2000 +0000')

    def test_commit_with_both_dates(self, tmpdir: TempDirectory, git):
        (git.path / 'content.txt').write_text('content')
        git.commit('commit', datetime(2000, 1, 1), datetime(2000, 1, 2))
        compare(git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')
        compare(git('log', '--pretty=format:%cd'), expected='Sun Jan 2 00:00:00 2000 +0000')

    def test_commit_with_both_dates_explicit(self, tmpdir: TempDirectory, git):
        (git.path / 'content.txt').write_text('content')
        git.commit('commit', author_date=datetime(2000, 1, 1), commit_date=datetime(2000, 1, 2))
        compare(git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')
        compare(git('log', '--pretty=format:%cd'), expected='Sun Jan 2 00:00:00 2000 +0000')
