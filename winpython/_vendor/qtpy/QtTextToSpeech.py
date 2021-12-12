# -----------------------------------------------------------------------------
# Copyright © 2009- The Spyder Development Team
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Provides QtTextToSpeech classes and functions."""

from . import PYQT5, PYSIDE2, PythonQtError

if PYQT5:
    from PyQt5.QtTextToSpeech import *
elif PYSIDE2:
    from PySide2.QtTextToSpeech import *
else:
    raise PythonQtError('No Qt bindings could be found')
