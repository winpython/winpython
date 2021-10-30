import contextlib
import os
import sys
import warnings

import pytest

from qtpy import PYSIDE6, PYSIDE2, QtWidgets
from qtpy.QtWidgets import QComboBox

if PYSIDE2:
    pytest.importorskip("pyside2uic", reason="pyside2uic not installed")

from qtpy import uic
from qtpy.uic import loadUi, loadUiType


QCOMBOBOX_SUBCLASS = """
from qtpy.QtWidgets import QComboBox
class _QComboBoxSubclass(QComboBox):
    pass
"""

@contextlib.contextmanager
def enabled_qcombobox_subclass(tmpdir):
    """
    Context manager that sets up a temporary module with a QComboBox subclass
    and then removes it once we are done.
    """

    with open(tmpdir.join('qcombobox_subclass.py').strpath, 'w') as f:
        f.write(QCOMBOBOX_SUBCLASS)

    sys.path.insert(0, tmpdir.strpath)

    yield

    sys.path.pop(0)


def get_qapp(icon_path=None):
    """
    Helper function to return a QApplication instance
    """
    qapp = QtWidgets.QApplication.instance()
    if qapp is None:
        qapp = QtWidgets.QApplication([''])
    return qapp


@pytest.mark.skipif(
    os.environ.get('CI', None) is not None
    and sys.platform.startswith('linux'),
    reason="Segfaults on Linux CIs under all bindings (PYSIDE2/6 & PYQT5/6)")
def test_load_ui():
    """
    Make sure that the patched loadUi function behaves as expected with a
    simple .ui file.
    """
    app = get_qapp()
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", category=DeprecationWarning, message=".*mode.*")
        ui = loadUi(os.path.join(os.path.dirname(__file__), 'test.ui'))
    assert isinstance(ui.pushButton, QtWidgets.QPushButton)
    assert isinstance(ui.comboBox, QComboBox)


@pytest.mark.skipif(
    PYSIDE2 or PYSIDE6,
    reason="PySide2uic not consistantly installed across platforms/versions")
@pytest.mark.skipif(
    os.environ.get('CI', None) is not None
    and sys.platform.startswith('linux'),
    reason="Segfaults on Linux CIs under all bindings (PYSIDE2/6 & PYQT5/6)")
def test_load_ui_type():
    """
    Make sure that the patched loadUiType function behaves as expected with a
    simple .ui file.
    """
    app = get_qapp()
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", category=DeprecationWarning, message=".*mode.*")
        ui_type, ui_base_type = loadUiType(
            os.path.join(os.path.dirname(__file__), 'test.ui'))
    assert ui_type.__name__ == 'Ui_Form'

    class Widget(ui_base_type, ui_type):
        def __init__(self):
            super().__init__()
            self.setupUi(self)

    ui = Widget()
    assert isinstance(ui, QtWidgets.QWidget)
    assert isinstance(ui.pushButton, QtWidgets.QPushButton)
    assert isinstance(ui.comboBox, QComboBox)


@pytest.mark.skipif(
    PYSIDE2 and sys.platform == "darwin"
    and sys.version_info.major == 3 and sys.version_info.minor == 9
    and os.environ.get('USE_CONDA', 'No') == 'No',
    reason="Fails on this specific platform, at least on our CIs")
@pytest.mark.skipif(
    os.environ.get('CI', None) is not None
    and sys.platform.startswith('linux'),
    reason="Segfaults on Linux CIs under all bindings (PYSIDE2/6 & PYQT5/6)")
def test_load_ui_custom_auto(tmpdir):
    """
    Test that we can load a .ui file with custom widgets without having to
    explicitly specify a dictionary of custom widgets, even in the case of
    PySide.
    """

    app = get_qapp()

    with enabled_qcombobox_subclass(tmpdir):
        from qcombobox_subclass import _QComboBoxSubclass
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", category=DeprecationWarning, message=".*mode.*")
            ui = loadUi(
                os.path.join(os.path.dirname(__file__), 'test_custom.ui'))

    assert isinstance(ui.pushButton, QtWidgets.QPushButton)
    assert isinstance(ui.comboBox, _QComboBoxSubclass)

@pytest.mark.skipif(PYSIDE6, reason="Unavailable on PySide6")
def test_load_full_uic():
    """Test that we load the full uic objects."""
    QT_API = os.environ.get('QT_API', '').lower()
    if QT_API.startswith('pyside'):
        assert hasattr(uic, 'loadUi')
        assert hasattr(uic, 'loadUiType')
    else:
        objects = ['compileUi', 'compileUiDir', 'loadUi', 'loadUiType',
                   'widgetPluginPath']
        assert all([hasattr(uic, o) for o in objects])
