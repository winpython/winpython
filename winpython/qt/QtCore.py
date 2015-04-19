# -*- coding: utf-8 -*-
#
# Copyright © 2011 Pierre Raybaut
# Licensed under the terms of the MIT License
# (copied from Spyder source code [spyderlib.qt])
#
# Qt5 migration would not have been possible without
#   2014-2015 Spyder Development Team work
# (MIT License too, same parent project)

import os

if os.environ['QT_API'] == 'pyqt5':
    from PyQt5.QtCore import *                                # analysis:ignore
    from PyQt5.QtCore import QCoreApplication
    from PyQt5.QtCore import pyqtSignal as Signal
    from PyQt5.QtCore import pyqtSlot as Slot
    from PyQt5.QtCore import pyqtProperty as Property
    from PyQt5.QtCore import QT_VERSION_STR as __version__
elif os.environ['QT_API'] == 'pyqt':
    from PyQt4.QtCore import *  # analysis:ignore
    # from PyQt4.Qt import QCoreApplication  # analysis:ignore
    # from PyQt4.Qt import Qt  # analysis:ignore
    from PyQt4.QtCore import QCoreApplication                 # analysis:ignore
    from PyQt4.QtCore import Qt                               # analysis:ignore
    from PyQt4.QtCore import pyqtSignal as Signal  # analysis:ignore
    from PyQt4.QtCore import pyqtSlot as Slot  # analysis:ignore
    from PyQt4.QtCore import pyqtProperty as Property  # analysis:ignore
    from PyQt4.QtCore import QT_VERSION_STR as __version__
else:
    import PySide.QtCore
    __version__ = PySide.QtCore.__version__  # analysis:ignore
    from PySide.QtCore import *  # analysis:ignore
