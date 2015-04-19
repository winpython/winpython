# -*- coding: utf-8 -*-
#
# Copyright © 2009-2011 Pierre Raybaut
# Licensed under the terms of the MIT License
# (copied from Spyder source code [spyderlib.qt])
#
# Qt5 migration would not have been possible without
#   2014-2015 Spyder Development Team work
# (MIT License too, same parent project)

"""Qt utilities"""

from winpython.qt.QtGui import (QAction, QStyle, QWidget, QIcon, QApplication,
                                QLabel, QVBoxLayout, QHBoxLayout, QLineEdit,
                                QKeyEvent, QMenu, QKeySequence, QToolButton,
                                QPixmap)
from winpython.qt.QtCore import (Signal, QObject, Qt, QLocale, QTranslator,
                                 QLibraryInfo, QEvent, Slot)
from winpython.qt.compat import to_qvariant, from_qvariant

import os
import re
import os.path as osp
import sys

# Local import
from winpython import config
from winpython.py3compat import is_text_string, to_text_string


def get_icon(name):
    """Return QIcon from icon name"""
    return QIcon(osp.join(config.IMAGE_PATH, name))


class MacApplication(QApplication):
    """Subclass to be able to open external files with our Mac app"""
    open_external_file = Signal(str)

    def __init__(self, *args):
        QApplication.__init__(self, *args)

    def event(self, event):
        if event.type() == QEvent.FileOpen:
            fname = str(event.file())
            # PyQt4 old SIGNAL: self.emit(SIGNAL('open_external_file(QString)'), fname)
            self.open_external_file.emit(fname)
        return QApplication.event(self, event)


def qapplication(translate=True):
    """Return QApplication instance
    Creates it if it doesn't already exist"""
    if sys.platform == "darwin" and 'Spyder.app' in __file__:
        SpyderApplication = MacApplication
    else:
        SpyderApplication = QApplication

    app = SpyderApplication.instance()
    if not app:
        # Set Application name for Gnome 3
        # https://groups.google.com/forum/#!topic/pyside/24qxvwfrRDs
        app = SpyderApplication(['Spyder'])
    if translate:
        install_translator(app)
    return app


def file_uri(fname):
    """Select the right file uri scheme according to the operating system"""
    if os.name == 'nt':
        # Local file
        if re.search(r'^[a-zA-Z]:', fname):
            return 'file:///' + fname
        # UNC based path
        else:
            return 'file://' + fname
    else:
        return 'file://' + fname


QT_TRANSLATOR = None


def install_translator(qapp):
    """Install Qt translator to the QApplication instance"""
    global QT_TRANSLATOR
    if QT_TRANSLATOR is None:
        qt_translator = QTranslator()
        if qt_translator.load("qt_"+QLocale.system().name(),
                      QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
            QT_TRANSLATOR = qt_translator  # Keep reference alive
    if QT_TRANSLATOR is not None:
        qapp.installTranslator(QT_TRANSLATOR)


def keybinding(attr):
    """Return keybinding"""
    ks = getattr(QKeySequence, attr)
    return from_qvariant(QKeySequence.keyBindings(ks)[0], str)


def _process_mime_path(path, extlist):
    if path.startswith(r"file://"):
        if os.name == 'nt':
            # On Windows platforms, a local path reads: file:///c:/...
            # and a UNC based path reads like: file://server/share
            if path.startswith(r"file:///"):  # this is a local path
                path = path[8:]
            else:  # this is a unc path
                path = path[5:]
        else:
            path = path[7:]
    if osp.exists(path):
        if extlist is None or osp.splitext(path)[1] in extlist:
            return path


def mimedata2url(source, extlist=None):
    """
    Extract url list from MIME data
    extlist: for example ('.py', '.pyw')
    """
    pathlist = []
    if source.hasUrls():
        for url in source.urls():
            path = _process_mime_path(to_text_string(url.toString()), extlist)
            if path is not None:
                pathlist.append(path)
    elif source.hasText():
        for rawpath in to_text_string(source.text()).splitlines():
            path = _process_mime_path(rawpath, extlist)
            if path is not None:
                pathlist.append(path)
    if pathlist:
        return pathlist


def action2button(action, autoraise=True, text_beside_icon=False, parent=None):
    """Create a QToolButton directly from a QAction object"""
    if parent is None:
        parent = action.parent()
    button = QToolButton(parent)
    button.setDefaultAction(action)
    button.setAutoRaise(autoraise)
    if text_beside_icon:
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    return button


def toggle_actions(actions, enable):
    """Enable/disable actions"""
    if actions is not None:
        for action in actions:
            if action is not None:
                action.setEnabled(enable)


def create_action(parent, text, shortcut=None, icon=None, tip=None,
                  toggled=None, triggered=None, data=None, menurole=None,
                  context=Qt.WindowShortcut):
    """Create a QAction"""
    action = QAction(text, parent)
    if triggered is not None:
        # PyQt4 old SIGNAL: parent.connect(action, SIGNAL("triggered()"), triggered)
        action.triggered.connect(triggered)
    if toggled is not None:
        # PyQt4 old SIGNAL: parent.connect(action, SIGNAL("toggled(bool)"), toggled)
        action.toggled.connect(toggled)
        action.setCheckable(True)
    if icon is not None:
        if is_text_string(icon):
            icon = get_icon(icon)
        action.setIcon(icon)
    if shortcut is not None:
        action.setShortcut(shortcut)
    if tip is not None:
        action.setToolTip(tip)
        action.setStatusTip(tip)
    if data is not None:
        action.setData(to_qvariant(data))
    if menurole is not None:
        action.setMenuRole(menurole)
    # TODO: Hard-code all shortcuts and choose context=Qt.WidgetShortcut
    # (this will avoid calling shortcuts from another dockwidget
    #  since the context thing doesn't work quite well with these widgets)
    action.setShortcutContext(context)
    return action


def add_actions(target, actions, insert_before=None):
    """Add actions to a menu"""
    previous_action = None
    target_actions = list(target.actions())
    if target_actions:
        previous_action = target_actions[-1]
        if previous_action.isSeparator():
            previous_action = None
    for action in actions:
        if (action is None) and (previous_action is not None):
            if insert_before is None:
                target.addSeparator()
            else:
                target.insertSeparator(insert_before)
        elif isinstance(action, QMenu):
            if insert_before is None:
                target.addMenu(action)
            else:
                target.insertMenu(insert_before, action)
        elif isinstance(action, QAction):
            if insert_before is None:
                target.addAction(action)
            else:
                target.insertAction(insert_before, action)
        previous_action = action


def get_std_icon(name, size=None):
    """Get standard platform icon
    Call 'show_std_icons()' for details"""
    if not name.startswith('SP_'):
        name = 'SP_'+name
    icon = QWidget().style().standardIcon(getattr(QStyle, name))
    if size is None:
        return icon
    else:
        return QIcon(icon.pixmap(size, size))
