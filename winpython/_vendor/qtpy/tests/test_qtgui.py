"""Test QtGui."""

import sys

import pytest

from qtpy import PYQT5, PYQT_VERSION, PYSIDE2, PYSIDE6, QtGui
from qtpy.tests.utils import not_using_conda


@pytest.mark.skipif(
    sys.platform.startswith('linux') and not_using_conda(),
    reason="Fatal Python error: Aborted on Linux CI when not using conda")
def test_qfontmetrics_width(qtbot):
    """Test QFontMetrics and QFontMetricsF width"""
    assert QtGui.QFontMetrics.width is not None
    assert QtGui.QFontMetricsF.width is not None
    font = QtGui.QFont("times", 24)
    font_metrics = QtGui.QFontMetrics(font)
    font_metricsF = QtGui.QFontMetricsF(font)
    width = font_metrics.width("Test")
    widthF = font_metricsF.width("Test")
    assert width in range(40, 62)
    assert 39 <= widthF <= 63


@pytest.mark.skipif(
    sys.platform.startswith('linux') and not_using_conda(),
    reason="Fatal Python error: Aborted on Linux CI when not using conda")
def test_qdrag_functions(qtbot):
    """Test functions mapping for QtGui.QDrag."""
    assert QtGui.QDrag.exec_ is not None
    drag = QtGui.QDrag(None)
    drag.exec_()


def test_qguiapplication_functions():
    """Test functions mapping for QtGui.QGuiApplication."""
    assert QtGui.QGuiApplication.exec_ is not None


@pytest.mark.skipif(
    sys.platform.startswith('linux') and not_using_conda(),
    reason="Segmentation fault/Aborted on Linux CI when not using conda")
def test_qtextdocument_functions(pdf_writer):
    """Test functions mapping for QtGui.QTextDocument."""
    assert QtGui.QTextDocument.print_ is not None
    text_document = QtGui.QTextDocument("Test")
    print_device, output_path = pdf_writer
    text_document.print_(print_device)
    assert output_path.exists()


@pytest.mark.skipif(PYQT5 and PYQT_VERSION.startswith('5.9'),
                    reason="A specific setup with at least sip 4.9.9 is needed for PyQt5 5.9.*"
                           "to work with scoped enum access")
def test_enum_access():
    """Test scoped and unscoped enum access for qtpy.QtWidgets.*."""
    assert QtGui.QColor.Rgb == QtGui.QColor.Spec.Rgb
    assert QtGui.QFont.AllUppercase == QtGui.QFont.Capitalization.AllUppercase
    assert QtGui.QIcon.Normal == QtGui.QIcon.Mode.Normal
    assert QtGui.QImage.Format_Invalid == QtGui.QImage.Format.Format_Invalid

@pytest.mark.skipif(not (PYSIDE2 or PYSIDE6), reason="PySide{2,6} specific test")
def test_qtextcursor_moveposition():
    """Test monkeypatched QTextCursor.movePosition"""
    doc = QtGui.QTextDocument("foo bar baz")
    cursor = QtGui.QTextCursor(doc)

    assert not cursor.movePosition(QtGui.QTextCursor.Start)
    assert cursor.movePosition(QtGui.QTextCursor.EndOfWord, mode=QtGui.QTextCursor.KeepAnchor)
    assert cursor.selectedText() == "foo"

    assert cursor.movePosition(QtGui.QTextCursor.Start)
    assert cursor.movePosition(QtGui.QTextCursor.WordRight, n=2, mode=QtGui.QTextCursor.KeepAnchor)
    assert cursor.selectedText() == "foo bar "

    assert cursor.movePosition(QtGui.QTextCursor.Start)
    assert cursor.position() == cursor.anchor()
    assert cursor.movePosition(QtGui.QTextCursor.NextWord, QtGui.QTextCursor.KeepAnchor, 3)
    assert cursor.selectedText() == "foo bar baz"
