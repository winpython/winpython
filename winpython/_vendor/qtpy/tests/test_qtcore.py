from __future__ import absolute_import

import pytest
from qtpy import QtCore

"""Test QtCore."""

def test_qtmsghandler():
    """Test the qtpy.QtMsgHandler"""
    assert QtCore.qInstallMessageHandler is not None
