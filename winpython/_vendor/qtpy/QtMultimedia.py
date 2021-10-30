import warnings

from . import PYQT5, PYQT6
from . import PYSIDE2
from . import PYSIDE6

if PYQT5:
    from PyQt5.QtMultimedia import *
elif PYQT6:
    from PyQt6.QtMultimedia import *
elif PYSIDE6:
    from PySide6.QtMultimedia import *
elif PYSIDE2:
    from PySide2.QtMultimedia import *
else:
    raise PythonQtError('No Qt bindings could be found')
