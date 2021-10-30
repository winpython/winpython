#
# Copyright © 2014-2015 Colin Duquesnoy
# Copyright © 2009- The Spyder development Team
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

"""
Provides QtWebEngineWidgets classes and functions.
"""

from . import PYQT5, PYQT6, PYSIDE2, PYSIDE6, PythonQtError


# To test if we are using WebEngine or WebKit
WEBENGINE = True


if PYQT5:
    try:
        from PyQt5.QtWebEngineWidgets import QWebEnginePage
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        from PyQt5.QtWebEngineWidgets import QWebEngineSettings
        # Based on the work at https://github.com/spyder-ide/qtpy/pull/203
        from PyQt5.QtWebEngineWidgets import QWebEngineProfile
    except ImportError:
        from PyQt5.QtWebKitWidgets import QWebPage as QWebEnginePage
        from PyQt5.QtWebKitWidgets import QWebView as QWebEngineView
        from PyQt5.QtWebKit import QWebSettings as QWebEngineSettings
        WEBENGINE = False
elif PYQT6:
    from PyQt6.QtWebEngineWidgets import *
    from PyQt6.QtWebEngineCore import QWebEnginePage
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    from PyQt6.QtWebEngineCore import QWebEngineProfile
elif PYSIDE6:
    from PySide6.QtWebEngineWidgets import *
    from PySide6.QtWebEngineCore import QWebEnginePage
    from PySide6.QtWebEngineCore import QWebEngineSettings
    from PySide6.QtWebEngineCore import QWebEngineProfile
elif PYSIDE2:
    from PySide2.QtWebEngineWidgets import QWebEnginePage
    from PySide2.QtWebEngineWidgets import QWebEngineView
    from PySide2.QtWebEngineWidgets import QWebEngineSettings
    # Based on the work at https://github.com/spyder-ide/qtpy/pull/203
    from PySide2.QtWebEngineWidgets import QWebEngineProfile
else:
    raise PythonQtError('No Qt bindings could be found')
