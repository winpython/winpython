# -----------------------------------------------------------------------------
# Copyright © 2009- The Spyder Development Team
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Provides QtMultimediaWidgets classes and functions."""

# Local imports
from . import PYSIDE2, PYSIDE6, PYQT5, PYQT6, PythonQtError

if PYQT5:
    from PyQt5.QtMultimediaWidgets import *
elif PYQT6:
    from PyQt6.QtMultimediaWidgets import *
elif PYSIDE2:
    from PySide2.QtMultimediaWidgets import *
elif PYSIDE6:
    from PySide6.QtMultimediaWidgets import *
else:
    raise PythonQtError('No Qt bindings could be found')
