#!/usr/bin/env python

import io

from setuptools import setup, find_packages

readme = io.open('README.md').read()

setup(
    name='emailx',
    version='0.1.1504223903',
    url='https://github.com/djrobstep/emailx',
    description='easy as hell email sending for python',
    long_description=readme,
    author='Robert Lechte',
    author_email='robertlechte@gmail.com',
    install_requires=[
        'six'
    ],
    zip_safe=False,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ]
)
