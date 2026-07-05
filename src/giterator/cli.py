from argparse import ArgumentParser, Namespace
from datetime import datetime
from glob import glob
from os import makedirs
from pathlib import Path
from re import sub
from shutil import copy2

from .git import Git
from .iterate import read


def split_mapping(mapping: str, sep: str) -> tuple[str, str]:
    source, found, target = mapping.partition(sep)
    if not found:
        raise SystemExit(f'mapping must contain {sep!r}')
    return source, target


class Command:
    def add_args(self, parser: ArgumentParser) -> None:
        parser.add_argument('--repo', type=Path, required=True, help='The repo to work with.')
        parser.add_argument('--sep', default=':', help='The separator used in the mapping.')
        parser.add_argument('mapping', help='A source and target, separated by --sep.')

    def __call__(self, args: Namespace) -> None: ...


class Pack(Command):
    """
    Commit dated files matching a strftime pattern to a repo.
    """

    def __call__(self, args: Namespace) -> None:
        pattern, name = split_mapping(args.mapping, args.sep)
        pattern = str(Path(pattern).expanduser())
        repo = Git(args.repo.expanduser())
        if not (repo.path / '.git').exists():
            repo.init()
        found = []
        for source in glob(sub('%[a-zA-Z]', '*', pattern)):
            try:
                at = datetime.strptime(source, pattern)
            except ValueError:
                continue
            found.append((at, source))
        for at, source in sorted(found):
            copy2(source, repo.path / name)
            rev = repo.commit(Path(source).name, author_date=at, commit_date=at, allow_empty=True)
            print(rev, source)


class Unpack(Command):
    """
    Write files matching a glob pattern to dated copies for each commit in a repo.
    """

    def __call__(self, args: Namespace) -> None:
        pattern, target = split_mapping(args.mapping, args.sep)
        target = str(Path(target).expanduser())
        for giteration in read(args.repo.expanduser()):
            assert giteration.at is not None
            for path in sorted(giteration.path.glob(pattern)):
                if '.git' in path.parts:
                    continue
                dest = Path(giteration.at.strftime(target))
                makedirs(dest.parent, exist_ok=True)
                copy2(path, dest)
                print(dest)


def parse_args() -> Namespace:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True
    for command_class in Command.__subclasses__():
        command_parser = subparsers.add_parser(
            command_class.__name__.lower(), help=command_class.__doc__
        )
        command = command_class()
        command.add_args(command_parser)
        command_parser.set_defaults(command=command)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.command(args)
