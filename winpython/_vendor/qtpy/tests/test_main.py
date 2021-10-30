import os

from qtpy import QtCore, QtGui, QtWidgets
try:
    # removed in qt 6.0
    from qtpy import QtWebEngineWidgets
except Exception:
    pass

def assert_pyside2():
    """
    Make sure that we are using PySide
    """
    import PySide2
    assert QtCore.QEvent is PySide2.QtCore.QEvent
    assert QtGui.QPainter is PySide2.QtGui.QPainter
    assert QtWidgets.QWidget is PySide2.QtWidgets.QWidget
    assert QtWebEngineWidgets.QWebEnginePage is PySide2.QtWebEngineWidgets.QWebEnginePage

def assert_pyside6():
    """
    Make sure that we are using PySide
    """
    import PySide6
    assert QtCore.QEvent is PySide6.QtCore.QEvent
    assert QtGui.QPainter is PySide6.QtGui.QPainter
    assert QtWidgets.QWidget is PySide6.QtWidgets.QWidget
    # Only valid for qt>=6.2
    # assert QtWebEngineWidgets.QWebEnginePage is PySide6.QtWebEngineCore.QWebEnginePage

def assert_pyqt5():
    """
    Make sure that we are using PyQt5
    """
    import PyQt5
    assert QtCore.QEvent is PyQt5.QtCore.QEvent
    assert QtGui.QPainter is PyQt5.QtGui.QPainter
    assert QtWidgets.QWidget is PyQt5.QtWidgets.QWidget
    if QtWebEngineWidgets.WEBENGINE:
        assert QtWebEngineWidgets.QWebEnginePage is PyQt5.QtWebEngineWidgets.QWebEnginePage
    else:
        assert QtWebEngineWidgets.QWebEnginePage is PyQt5.QtWebKitWidgets.QWebPage

def assert_pyqt6():
    """
    Make sure that we are using PyQt6
    """
    import PyQt6
    assert QtCore.QEvent is PyQt6.QtCore.QEvent
    assert QtGui.QPainter is PyQt6.QtGui.QPainter
    assert QtWidgets.QWidget is PyQt6.QtWidgets.QWidget


def test_qt_api():
    """
    If QT_API is specified, we check that the correct Qt wrapper was used
    """

    QT_API = os.environ.get('QT_API', '').lower()

    if QT_API == 'pyqt5':
        assert_pyqt5()
    elif QT_API == 'pyqt6':
        assert_pyqt6()
    elif QT_API == 'pyside2':
        assert_pyside2()
    elif QT_API == 'pyside6':
        assert_pyside6()
    else:
        # If the tests are run locally, USE_QT_API and QT_API may not be
        # defined, but we still want to make sure qtpy is behaving sensibly.
        # We should then be loading, in order of decreasing preference, PyQt5,
        # PyQt6, and PySide2.
        try:
            import PyQt5
        except ImportError:
            try:
                import PyQt6
            except ImportError:
                import PySide2
                assert_pyside2()
            else:
                assert_pyqt6()
        else:
            assert_pyqt5()
