# -----------------------------------------------------------------------------
# Copyright © 2009- The Spyder Development Team
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Provides QtOpenGL classes and functions."""

# Local imports
from . import PYQT5, PYSIDE2, PythonQtError

if PYQT5:
    from PyQt5.QtOpenGL import *
elif PYQT6:
    from PyQt6.QtOpenGL import *
elif PYSIDE6:
    from PySide6.QtOpenGL import *
elif PYSIDE2:
    from PySide2.QtOpenGL import *
else:
    raise PythonQtError('No Qt bindings could be found')

