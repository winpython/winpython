import pytest
from qtpy import PYSIDE2, PYSIDE6, PYQT5, PYQT6

@pytest.mark.skipif(PYSIDE2 or PYSIDE6, reason="Not available in PySide2, not on CI for PySide6")
def test_qtdbus():
    """Test the qtpy.QtDBus namespace"""
    from qtpy import QtDBus

    assert QtDBus.QDBusAbstractAdaptor is not None
    assert QtDBus.QDBusAbstractInterface is not None
    assert QtDBus.QDBusArgument is not None
    assert QtDBus.QDBusConnection is not None
