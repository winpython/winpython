from __future__ import absolute_import

import pytest
from qtpy import PYSIDE6

@pytest.mark.skipif(PYSIDE6, reason="Only available in Qt<6 bindings")
def test_qtwebenginewidgets():
    """Test the qtpy.QtWebSockets namespace"""

    QtWebEngineWidgets = pytest.importorskip("qtpy.QtWebEngineWidgets")

    assert QtWebEngineWidgets.QWebEnginePage is not None
    assert QtWebEngineWidgets.QWebEngineView is not None
    assert QtWebEngineWidgets.QWebEngineSettings is not None
