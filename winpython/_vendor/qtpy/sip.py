#
# Copyright © 2009- The Spyder Development Team
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

from . import PYQT6, PYQT5, PythonQtError

if PYQT6:
    from PyQt6.sip import *
elif PYQT5:
    from PyQt5.sip import *
else:
    raise PythonQtError(
        'Currently selected Qt binding does not support this module')
