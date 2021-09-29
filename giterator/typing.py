from datetime import date, datetime
from enum import Enum
from typing import Union, Sequence, Dict, Tuple


def parse_date(text):
    return datetime.utcfromtimestamp(int(text))


class LogFormat(Enum):

    hash = '%H'
    author_name = '%an'
    author_email = '%ae'
    author_date = '%at', parse_date
    committer_name = '%cn'
    committer_email = '%ce'
    committer_date = '%ct', parse_date


Date = Union[date, datetime, str]

LogConverter = Tuple[str, callable]
LogFormatMapping = Dict[str, Union[str, LogConverter]]
LogAttribute = Union[LogFormat, str, LogFormatMapping]
LogAttributes = Sequence[LogAttribute]
