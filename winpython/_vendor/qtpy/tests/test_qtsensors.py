import pytest
from qtpy import PYSIDE6, PYQT6

def test_qtsensors():
    """Test the qtpy.QtSensors namespace"""
    from qtpy import QtSensors

    assert QtSensors.QAccelerometer is not None
    assert QtSensors.QAccelerometerFilter is not None
    assert QtSensors.QAccelerometerReading is not None

