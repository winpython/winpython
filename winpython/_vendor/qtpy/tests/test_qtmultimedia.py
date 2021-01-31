from __future__ import absolute_import
import os
import sys

import pytest
from qtpy import PYSIDE6

@pytest.mark.skipif((os.name == 'nt' and sys.version_info[:2] == (3, 5)) or PYSIDE6,
                    reason="Conda packages don't seem to include QtMultimedia, not available with qt 6.0")
def test_qtmultimedia():
    """Test the qtpy.QtMultimedia namespace"""
    from qtpy import QtMultimedia

    assert QtMultimedia.QAbstractVideoBuffer is not None
    assert QtMultimedia.QAudio is not None
    assert QtMultimedia.QAudioDeviceInfo is not None
    assert QtMultimedia.QAudioInput is not None
    assert QtMultimedia.QSound is not None
