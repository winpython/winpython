import pytest
from qtpy import QtTest


def test_qttest():
    """Test the qtpy.QtTest namespace"""
    assert QtTest.QTest is not None
