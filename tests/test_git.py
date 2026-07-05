import os
from datetime import datetime, timezone

import pytest
from testfixtures import TempDirectory, compare, ShouldRaise, StringComparison

from giterator import Commit, Git, User
from giterator.git import GitError
from giterator.testing import DEFAULT_USER, Repo


class TestCall:
    def test_bad_command(self, git: Git) -> None:
        with ShouldRaise(GitError) as s:
            git('wut')
        compare(
            str(s.raised),
            expected=StringComparison(
                r"(?s)'git wut' gave return code 1:.*git: 'wut' is not a git command.*"
            ),
        )


class TestInit:
    def test_init(self, tmpdir: TempDirectory) -> None:
        tmpdir.makedir('foo')
        Git(tmpdir.getpath('foo')).init()
        assert os.path.exists(tmpdir.getpath('foo/.git'))

    def test_init_make_path(self, tmpdir: TempDirectory) -> None:
        Git(tmpdir.getpath('foo/bar')).init()
        assert os.path.exists(tmpdir.getpath('foo/bar/.git'))

    def test_init_with_user(self, tmpdir: TempDirectory) -> None:
        Git(tmpdir.getpath('foo')).init(User(name='Foo Bar', email='foo@example.com'))
        config = tmpdir.read('foo/.git/config', encoding='utf-8')
        compare(
            config,
            expected=StringComparison(r'(?s).*name = Foo Bar.*email = foo@example\.com.*'),
        )

    def test_init_with_branch(self, tmpdir: TempDirectory) -> None:
        git = Git(tmpdir.getpath('foo'))
        git.init(branch='trunk')
        compare(git('symbolic-ref', 'HEAD'), expected='refs/heads/trunk\n')


class TestClone:
    def test_minimal(self, repo: Repo, tmpdir: TempDirectory) -> None:
        hash = repo.commit_content('a')
        git = Git.clone(repo.path, tmpdir.getpath('clone'))
        (commit,) = git('log', '--format=%h').split()
        compare(hash, expected=commit)
        compare(
            git.git('show', '--pretty=format:%s', '--stat', commit),
            expected=('a commit\n a | 1 +\n 1 file changed, 1 insertion(+)\n'),
        )
        compare(
            git('remote', '-v').split(),
            expected=['origin', str(repo.path), '(fetch)', 'origin', str(repo.path), '(push)'],
        )

    def test_with_user(self, repo: Repo, tmpdir: TempDirectory) -> None:
        repo.commit_content('a')
        git = Git.clone(
            repo.path, tmpdir.getpath('clone'), User(name='Foo Bar', email='foo@example.com')
        )
        config = (git.path / '.git' / 'config').read_text()
        compare(
            config,
            expected=StringComparison(r'(?s).*name = Foo Bar.*email = foo@example\.com.*'),
        )

    def test_repo(self, repo: Repo, tmpdir: TempDirectory) -> None:
        repo.commit_content('a')
        source = Git(repo.path)
        git = Git.clone(source, tmpdir.getpath('clone'))
        (commit,) = git('log', '--format=%h').split()
        compare(
            git('show', '--pretty=format:%s', '--stat', commit),
            expected=('a commit\n a | 1 +\n 1 file changed, 1 insertion(+)\n'),
        )


class TestCommit:
    def test_from_empty(self, git: Git) -> None:
        (git.path / 'a').write_text('content')
        git.commit('a commit')
        compare(git.git('status', '-s'), expected='')
        (commit,) = git.git('log', '--format=%h').split()
        compare(
            git.git('show', '--pretty=format:%s', '--stat', commit),
            expected=('a commit\n a | 1 +\n 1 file changed, 1 insertion(+)\n'),
        )

    def test_from_one_commit(self, git: Git) -> None:
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
        compare(
            git.git('show', '--pretty=format:%s', '--stat', commit1),
            expected=(
                'commit 1\n a | 1 +\n b | 1 +\n c | 1 +\n 3 files changed, 3 insertions(+)\n'
            ),
        )
        compare(
            git.git('show', '--pretty=format:%s', '--stat', commit2),
            expected=(
                'commit 2\n'
                ' b | 2 +-\n'
                ' c | 1 -\n'
                ' d | 1 +\n'
                ' 3 files changed, 2 insertions(+), 2 deletions(-)\n'
            ),
        )

    def test_with_author_date(self, git: Git) -> None:
        (git.path / 'content.txt').write_text('content')
        git.commit('commit', author_date=datetime(2000, 1, 1))
        compare(git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')

    def test_with_committer_date(self, git: Git) -> None:
        (git.path / 'content.txt').write_text('content')
        git.commit('commit', commit_date=datetime(2000, 1, 1))
        compare(git('log', '--pretty=format:%cd'), expected='Sat Jan 1 00:00:00 2000 +0000')

    def test_with_dates_as_strings(self, git: Git) -> None:
        (git.path / 'content.txt').write_text('content')
        git.commit(
            'commit',
            author_date='format:iso8601:' + datetime(2000, 1, 1).isoformat(),
            commit_date='format:iso8601:' + datetime(2000, 1, 2).isoformat(),
        )
        compare(git('log', '--pretty=format:%ad'), expected='Sat Jan 1 00:00:00 2000 +0000')
        compare(git('log', '--pretty=format:%cd'), expected='Sun Jan 2 00:00:00 2000 +0000')

    def test_with_naive_datetime(self, git: Git) -> None:
        (git.path / 'a').write_text('content')
        dt = datetime(2001, 1, 1, 10)
        git.commit('a commit', dt, dt)
        compare(
            git('log', '--format=%aI %cI').replace("Z", "+00:00"),
            expected='2001-01-01T10:00:00+00:00 2001-01-01T10:00:00+00:00\n',
        )

    def test_multi_line_message(self, git: Git) -> None:
        (git.path / 'a').write_text('content')
        git.commit('subject\n\nbody line 1\nbody line 2')
        compare(git('log', '--format=%B'), expected='subject\n\nbody line 1\nbody line 2\n\n')

    def test_identity_from_environment(
        self, tmpdir: TempDirectory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Only environment variables carry identity here, no repo-local
        # user.name/email and no reliance on the machine's global git config,
        # so this fails unless env is merged with the process environment
        # rather than replacing it for the internal 'git commit' call.
        monkeypatch.setenv('GIT_AUTHOR_NAME', 'Env Author')
        monkeypatch.setenv('GIT_AUTHOR_EMAIL', 'env@example.com')
        monkeypatch.setenv('GIT_COMMITTER_NAME', 'Env Author')
        monkeypatch.setenv('GIT_COMMITTER_EMAIL', 'env@example.com')
        git = Git(tmpdir.getpath('env-repo'))
        git.init()
        (git.path / 'a').write_text('content')
        git.commit('a commit', commit_date=datetime(2000, 1, 1))
        compare(git('log', '--format=%an <%ae>'), expected='Env Author <env@example.com>\n')

    def test_nothing_to_commit(self, git: Git) -> None:
        (git.path / 'a').write_text('content')
        git.commit('commit 1')
        with ShouldRaise(GitError) as s:
            git.commit('commit 2')
        compare(
            str(s.raised),
            expected=StringComparison(r'(?s).*gave return code 1:.*nothing to commit.*'),
        )

    def test_nothing_to_commit_allow_empty(self, git: Git) -> None:
        (git.path / 'a').write_text('content')
        git.commit('commit 1')
        git.commit('commit 2', allow_empty=True)
        compare(git('log', '--reverse', '--format=%s'), expected='commit 1\ncommit 2\n')

    def test_with_tz_datetime(self, git: Git) -> None:
        (git.path / 'a').write_text('content')
        dt = datetime(2001, 1, 1, 10).astimezone(timezone.utc)
        git.commit('a commit', dt, dt)
        compare(
            git('log', '--format=%aI %cI').replace("Z", "+00:00"),
            expected='2001-01-01T10:00:00+00:00 2001-01-01T10:00:00+00:00\n',
        )


class TestLog:
    def test_empty_repo(self, repo: Repo) -> None:
        with ShouldRaise(GitError):
            repo.log()

    def test_commits(self, repo: Repo) -> None:
        rev_1 = repo.commit_content('a', datetime(2001, 1, 1, 10, tzinfo=timezone.utc))
        rev_2 = repo.commit_content('b', datetime(2001, 1, 2, 12, tzinfo=timezone.utc))
        compare(
            repo.log(),
            expected=[
                Commit(
                    rev=rev_2,
                    author=DEFAULT_USER,
                    author_date=datetime(2001, 1, 2, 12, tzinfo=timezone.utc),
                    committer=DEFAULT_USER,
                    committer_date=datetime(2001, 1, 2, 12, tzinfo=timezone.utc),
                    message='a commit',
                ),
                Commit(
                    rev=rev_1,
                    author=DEFAULT_USER,
                    author_date=datetime(2001, 1, 1, 10, tzinfo=timezone.utc),
                    committer=DEFAULT_USER,
                    committer_date=datetime(2001, 1, 1, 10, tzinfo=timezone.utc),
                    message='a commit',
                ),
            ],
        )

    def test_options(self, repo: Repo) -> None:
        rev_1 = repo.commit_content('a', datetime(2001, 1, 1, 10, tzinfo=timezone.utc))
        rev_2 = repo.commit_content('b', datetime(2001, 1, 2, 12, tzinfo=timezone.utc))
        compare(
            [commit.rev for commit in repo.log('--reverse')],
            expected=[rev_1, rev_2],
        )
        compare(
            [commit.rev for commit in repo.log('-1')],
            expected=[rev_2],
        )

    def test_multi_line_message(self, git: Git) -> None:
        (git.path / 'a').write_text('a content')
        git.commit('subject\n\nbody line 1\nbody line 2', datetime(2001, 1, 1))
        (git.path / 'b').write_text('b content')
        git.commit('another commit', datetime(2001, 1, 2))
        compare(
            [commit.message for commit in git.log()],
            expected=['another commit', 'subject\n\nbody line 1\nbody line 2'],
        )


class TestLabels:
    def test_rev_parse(self, repo: Repo) -> None:
        repo.commit_content('a', datetime(2001, 1, 1, 10))
        compare(repo.rev_parse('HEAD'), expected='5ee580a')

    def test_rev_parse_full(self, repo: Repo) -> None:
        repo.commit_content('a', datetime(2001, 1, 1, 10))
        compare(
            repo.rev_parse('HEAD', short=False), expected='5ee580aba98816af22cfa4e76ddf96bb3994964b'
        )

    def test_tags_empty(self, repo: Repo) -> None:
        compare(repo.tags(), expected=[])

    def test_tags(self, repo: Repo) -> None:
        repo.commit_content('a', tag='a-tag')
        repo.commit_content('b', tag='b-tag')
        compare(repo.tags(), expected=['a-tag', 'b-tag'])

    def test_tag_hashes_empty(self, repo: Repo) -> None:
        compare(repo.tag_hashes(), expected={})

    def test_tag_hashes(self, repo: Repo) -> None:
        repo.commit_content('a', tag='a-tag')
        repo.commit_content('b', tag='b-tag')
        compare(
            repo.tag_hashes(),
            expected={'a-tag': repo.rev_parse('a-tag'), 'b-tag': repo.rev_parse('b-tag')},
        )

    def test_branches_empty(self, repo: Repo) -> None:
        compare(repo.branches(), expected=[])

    def test_branch(self, repo: Repo) -> None:
        repo.commit_content('a', branch='a-branch')
        repo.commit_content('b', branch='b-branch')
        compare(repo.branches(), expected=['a-branch', 'b-branch'])

    def test_branch_hashes_empty(self, repo: Repo) -> None:
        compare(repo.branch_hashes(), expected={})

    def test_branch_hashes(self, repo: Repo) -> None:
        repo.commit_content('a', branch='a-branch')
        repo.commit_content('b', branch='b-branch')
        compare(
            repo.branch_hashes(),
            expected={
                'a-branch': repo.rev_parse('a-branch'),
                'b-branch': repo.rev_parse('b-branch'),
            },
        )
