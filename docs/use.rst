.. py:currentmodule:: giterator

Using giterator
===============


Installation
~~~~~~~~~~~~

giterator is available on the `Python Package Index`__ and can be installed
with any tools for managing Python environments.

__ https://pypi.org


giterator unpack --repo ~/vcs/git/foo --sep : '*.csv:~/Downloads/foo-%Y-%m-%d.csv'


giterator pack --repo ~/vcs/git/foo --sep : '~/Downloads/foo-%Y-%m-%d.csv:foo.csv'

Original answer (mid 2014)

The --date option (introduced in commit 02b47cd in Dec. 2009, for git1.7.0) uses the same format than for GIT_AUTHOR_DATE, with date formats tested in commit 96b2d4f:

There you can see the various format accepted:

rfc2822: Mon, 3 Jul 2006 17:18:43 +0200
iso8601: 2006-07-03 17:18:43 +0200
local: Mon Jul 3 15:18:43 2006
short: 2006-07-03 (not in 1.9.1, works in 2.3.0)
relative: see commit 34dc6e7:

5.seconds.ago,
2.years.3.months.ago,
'6am yesterday'
raw: see commit 7dff9b3 (git 1.6.2, March 2009)
internal raw git format - seconds since epoch plus timezone
(put another way: 'date +"%s %z"' format)

default: Mon Jul 3 17:18:43 2006 +0200

https://stackoverflow.com/questions/19742345/what-is-the-format-for-date-parameter-of-git-commit
