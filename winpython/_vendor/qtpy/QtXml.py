# -----------------------------------------------------------------------------
# Copyright © 2009- The Spyder Development Team
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Provides QtXml classes and functions."""

# Local imports
from . import PYSIDE2, PYSIDE6, PYQT5, PYQT6, PythonQtError

if PYQT5:
    from PyQt5.QtXml import *
elif PYQT6:
    from PyQt6.QtXml import *
elif PYSIDE6:
    from PySide6.QtXml import *
elif PYSIDE2:
    from PySide2.QtXml import *
else:
    raise PythonQtError('No Qt bindings could be found')
