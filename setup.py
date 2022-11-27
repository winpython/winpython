# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
WinPython
=========

The WinPython distribution tools (wppm, ...)
"""

# for wheels creation
import setuptools

from distutils.core import setup
import os
from pathlib import Path

def get_package_data(name, extlist):
    """Return data files for package *name* with extensions in *extlist*"""
    flist = []
    # Workaround to replace os.path.relpath (not available until Python 2.6):
    offset = len(name) + len(os.pathsep)
    for dirpath, _dirnames, filenames in os.walk(name):
        for fname in filenames:
            if (
                not fname.startswith('.')
                and Path(fname).suffix in extlist
            ):
                flist.append(
                    str(Path(dirpath) / fname)[offset:]
                )
    return flist


def get_subpackages(name):
    """Return subpackages of package *name*"""
    splist = []
    for dirpath, _dirnames, _filenames in os.walk(name):
        if (Path(dirpath) / '__init__.py').is_file():
            splist.append(".".join(dirpath.split(os.sep)))
    return splist


NAME = LIBNAME = 'winpython'
from winpython import __version__, __project_url__

PROJECT_NAME = 'WinPython'

setup(
    name=NAME,
    version=__version__,
    description='%s distribution tools, including WPPM'
    % PROJECT_NAME,
    long_description="""%s is a portable distribution of the Python programming language
for Windows. It is a full-featured Python-based scientific environment, :
including a package manager, WPPM."""
    % PROJECT_NAME,
    download_url='%s/files/%s-%s.zip'
    % (__project_url__, NAME, __version__),
    author="Pierre Raybaut",
    author_email='pierre.raybaut@gmail.com',
    url=__project_url__,
    license='MIT',
    keywords='PyQt5 PyQt4 PySide',
    platforms=['any'],
    packages=get_subpackages(LIBNAME),
    package_data={
        LIBNAME: get_package_data(
            LIBNAME,
            (
                '.mo',
                '.svg',
                '.png',
                '.css',
                '.html',
                '.js',
                '.ini',
            ),
        )
    },
    # use setuptools functionalities
    entry_points={
        'console_scripts': [
            'wpcp = winpython.controlpanel:main',
            'wppm = winpython.wppm:main',
        ]
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Development Status :: 5 - Production/Stable',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Widget Sets',
    ],
)
