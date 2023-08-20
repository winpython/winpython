# -*- coding: utf-8 -*-
#
# Copyright © 2009-2011 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

# pylint: disable=W0613

"""
disthelpers
-----------

The ``guidata.disthelpers`` module provides helper functions for Python 
package distribution on Microsoft Windows platforms with ``py2exe`` or on 
all platforms thanks to ``cx_Freeze``.
"""

import sys
import os
from pathlib import Path
import shutil
import traceback
import atexit
import imp
from subprocess import Popen, PIPE
import warnings
from distutils.version import LooseVersion, StrictVersion

# ==============================================================================
# Module, scripts, programs
# ==============================================================================
def get_module_path(modname):
    """Return module *modname* base path"""
    module = sys.modules.get(modname, __import__(modname))
    return str(Path(module.__file__).parent.resolve())


# ==============================================================================
# Dependency management
# ==============================================================================
def get_changeset(path, rev=None):
    """Return Mercurial repository *path* revision number"""
    args = ['hg', 'parent']
    if rev is not None:
        args += ['--rev', str(rev)]
    process = Popen(
        args, stdout=PIPE, stderr=PIPE, cwd=path, shell=True
    )
    try:
        return (
            process.stdout.read().splitlines()[0].split()[1]
        )
    except IndexError:
        raise RuntimeError(process.stderr.read())


def prepend_module_to_path(module_path):
    """
    Prepend to sys.path module located in *module_path*
    Return string with module infos: name, revision, changeset
    
    Use this function:
    1) In your application to import local frozen copies of internal libraries
    2) In your py2exe distributed package to add a text file containing the returned string
    """
    if not Path(module_path).is_dir():
        # Assuming py2exe distribution
        return
    sys.path.insert(0, str(Path(module_path).resolve()))
    changeset = get_changeset(module_path)
    name = Path(module_path).name
    prefix = "Prepending module to sys.path"
    message = prefix + (
        f"{name} [revision {changeset}]"
    ).rjust(80 - len(prefix), ".")
    print(message, file=sys.stderr)
    if name in sys.modules:
        sys.modules.pop(name)
        nbsp = 0
        for modname in sys.modules.keys():
            if modname.startswith(name + '.'):
                sys.modules.pop(modname)
                nbsp += 1
        warning = f'(removed {name} from sys.modules'
        if nbsp:
            warning += f' and {nbsp} subpackages'
        warning += ')'
        print(warning.rjust(80), file=sys.stderr)
    return message


def prepend_modules_to_path(module_base_path):
    """Prepend to sys.path all modules located in *module_base_path*"""
    if not Path(module_base_path).is_dir():
        # Assuming py2exe distribution
        return
    fnames = [
        str(Path(module_base_path) / name)
        for name in os.listdir(module_base_path)
    ]
    messages = [
        prepend_module_to_path(dirname)
        for dirname in fnames
        if Path(dirname).is_dir()
    ]
    return os.linesep.join(messages)


# ==============================================================================
# Distribution helpers
# ==============================================================================
def _remove_later(fname):
    """Try to remove file later (at exit)"""

    def try_to_remove(fname):
        if Path(fname).exists():
            os.remove(fname)

    atexit.register(try_to_remove, str(Path(fname).resolve()))


def to_include_files(data_files):
    """Convert data_files list to include_files list
    
    data_files:
      * this is the ``py2exe`` data files format
      * list of tuples (dest_dirname, (src_fname1, src_fname2, ...))
    
    include_files:
      * this is the ``cx_Freeze`` data files format
      * list of tuples ((src_fname1, dst_fname1),
                        (src_fname2, dst_fname2), ...))
    """
    include_files = []
    for dest_dir, fnames in data_files:
        for source_fname in fnames:
            dest_fname = str(Path(dest_dir) / 
                Path(source_fname).name)
            include_files.append((source_fname, dest_fname))
    return include_files


def strip_version(version):
    """Return version number with digits only
    (Windows does not support strings in version numbers)"""
    return (
        version.split('beta')[0]
        .split('alpha')[0]
        .split('rc')[0]
        .split('dev')[0]
    )


def remove_dir(dirname):
    """Remove directory *dirname* and all its contents
    Print details about the operation (progress, success/failure)"""
    print(f"Removing directory '{dirname}'...", end=' ')
    try:
        shutil.rmtree(dirname, ignore_errors=True)
        print("OK")
    except Exception:
        print("Failed!")
        traceback.print_exc()


class Distribution(object):
    """Distribution object
    
    Help creating an executable using ``py2exe`` or ``cx_Freeze``
    """

    DEFAULT_EXCLUDES = [
        'Tkconstants',
        'Tkinter',
        'tcl',
        'tk',
        'wx',
        '_imagingtk',
        'curses',
        'PIL._imagingtk',
        'ImageTk',
        'PIL.ImageTk',
        'FixTk',
        'bsddb',
        'email',
        'pywin.debugger',
        'pywin.debugger.dbgcon',
        'matplotlib',
    ]
    DEFAULT_INCLUDES = []
    DEFAULT_BIN_EXCLUDES = [
        'MSVCP100.dll',
        'MSVCP90.dll',
        'w9xpopen.exe',
        'MSVCP80.dll',
        'MSVCR80.dll',
    ]
    DEFAULT_BIN_INCLUDES = []
    DEFAULT_BIN_PATH_INCLUDES = []
    DEFAULT_BIN_PATH_EXCLUDES = []

    def __init__(self):
        self.name = None
        self.version = None
        self.description = None
        self.target_name = None
        self._target_dir = None
        self.icon = None
        self.data_files = []
        self.includes = self.DEFAULT_INCLUDES
        self.excludes = self.DEFAULT_EXCLUDES
        self.bin_includes = self.DEFAULT_BIN_INCLUDES
        self.bin_excludes = self.DEFAULT_BIN_EXCLUDES
        self.bin_path_includes = (
            self.DEFAULT_BIN_PATH_INCLUDES
        )
        self.bin_path_excludes = (
            self.DEFAULT_BIN_PATH_EXCLUDES
        )
        self.msvc = os.name == 'nt'
        self._py2exe_is_loaded = False
        self._pyqt4_added = False
        self._pyside_added = False
        # Attributes relative to cx_Freeze:
        self.executables = []

    @property
    def target_dir(self):
        """Return target directory (default: 'dist')"""
        dirname = self._target_dir
        if dirname is None:
            return 'dist'
        else:
            return dirname

    @target_dir.setter  # analysis:ignore
    def target_dir(self, value):
        self._target_dir = value

    def setup(
        self,
        name,
        version,
        description,
        script,
        target_name=None,
        target_dir=None,
        icon=None,
        data_files=None,
        includes=None,
        excludes=None,
        bin_includes=None,
        bin_excludes=None,
        bin_path_includes=None,
        bin_path_excludes=None,
        msvc=None,
    ):
        """Setup distribution object
        
        Notes:
          * bin_path_excludes is specific to cx_Freeze (ignored if it's None)
          * if msvc is None, it's set to True by default on Windows 
            platforms, False on non-Windows platforms
        """
        self.name = name
        self.version = (
            strip_version(version)
            if os.name == 'nt'
            else version
        )
        self.description = description
        assert Path(script).is_file()
        self.script = script
        self.target_name = target_name
        self.target_dir = target_dir
        self.icon = icon
        if data_files is not None:
            self.data_files += data_files
        if includes is not None:
            self.includes += includes
        if excludes is not None:
            self.excludes += excludes
        if bin_includes is not None:
            self.bin_includes += bin_includes
        if bin_excludes is not None:
            self.bin_excludes += bin_excludes
        if bin_path_includes is not None:
            self.bin_path_includes += bin_path_includes
        if bin_path_excludes is not None:
            self.bin_path_excludes += bin_path_excludes
        if msvc is not None:
            self.msvc = msvc
        if self.msvc:
            try:
                pass  # manage via msvc_runtime wheel (or give up anyway)
                #  self.data_files += create_msvc_data_files()
            except IOError:
                print(
                    "Setting the msvc option to False "
                    "will avoid this error",
                    file=sys.stderr,
                )
                raise
        # cx_Freeze:
        self.add_executable(
            self.script, self.target_name, icon=self.icon
        )

    def add_text_data_file(self, filename, contents):
        """Create temporary data file *filename* with *contents*
        and add it to *data_files*"""
        open(filename, 'wb').write(contents)
        self.data_files += [("", (filename,))]
        _remove_later(filename)

    def add_data_file(self, filename, destdir=''):
        self.data_files += [(destdir, (filename,))]

    # ------ Adding packages
    def add_pyqt4(self):
        """Include module PyQt4 to the distribution"""
        if self._pyqt4_added:
            return
        self._pyqt4_added = True

        self.includes += [
            'sip',
            'PyQt4.Qt',
            'PyQt4.QtSvg',
            'PyQt4.QtNetwork',
        ]

        import PyQt4

        pyqt_path = str(Path(PyQt4.__file__).parent)

        # Configuring PyQt4
        conf = os.linesep.join(
            ["[Paths]", "Prefix = .", "Binaries = ."]
        )
        self.add_text_data_file('qt.conf', conf)

        # Including plugins (.svg icons support, QtDesigner support, ...)
        if self.msvc:
            vc90man = "Microsoft.VC90.CRT.manifest"
            pyqt_tmp = 'pyqt_tmp'
            if Path(pyqt_tmp).is_dir():
                shutil.rmtree(pyqt_tmp)
            os.mkdir(pyqt_tmp)
            vc90man_pyqt = str(Path(pyqt_tmp) / vc90man)
            man = (
                open(vc90man, "r")
                .read()
                .replace(
                    '<file name="',
                    '<file name="Microsoft.VC90.CRT\\',
                )
            )
            open(vc90man_pyqt, 'w').write(man)
        for dirpath, _, filenames in os.walk(
            str(Path(pyqt_path) / "plugins")
        ):
            filelist = [
                str(Path(dirpath) / f)     
                for f in filenames
                if Path(f).suffix in ('.dll', '.py')
            ]
            if self.msvc and [
                f
                for f in filelist
                if Path(f).suffix == '.dll'
            ]:
                # Where there is a DLL build with Microsoft Visual C++ 2008,
                # there must be a manifest file as well...
                # ...congrats to Microsoft for this great simplification!
                filelist.append(vc90man_pyqt)
            self.data_files.append(
                (
                    dirpath[
                        len(pyqt_path) + len(os.pathsep) :
                    ],
                    filelist,
                )
            )
        if self.msvc:
            atexit.register(remove_dir, pyqt_tmp)
        # Including french translation
        fr_trans = str(Path(pyqt_path) / "translations" / "qt_fr.qm")  
        if Path(fr_trans).exists():
            self.data_files.append(
                ('translations', (fr_trans,))
            )

    def add_pyside(self):
        """Include module PySide to the distribution"""
        if self._pyside_added:
            return
        self._pyside_added = True

        self.includes += [
            'PySide.QtDeclarative',
            'PySide.QtHelp',
            'PySide.QtMultimedia',
            'PySide.QtNetwork',
            'PySide.QtOpenGL',
            'PySide.QtScript',
            'PySide.QtScriptTools',
            'PySide.QtSql',
            'PySide.QtSvg',
            'PySide.QtTest',
            'PySide.QtUiTools',
            'PySide.QtWebKit',
            'PySide.QtXml',
            'PySide.QtXmlPatterns',
        ]

        import PySide

        pyside_path = str(Path(PySide.__file__).parent)

        # Configuring PySide
        conf = os.linesep.join(
            ["[Paths]", "Prefix = .", "Binaries = ."]
        )
        self.add_text_data_file('qt.conf', conf)

        # Including plugins (.svg icons support, QtDesigner support, ...)
        if self.msvc:
            vc90man = "Microsoft.VC90.CRT.manifest"
            os.mkdir('pyside_tmp')
            vc90man_pyside = str(Path('pyside_tmp') / vc90man)  
            man = (
                open(vc90man, "r")
                .read()
                .replace(
                    '<file name="',
                    '<file name="Microsoft.VC90.CRT\\',
                )
            )
            open(vc90man_pyside, 'w').write(man)
        for dirpath, _, filenames in os.walk(
            str(Path(pyside_path) / "plugins")  
        ):
            filelist = [
                str(Path(dirpath) / f)  
                for f in filenames
                if Path(f).suffix in ('.dll', '.py')
            ]
            if self.msvc and [
                f
                for f in filelist
                if Path(f).suffix == '.dll'
            ]:
                # Where there is a DLL build with Microsoft Visual C++ 2008,
                # there must be a manifest file as well...
                # ...congrats to Microsoft for this great simplification!
                filelist.append(vc90man_pyside)
            self.data_files.append(
                (
                    dirpath[
                        len(pyside_path) + len(os.pathsep) :
                    ],
                    filelist,
                )
            )
        # Replacing dlls found by cx_Freeze by the real PySide Qt dlls:
        # (http://qt-project.org/wiki/Packaging_PySide_applications_on_Windows)
        dlls = [
            str(Path(pyside_path) / fname) 
            for fname in os.listdir(pyside_path)
            if Path(fname).suffix == '.dll'
        ]
        self.data_files.append(('', dlls))

        if self.msvc:
            atexit.register(remove_dir, 'pyside_tmp')
        # Including french translation
        fr_trans = str(Path(pyside_path) / "translations" / "qt_fr.qm")     
        if Path(fr_trans).exists():
            self.data_files.append(
                ('translations', (fr_trans,))
            )

    def add_qt_bindings(self):
        """Include Qt bindings, i.e. PyQt4 or PySide"""
        try:
            imp.find_module('PyQt4')
            self.add_modules('PyQt4')
        except ImportError:
            self.add_modules('PySide')

    def add_matplotlib(self):
        """Include module Matplotlib to the distribution"""
        if 'matplotlib' in self.excludes:
            self.excludes.pop(
                self.excludes.index('matplotlib')
            )
        try:
            import matplotlib.numerix  # analysis:ignore

            self.includes += [
                'matplotlib.numerix.ma',
                'matplotlib.numerix.fft',
                'matplotlib.numerix.linear_algebra',
                'matplotlib.numerix.mlab',
                'matplotlib.numerix.random_array',
            ]
        except ImportError:
            pass
        self.add_module_data_files(
            'matplotlib',
            ('mpl-data',),
            (
                '.conf',
                '.glade',
                '',
                '.png',
                '.svg',
                '.xpm',
                '.ppm',
                '.npy',
                '.afm',
                '.ttf',
            ),
        )

    def add_modules(self, *module_names):
        """Include module *module_name*"""
        for module_name in module_names:
            print(f"Configuring module '{module_name}'")
            if module_name == 'PyQt4':
                self.add_pyqt4()
            elif module_name == 'PySide':
                self.add_pyside()
            elif module_name == 'scipy.io':
                self.includes += ['scipy.io.matlab.streams']
            elif module_name == 'matplotlib':
                self.add_matplotlib()
            elif module_name == 'h5py':
                import h5py

                for attr in [
                    '_stub',
                    '_sync',
                    'utils',
                    '_conv',
                    '_proxy',
                    'defs',
                ]:
                    if hasattr(h5py, attr):
                        self.includes.append(
                            f'h5py.{attr}'
                        )
                if (
                    self.bin_path_excludes is not None
                    and os.name == 'nt'
                ):
                    # Specific to cx_Freeze on Windows: avoid including a zlib dll
                    # built with another version of Microsoft Visual Studio
                    self.bin_path_excludes += [
                        r'C:\Program Files',
                        r'C:\Program Files (x86)',
                    ]
                    self.data_files.append(  # necessary for cx_Freeze only
                        (
                            '',
                            (
                                str(Path(get_module_path('h5py')) / 'zlib1.dll' 
                                ),
                            ),
                        )
                    )
            elif module_name in (
                'docutils',
                'rst2pdf',
                'sphinx',
            ):
                self.includes += [
                    'docutils.writers.null',
                    'docutils.languages.en',
                    'docutils.languages.fr',
                ]
                if module_name == 'rst2pdf':
                    self.add_module_data_files(
                        "rst2pdf",
                        ("styles",),
                        ('.json', '.style'),
                        copy_to_root=True,
                    )
                if module_name == 'sphinx':
                    import sphinx.ext

                    for fname in os.listdir(
                        str(Path(sphinx.ext.__file__).parent)
                    ):
                        if Path(fname).suffix == '.py':
                            modname = (
                                f'sphinx.ext.{Path(fname).stem}'
                            )
                            self.includes.append(modname)
            elif module_name == 'pygments':
                self.includes += [
                    'pygments',
                    'pygments.formatters',
                    'pygments.lexers',
                    'pygments.lexers.agile',
                ]
            elif module_name == 'zmq':
                # FIXME: this is not working, yet... (missing DLL)
                self.includes += [
                    'zmq',
                    'zmq.core._poll',
                    'zmq.core._version',
                    'zmq.core.constants',
                    'zmq.core.context',
                    'zmq.core.device',
                    'zmq.core.error',
                    'zmq.core.message',
                    'zmq.core.socket',
                    'zmq.core.stopwatch',
                ]
                if os.name == 'nt':
                    self.bin_includes += ['libzmq.dll']
            elif module_name == 'guidata':
                self.add_module_data_files(
                    'guidata',
                    ("images",),
                    ('.png', '.svg'),
                    copy_to_root=False,
                )
                try:
                    imp.find_module('PyQt4')
                    self.add_pyqt4()
                except ImportError:
                    self.add_pyside()
            elif module_name == 'guiqwt':
                self.add_module_data_files(
                    'guiqwt',
                    ("images",),
                    ('.png', '.svg'),
                    copy_to_root=False,
                )
                if os.name == 'nt':
                    # Specific to cx_Freeze: including manually MinGW DLLs
                    self.bin_includes += [
                        'libgcc_s_dw2-1.dll',
                        'libstdc++-6.dll',
                    ]
            else:
                try:
                    # Modules based on the same scheme as guidata and guiqwt
                    self.add_module_data_files(
                        module_name,
                        ("images",),
                        ('.png', '.svg'),
                        copy_to_root=False,
                    )
                except IOError:
                    raise RuntimeError(
                        f"Module not supported: {module_name}"
                    )

    def add_module_data_dir(
        self,
        module_name,
        data_dir_name,
        extensions,
        copy_to_root=True,
        verbose=False,
        exclude_dirs=[],
    ):
        """
        Collect data files in *data_dir_name* for module *module_name*
        and add them to *data_files*
        *extensions*: list of file extensions, e.g. ('.png', '.svg')
        """
        module_dir = get_module_path(module_name)
        nstrip = len(module_dir) + len(os.sep)
        data_dir = str(Path(module_dir) / data_dir_name)
        if not Path(data_dir).is_dir():
            raise IOError(
                f"Directory not found: {data_dir}"
            )
        for dirpath, _dirnames, filenames in os.walk(
            data_dir
        ):
            dirname = dirpath[nstrip:]
            if Path(dirpath).name in exclude_dirs:
                continue
            if not copy_to_root:
                dirname = str(Path(module_name) / dirname)
            pathlist = [
                str(Path(dirpath) / f)
                for f in filenames
                if Path(f).suffix.lower() in extensions
            ]
            self.data_files.append((dirname, pathlist))
            if verbose:
                for name in pathlist:
                    print("  ", name)

    def add_module_data_files(
        self,
        module_name,
        data_dir_names,
        extensions,
        copy_to_root=True,
        verbose=False,
        exclude_dirs=[],
    ):
        """
        Collect data files for module *module_name* and add them to *data_files*
        *data_dir_names*: list of dirnames, e.g. ('images', )
        *extensions*: list of file extensions, e.g. ('.png', '.svg')
        """
        print(
            f"Adding module '{module_name}' data files in {', '.join(data_dir_names)} ({', '.join(extensions)})"
        )
        module_dir = get_module_path(module_name)
        for data_dir_name in data_dir_names:
            self.add_module_data_dir(
                module_name,
                data_dir_name,
                extensions,
                copy_to_root,
                verbose,
                exclude_dirs,
            )
        translation_file = str(Path(module_dir) / "locale" / "fr" / 
                               "LC_MESSAGES" / f"{module_name}.mo" ) 
        if Path(translation_file).is_file():
            self.data_files.append(
                (
                    str(Path(
                        module_name) /
                        "locale" /
                        "fr" /
                        "LC_MESSAGES"),
                    (translation_file,),
                )
            )
            print(
                f"Adding module '{module_name}' translation file: {Path(translation_file).name}"
            )

    def build(
        self, library, cleanup=True, create_archive=None
    ):
        """Build executable with given library.

        library:
            * 'py2exe': deploy using the `py2exe` library
            * 'cx_Freeze': deploy using the `cx_Freeze` library

        cleanup: remove 'build/dist' directories before building distribution

        create_archive (requires the executable `zip`):
            * None or False: do nothing
            * 'add': add target directory to a ZIP archive
            * 'move': move target directory to a ZIP archive
        """
        if library == 'py2exe':
            self.build_py2exe(
                cleanup=cleanup,
                create_archive=create_archive,
            )
        elif library == 'cx_Freeze':
            self.build_cx_freeze(
                cleanup=cleanup,
                create_archive=create_archive,
            )
        else:
            raise RuntimeError(
                f"Unsupported library {library}"
            )

    def __cleanup(self):
        """Remove old build and dist directories"""
        remove_dir("build")
        if Path("dist").is_dir():
            remove_dir("dist")
        remove_dir(self.target_dir)

    def __create_archive(self, option):
        """Create a ZIP archive

        option:
            * 'add': add target directory to a ZIP archive
            * 'move': move target directory to a ZIP archive
        """
        name = self.target_dir
        os.system(f'zip "{name}.zip" -r "{name}"')
        if option == 'move':
            shutil.rmtree(name)

    def build_py2exe(
        self,
        cleanup=True,
        compressed=2,
        optimize=2,
        company_name=None,
        copyright=None,
        create_archive=None,
    ):
        """Build executable with py2exe

        cleanup: remove 'build/dist' directories before building distribution

        create_archive (requires the executable `zip`):
            * None or False: do nothing
            * 'add': add target directory to a ZIP archive
            * 'move': move target directory to a ZIP archive
        """
        from distutils.core import setup
        import py2exe  # Patching distutils -- analysis:ignore

        self._py2exe_is_loaded = True
        if cleanup:
            self.__cleanup()
        sys.argv += ["py2exe"]
        options = dict(
            compressed=compressed,
            optimize=optimize,
            includes=self.includes,
            excludes=self.excludes,
            dll_excludes=self.bin_excludes,
            dist_dir=self.target_dir,
        )
        windows = dict(
            name=self.name,
            description=self.description,
            script=self.script,
            icon_resources=[(0, self.icon)],
            bitmap_resources=[],
            other_resources=[],
            dest_base=Path(self.target_name).stem,
            version=self.version,
            company_name=company_name,
            copyright=copyright,
        )
        setup(
            data_files=self.data_files,
            windows=[windows],
            options=dict(py2exe=options),
        )
        if create_archive:
            self.__create_archive(create_archive)

    def add_executable(
        self, script, target_name, icon=None
    ):
        """Add executable to the cx_Freeze distribution
        Not supported for py2exe"""
        from cx_Freeze import Executable

        base = None
        if script.endswith('.pyw') and os.name == 'nt':
            base = 'win32gui'
        self.executables += [
            Executable(
                self.script,
                base=base,
                icon=self.icon,
                targetName=self.target_name,
            )
        ]

    def build_cx_freeze(
        self, cleanup=True, create_archive=None
    ):
        """Build executable with cx_Freeze

        cleanup: remove 'build/dist' directories before building distribution

        create_archive (requires the executable `zip`):
            * None or False: do nothing
            * 'add': add target directory to a ZIP archive
            * 'move': move target directory to a ZIP archive
        """
        assert (
            not self._py2exe_is_loaded
        ), "cx_Freeze can't be executed after py2exe"
        from cx_Freeze import setup

        if cleanup:
            self.__cleanup()
        sys.argv += ["build"]
        build_exe = dict(
            include_files=to_include_files(self.data_files),
            includes=self.includes,
            excludes=self.excludes,
            bin_excludes=self.bin_excludes,
            bin_includes=self.bin_includes,
            bin_path_includes=self.bin_path_includes,
            bin_path_excludes=self.bin_path_excludes,
            build_exe=self.target_dir,
        )
        setup(
            name=self.name,
            version=self.version,
            description=self.description,
            executables=self.executables,
            options=dict(build_exe=build_exe),
        )
        if create_archive:
            self.__create_archive(create_archive)
