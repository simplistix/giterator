# See license.txt for license details.
# Copyright (c) 2020-2021, Chris Withers

import os

from setuptools import setup, find_packages

base_dir = os.path.dirname(__file__)

setup(
    name='giterator',
    version='0.3.0',
    author='Chris Withers',
    author_email='chris@withers.org',
    license='MIT',
    description=(
        "Python tools for doing git things."
    ),
    long_description=open('README.rst').read(),
    url='https://github.com/simplistix/giterator',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    packages=find_packages(exclude=["tests"]),
    zip_safe=False,
    include_package_data=True,
    python_requires=">=3.9",
    extras_require=dict(
        test=[
            'coverage-enable-subprocess',
            'pytest',
            'pytest-cov',
            'sybil',
            'testfixtures',
        ],
        build=['furo', 'sphinx', 'setuptools-git', 'twine', 'wheel']
    ),
    entry_points={
        'console_scripts': ['giterator=giterator.cli:main'],
    }
)
