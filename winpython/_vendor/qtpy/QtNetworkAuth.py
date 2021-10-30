# -----------------------------------------------------------------------------
# Copyright © 2009- The Spyder Development Team
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Provides QtNetworkAuth classes and functions."""

# Local imports
from . import PYQT5, PYQT6, PYSIDE2, PYSIDE6, PythonQtError

if PYQT6:
    from PyQt6.QtNetworkAuth import *
elif PYQT5:
    from PyQt5.QtNetworkAuth import *
elif PYSIDE6:
    from PySide6.QtNetworkAuth import *
else:
    raise PythonQtError('No Qt bindings could be found')
