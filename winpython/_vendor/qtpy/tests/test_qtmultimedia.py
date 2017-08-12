from __future__ import absolute_import

import pytest
from qtpy import PYSIDE2, QtMultimedia


@pytest.mark.skipif(PYSIDE2, reason="It fails on PySide2")
def test_qtmultimedia():
    """Test the qtpy.QtMultimedia namespace"""
    assert QtMultimedia.QAbstractVideoBuffer is not None
    assert QtMultimedia.QAudio is not None
    assert QtMultimedia.QAudioDeviceInfo is not None
    assert QtMultimedia.QAudioInput is not None
    assert QtMultimedia.QSound is not None
