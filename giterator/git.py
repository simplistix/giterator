from os import makedirs
from pathlib import Path
from subprocess import check_output, STDOUT
from typing import Union


class User:

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email


class Git:

    def __init__(self, path: Union[Path, str]):
        if not isinstance(path, Path):
            path = Path(path)
        self.path: Path = path

    def init(self, user: User = None):
        makedirs(self.path, exist_ok=True)
        self('init')
        if user:
            self('config', 'user.name', user.name)
            self('config', 'user.email', user.email)

    def __call__(self, *command):
        return check_output(('git',) + command, cwd=self.path, stderr=STDOUT)
