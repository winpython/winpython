from __future__ import absolute_import

import pytest
from qtpy import PYSIDE2

"""Test QDesktopServices split in Qt5."""

@pytest.mark.skipif(PYSIDE2, reason="It fails on PySide2")
def test_qstandarpath():
    """Test the qtpy.QStandardPaths namespace"""
    from qtpy.QtCore import QStandardPaths

    assert QStandardPaths.StandardLocation is not None

    # Attributes from QDesktopServices shouldn't be in QStandardPaths
    with pytest.raises(AttributeError) as excinfo:
        QStandardPaths.setUrlHandler

@pytest.mark.skipif(PYSIDE2, reason="It fails on PySide2")
def test_qdesktopservice():
    """Test the qtpy.QDesktopServices namespace"""
    from qtpy.QtGui import QDesktopServices

    assert QDesktopServices.setUrlHandler is not None

    # Attributes from QStandardPaths shouldn't be in QDesktopServices
    with pytest.raises(AttributeError) as excinfo:
        QDesktopServices.StandardLocation