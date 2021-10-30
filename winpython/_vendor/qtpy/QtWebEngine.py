#
# Copyright © 2014-2015 Colin Duquesnoy
# Copyright © 2009- The Spyder development Team
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

"""
Provides QtWebEngine classes and functions.
"""

from . import PYQT5, PYSIDE6

if PYQT5:
    from PyQt5.QtWebEngine import *
elif PYSIDE6:
    from PySide6.QtWebEngine import *
else:
    raise PythonQtError('No Qt bindings could be found')
