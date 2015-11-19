# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
WinPython build script

Created on Sun Aug 12 11:17:50 2012
"""

from __future__ import print_function

import os
import os.path as osp
import re
import subprocess
import shutil
import sys

# Local imports
from winpython import disthelpers as dh
from winpython import wppm, utils
import diff


CHANGELOGS_DIR = osp.join(osp.dirname(__file__), 'changelogs')
assert osp.isdir(CHANGELOGS_DIR)


def get_drives():
    """Return all active drives"""
    import win32api
    return win32api.GetLogicalDriveStrings().split('\000')[:-1]


def get_nsis_exe():
    """Return NSIS executable"""
    localdir = osp.join(sys.prefix, os.pardir, os.pardir)
    for drive in get_drives():
        for dirname in (r'C:\Program Files', r'C:\Program Files (x86)',
                        drive+r'PortableApps\NSISPortableANSI',
                        drive+r'PortableApps\NSISPortable',
                        osp.join(localdir, 'NSISPortableANSI'),
                        osp.join(localdir, 'NSISPortable'),
                        ):
            for subdirname in ('.', 'App'):
                exe = osp.join(dirname, subdirname, 'NSIS', 'makensis.exe')
                include = osp.join(dirname, subdirname, 'NSIS', 'include')
                if osp.isfile(exe) and\
                   osp.isfile(osp.join(include, 'TextReplace.nsh')):
                    return exe
    else:
        raise RuntimeError("NSIS (with TextReplace plugin) is not installed " +
                           "on this computer.")

NSIS_EXE = get_nsis_exe()


def replace_in_nsis_file(fname, data):
    """Replace text in line starting with *start*, from this position:
    data is a list of (start, text) tuples"""
    fd = open(fname, 'U')
    lines = fd.readlines()
    fd.close()
    for idx, line in enumerate(lines):
        for start, text in data:
            if start not in ('Icon', 'OutFile') and not start.startswith('!'):
                start = '!define ' + start
            if line.startswith(start + ' '):
                lines[idx] = line[:len(start)+1] + ('"%s"' % text) + '\n'
    fd = open(fname, 'w')
    fd.writelines(lines)
    print('nsis for ', fname, 'is', lines)
    fd.close()


def build_nsis(srcname, dstname, data):
    """Build NSIS script"""
    portable_dir = osp.join(osp.dirname(osp.abspath(__file__)), 'portable')
    shutil.copy(osp.join(portable_dir, srcname), dstname)
    data = [('!addincludedir', osp.join(portable_dir, 'include'))
            ] + list(data)
    replace_in_nsis_file(dstname, data)
    try:
        retcode = subprocess.call('"%s" -V2 "%s"' % (NSIS_EXE, dstname),
                                  shell=True, stdout=sys.stderr)
        if retcode < 0:
            print("Child was terminated by signal", -retcode, file=sys.stderr)
    except OSError as e:
        print("Execution failed:", e, file=sys.stderr)
    os.remove(dstname)


class WinPythonDistribution(object):
    """WinPython distribution"""
    MINGW32_PATH = r'\tools\mingw32\bin'
    R_PATH = r'\tools\R\bin'
    JULIA_PATH = r'\tools\Julia\bin'

    def __init__(self, build_number, release_level, target, wheeldir,
                 toolsdirs=None, verbose=False, simulation=False,
                 rootdir=None, install_options=None, flavor='', docsdirs=None):
        assert isinstance(build_number, int)
        assert isinstance(release_level, str)
        self.build_number = build_number
        self.release_level = release_level
        self.target = target
        self.wheeldir = wheeldir
        if toolsdirs is None:
            toolsdirs = []
        self._toolsdirs = toolsdirs
        if docsdirs is None:
            docsdirs = []
        self._docsdirs = docsdirs
        self.verbose = verbose
        self.winpydir = None
        self.python_fname = None
        self.python_name = None
        self.python_version = None
        self.python_fullversion = None
        self.distribution = None
        self.installed_packages = []
        self.simulation = simulation
        self.rootdir = rootdir  # addded to build from winpython
        self.install_options = install_options
        self.flavor = flavor

    @property
    def package_index_wiki(self):
        """Return Package Index page in Wiki format"""
        installed_tools = [('SciTE', '3.3.7')]

        def get_tool_path(relpath, checkfunc):
            if self.simulation:
                for dirname in self.toolsdirs:
                    path = dirname + relpath.replace(r'\tools', '')
                    if checkfunc(path):
                        return path
            else:
                path = self.winpydir + relpath
                if checkfunc(path):
                    return path
        gccpath = get_tool_path(self.MINGW32_PATH, osp.isdir)
        if gccpath is not None:
            gccver = utils.get_gcc_version(gccpath)
            installed_tools += [('MinGW32', gccver)]

        rpath = get_tool_path(self.R_PATH, osp.isdir)
        if rpath is not None:
            rver = utils.get_r_version(rpath)
            installed_tools += [('R', rver)]

        juliapath = get_tool_path(self.JULIA_PATH, osp.isdir)
        if juliapath is not None:
            juliaver = utils.get_julia_version(juliapath)
            installed_tools += [('Julia', juliaver)]

        tools = []
        for name, ver in installed_tools:
            metadata = wppm.get_package_metadata('tools.ini', name)
            url, desc = metadata['url'], metadata['description']
            tools += ['[%s](%s) | %s | %s' % (name, url, ver, desc)]

        # get all packages installed in the changelog, whatever the method
        self.installed_packages = []
        self.installed_packages = self.distribution.get_installed_packages()

        packages = ['[%s](%s) | %s | %s'
                    % (pack.name, pack.url, pack.version, pack.description)
                    for pack in sorted(self.installed_packages,
                                       key=lambda p: p.name.lower())]
        python_desc = 'Python programming language with standard library'
        return """## WinPython %s 

The following packages are included in WinPython v%s%s.

### Tools

Name | Version | Description
-----|---------|------------
%s

### Python packages

Name | Version | Description
-----|---------|------------
[Python](http://www.python.org/) | %s | %s
%s""" % (self.winpyver2+self.flavor, self.winpyver2+self.flavor,
(' %s' % self.release_level), '\n'.join(tools),
         self.python_fullversion, python_desc, '\n'.join(packages))

    @property
    def winpyver(self):
        """Return WinPython version (with flavor and release level!)"""
        return '%s.%d%s%s' % (self.python_fullversion, self.build_number,
                            self.flavor,self.release_level)

    @property
    def python_dir(self):
        """Return Python dirname (full path) of the target distribution"""
        return osp.join(self.winpydir, self.python_name)

    @property
    def winpy_arch(self):
        """Return WinPython architecture"""
        return '%dbit' % self.distribution.architecture

    @property
    def pyqt_arch(self):
        """Return distribution architecture, in PyQt format: x32/x64"""
        return 'x%d' % self.distribution.architecture

    @property
    def py_arch(self):
        """Return distribution architecture, in Python distutils format:
        win-amd64 or win32"""
        if self.distribution.architecture == 64:
            return 'win-amd64'
        else:
            return 'win32'

    @property
    def prepath(self):
        """Return PATH contents to be prepend to the environment variable"""
        path = [r"Lib\site-packages\PyQt5", r"Lib\site-packages\PyQt4",
                "",  # Python root directory (python.exe)
                "DLLs", "Scripts", r"..\tools", r"..\tools\mingw32\bin"
                ]
        if self.distribution.architecture == 32 \
           and osp.isdir(self.winpydir + self.MINGW32_PATH):
            path += [r".." + self.MINGW32_PATH]

        if self.distribution.architecture == 32:
            path += [r".." + self.R_PATH + r"\i386"]

        if self.distribution.architecture == 64:
            path += [r".." + self.R_PATH + r"\x64"]

        path += [r".." + self.JULIA_PATH]

        return path

    @property
    def postpath(self):
        """Return PATH contents to be append to the environment variable"""
        path = []
        # if osp.isfile(self.winpydir + self.THG_PATH):
        #     path += [r"..\tools\TortoiseHg"]
        return path

    @property
    def toolsdirs(self):
        """Return tools directory list"""
        return [osp.join(osp.dirname(osp.abspath(__file__)), 'tools')] + self._toolsdirs

    @property
    def docsdirs(self):
        """Return docs directory list"""
        if osp.isdir(osp.join(osp.dirname(osp.abspath(__file__)), 'docs')):
            return [osp.join(osp.dirname(osp.abspath(__file__)), 'docs')] + self._docsdirs
        else:
            return self._docsdirs

    def get_package_fname(self, pattern):
        """Get package matching pattern in wheeldir"""
        path = self.wheeldir
        for fname in os.listdir(path):
            match = re.match(pattern, fname)
            if match is not None or pattern == fname:
                return osp.abspath(osp.join(path, fname))
        else:
            raise RuntimeError(
                'Could not find required package matching %s' % pattern)

    def install_package(self, pattern, install_options=None):
        """Install package matching pattern"""
        fname = self.get_package_fname(pattern)
        if fname not in [p.fname for p in self.installed_packages]:
            pack = wppm.Package(fname)
            if self.simulation:
                self.distribution._print(pack, "Installing")
                self.distribution._print_done()
            else:
                if install_options:
                    self.distribution.install(pack, install_options)
                else:
                    self.distribution.install(pack,
                                         install_options=self.install_options)
            self.installed_packages.append(pack)

    def create_batch_script(self, name, contents):
        """Create batch script %WINPYDIR%/name"""
        scriptdir = osp.join(self.winpydir, 'scripts')
        if not osp.isdir(scriptdir):
            os.mkdir(scriptdir)
        fd = open(osp.join(scriptdir, name), 'w')
        fd.write(contents)
        fd.close()

    def create_launcher(self, name, icon, command=None,
                        args=None, workdir=None, settingspath=None,
                        bettercommand=None, betterworkdir=None, betterargs=None):
        """Create exe launcher with NSIS"""
        assert name.endswith('.exe')
        portable_dir = osp.join(osp.dirname(osp.abspath(__file__)), 'portable')
        icon_fname = osp.join(portable_dir, 'icons', icon)
        assert osp.isfile(icon_fname)

        # Customizing NSIS script
        conv = lambda path: ";".join(['${WINPYDIR}\\'+pth for pth in path])
        prepath = conv(self.prepath)
        postpath = conv(self.postpath)
        if command is None:
            if args is not None and '.pyw' in args:
                command = '${WINPYDIR}\pythonw.exe'
            else:
                command = '${WINPYDIR}\python.exe'
        if args is None:
            args = ''
        if workdir is None:
            workdir = ''

        if bettercommand is None:
            bettercommand = command
        if betterworkdir is None:
            betterworkdir = workdir
        if betterargs is None:
            betterargs = args

        fname = osp.join(self.winpydir, osp.splitext(name)[0]+'.nsi')

        data = [('WINPYDIR', '$EXEDIR\%s' % self.python_name),
                ('WINPYVER', self.winpyver),
                ('COMMAND', command),
                ('PARAMETERS', args),
                ('WORKDIR', workdir),
                ('PREPATH', prepath),
                ('POSTPATH', postpath),
                ('BETTERCOMMAND', bettercommand),
                ('BETTERWORKDIR', betterworkdir),
                ('BETTERPARAMETERS', betterargs),
                ('JUPYTER_DATA_DIR', '$EXEDIR\%s' % 'settings'),
                ('Icon', icon_fname),
                ('OutFile', name)]

        # handle well Flavor with R or JULIA
        data += [('R_HOME', '$EXEDIR%s' % r'\tools\R'),
                 ('JULIA_PKGDIR', '$EXEDIR%s' % r'\settings\.julia'),
                 ('JULIA_HOME', '$EXEDIR%s' % r'\tools\Julia\bin'),
                 ('JULIA', '$EXEDIR%s' % r'\tools\Julia\bin\julia.exe')]

        if settingspath is not None:
            data += [('SETTINGSDIR', osp.dirname(settingspath)),
                     ('SETTINGSNAME', osp.basename(settingspath))]

        build_nsis('launcher.nsi', fname, data)

    def create_python_batch(self, name, script_name,
                            workdir=None, options=None, command=None):
        """Create batch file to run a Python script"""
        if options is None:
            options = ''
        else:
            options = ' ' + options

        if command is None:
            if script_name.endswith('.pyw'):
                command = 'start %WINPYDIR%\pythonw.exe'
            else:
                command = '%WINPYDIR%\python.exe'
        changedir = ''
        if workdir is not None:
            workdir = osp.join('%WINPYDIR%', workdir)
            changedir = r"""cd %s
""" % workdir
        if script_name:
            script_name = ' ' + script_name
        self.create_batch_script(name, r"""@echo off
call %~dp0env.bat
""" + changedir + command + script_name + options + " %*")

    def create_installer(self):
        """Create installer with NSIS"""
        self._print("Creating WinPython installer")
        portable_dir = osp.join(osp.dirname(osp.abspath(__file__)), 'portable')
        fname = osp.join(portable_dir, 'installer-tmp.nsi')
        data = (('DISTDIR', self.winpydir),
                ('ARCH', self.winpy_arch),
                ('VERSION', '%s.%d%s' % (self.python_fullversion,
                                       self.build_number, self.flavor)),
                ('RELEASELEVEL', self.release_level),)
        build_nsis('installer.nsi', fname, data)
        self._print_done()

    def _print(self, text):
        """Print action text indicating progress"""
        if self.verbose:
            utils.print_box(text)
        else:
            print(text + '...', end=" ")

    def _print_done(self):
        """Print OK at the end of a process"""
        if not self.verbose:
            print("OK")

    def _extract_python(self):
        """Extracting Python installer, creating distribution object"""
        self._print("Extracting Python installer")
        os.mkdir(self.python_dir)
        if  self.python_fname[-3:] == 'zip':  # Python3.5
           utils.extract_archive(self.python_fname, targetdir=self.python_dir+r'\..')
        else:   
           utils.extract_msi(self.python_fname, targetdir=self.python_dir)
           os.remove(osp.join(self.python_dir, osp.basename(self.python_fname)))
           if not os.path.exists(osp.join(self.python_dir, 'Scripts')):
               os.mkdir(osp.join(self.python_dir, 'Scripts'))
        self._print_done()

    def _add_msvc_files(self):
        """Adding Microsoft Visual C++ DLLs"""
        print("Adding Microsoft Visual C++ DLLs""")
        msvc_version = dh.get_msvc_version(self.distribution.version)
        for fname in dh.get_msvc_dlls(msvc_version,
                                  architecture=self.distribution.architecture):
            shutil.copy(fname, self.python_dir)

    def _check_packages(self):
        """Check packages for duplicates or unsupported packages"""
        print("Checking packages")
        packages = []
        my_plist = []
        my_plist += os.listdir(self.wheeldir)
        for fname0 in my_plist:
            fname = self.get_package_fname(fname0)
            if fname == self.python_fname:
                continue
            try:
                pack = wppm.Package(fname)
            except NotImplementedError:
                print("WARNING: package %s is not supported"
                      % osp.basename(fname), file=sys.stderr)
                continue
            packages.append(pack)
        all_duplicates = []
        for pack in packages:
            if pack.name in all_duplicates:
                continue
            all_duplicates.append(pack.name)
            duplicates = [p for p in packages if p.name == pack.name]
            if len(duplicates) > 1:
                print("WARNING: duplicate packages %s (%s)" %
                      (pack.name, ", ".join([p.version for p in duplicates])),
                      file=sys.stderr)

    def _install_all_other_packages(self):
        """Try to install all other packages in wheeldir"""
        print("Installing other packages")
        my_list = []
        my_list += os.listdir(self.wheeldir)
        for fname in my_list:
            if osp.basename(fname) != osp.basename(self.python_fname):
                try:
                    self.install_package(fname)
                except NotImplementedError:
                    print("WARNING: unable to install package %s"
                          % osp.basename(fname), file=sys.stderr)

    def _copy_dev_tools(self):
        """Copy dev tools"""
        self._print("Copying tools")
        toolsdir = osp.join(self.winpydir, 'tools')
        os.mkdir(toolsdir)
        for dirname in self.toolsdirs:
            for name in os.listdir(dirname):
                path = osp.join(dirname, name)
                copy = shutil.copytree if osp.isdir(path) else shutil.copyfile
                copy(path, osp.join(toolsdir, name))
                if self.verbose:
                    print(path + ' --> ' + osp.join(toolsdir, name))
        self._print_done()

    def _copy_dev_docs(self):
        """Copy dev docs"""
        self._print("Copying Noteebook docs")
        docsdir = osp.join(self.winpydir, 'notebooks')
        os.mkdir(docsdir)
        docsdir = osp.join(self.winpydir, 'notebooks', 'docs')
        os.mkdir(docsdir)
        for dirname in self.docsdirs:
            for name in os.listdir(dirname):
                path = osp.join(dirname, name)
                copy = shutil.copytree if osp.isdir(path) else shutil.copyfile
                copy(path, osp.join(docsdir, name))
                if self.verbose:
                    print(path + ' --> ' + osp.join(docsdir, name))
        self._print_done()

    def _create_launchers(self):
        """Create launchers"""
        self._print("Creating launchers")
        self.create_launcher('WinPython Command Prompt.exe', 'cmd.ico',
                             command='$SYSDIR\cmd.exe',
                             args='/k', workdir='${WINPYDIR}')
        self.create_launcher('WinPython Interpreter.exe', 'python.ico')
        self.create_launcher('IDLE (Python GUI).exe', 'python.ico',
                             args='idle.pyw',
                             workdir='${WINPYDIR}\Lib\idlelib')
        settingspath = osp.join('.spyder2', '.spyder.ini')
        self.create_launcher('Spyder.exe', 'spyder.ico',
                             command='${WINPYDIR}\python.exe',
                             args='-m spyderlib.start_app',
                             workdir='${WINPYDIR}\Scripts',
                             settingspath=settingspath)
        self.create_launcher('Spyder (light).exe', 'spyder_light.ico',
                             command='${WINPYDIR}\python.exe',
                             args='-m spyderlib.start_app --light',
                             workdir='${WINPYDIR}\Scripts',
                             settingspath=settingspath)

        self.create_launcher('WinPython Control Panel.exe', 'winpython.ico',
                             command='${WINPYDIR}\pythonw.exe',
                             args='-m winpython.controlpanel',
                             workdir='${WINPYDIR}\Scripts')

        python_lib_dir = osp.join(self.winpydir, self.python_name,
                                  r"Lib\site-packages")

        # Multi-Qt launchers (Qt5 has priority if found)
        Qt4_dir = r'${WINPYDIR}\Lib\site-packages\PyQt4'
        Qt5_dir = r'${WINPYDIR}\Lib\site-packages\PyQt5'

        self.create_launcher('Qt Demo.exe', 'qt.ico',
                             command=r'${WINPYDIR}\pythonw.exe',
                             args='qtdemo.pyw',
                             workdir=Qt4_dir+r'\examples\%s' % r'demos\qtdemo',
                             bettercommand=r'${WINPYDIR}\python.exe',
                             betterargs='qtdemo.py',
                             betterworkdir=Qt5_dir+r'\examples\%s' % r'qtdemo')

        self.create_launcher('Qt Assistant.exe', 'qtassistant.ico',
                             command=Qt4_dir + r'\assistant.exe',
                             workdir=r'${WINPYDIR}',
                             bettercommand=Qt5_dir + r'\assistant.exe')
        self.create_launcher('Qt Designer.exe', 'qtdesigner.ico',
                             command=Qt4_dir + r'\designer.exe',
                             workdir=r'${WINPYDIR}',
                             bettercommand=Qt5_dir + r'\designer.exe')
        self.create_launcher('Qt Linguist.exe', 'qtlinguist.ico',
                             command=(Qt4_dir + r'\linguist.exe'),
                             workdir=r'${WINPYDIR}',
                             bettercommand=Qt5_dir + r'\linguist.exe')

        # Jupyter launchers
        if osp.isfile(osp.join(self.python_dir, 'Scripts', 'jupyter.exe')):
            self.create_launcher('IPython Qt Console.exe', 'ipython.ico',
                                 command='${WINPYDIR}\Scripts\%s' %
                                         'jupyter-qtconsole.exe',
                                 workdir=r'${WINPYDIR}\..\notebooks')

            self.create_launcher('Jupyter Notebook.exe', 'jupyter.ico',
                                 command='${WINPYDIR}\Scripts\%s' %
                                         'jupyter-notebook.exe',
                                 workdir=r'${WINPYDIR}\..\notebooks')

        # R console launchers
        r_exe = self.R_PATH + r"\i386\R.exe"
        if osp.isfile(self.winpydir + r_exe):
            self.create_launcher('R Console32.exe', 'r.ico',
                                 command='${WINPYDIR}\..' + r_exe,
                                 workdir=r'${WINPYDIR}\..\notebooks')
        r_exe = self.R_PATH + r"\x64\R.exe"
        if osp.isfile(self.winpydir + r_exe):
            self.create_launcher('R Console64.exe', 'r.ico',
                                 command='${WINPYDIR}\..' + r_exe,
                                 workdir=r'${WINPYDIR}\..\notebooks')

        # Julia console launcher
        julia_exe   =  self.JULIA_PATH + r"\julia.exe"
        if osp.isfile(self.winpydir + julia_exe):
            self.create_launcher('Julia Console.exe', 'julia.ico',
                                 command='${WINPYDIR}\..'+ julia_exe,
                                 workdir=r'${WINPYDIR}\..\notebooks')

        self._print_done()

    def _create_batch_scripts_initial(self):
        """Create batch scripts"""
        self._print("Creating batch scripts initial")
        conv = lambda path: ";".join(['%WINPYDIR%\\'+pth for pth in path])
        path = conv(self.prepath) + ";%PATH%;" + conv(self.postpath)
        self.create_batch_script('env.bat', """@echo off
set WINPYDIR=%~dp0..\\""" + self.python_name + r"""
set WINPYVER=""" + self.winpyver + r"""
set HOME=%WINPYDIR%\..\settings
set WINPYARCH="WIN32"
if  "%WINPYDIR:~-5%"=="amd64" set WINPYARCH="WIN-AMD64"

rem handle R if included
if not exist "%WINPYDIR%\..\tools\R\bin" goto r_bad
set R_HOME=%WINPYDIR%\..\tools\R
if %WINPYARCH%=="WIN32"     set R_HOMEbin=%R_HOME%\bin\i386
if not %WINPYARCH%=="WIN32" set R_HOMEbin=%R_HOME%\bin\x64
:r_bad

rem handle Julia if included
if not exist "%WINPYDIR%\..\tools\Julia\bin" goto julia_bad
set JULIA_HOME=%WINPYDIR%\..\tools\Julia\bin\
set JULIA_EXE=julia.exe
set JULIA=%JULIA_HOME%%JULIA_EXE%
set JULIA_PKGDIR=%WINPYDIR%\..\settings\.julia
:julia_bad

set PATH=""" + path + """

rem force default pyqt5 kit for Spyder if PyQt5 module is there
if exist %WINPYDIR%\Lib\site-packages\PyQt5 set QT_API=pyqt5

rem keep nbextensions in Winpython directory, rather then %APPDATA% default
set JUPYTER_DATA_DIR=%WINPYDIR%\..\settings
""")

    def _create_batch_scripts(self):
        """Create batch scripts"""
        self._print("Creating batch scripts")
        self.create_batch_script('readme.txt',
r"""These batch files are not required to run WinPython.

The purpose of these files is to help the user writing his/her own
batch file to call Python scripts inside WinPython.
The examples here ('spyder.bat', 'spyder_light.bat', 'wpcp.bat',
'pyqt_demo.bat', 'python.bat' and 'cmd.bat') are quite similar to the
launchers located in the parent directory.
The environment variables are set-up in 'env.bat'.""")
        conv = lambda path: ";".join(['%WINPYDIR%\\'+pth for pth in path])
        path = conv(self.prepath) + ";%PATH%;" + conv(self.postpath)


        self.create_batch_script('make_cython_use_mingw.bat', r"""@echo off
call %~dp0env.bat

rem ******************
rem mingw part
rem ******************

set pydistutils_cfg=%WINPYDIR%\..\settings\pydistutils.cfg

set tmp_blank=
echo [config]>%pydistutils_cfg%
echo compiler=mingw32>>%pydistutils_cfg%

echo [build]>>%pydistutils_cfg%
echo compiler=mingw32>>%pydistutils_cfg%

echo [build_ext]>>%pydistutils_cfg%
echo compiler=mingw32>>%pydistutils_cfg%

echo cython has been set to use mingw32
echo to remove this, remove file "%pydistutils_cfg%"

rem pause

""")

        self.create_batch_script('make_cython_use_vc.bat', r"""@echo off
set pydistutils_cfg=%WINPYDIR%\..\settings\pydistutils.cfg
echo [config]>%pydistutils_cfg%
        """)

        self.create_batch_script('make_winpython_movable.bat',r"""@echo off
call %~dp0env.bat
echo patch pip and current launchers fopr move
rem %WINPYDIR%\python.exe -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%WINPYDIR%\Lib\site-packages\pip\_vendor\distlib\scripts.py', 'executable = get_executable()', 'executable = os.path.join(os.path.basename(get_executable()))' )"

%WINPYDIR%\python.exe -c "from winpython import wppm;dist=wppm.Distribution(r'%WINPYDIR%');dist.patch_standard_packages('pip');dist.patch_all_shebang(to_movable=True)"
pause
        """)

        self.create_batch_script('make_winpython_fix.bat',r"""@echo off
call %~dp0env.bat
echo patch pip and current launchers for non-move
%WINPYDIR%\python.exe -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%WINPYDIR%\Lib\site-packages\pip\_vendor\distlib\scripts.py', 'executable = os.path.join(os.path.basename(get_executable()))', 'executable = get_executable()' )"

%WINPYDIR%\python.exe -c "from winpython import wppm;dist=wppm.Distribution(r'%WINPYDIR%');dist.patch_all_shebang(to_movable=False)"
pause
        """)

        self.create_batch_script('cmd.bat', r"""@echo off
call %~dp0env.bat
cmd.exe /k""")
        self.create_python_batch('python.bat', '')
        self.create_python_batch('spyder.bat', 'spyderlib.start_app',
                                 workdir='Scripts',
                                 command = '%WINPYDIR%\python.exe -m')
        self.create_python_batch('spyder_light.bat', 'spyderlib.start_app',
                                 workdir='Scripts',
                                 command = '%WINPYDIR%\python.exe -m',
                                 options='--light')
        self.create_python_batch('register_python.bat', 'register_python',
                                 workdir='Scripts')
        self.create_batch_script('register_python_for_all.bat',
                                 r"""@echo off
call %~dp0env.bat
call %~dp0register_python.bat --all""")
        self.create_python_batch('wpcp.bat', '-m winpython.controlpanel', workdir='Scripts')
        self.create_python_batch('pyqt4_demo.bat', 'qtdemo.pyw',
             workdir=r'Lib\site-packages\PyQt4\examples\demos\qtdemo')
        self.create_python_batch('pyqt5_demo.bat', 'qtdemo.py',
             workdir=r'Lib\site-packages\PyQt5\examples\qtdemo')

        self.create_batch_script('ipython_notebook.bat', r"""@echo off
call %~dp0env.bat
cd %WINPYDIR%\Scripts
%WINPYDIR%\scripts\jupyter-notebook.exe --notebook-dir=%WINPYDIR%\..\notebooks %*
""")

        # pre-run mingw batch
        print('now pre-running extra mingw')
        filepath = osp.join(self.winpydir, 'scripts', 'make_cython_use_mingw.bat')
        p = subprocess.Popen(filepath, shell=True, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()

        self._print_done()

    def _run_complement_batch_scripts(self, this_batch="run_complement.bat"):
        """ tools\..\run_complement.bat for final complements"""
        print('now %s in tooldirs\..' % this_batch)
        for post_complement in list(set([osp.dirname(s)
                                         for s in self._toolsdirs])):
            filepath = osp.join(post_complement, this_batch)
            if osp.isfile(filepath):
                print('launch "%s"  for  "%s"' % (filepath,  self.winpydir))
                try:
                    retcode = subprocess.call('"%s"   "%s"' % (filepath,  self.winpydir),
                                              shell=True, stdout=sys.stderr)
                    if retcode < 0:
                        print("Child was terminated by signal", -retcode, file=sys.stderr)
                except OSError as e:
                    print("Execution failed:", e, file=sys.stderr)

        self._print_done()

    def make(self, remove_existing=True, requirements=None):  #, find_links=None):
        """Make WinPython distribution in target directory from the installers
        located in wheeldir

        remove_existing=True: (default) install all from scratch
        remove_existing=False: only for test purpose (launchers/scripts)
        requirements=file(s) of requirements (separated by space if several)"""
        if self.simulation:
            print("WARNING: this is just a simulation!", file=sys.stderr)

        self.python_fname = self.get_package_fname(
                            r'python-([0-9\.rc]*)((\.|\-)amd64)?\.(msi|zip)')
        self.python_name = osp.basename(self.python_fname)[:-4]
        distname = 'win%s' % self.python_name
        vlst = re.match(r'winpython-([0-9\.]*)', distname
                        ).groups()[0].split('.')
        self.python_version = '.'.join(vlst[:2])
        self.python_fullversion = '.'.join(vlst[:3])
        print(self.python_fname,self.python_name , distname, self.python_version, self.python_fullversion)
        # Create the WinPython base directory
        self._print("Creating WinPython %s base directory"
                    % self.python_version)
        self.winpydir = osp.join(self.target, distname)
        if osp.isdir(self.winpydir) and remove_existing \
           and not self.simulation:
            shutil.rmtree(self.winpydir, onerror=utils.onerror)
        if not osp.isdir(self.winpydir):
            os.mkdir(self.winpydir)
        if remove_existing and not self.simulation:
            # Create settings directory
            # (only necessary if user is starting an application with a batch
            #  scripts before using an executable launcher, because the latter
            #  is creating the directory automatically)
            os.mkdir(osp.join(self.winpydir, 'settings'))
        self._print_done()

        if remove_existing and not self.simulation:
            self._extract_python()
        self.distribution = wppm.Distribution(self.python_dir,
                                              verbose=self.verbose,
                                              indent=True)

        self._check_packages()

        if remove_existing:
            if not self.simulation:
                self._add_msvc_files()
            if not self.simulation:
                self._create_batch_scripts_initial()
                self._create_batch_scripts()  # which set mingwpy as compiler
                self._run_complement_batch_scripts("run_required_first.bat")

            # force update of pip (FIRST) and setuptools here
            for req in ('pip', 'setuptools'):   
                actions = ["install","--upgrade", req]
                if self.install_options is not None:
                    actions += self.install_options
                print("piping %s" % ' '.join(actions))
                self._print("piping %s" % ' '.join(actions))
                self.distribution.do_pip_action(actions)
                
            # install packages in source_dirs (not using requirements.txt)
            self._install_all_other_packages()
            if not self.simulation:
                self._copy_dev_tools()
                self._copy_dev_docs()
        if not self.simulation:

            if requirements:
                if not list(requirements)==requirements:
                    requirements = requirements.split()
                for req in requirements:
                    actions = ["install","-r", req]
                    if self.install_options is not None:
                        actions += self.install_options
                    print("piping %s" % ' '.join(actions))
                    self._print("piping %s" % ' '.join(actions))
                    self.distribution.do_pip_action(actions)
                    #actions=["install","-r", req, "--no-index",
                    #         "--trusted-host=None"]+ links,
                    #         install_options=None)

            self._run_complement_batch_scripts()  # run_complement.bat
            self.distribution.patch_standard_packages()
            # launchers at the very end
            self._create_launchers()

        if remove_existing and not self.simulation:
            self._print("Cleaning up distribution")
            self.distribution.clean_up()
            self._print_done()

        # Writing package index
        self._print("Writing package index")
        # winpyver2 = need the version without build part
        self.winpyver2 = '%s.%s' % (self.python_fullversion, self.build_number)
        fname = osp.join(self.winpydir, os.pardir,
                         'WinPython%s-%s.txt' % (self.flavor, self.winpyver2))
        open(fname, 'w').write(self.package_index_wiki)
        # Copy to winpython/changelogs
        shutil.copyfile(fname, osp.join(CHANGELOGS_DIR, osp.basename(fname)))
        self._print_done()

        # Writing changelog
        self._print("Writing changelog")
        diff.write_changelog(self.winpyver2, rootdir=self.rootdir,
                             flavor=self.flavor, release_level=self.release_level)
        self._print_done()


def rebuild_winpython(basedir=None, verbose=False, archis=(32, 64)):
    """Rebuild winpython package from source"""
    basedir = basedir if basedir is not None else utils.BASE_DIR
    for architecture in archis:
        suffix = '.win32' if architecture == 32 else '.win-amd64'
        packdir = osp.join(basedir, 'packages' + suffix)
        for name in os.listdir(packdir):
            if name.startswith('winpython-') and name.endswith(('.exe', '.whl')):
                os.remove(osp.join(packdir, name))
        utils.build_wininst(osp.dirname(osp.abspath(__file__)), copy_to=packdir,
                            architecture=architecture, verbose=verbose, installer='bdist_wheel')


def make_winpython(build_number, release_level, architecture,
                   basedir=None, verbose=False, remove_existing=True,
                   create_installer=True, simulation=False, rootdir=None,
                   install_options=None, flavor='', requirements=None,
                   find_links=None, source_dirs=None, toolsdirs=None,
                   docsdirs=None):
    """Make WinPython distribution, for a given base directory and
    architecture:

    make_winpython(build_number, release_level, architecture,
                   basedir=None, verbose=False, remove_existing=True,
                   create_installer=True, simulation=False)

    `build_number`: build number [int]
    `release_level`: release level (e.g. 'beta1', '') [str]
    `architecture`: [int] (32 or 64)
    `basedir`: [str] if None, WINPYTHONBASEDIR env var must be set
    (rootdir: root directory containing 'basedir27', 'basedir33', etc.)
    """ + utils.ROOTDIR_DOC
    basedir = basedir if basedir is not None else utils.BASE_DIR
    assert basedir is not None, "The *basedir* directory must be specified"
    assert architecture in (32, 64)
    utils.print_box("Making WinPython %dbits" % architecture)
    suffix = '.win32' if architecture == 32 else '.win-amd64'

    # Create Build director, where Winpython will be constructed
    builddir = osp.join(basedir, 'build' + flavor)
    if not osp.isdir(builddir):
        os.mkdir(builddir)

    # Create 1 wheel directory to receive all packages whished  for build
    wheeldir = osp.join(builddir, 'wheels_tmp_%s' % architecture)
    if osp.isdir(wheeldir):
        shutil.rmtree(wheeldir, onerror=utils.onerror)
    os.mkdir(wheeldir)
    #  Copy Every package directory to the wheel directory

    # Optional pre-defined source_dirs
    if source_dirs is None:
        source_dirs = ''
    if not source_dirs == list(source_dirs):
        source_dirs = source_dirs.split()
    
    # Default natural behavior
    if source_dirs == []:
        source_dirs = [osp.join(basedir, 'packages' + suffix),
                       osp.join(basedir, 'packages.src'),
                       osp.join(basedir, flavor, 'packages' + suffix),
                       osp.join(basedir, flavor, 'packages.src')]
    print('source_dirs=', source_dirs)
    for m in list(set(source_dirs)):
        if osp.isdir(m):
            src_files = os.listdir(m)
            for file_name in src_files:
                full_file_name = os.path.join(m, file_name)
                shutil.copy(full_file_name, wheeldir)

    # Optional pre-defined toolsdirs
    if toolsdirs is None:
        toolsdirs = ''
    if not toolsdirs == list(toolsdirs):
        toolsdirs = toolsdirs.split()

    # Default natural behavior
    if toolsdirs == []:

        # Define List of Tools directory to collect
        toolsdir1 = osp.join(basedir, 'tools')
        assert osp.isdir(toolsdir1)
        toolsdirs = [toolsdir1]
        toolsdir2 = osp.join(basedir, 'tools' + suffix)
        if osp.isdir(toolsdir2):
            toolsdirs.append(toolsdir2)
    print('toolsdirs=', toolsdirs)

    # Optional pre-defined toolsdirs
    if docsdirs is None:
        docsdirs = ''
    if not docsdirs == list(docsdirs):
        docsdirs = docsdirs.split()

    # Default natural behavior
    if docsdirs == []:
        # Define List of docs directory to collect
        docsdir1 = osp.join(basedir, 'docs')
        assert osp.isdir(docsdir1)
        docsdirs = [docsdir1]
        docsdir2 = osp.join(basedir, 'docs' + suffix)
        if osp.isdir(docsdir2):
            docsdirs.append(docsdir2)
    print('docsdirs=', docsdirs)

    # install_options = ['--no-index', '--pre', '--find-links=%s' % wheeldir]

    if find_links is None:
        find_links = ''
    if not find_links == list(find_links):
        find_links = find_links.split()
    find_list = ['--find-links=%s' % l for l in find_links +[wheeldir]]
    dist = WinPythonDistribution(build_number, release_level,
                                 builddir, wheeldir, toolsdirs,
                                 verbose=verbose, simulation=simulation,
                                 rootdir=rootdir,
                                 install_options=install_options + find_list,
                                 flavor=flavor, docsdirs=docsdirs)
    dist.make(remove_existing=remove_existing, requirements=requirements)
    #          ,find_links=osp.join(basedir, 'packages.srcreq'))
    if create_installer and not simulation:
        dist.create_installer()
    return dist


def make_all(build_number, release_level, pyver,
             rootdir=None, simulation=False, create_installer=True,
             verbose=False, remove_existing=True, archis=(32, 64),
             install_options=['--no-index'], flavor='', requirements=None,
             find_links=None, source_dirs=None, toolsdirs=None, docsdirs=None):
    """Make WinPython for both 32 and 64bit architectures:

    make_all(build_number, release_level, pyver, rootdir, simulation=False,
             create_installer=True, verbose=False, remove_existing=True)

    `build_number`: build number [int]
    `release_level`: release level (e.g. 'beta1', '') [str]
    `pyver`: Python version (X.Y format) [str]
    `rootdir`: [str] if None, WINPYTHONROOTDIR env var must be set
    (rootdir: root directory containing 'basedir27', 'basedir33', etc.)
    """ + utils.ROOTDIR_DOC

    if install_options:
        if not list(install_options) == install_options:
            install_options = install_options.split()
        print('install_options', install_options)
    basedir = utils.get_basedir(pyver, rootdir=rootdir)
    rebuild_winpython(basedir=basedir, archis=archis)
    for architecture in archis:
        make_winpython(build_number, release_level, architecture, basedir,
                       verbose, remove_existing, create_installer, simulation,
                       rootdir=rootdir, install_options=install_options,
                       flavor=flavor, requirements=requirements,
                       find_links=find_links, source_dirs=source_dirs,
                       toolsdirs=toolsdirs, docsdirs=docsdirs)


if __name__ == '__main__':
    # DO create only one version at a time
    # You may have to manually delete previous build\winpython-.. directory

    #make_all(7, release_level='build1', pyver='3.4', rootdir=r'D:\WinpythonQt5', verbose=True,
    #         archis=(64, ), flavor='Qt5',
    #         requirements=r'D:\WinpythonQt5\basedir34\requirements.txt D:\WinpythonQt5\basedir34\requirements2.txt D:\WinpythonQt5\basedir34\requirements3.txt',
    #         install_options=r'--no-index --pre --trusted-host=None',
    #         find_links=r'D:\Winpython\basedir34\packages.srcreq')

    make_all(1, release_level='build3', pyver='3.4', rootdir=r'D:\Winpython', verbose=True,
             archis=(64, ), flavor='Barebone',
             requirements=r'D:\Winpython\basedir34\barebone_requirements.txt',
             install_options=r'--no-index --pre --trusted-host=None',
             find_links=r'D:\Winpython\packages.srcreq',
             source_dirs=r'D:\WinPython\basedir34\packages.src D:\WinPython\basedir34\packages.win-amd64',
             toolsdirs=r'D:\WinPython\basedir34\Tools.Slim',
             docsdirs=r'D:\WinPython\basedir34\docs.Slim'
)
