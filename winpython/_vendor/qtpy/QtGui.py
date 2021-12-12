#
# Copyright © 2014-2015 Colin Duquesnoy
# Copyright © 2009- The Spyder Development Team
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

"""
Provides QtGui classes and functions.
"""
from . import PYQT6, PYQT5, PYSIDE2, PYSIDE6, PythonQtError


if PYQT6:
    from PyQt6 import QtGui
    from PyQt6.QtGui import *

    # Map missing/renamed methods
    QDrag.exec_ = QDrag.exec
    QGuiApplication.exec_ = QGuiApplication.exec
    QTextDocument.print_ = QTextDocument.print

    # Allow unscoped access for enums inside the QtGui module
    from .enums_compat import promote_enums
    promote_enums(QtGui)
    del QtGui
elif PYQT5:
    from PyQt5.QtGui import *
elif PYSIDE2:
    from PySide2.QtGui import *
elif PYSIDE6:
    from PySide6.QtGui import *
    QFontMetrics.width = QFontMetrics.horizontalAdvance

    # Map DeprecationWarning methods
    QDrag.exec_ = QDrag.exec
    QGuiApplication.exec_ = QGuiApplication.exec
else:
    raise PythonQtError('No Qt bindings could be found')
