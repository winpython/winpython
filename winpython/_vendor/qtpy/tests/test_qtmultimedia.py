from __future__ import absolute_import

from qtpy import QtMultimedia


def test_qtmultimedia():
    """Test the qtpy.QtMultimedia namespace"""
    assert QtMultimedia.QAbstractVideoBuffer is not None
    assert QtMultimedia.QAudio is not None
    assert QtMultimedia.QAudioDeviceInfo is not None
    assert QtMultimedia.QAudioInput is not None
    assert QtMultimedia.QSound is not None
