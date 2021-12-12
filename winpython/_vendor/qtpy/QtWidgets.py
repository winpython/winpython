#
# Copyright © 2014-2015 Colin Duquesnoy
# Copyright © 2009- The Spyder Developmet Team
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

"""
Provides widget classes and functions.
"""
from . import PYQT5, PYQT6, PYSIDE2, PYSIDE6, PythonQtError


if PYQT6:
    from PyQt6 import QtWidgets
    from PyQt6.QtWidgets import *
    from PyQt6.QtGui import QAction, QActionGroup, QShortcut
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget

    # Map missing/renamed methods
    QTextEdit.setTabStopWidth = QTextEdit.setTabStopDistance
    QTextEdit.tabStopWidth = QTextEdit.tabStopDistance
    QTextEdit.print_ = QTextEdit.print
    QPlainTextEdit.setTabStopWidth = QPlainTextEdit.setTabStopDistance
    QPlainTextEdit.tabStopWidth = QPlainTextEdit.tabStopDistance
    QPlainTextEdit.print_ = QPlainTextEdit.print
    QApplication.exec_ = QApplication.exec
    QDialog.exec_ = QDialog.exec
    QMenu.exec_ = QMenu.exec

    # Allow unscoped access for enums inside the QtWidgets module
    from .enums_compat import promote_enums
    promote_enums(QtWidgets)
    del QtWidgets
elif PYQT5:
    from PyQt5.QtWidgets import *
elif PYSIDE6:
    from PySide6.QtWidgets import *
    from PySide6.QtGui import QAction, QActionGroup, QShortcut
    from PySide6.QtOpenGLWidgets import QOpenGLWidget

    # Map missing/renamed methods
    QTextEdit.setTabStopWidth = QTextEdit.setTabStopDistance
    QTextEdit.tabStopWidth = QTextEdit.tabStopDistance
    QPlainTextEdit.setTabStopWidth = QPlainTextEdit.setTabStopDistance
    QPlainTextEdit.tabStopWidth = QPlainTextEdit.tabStopDistance

    # Map DeprecationWarning methods
    QApplication.exec_ = QApplication.exec
    QDialog.exec_ = QDialog.exec
    QMenu.exec_ = QMenu.exec
elif PYSIDE2:
    from PySide2.QtWidgets import *
else:
    raise PythonQtError('No Qt bindings could be found')
