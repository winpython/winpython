# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
WinPython Package Manager GUI

Created on Mon Aug 13 11:40:01 2012
"""

import os.path as osp
import os
import sys
import platform
import locale

from winpython.qt.QtGui import (QApplication, QMainWindow, QWidget, QLineEdit,
                                QHBoxLayout, QVBoxLayout, QColor, QMessageBox,
                                QAbstractItemView, QProgressDialog, QTableView,
                                QPushButton, QLabel, QTabWidget, QToolTip,
                                QDesktopServices)
from winpython.qt.QtCore import (Qt, QAbstractTableModel, QModelIndex, Signal,
                                 QThread, QTimer, QUrl)
from winpython.qt.compat import (to_qvariant, getopenfilenames,
                                 getexistingdirectory)
import winpython.qt

from winpython.qthelpers import (get_icon, add_actions, create_action,
                                 keybinding, get_std_icon, action2button,
                                 mimedata2url)

# Local imports
from winpython import __version__, __project_url__
from winpython import wppm, associate, utils
from winpython.py3compat import getcwd, to_text_string


COLUMNS = ACTION, CHECK, NAME, VERSION, DESCRIPTION = list(range(5))


class PackagesModel(QAbstractTableModel):
    # Signals after PyQt4 old SIGNAL removal
    dataChanged = Signal(QModelIndex, QModelIndex)

    def __init__(self):
        QAbstractTableModel.__init__(self)
        self.packages = []
        self.checked = set()
        self.actions = {}

    def sortByName(self):
        self.packages = sorted(self.packages, key=lambda x: x.name)
        self.reset()

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        column = index.column()
        if column in (NAME, VERSION, ACTION, DESCRIPTION):
            return Qt.ItemFlags(QAbstractTableModel.flags(self, index))
        else:
            return Qt.ItemFlags(QAbstractTableModel.flags(self, index) |
                                Qt.ItemIsUserCheckable | Qt.ItemIsEditable)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.packages)):
            return to_qvariant()
        package = self.packages[index.row()]
        column = index.column()
        if role == Qt.CheckStateRole and column == CHECK:
            return to_qvariant(package in self.checked)
        elif role == Qt.DisplayRole:
            if column == NAME:
                return to_qvariant(package.name)
            elif column == VERSION:
                return to_qvariant(package.version)
            elif column == ACTION:
                action = self.actions.get(package)
                if action is not None:
                    return to_qvariant(action)
            elif column == DESCRIPTION:
                return to_qvariant(package.description)
        elif role == Qt.TextAlignmentRole:
            if column == ACTION:
                return to_qvariant(int(Qt.AlignRight | Qt.AlignVCenter))
            else:
                return to_qvariant(int(Qt.AlignLeft | Qt.AlignVCenter))
        elif role == Qt.BackgroundColorRole:
            if package in self.checked:
                color = QColor(Qt.darkGreen)
                color.setAlphaF(.1)
                return to_qvariant(color)
            else:
                color = QColor(Qt.lightGray)
                color.setAlphaF(.3)
                return to_qvariant(color)
        return to_qvariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                return to_qvariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
            return to_qvariant(int(Qt.AlignRight | Qt.AlignVCenter))
        if role != Qt.DisplayRole:
            return to_qvariant()
        if orientation == Qt.Horizontal:
            if section == NAME:
                return to_qvariant("Name")
            elif section == VERSION:
                return to_qvariant("Version")
            elif section == ACTION:
                return to_qvariant("Action")
            elif section == DESCRIPTION:
                return to_qvariant("Description")
        return to_qvariant()

    def rowCount(self, index=QModelIndex()):
        return len(self.packages)

    def columnCount(self, index=QModelIndex()):
        return len(COLUMNS)

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid() and 0 <= index.row() < len(self.packages)\
           and role == Qt.CheckStateRole:
            package = self.packages[index.row()]
            if package in self.checked:
                self.checked.remove(package)
            else:
                self.checked.add(package)
            # PyQt4 old SIGNAL: self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
            # PyQt4 old SIGNAL:           index, index)
            self.dataChanged.emit(index, index)
            return True
        return False


INSTALL_ACTION = 'Install'
REPAIR_ACTION = 'Repair (reinstall)'
NO_REPAIR_ACTION = 'None (Already installed)'
UPGRADE_ACTION = 'Upgrade from v'
NONE_ACTION = '-'


class PackagesTable(QTableView):
    # Signals after PyQt4 old SIGNAL removal, to be emitted after package_added event
    package_added = Signal()

    def __init__(self, parent, process, winname):
        QTableView.__init__(self, parent)
        assert process in ('install', 'uninstall')
        self.process = process
        self.model = PackagesModel()
        self.setModel(self.model)
        self.winname = winname
        self.repair = False
        self.resizeColumnToContents(0)
        self.setAcceptDrops(process == 'install')
        if process == 'uninstall':
            self.hideColumn(0)
        self.distribution = None

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().hide()
        self.setShowGrid(False)

    def reset_model(self):
        # self.model.reset() is deprecated in Qt5
        self.model.beginResetModel()
        self.model.endResetModel()
        self.horizontalHeader().setStretchLastSection(True)
        for colnb in (ACTION, CHECK, NAME, VERSION):
            self.resizeColumnToContents(colnb)

    def get_selected_packages(self):
        """Return selected packages"""
        return [pack for pack in self.model.packages
                if pack in self.model.checked]

    def add_packages(self, fnames):
        """Add packages"""
        notsupported = []
        notcompatible = []
        dist = self.distribution
        for fname in fnames:
            bname = osp.basename(fname)
            try:
                package = wppm.Package(fname)
                if package.is_compatible_with(dist):
                    self.add_package(package)
                else:
                    notcompatible.append(bname)
            except NotImplementedError:
                notsupported.append(bname)
        # PyQt4 old SIGNAL: self.emit(SIGNAL('package_added()'))
        self.package_added.emit()
        if notsupported:
            QMessageBox.warning(self, "Warning",
                                "The following packages filenaming are <b>not "
                                "recognized</b> by %s:\n\n%s"
                                % (self.winname, "<br>".join(notsupported)),
                                QMessageBox.Ok)
        if notcompatible:
            QMessageBox.warning(self, "Warning", "The following packages "
                                "are <b>not compatible</b> with "
                                "Python <u>%s %dbit</u>:\n\n%s"
                                % (dist.version, dist.architecture,
                                   "<br>".join(notcompatible)),
                                QMessageBox.Ok)

    def add_package(self, package):
        for pack in self.model.packages:
            if pack.name == package.name:
                return
        self.model.packages.append(package)
        self.model.packages.sort(key=lambda x: x.name)
        self.model.checked.add(package)
        self.reset_model()

    def remove_package(self, package):
        self.model.packages = [pack for pack in self.model.packages
                               if pack.fname != package.fname]
        if package in self.model.checked:
            self.model.checked.remove(package)
        if package in self.model.actions:
            self.model.actions.pop(package)
        self.reset_model()

    def refresh_distribution(self, dist):
        self.distribution = dist
        if self.process == 'install':
            for package in self.model.packages:
                pack = dist.find_package(package.name)
                if pack is None:
                    action = INSTALL_ACTION
                elif pack.version == package.version:
                    if self.repair:
                        action = REPAIR_ACTION
                    else:
                        action = NO_REPAIR_ACTION
                else:
                    action = UPGRADE_ACTION + pack.version
                self.model.actions[package] = action
        else:
            self.model.packages = self.distribution.get_installed_packages()
            for package in self.model.packages:
                self.model.actions[package] = NONE_ACTION
        self.reset_model()

    def select_all(self):
        allpk = set(self.model.packages)
        if self.model.checked == allpk:
            self.model.checked = set()
        else:
            self.model.checked = allpk
        self.model.reset()

    def dragMoveEvent(self, event):
        """Reimplement Qt method, just to avoid default drag'n drop
        implementation of QTableView to handle events"""
        event.acceptProposedAction()

    def dragEnterEvent(self, event):
        """Reimplement Qt method
        Inform Qt about the types of data that the widget accepts"""
        source = event.mimeData()
        if source.hasUrls() and mimedata2url(source):
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Reimplement Qt method
        Unpack dropped data and handle it"""
        source = event.mimeData()
        fnames = [path for path in mimedata2url(source) if osp.isfile(path)]
        self.add_packages(fnames)
        event.acceptProposedAction()


class DistributionSelector(QWidget):
    """Python distribution selector widget"""
    TITLE = 'Select a Python distribution path'

    # Signals after PyQt4 old SIGNAL removal
    selected_distribution = Signal(str)

    def __init__(self, parent):
        super(DistributionSelector, self).__init__(parent)
        self.browse_btn = None
        self.label = None
        self.line_edit = None
        self.setup_widget()

    def set_distribution(self, path):
        """Set distribution directory"""
        self.line_edit.setText(path)

    def setup_widget(self):
        """Setup workspace selector widget"""
        self.label = QLabel()
        self.line_edit = QLineEdit()
        self.line_edit.setAlignment(Qt.AlignRight)
        self.line_edit.setReadOnly(True)
        # self.line_edit.setDisabled(True)
        self.browse_btn = QPushButton(get_std_icon('DirOpenIcon'), "", self)
        self.browse_btn.setToolTip(self.TITLE)
        # PyQt4 old SIGNAL:self.connect(self.browse_btn, SIGNAL("clicked()"),
        # PyQt4 old SIGNAL:             self.select_directory)
        self.browse_btn.clicked.connect(self.select_directory)
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.browse_btn)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def select_directory(self):
        """Select directory"""
        basedir = to_text_string(self.line_edit.text())
        if not osp.isdir(basedir):
            basedir = getcwd()
        while True:
            directory = getexistingdirectory(self, self.TITLE, basedir)
            if not directory:
                break
            if not utils.is_python_distribution(directory):
                QMessageBox.warning(self, self.TITLE,
                    "The following directory is not a Python distribution.",
                    QMessageBox.Ok)
                basedir = directory
                continue
            directory = osp.abspath(osp.normpath(directory))
            self.set_distribution(directory)
            # PyQt4 old SIGNAL: self.emit(SIGNAL('selected_distribution(QString)'), directory)
            self.selected_distribution.emit(directory)
            break


class Thread(QThread):
    """Installation/Uninstallation thread"""
    def __init__(self, parent):
        QThread.__init__(self, parent)
        self.callback = None
        self.error = None

    def run(self):
        try:
            self.callback()
        except Exception as error:
            error_str = str(error)
            fs_encoding = sys.getfilesystemencoding()\
                          or locale.getpreferredencoding()
            try:
                error_str = error_str.decode(fs_encoding)
            except (UnicodeError, TypeError, AttributeError):
                pass
            self.error = error_str


def python_distribution_infos():
    """Return Python distribution infos (not selected distribution but
    the one used to run this script)"""
    winpyver = os.environ.get('WINPYVER')
    if winpyver is None:
        return 'Unknown Python distribution'
    else:
        return 'WinPython ' + winpyver


class PMWindow(QMainWindow):
    NAME = 'WinPython Control Panel'

    def __init__(self):
        QMainWindow.__init__(self)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.distribution = None

        self.tabwidget = None
        self.selector = None
        self.table = None
        self.untable = None

        self.basedir = None

        self.select_all_action = None
        self.install_action = None
        self.uninstall_action = None
        self.remove_action = None
        self.packages_icon = get_std_icon('FileDialogContentsView')

        self.setup_window()

    def _add_table(self, table, title, icon):
        """Add table tab to main tab widget, return button layout"""
        widget = QWidget()
        tabvlayout = QVBoxLayout()
        widget.setLayout(tabvlayout)
        tabvlayout.addWidget(table)
        btn_layout = QHBoxLayout()
        tabvlayout.addLayout(btn_layout)
        self.tabwidget.addTab(widget, icon, title)
        return btn_layout

    def setup_window(self):
        """Setup main window"""
        self.setWindowTitle(self.NAME)
        self.setWindowIcon(get_icon('winpython.svg'))

        self.selector = DistributionSelector(self)
        # PyQt4 old SIGNAL: self.connect(self.selector, SIGNAL('selected_distribution(QString)'),
        # PyQt4 old SIGNAL:              self.distribution_changed)
        self.selector.selected_distribution.connect(self.distribution_changed)

        self.table = PackagesTable(self, 'install', self.NAME)
        # PyQt4 old SIGNAL:self.connect(self.table, SIGNAL('package_added()'),
        # PyQt4 old SIGNAL:             self.refresh_install_button)
        self.table.package_added.connect(self.refresh_install_button)

        # PyQt4 old SIGNAL: self.connect(self.table, SIGNAL("clicked(QModelIndex)"),
        # PyQt4 old SIGNAL:              lambda index: self.refresh_install_button())
        self.table.clicked.connect(lambda index: self.refresh_install_button())

        self.untable = PackagesTable(self, 'uninstall', self.NAME)
        # PyQt4 old SIGNAL:self.connect(self.untable, SIGNAL("clicked(QModelIndex)"),
        # PyQt4 old SIGNAL:             lambda index: self.refresh_uninstall_button())
        self.untable.clicked.connect(lambda index: self.refresh_uninstall_button())

        self.selector.set_distribution(sys.prefix)
        self.distribution_changed(sys.prefix)

        self.tabwidget = QTabWidget()
        # PyQt4 old SIGNAL:self.connect(self.tabwidget, SIGNAL('currentChanged(int)'),
        # PyQt4 old SIGNAL:             self.current_tab_changed)
        self.tabwidget.currentChanged.connect(self.current_tab_changed)

        btn_layout = self._add_table(self.table, "Install/upgrade packages",
                                     get_std_icon("ArrowDown"))
        unbtn_layout = self._add_table(self.untable, "Uninstall packages",
                                       get_std_icon("DialogResetButton"))

        central_widget = QWidget()
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.selector)
        vlayout.addWidget(self.tabwidget)
        central_widget.setLayout(vlayout)
        self.setCentralWidget(central_widget)

        # Install tab
        add_action = create_action(self, "&Add packages...",
                                   icon=get_std_icon('DialogOpenButton'),
                                   triggered=self.add_packages)
        self.remove_action = create_action(self, "Remove",
                                           shortcut=keybinding('Delete'),
                                           icon=get_std_icon('TrashIcon'),
                                           triggered=self.remove_packages)
        self.remove_action.setEnabled(False)
        self.select_all_action = create_action(self, "(Un)Select all",
                                   shortcut=keybinding('SelectAll'),
                                   icon=get_std_icon('DialogYesButton'),
                                   triggered=self.table.select_all)
        self.install_action = create_action(self, "&Install packages",
                            icon=get_std_icon('DialogApplyButton'),
                            triggered=lambda: self.process_packages('install'))
        self.install_action.setEnabled(False)
        quit_action = create_action(self, "&Quit",
                                    icon=get_std_icon('DialogCloseButton'),
                                    triggered=self.close)
        packages_menu = self.menuBar().addMenu("&Packages")
        add_actions(packages_menu, [add_action, self.remove_action,
                                    self.install_action,
                                    None, quit_action])

        # Uninstall tab
        self.uninstall_action = create_action(self, "&Uninstall packages",
                       icon=get_std_icon('DialogCancelButton'),
                       triggered=lambda: self.process_packages('uninstall'))
        self.uninstall_action.setEnabled(False)

        uninstall_btn = action2button(self.uninstall_action, autoraise=False,
                                      text_beside_icon=True)

        # Option menu
        option_menu = self.menuBar().addMenu("&Options")
        repair_action = create_action(self, "Repair packages",
                      tip="Reinstall packages even if version is unchanged",
                      toggled=self.toggle_repair)
        add_actions(option_menu, (repair_action,))

        # Advanced menu
        option_menu = self.menuBar().addMenu("&Advanced")
        register_action = create_action(self, "Register distribution...",
                      tip="Register file extensions, icons and context menu",
                      triggered=self.register_distribution)
        unregister_action = create_action(self, "Unregister distribution...",
                      tip="Unregister file extensions, icons and context menu",
                      triggered=self.unregister_distribution)
        open_console_action = create_action(self, "Open console here",
                    triggered=lambda: os.startfile(self.command_prompt_path))
        open_console_action.setEnabled(osp.exists(self.command_prompt_path))
        add_actions(option_menu, (register_action, unregister_action,
                                  None, open_console_action))

        # # View menu
        # view_menu = self.menuBar().addMenu("&View")
        # popmenu = self.createPopupMenu()
        # add_actions(view_menu, popmenu.actions())

        # Help menu
        about_action = create_action(self, "About %s..." % self.NAME,
                                icon=get_std_icon('MessageBoxInformation'),
                                triggered=self.about)
        report_action = create_action(self, "Report issue...",
                                icon=get_icon('bug.png'),
                                triggered=self.report_issue)
        help_menu = self.menuBar().addMenu("?")
        add_actions(help_menu, [about_action, None, report_action])

        # Status bar
        status = self.statusBar()
        status.setObjectName("StatusBar")
        status.showMessage("Welcome to %s!" % self.NAME, 5000)

        # Button layouts
        for act in (add_action, self.remove_action, None,
                    self.select_all_action, self.install_action):
            if act is None:
                btn_layout.addStretch()
            else:
                btn_layout.addWidget(action2button(act, autoraise=False,
                                                   text_beside_icon=True))
        unbtn_layout.addWidget(uninstall_btn)
        unbtn_layout.addStretch()

        self.resize(400, 500)

    def current_tab_changed(self, index):
        """Current tab has just changed"""
        if index == 0:
            self.show_drop_tip()

    def refresh_install_button(self):
        """Refresh install button enable state"""
        self.table.refresh_distribution(self.distribution)
        self.install_action.setEnabled(
            len(self.get_packages_to_be_installed()) > 0)
        nbp = len(self.table.get_selected_packages())
        for act in (self.remove_action, self.select_all_action):
            act.setEnabled(nbp > 0)
        self.show_drop_tip()

    def show_drop_tip(self):
        """Show drop tip on install table"""
        callback = lambda: QToolTip.showText(
                        self.table.mapToGlobal(self.table.pos()),
                        '<b>Drop files here</b><br>'\
                        'Executable installers (distutils) or source packages',
                        self)
        QTimer.singleShot(500, callback)

    def refresh_uninstall_button(self):
        """Refresh uninstall button enable state"""
        nbp = len(self.untable.get_selected_packages())
        self.uninstall_action.setEnabled(nbp > 0)

    def toggle_repair(self, state):
        """Toggle repair mode"""
        self.table.repair = state
        self.refresh_install_button()

    def register_distribution(self):
        """Register distribution"""
        answer = QMessageBox.warning(self, "Register distribution",
            "This will associate file extensions, icons and "
            "Windows explorer's context menu entries ('Edit with IDLE', ...) "
            "with selected Python distribution in Windows registry. "
            "<br>Shortcuts for all WinPython launchers will be installed "
            "in <i>WinPython</i> Start menu group (replacing existing "
            "shortcuts)."
            "<br>If <i>pywin32</i> is installed (it should be on any "
            "WinPython distribution), the Python ActiveX Scripting client "
            "will also be registered."
            "<br><br><u>Warning</u>: the only way to undo this change is to "
            "register another Python distribution to Windows registry."
            "<br><br><u>Note</u>: these actions are exactly the same as those "
            "performed when installing Python with the official installer "
            "for Windows.<br><br>Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            associate.register(self.distribution.target)

    def unregister_distribution(self):
        """Unregister distribution"""
        answer = QMessageBox.warning(self, "Unregister distribution",
            "This will remove file extensions associations, icons and "
            "Windows explorer's context menu entries ('Edit with IDLE', ...) "
            "with selected Python distribution in Windows registry. "
            "<br>Shortcuts for all WinPython launchers will be removed "
            "from <i>WinPython</i> Start menu group."
            "<br>If <i>pywin32</i> is installed (it should be on any "
            "WinPython distribution), the Python ActiveX Scripting client "
            "will also be unregistered."
            "<br><br>Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            associate.unregister(self.distribution.target)

    @property
    def command_prompt_path(self):
        return osp.join(self.distribution.target, osp.pardir,
                        "WinPython Command Prompt.exe")

    def distribution_changed(self, path):
        """Distribution path has just changed"""
        for package in self.table.model.packages:
            self.table.remove_package(package)
        dist = wppm.Distribution(to_text_string(path))
        self.table.refresh_distribution(dist)
        self.untable.refresh_distribution(dist)
        self.distribution = dist
        self.selector.label.setText('Python %s %dbit:'
                                    % (dist.version, dist.architecture))

    def add_packages(self):
        """Add packages"""
        basedir = self.basedir if self.basedir is not None else ''
        fnames, _selfilter = getopenfilenames(parent=self, basedir=basedir,
                                 caption='Add packages',
                                 filters='*.exe *.zip *.tar.gz *.whl')
        if fnames:
            self.basedir = osp.dirname(fnames[0])
            self.table.add_packages(fnames)

    def get_packages_to_be_installed(self):
        """Return packages to be installed"""
        return [pack for pack in self.table.get_selected_packages()
                if self.table.model.actions[pack]
                not in (NO_REPAIR_ACTION, NONE_ACTION)]

    def remove_packages(self):
        """Remove selected packages"""
        for package in self.table.get_selected_packages():
            self.table.remove_package(package)

    def process_packages(self, action):
        """Install/uninstall packages"""
        if action == 'install':
            text, table = 'Installing', self.table
            if not self.get_packages_to_be_installed():
                return
        elif action == 'uninstall':
            text, table = 'Uninstalling', self.untable
        else:
            raise AssertionError
        packages = table.get_selected_packages()
        if not packages:
            return
        func = getattr(self.distribution, action)
        thread = Thread(self)
        for widget in self.children():
            if isinstance(widget, QWidget):
                widget.setEnabled(False)
        try:
            status = self.statusBar()
        except AttributeError:
            status = self.parent().statusBar()
        progress = QProgressDialog(self, Qt.FramelessWindowHint)
        progress.setMaximum(len(packages)) #  old vicious bug:len(packages)-1
        for index, package in enumerate(packages):
            progress.setValue(index)
            progress.setLabelText("%s %s %s..."
                                  % (text, package.name, package.version))
            QApplication.processEvents()
            if progress.wasCanceled():
                break
            if package in table.model.actions:
                try:
                    thread.callback = lambda: func(package)
                    thread.start()
                    while thread.isRunning():
                        QApplication.processEvents()
                        if progress.wasCanceled():
                            status.setEnabled(True)
                            status.showMessage("Cancelling operation...")
                    table.remove_package(package)
                    error = thread.error
                except Exception as error:
                    error = to_text_string(error)
                if error is not None:
                    pstr = package.name + ' ' + package.version
                    QMessageBox.critical(self, "Error",
                                         "<b>Unable to %s <i>%s</i></b>"
                                         "<br><br>Error message:<br>%s"
                                         % (action, pstr, error))
        progress.setValue(progress.maximum())
        status.clearMessage()
        for widget in self.children():
            if isinstance(widget, QWidget):
                widget.setEnabled(True)
        thread = None
        for table in (self.table, self.untable):
            table.refresh_distribution(self.distribution)

    def report_issue(self):

        issue_template = """\
Python distribution:   %s
Control panel version: %s

Python Version:  %s
Qt Version:      %s, %s %s

What steps will reproduce the problem?
1.
2.
3.

What is the expected output? What do you see instead?


Please provide any additional information below.
""" % (python_distribution_infos(),
       __version__, platform.python_version(),
       winpython.qt.QtCore.__version__, winpython.qt.API_NAME,
       winpython.qt.__version__)

        url = QUrl("%s/issues/entry" % __project_url__)
        url.addQueryItem("comment", issue_template)
        QDesktopServices.openUrl(url)

    def about(self):
        """About this program"""
        QMessageBox.about(self,
            "About %s" % self.NAME,
            """<b>%s %s</b>
            <br>Package Manager and Advanced Tasks
            <p>Copyright &copy; 2012 Pierre Raybaut
            <br>Licensed under the terms of the MIT License
            <p>Created, developed and maintained by Pierre Raybaut
            <p><a href="%s">WinPython at Github.io</a>: downloads, bug reports,
            discussions, etc.</p>
            <p>This program is executed by:<br>
            <b>%s</b><br>
            Python %s, Qt %s, %s %s"""
            % (self.NAME, __version__, __project_url__,
               python_distribution_infos(),
               platform.python_version(), winpython.qt.QtCore.__version__,
               winpython.qt.API_NAME, winpython.qt.__version__,))


def main(test=False):
    app = QApplication([])
    win = PMWindow()
    win.show()
    if test:
        return app, win
    else:
        app.exec_()


def test():
    app, win = main(test=True)
    print(sys.modules)
    app.exec_()


if __name__ == "__main__":
    main()
