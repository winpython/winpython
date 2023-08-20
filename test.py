# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
Created on Thu Oct 04 11:02:40 2012

@author: Pierre Raybaut
"""

import sys
import os
from pathlib import Path
import re

# Local imports
from winpython import utils, wppm


def test_python_packages(pyver):
    """Check if all Python packages are supported by WinPython"""
    basedir = utils.get_basedir(pyver)
    for suffix in ('src', 'win32', 'win-amd64'):
        dirname = str(Path(basedir) / f'packages.{suffix}')
        for name in os.listdir(dirname):
            if (Path(dirname) / name).is_file() \
               and not re.match(r'python-([0-9\.]*)(\.amd64)?\.msi', name):
                try:
                    print(wppm.Package(name))
                    print('')
                except:
                    print('failed: %s' % name, file=sys.stderr)


if __name__ == '__main__':
    test_python_packages('2.7')
    test_python_packages('3.3')