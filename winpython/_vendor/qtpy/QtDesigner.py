#
# Copyright © 2014-2015 Colin Duquesnoy
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

"""
Provides QtDesigner classes and functions.
"""

from . import PYQT5, PYQT6, PYSIDE6, PythonQtError


if PYQT5:
    from PyQt5.QtDesigner import *
elif PYQT6:
    from PyQt6.QtDesigner import *
elif PYSIDE6:
    from PySide6.QtDesigner import *
else:
    raise PythonQtError('No Qt bindings could be found')
