import os
from collections.abc import Iterator
from doctest import ELLIPSIS, REPORT_NDIFF

import pytest
from sybil import Sybil
from sybil.parsers.rest import DocTestParser, PythonCodeBlockParser, SkipParser
from testfixtures import Replacer, TempDirectory

GIT_CONFIG = b'[user]\n\tname = Giterator\n\temail = giterator@example.com\n'


@pytest.fixture(scope='module')
def sandbox() -> Iterator[None]:
    # Module scope makes this one sandbox per document: examples create real
    # repos with relative paths, so each document runs in its own temporary
    # directory, with git pointed away from the machine's own configuration.
    with TempDirectory(cwd=True) as tempdir, Replacer() as replace:
        replace.in_environ('GIT_CONFIG_GLOBAL', tempdir.write('gitconfig', GIT_CONFIG))
        replace.in_environ('GIT_CONFIG_SYSTEM', os.devnull)
        yield


pytest_collect_file = Sybil(
    parsers=[
        DocTestParser(optionflags=REPORT_NDIFF | ELLIPSIS),
        PythonCodeBlockParser(),
        SkipParser(),
    ],
    pattern='*.rst',
    fixtures=['sandbox', 'tmp_path'],
).pytest()
