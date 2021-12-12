#
# Copyright © 2014-2015 Colin Duquesnoy
# Copyright © 2009- The Spyder Developmet Team
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

"""
Provides QtTest and functions
"""

from . import PYQT5, PYQT6, PYSIDE6, PYSIDE2, PythonQtError

if PYQT6:
    from PyQt6 import QtTest
    from PyQt6.QtTest import *

    # Allow unscoped access for enums inside the QtTest module
    from .enums_compat import promote_enums
    promote_enums(QtTest)
    del QtTest
elif PYQT5:
    from PyQt5.QtTest import *
elif PYSIDE6:
    from PySide6.QtTest import *
elif PYSIDE2:
    from PySide2.QtTest import *
else:
    raise PythonQtError('No Qt bindings could be found')
