import os
from datetime import datetime, timezone

from testfixtures import TempDirectory, compare, ShouldRaise

from giterator import Git, User
from giterator.git import GitError
from giterator.testing import Repo


class TestCall:

    def test_bad_command(self, git: Git):
        with ShouldRaise(GitError) as s:
            git('wut')
        assert str(s.raised).startswith("'git wut' gave return code 1:")
        assert "git: 'wut' is not a git command" in str(s.raised)


class TestInit:

    def test_init(self, tmpdir: TempDirectory):
        tmpdir.makedir('foo')
        Git(tmpdir.getpath('foo')).init()
        assert os.path.exists(tmpdir.getpath('foo/.git'))

    def test_init_make_path(self, tmpdir):
        Git(tmpdir.getpath('foo/bar')).init()
        assert os.path.exists(tmpdir.getpath('foo/bar/.git'))

    def test_init_with_user(self, tmpdir: TempDirectory):
        Git(tmpdir.getpath('foo')).init(User(name='Foo Bar', email='foo@example.com'))
        config = tmpdir.read('foo/.git/config')
        assert b'name = Foo Bar' in config
        assert b'email = foo@example.com' in config


class TestClone:

    def test_minimal(self, repo: Repo, tmpdir: TempDirectory):
        hash = repo.commit_content('a')
        git = Git.clone(repo.path, tmpdir.getpath('clone'))
        commit, = git('log', '--format=%h').split()
        compare(hash, expected=commit)
        compare(git.git('show', '--pretty=format:%s', '--stat', commit), expected=(
            'a commit\n'
            ' a | 1 +\n'
            ' 1 file changed, 1 insertion(+)\n'
        ))
        compare(git('remote', '-v').split(), expected=[
            'origin', str(repo.path), '(fetch)',
            'origin', str(repo.path), '(push)'
        ])

    def test_with_user(self, repo: Repo, tmpdir: TempDirectory):
        repo.commit_content('a')
        git = Git.clone(
            repo.path, tmpdir.getpath('clone'), User(name='Foo Bar', email='foo@example.com')
        )
        config = (git.path / '.git' / 'config').read_text()
        assert 'name = Foo Bar' in config
        assert 'email = foo@example.com' in config

    def test_repo(self, repo: Repo, tmpdir: TempDirectory):
        repo.commit_content('a')
        source = Git(repo.path)
        git = Git.clone(source, tmpdir.getpath('clone'))
        commit, = git('log', '--format=%h').split()
        compare(git('show', '--pretty=format:%s', '--stat', commit), expected=(
            'a commit\n'
            ' a | 1 +\n'
            ' 1 file changed, 1 insertion(+)\n'
        ))


class TestCommit:

    def test_from_empty(self, git: Git):
        (git.path / 'a').write_text('content')
        git.commit('a commit')
        compare(git.git('status', '-s'), expected='')
        commit, = git.git('log', '--format=%h').split()
        compare(git.git('show', '--pretty=format:%s', '--stat', commit), expected=(
            'a commit\n'
            ' a | 1 +\n'
            ' 1 file changed, 1 insertion(+)\n'
        ))

    def test_from_one_commit(self, git: Git):
        (git.path / 'a').write_text('a content')
        (git.path / 'b').write_text('b content')
        (git.path / 'c').write_text('c content')
        git.commit('commit 1')
        (git.path / 'b').write_text('new content')
        (git.path / 'c').unlink()
        (git.path / 'd').write_text('d content')
        git.commit('commit 2')
        compare(git.git('status', '-s'), expected='')
        commit2, commit1 = git.git('log', '--format=%h').split()
        compare(git.git('show', '--pretty=format:%s', '--stat', commit1), expected=(
            'commit 1\n'
            ' a | 1 +\n'
            ' b | 1 +\n'
            ' c | 1 +\n'
            ' 3 files changed, 3 insertions(+)\n'
        ))
        compare(git.git('show', '--pretty=format:%s', '--stat', commit2), expected=(
            'commit 2\n'
            ' b | 2 +-\n'
            ' c | 1 -\n'
            ' d | 1 +\n'
            ' 3 files changed, 2 insertions(+), 2 deletions(-)\n'
        ))

    def test_with_author_date(self, git: Git):
        (git.path / 'content.txt').write_text('content')
        git.commit('commit', author_date=datetime(2000, 1, 1))
        compare(git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')

    def test_with_committer_date(self, git: Git):
        (git.path / 'content.txt').write_text('content')
        git.commit('commit', commit_date=datetime(2000, 1, 1))
        compare(git('log', '--pretty=format:%cd'), expected='Sat Jan 1 00:00:00 2000 +0000')

    def test_with_dates_as_strings(self, git: Git):
        (git.path / 'content.txt').write_text('content')
        git.commit('commit',
                   author_date='format:iso8601:'+datetime(2000, 1, 1).isoformat(),
                   commit_date='format:iso8601:'+datetime(2000, 1, 2).isoformat())
        compare(git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')
        compare(git('log', '--pretty=format:%cd'), expected='Sun Jan 2 00:00:00 2000 +0000')

    def test_with_naive_datetime(self, git: Git):
        (git.path / 'a').write_text('content')
        dt = datetime(2001, 1, 1, 10)
        git.commit('a commit', dt, dt)
        compare(git('log', '--format=%aI %cI'),
                expected='2001-01-01T10:00:00+00:00 2001-01-01T10:00:00+00:00\n')

    def test_with_tz_datetime(self, git: Git):
        (git.path / 'a').write_text('content')
        dt = datetime(2001, 1, 1, 10).astimezone(timezone.utc)
        git.commit('a commit', dt, dt)
        compare(git('log', '--format=%aI %cI'),
                expected='2001-01-01T10:00:00+00:00 2001-01-01T10:00:00+00:00\n')


class TestLabels:

    def test_rev_parse(self, repo: Repo):
        repo.commit_content('a', datetime(2001, 1, 1, 10))
        compare(repo.rev_parse('HEAD'), expected='5ee580a')

    def test_tags_empty(self, repo: Repo):
        compare(repo.tags(), expected=[])

    def test_tags(self, repo: Repo):
        repo.commit_content('a', tag='a-tag')
        repo.commit_content('b', tag='b-tag')
        compare(repo.tags(), expected=['a-tag', 'b-tag'])

    def test_tag_hashes_empty(self, repo: Repo):
        compare(repo.tag_hashes(), expected={})

    def test_tag_hashes(self, repo: Repo):
        repo.commit_content('a', tag='a-tag')
        repo.commit_content('b', tag='b-tag')
        compare(repo.tag_hashes(),
                expected={'a-tag': repo.rev_parse('a-tag'),
                          'b-tag': repo.rev_parse('b-tag')})

    def test_branches_empty(self, repo: Repo):
        compare(repo.branches(), expected=[])

    def test_branch(self, repo: Repo):
        repo.commit_content('a', branch='a-branch')
        repo.commit_content('b', branch='b-branch')
        compare(repo.branches(), expected=['a-branch', 'b-branch'])

    def test_branch_hashes_empty(self, repo: Repo):
        compare(repo.branch_hashes(), expected={})

    def test_branch_hashes(self, repo: Repo):
        repo.commit_content('a', branch='a-branch')
        repo.commit_content('b', branch='b-branch')
        compare(repo.branch_hashes(),
                expected={'a-branch': repo.rev_parse('a-branch'),
                          'b-branch': repo.rev_parse('b-branch')})
