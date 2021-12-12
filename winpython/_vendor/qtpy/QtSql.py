# -----------------------------------------------------------------------------
# Copyright © 2009- The Spyder Development Team
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Provides QtSql classes and functions."""

# Local imports
from . import PYQT5, PYQT6, PYSIDE6, PYSIDE2, PythonQtError

if PYQT5:
    from PyQt5.QtSql import *
elif PYQT6:
    from PyQt6.QtSql import *
    QSqlDatabase.exec_ = QSqlDatabase.exec
    QSqlQuery.exec_ = QSqlQuery.exec
    QSqlResult.exec_ = QSqlResult.exec
elif PYSIDE6:
    from PySide6.QtSql import *
    # Map DeprecationWarning methods
    QSqlDatabase.exec_ = QSqlDatabase.exec
    QSqlQuery.exec_ = QSqlQuery.exec
    QSqlResult.exec_ = QSqlResult.exec
elif PYSIDE2:
    from PySide2.QtSql import *
else:
    raise PythonQtError('No Qt bindings could be found')

