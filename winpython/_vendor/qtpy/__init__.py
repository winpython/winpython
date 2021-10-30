#
# Copyright © 2009- The Spyder Development Team
# Copyright © 2014-2015 Colin Duquesnoy
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

"""
**QtPy** is a shim over the various Python Qt bindings. It is used to write
Qt binding independent libraries or applications.

If one of the APIs has already been imported, then it will be used.

Otherwise, the shim will automatically select the first available API (PyQt5, PyQt6,
PySide2 and PySide6); in that case, you can force the use of one
specific bindings (e.g. if your application is using one specific bindings and
you need to use library that use QtPy) by setting up the ``QT_API`` environment
variable.

PyQt5
=====

For PyQt5, you don't have to set anything as it will be used automatically::

    >>> from qtpy import QtGui, QtWidgets, QtCore
    >>> print(QtWidgets.QWidget)

PyQt6
=====

    >>> import os
    >>> os.environ['QT_API'] = 'pyqt6'
    >>> from qtpy import QtGui, QtWidgets, QtCore
    >>> print(QtWidgets.QWidget)

PySide2
======

Set the QT_API environment variable to 'pyside2' before importing other
packages::

    >>> import os
    >>> os.environ['QT_API'] = 'pyside2'
    >>> from qtpy import QtGui, QtWidgets, QtCore
    >>> print(QtWidgets.QWidget)

PySide6
=======

    >>> import os
    >>> os.environ['QT_API'] = 'pyside6'
    >>> from qtpy import QtGui, QtWidgets, QtCore
    >>> print(QtWidgets.QWidget)

"""

from packaging.version import parse
import os
import platform
import sys
import warnings

# Version of QtPy
from ._version import __version__


class PythonQtError(RuntimeError):
    """Error raise if no bindings could be selected."""
    pass


class PythonQtWarning(Warning):
    """Warning if some features are not implemented in a binding."""
    pass


# Qt API environment variable name
QT_API = 'QT_API'

# Names of the expected PyQt5 api
PYQT5_API = ['pyqt5']

PYQT6_API = ['pyqt6']

# Names of the expected PySide2 api
PYSIDE2_API = ['pyside2']

# Names of the expected PySide6 api
PYSIDE6_API = ['pyside6']

# Detecting if a binding was specified by the user
binding_specified = QT_API in os.environ

# Setting a default value for QT_API
os.environ.setdefault(QT_API, 'pyqt5')

API = os.environ[QT_API].lower()
initial_api = API
assert API in (PYQT5_API + PYQT6_API + PYSIDE2_API + PYSIDE6_API)

is_old_pyqt = is_pyqt46 = False
PYQT5 = True
PYQT6 = PYSIDE2 = PYSIDE6 = False

# When `FORCE_QT_API` is set, we disregard
# any previously imported python bindings.
if 'FORCE_QT_API' in os.environ:
    if 'PyQt6' in sys.modules:
        API = initial_api if initial_api in PYQT6_API else 'pyqt6'
    elif 'PyQt5' in sys.modules:
        API = initial_api if initial_api in PYQT5_API else 'pyqt5'
    elif 'PySide6' in sys.modules:
       API = initial_api if initial_api in PYSIDE6_API else 'pyside6'
    elif 'PySide2' in sys.modules:
        API = initial_api if initial_api in PYSIDE2_API else 'pyside2'

if API in PYQT5_API:
    try:
        from PyQt5.QtCore import PYQT_VERSION_STR as PYQT_VERSION  # analysis:ignore
        from PyQt5.QtCore import QT_VERSION_STR as QT_VERSION  # analysis:ignore
        PYSIDE_VERSION = None

        if sys.platform == 'darwin':
            macos_version = parse(platform.mac_ver()[0])
            if macos_version < parse('10.10'):
                if parse(QT_VERSION) >= parse('5.9'):
                    raise PythonQtError("Qt 5.9 or higher only works in "
                                        "macOS 10.10 or higher. Your "
                                        "program will fail in this "
                                        "system.")
            elif macos_version < parse('10.11'):
                if parse(QT_VERSION) >= parse('5.11'):
                    raise PythonQtError("Qt 5.11 or higher only works in "
                                        "macOS 10.11 or higher. Your "
                                        "program will fail in this "
                                        "system.")

            del macos_version
    except ImportError:
        API = os.environ['QT_API'] = 'pyqt6'

if API in PYQT6_API:
    try:
        from PyQt6.QtCore import PYQT_VERSION_STR as PYQT_VERSION  # analysis:ignore
        from PyQt6.QtCore import QT_VERSION_STR as QT_VERSION  # analysis:ignore
        PYSIDE_VERSION = None
        PYQT5 = False
        PYQT6 = True
    except ImportError:
        API = os.environ['QT_API'] = 'pyside2'


if API in PYSIDE2_API:
    try:
        from PySide2 import __version__ as PYSIDE_VERSION  # analysis:ignore
        from PySide2.QtCore import __version__ as QT_VERSION  # analysis:ignore

        PYQT_VERSION = None
        PYQT5 = False
        PYSIDE2 = True

        if sys.platform == 'darwin':
            macos_version = parse(platform.mac_ver()[0])
            if macos_version < parse('10.11'):
                if parse(QT_VERSION) >= parse('5.11'):
                    raise PythonQtError("Qt 5.11 or higher only works in "
                                        "macOS 10.11 or higher. Your "
                                        "program will fail in this "
                                        "system.")

            del macos_version
    except ImportError:
        API = os.environ['QT_API'] = 'pyside6'

if API in PYSIDE6_API:
    try:
        from PySide6 import __version__ as PYSIDE_VERSION  # analysis:ignore
        from PySide6.QtCore import __version__ as QT_VERSION  # analysis:ignore

        PYQT_VERSION = None
        PYQT5 = False
        PYSIDE6 = True

    except ImportError:
        API = os.environ['QT_API'] = 'pyqt5'


# If a correct API name is passed to QT_API and it could not be found,
# switches to another and informs through the warning
if API != initial_api and binding_specified:
    warnings.warn('Selected binding "{}" could not be found, '
                  'using "{}"'.format(initial_api, API), RuntimeWarning)

API_NAME = {'pyqt6': 'PyQt6', 'pyqt5': 'PyQt5',
            'pyside2':'PySide2', 'pyside6': 'PySide6'}[API]

try:
    # QtDataVisualization backward compatibility (QtDataVisualization vs. QtDatavisualization)
    # Only available for Qt5 bindings > 5.9 on Windows
    from . import QtDataVisualization as QtDatavisualization
except ImportError:
    pass
