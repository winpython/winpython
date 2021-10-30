# -----------------------------------------------------------------------------
# Copyright © 2009- The Spyder Development Team
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Provides Qt3DInput classes and functions."""

# Local imports
from . import PYQT5, PYQT6, PYSIDE2, PYSIDE6, PythonQtError

if PYQT5:
    from PyQt5.Qt3DInput import *
elif PYQT6:
    from PyQt6.Qt3DInput import *
elif PYSIDE6:
    from PySide6.Qt3DInput.Qt3DInput import *
elif PYSIDE2:
    # https://bugreports.qt.io/projects/PYSIDE/issues/PYSIDE-1026
    import PySide2.Qt3DInput as __temp
    import inspect
    for __name in inspect.getmembers(__temp.Qt3DInput):
        globals()[__name[0]] = __name[1]
else:
    raise PythonQtError('No Qt bindings could be found')
