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

from guidata import disthelpers as dh

# Local imports
from winpython import wppm, utils
import diff


CHANGELOGS_DIR = osp.join(osp.dirname(__file__), 'changelogs')
assert osp.isdir(CHANGELOGS_DIR)


# =============================================================================
# How to prepare the MinGW package:
# =============================================================================
#
# * download and install MinGW using the latest mingw-get-inst-YYYYMMDD.exe
#   (the default target installation directory is C:\MinGW) and install the
#   C/C++/Fortran compilers
# * create WinPython MinGW32 directory %WINPYTHONBASEDIR%\tools.win32\mingw32
#   (where the WINPYTHONBASEDIR environment variable points to your WinPython
#    base directory -- see function `make_winpython` below)
# * explore the target MinGW installation directory (default: C:\MinGW)
# * copy the `bin`, `doc`, `include`, `lib` and `libexec` folders from
#   C:\MinGW to %WINPYTHONBASEDIR%\tools.win32\mingw32 (with MinGW 4.6.2,
#   the overall size should be around 151 MB for 1435 files and 63 folders):
#   * %WINPYTHONBASEDIR%\tools.win32\mingw32\bin
#   * %WINPYTHONBASEDIR%\tools.win32\mingw32\doc
#   * %WINPYTHONBASEDIR%\tools.win32\mingw32\include
#   * %WINPYTHONBASEDIR%\tools.win32\mingw32\lib
#   * %WINPYTHONBASEDIR%\tools.win32\mingw32\libexec


# =============================================================================
# How to prepare the gettext package:
# =============================================================================
#
# * download the latest gettext binaries for win32 (the latest should still be
#   from 2005... anyway)
# * add the missing 'libiconv2.dll' by copying the 'libiconv-2.dll' from MinGW
#   and renaming to 'libiconv2.dll'


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
            if line.startswith(start):
                lines[idx] = line[:len(start)+1] + ('"%s"' % text) + '\n'
    fd = open(fname, 'w')
    fd.writelines(lines)
    fd.close()


def build_nsis(srcname, dstname, data):
    """Build NSIS script"""
    portable_dir = osp.join(osp.dirname(__file__), 'portable')
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
    THG_PATH = r'\tools\TortoiseHg\thgw.exe'
    WINMERGE_PATH = r'\tools\WinMerge\WinMergeU.exe'
    MINGW32_PATH = r'\tools\mingw32\bin'

    def __init__(self, build_number, release_level, target, instdir,
                 srcdir=None, toolsdirs=None, verbose=False, simulation=False,
                 rootdir=None, install_options=None):
        assert isinstance(build_number, int)
        assert isinstance(release_level, str)
        self.build_number = build_number
        self.release_level = release_level
        self.target = target
        self.instdir = instdir
        self.srcdir = srcdir
        if toolsdirs is None:
            toolsdirs = []
        self._toolsdirs = toolsdirs
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

    @property
    def package_index_wiki(self):
        """Return Package Index page in Wiki format"""
        installed_tools = [('gettext', '0.14.4'), ('SciTE', '3.3.7')]

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
        thgpath = get_tool_path(self.THG_PATH, osp.isfile)
        if thgpath is not None:
            thgver = utils.get_thg_version(osp.dirname(thgpath))
            installed_tools += [('TortoiseHg', thgver)]
        if get_tool_path(self.WINMERGE_PATH, osp.isfile) is not None:
            installed_tools += [('WinMerge', '2.12.4')]
        gccpath = get_tool_path(self.MINGW32_PATH, osp.isdir)
        if gccpath is not None:
            gccver = utils.get_gcc_version(gccpath)
            installed_tools += [('MinGW32', gccver)]
        tools = []
        for name, ver in installed_tools:
            metadata = wppm.get_package_metadata('tools.ini', name)
            url, desc = metadata['url'], metadata['description']
            tools += ['[%s](%s) | %s | %s' % (name, url, ver, desc)]
        packages = ['[%s](%s) | %s | %s'
                    % (pack.name, pack.url, pack.version, pack.description)
                    for pack in sorted(self.installed_packages,
                                       key=lambda p: p.name.lower())]
        python_desc = 'Python programming language with standard library'
        return """## WinPython %s

The following packages are included in WinPython v%s.

### Tools

Name | Version | Description
-----|---------|------------
%s

### Python packages

Name | Version | Description
-----|---------|------------
[Python](http://www.python.org/) | %s | %s
%s""" % (self.winpyver, self.winpyver, '\n'.join(tools),
         self.python_fullversion, python_desc, '\n'.join(packages))

    @property
    def winpyver(self):
        """Return WinPython version (with release level!)"""
        return '%s.%d%s' % (self.python_fullversion, self.build_number,
                            self.release_level)

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
        path = [r"Lib\site-packages\PyQt4",
                "",  # Python root directory (python.exe)
                "DLLs", "Scripts", r"..\tools", r"..\tools\mingw32\bin"
                # , r"..\tools\Julia\bin"
                # , r"..\tools\R\bin"
                ]
        if self.distribution.architecture == 32 \
           and osp.isdir(self.winpydir + self.MINGW32_PATH):
            path += [r".." + self.MINGW32_PATH]
        return path

    @property
    def postpath(self):
        """Return PATH contents to be append to the environment variable"""
        path = []
        if osp.isfile(self.winpydir + self.THG_PATH):
            path += [r"..\tools\TortoiseHg"]
        return path

    @property
    def toolsdirs(self):
        """Return tools directory list"""
        return [osp.join(osp.dirname(__file__), 'tools')] + self._toolsdirs

    def get_package_fname(self, pattern):
        """Get package matching pattern in instdir"""
        for path in (self.instdir, self.srcdir):
            for fname in os.listdir(path):
                match = re.match(pattern, fname)
                if match is not None:
                    return osp.abspath(osp.join(path, fname))
        else:
            raise RuntimeError(
                'Could not found required package matching %s' % pattern)

    def install_package(self, pattern):
        """Install package matching pattern"""
        fname = self.get_package_fname(pattern)
        if fname not in [p.fname for p in self.installed_packages]:
            pack = wppm.Package(fname)
            if self.simulation:
                self.distribution._print(pack, "Installing")
                self.distribution._print_done()
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
                        args=None, workdir=None, settingspath=None):
        """Create exe launcher with NSIS"""
        assert name.endswith('.exe')
        portable_dir = osp.join(osp.dirname(__file__), 'portable')
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

        fname = osp.join(self.winpydir, osp.splitext(name)[0]+'.nsi')

        data = [('WINPYDIR', '$EXEDIR\%s' % self.python_name),
                ('WINPYVER', self.winpyver),
                # ('JULIA_HOME','$EXEDIR\%s' % r'\tools\Julia\bin'),
                # ('JULIA', '$EXEDIR\%s' % r'\tools\Julia\bin\julia.exe'),
                # ('R_HOME', '$EXEDIR\%s' % r'\tools\R'),
                ('COMMAND', command),
                ('PARAMETERS', args),
                ('WORKDIR', workdir),
                ('PREPATH', prepath),
                ('POSTPATH', postpath),
                ('Icon', icon_fname),
                ('OutFile', name)]
        if settingspath is not None:
            data += [('SETTINGSDIR', osp.dirname(settingspath)),
                     ('SETTINGSNAME', osp.basename(settingspath))]

        build_nsis('launcher.nsi', fname, data)

    def create_python_batch(self, name, script_name,
                            workdir=None, options=None):
        """Create batch file to run a Python script"""
        if options is None:
            options = ''
        else:
            options = ' ' + options
        if script_name.endswith('.pyw'):
            cmd = 'start %WINPYDIR%\pythonw.exe'
        else:
            cmd = '%WINPYDIR%\python.exe'
        changedir = ''
        if workdir is not None:
            workdir = osp.join('%WINPYDIR%', workdir)
            changedir = r"""cd %s
""" % workdir
        if script_name:
            script_name = ' ' + script_name
        self.create_batch_script(name, r"""@echo off
call %~dp0env.bat
""" + changedir + cmd + script_name + options + " %*")

    def create_installer(self):
        """Create installer with NSIS"""
        self._print("Creating WinPython installer")
        portable_dir = osp.join(osp.dirname(__file__), 'portable')
        fname = osp.join(portable_dir, 'installer-tmp.nsi')
        data = (('DISTDIR', self.winpydir),
                ('ARCH', self.winpy_arch),
                ('VERSION', '%s.%d' % (self.python_fullversion,
                                       self.build_number)),
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
        utils.extract_msi(self.python_fname, targetdir=self.python_dir)
        os.remove(osp.join(self.python_dir, osp.basename(self.python_fname)))
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
        for fname0 in os.listdir(self.srcdir) + os.listdir(self.instdir):
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

    def _install_required_packages(self):
        """Installing required packages"""
        print("Installing required packages")
        self.install_package('pywin32-([0-9\.]*[a-z]*).%s-py%s.exe'
                             % (self.py_arch, self.python_version))
        self.install_package('setuptools-([0-9\.]*[a-z]*[0-9]?).%s(-py%s)?.exe'
                             % (self.py_arch, self.python_version))
        # Install First these two packages to support wheel format
        self.install_package('pip-([0-9\.]*[a-z]*[0-9]?).%s(-py%s)?.exe'
                             % (self.py_arch, self.python_version))
        self.install_package('wheel-([0-9\.]*[a-z]*[0-9]?).tar.gz')

        self.install_package(
            'spyder(lib)?-([0-9\.]*[a-z]*[0-9]?).%s(-py%s)?.exe'
            % (self.py_arch, self.python_version))
        # PyQt module is now like :PyQt4-4.10.4-gpl-Py3.4-Qt4.8.6-x32.exe
        self.install_package(
            'PyQt4-([0-9\.\-]*)-gpl-Py%s-Qt([0-9\.\-]*)%s.exe'
            % (self.python_version, self.pyqt_arch))
        self.install_package(
            'PyQwt-([0-9\.]*)-py%s-%s-([a-z0-9\.\-]*).exe'
            % (self.python_version, self.pyqt_arch))

        # Install 'main packages' first (was before Wheel idea, keep for now)
        for happy_few in['numpy-MKL', 'scipy', 'matplotlib', 'pandas']:
            self.install_package(
                '%s-([0-9\.]*[a-z]*[0-9]?).%s(-py%s)?.exe'
                % (happy_few, self.py_arch, self.python_version))

    def _install_all_other_packages(self):
        """Try to install all other packages in instdir"""
        print("Installing other packages")
        for fname in os.listdir(self.srcdir) + os.listdir(self.instdir):
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
                             args='spyder', workdir='${WINPYDIR}\Scripts',
                             settingspath=settingspath)
        self.create_launcher('Spyder (light).exe', 'spyder_light.ico',
                             args='spyder --light',
                             workdir='${WINPYDIR}\Scripts',
                             settingspath=settingspath)
        self.create_launcher('WinPython Control Panel.exe', 'winpython.ico',
                             command='${WINPYDIR}\pythonw.exe',
                             args='wpcp', workdir='${WINPYDIR}\Scripts')

        # XXX: Uncomment this part only when we are clear on how to handle
        # the registration process during installation. "Register.exe" was
        # only intended to be executed during installation by installer.nsi,
        # but, we can't let this executable at the root of WinPython directory
        # (too dangerous) and we can't move it easily as launchers are made
        # to be executed when located at root directory... so we could remove
        # it just after executing it, but is it even possible?
        # self.create_launcher('Register.exe', 'winpython.ico',
        #                     args='register_python',
        #                     workdir='${WINPYDIR}\Scripts')

        self.create_launcher('Qt Demo.exe', 'qt.ico', args='qtdemo.pyw',
          workdir=r'${WINPYDIR}\Lib\site-packages\PyQt4\examples\demos\qtdemo')
        self.create_launcher('Qt Assistant.exe', 'qtassistant.ico',
                  command=r'${WINPYDIR}\Lib\site-packages\PyQt4\assistant.exe',
                  workdir=r'${WINPYDIR}')
        self.create_launcher('Qt Designer.exe', 'qtdesigner.ico',
                   command=r'${WINPYDIR}\Lib\site-packages\PyQt4\designer.exe',
                   workdir=r'${WINPYDIR}')
        self.create_launcher('Qt Linguist.exe', 'qtlinguist.ico',
                   command=r'${WINPYDIR}\Lib\site-packages\PyQt4\linguist.exe',
                   workdir=r'${WINPYDIR}')
        if self.python_version[0] == '3':
            ipython_exe = 'ipython3.exe'
            ipython_scr = 'ipython3-script.py'
        else:
            ipython_exe = 'ipython.exe'
            ipython_scr = 'ipython-script.py'
        if osp.isfile(osp.join(self.python_dir, 'Scripts', ipython_exe)):
            self.create_launcher('IPython Qt Console.exe', 'ipython.ico',
                                 command='${WINPYDIR}\pythonw.exe',
                                 args='%s qtconsole --matplotlib=inline' %
                                      ipython_scr,
                                 workdir='${WINPYDIR}\Scripts')
            self.create_launcher('IPython Notebook.exe', 'ipython.ico',
                                 command='${WINPYDIR}\python.exe',
                                 args='%s notebook --matplotlib=inline' %
                                      ipython_scr,
                                 workdir='${WINPYDIR}\Scripts')
        if osp.isfile(self.winpydir + self.THG_PATH):
            self.create_launcher('TortoiseHg.exe', 'tortoisehg.ico',
                                 command=r'${WINPYDIR}\..'+self.THG_PATH,
                                 workdir=r'${WINPYDIR}')
        if osp.isfile(self.winpydir + self.WINMERGE_PATH):
            self.create_launcher('WinMergeU.exe', 'winmerge.ico',
                                 command=r'${WINPYDIR}\..'+self.WINMERGE_PATH,
                                 workdir=r'${WINPYDIR}')
        self._print_done()

    def _create_batch_scripts(self):
        """Create batch scripts"""
        self._print("Creating batch scripts")
        self.create_batch_script('readme.txt',
r"""These batch files are not required to run WinPython.

The purpose of these files is to help the user writing his/her own
batch file to call Python scripts inside WinPython.
The examples here ('spyder.bat', 'spyder_light.bat', 'wppm.bat',
'pyqt_demo.bat', 'python.bat' and 'cmd.bat') are quite similar to the
launchers located in the parent directory.
The environment variables are set-up in 'env.bat'.""")
        conv = lambda path: ";".join(['%WINPYDIR%\\'+pth for pth in path])
        path = conv(self.prepath) + ";%PATH%;" + conv(self.postpath)
        self.create_batch_script('env.bat', """@echo off
set WINPYDIR=%~dp0..\\""" + self.python_name + r"""
set WINPYVER=""" + self.winpyver + """
set HOME=%WINPYDIR%\..\settings
set PATH=""" + path)

        self.create_batch_script('start_ijulia.bat', r"""@echo off
call %~dp0env.bat

rem ******************
rem Starting Ijulia  (supposing you install it in \tools\Julia of winpython)
rem ******************

set JULIA_HOME=%WINPYDIR%\..\tools\Julia\bin\
if  exist "%JULIA_HOME%" goto julia_next
echo --------------------
echo First install Julia in \tools\Julia of winpython
echo suggestion : don't create Julia shortcuts, nor menu, nor desktop icons
echo (they would create a .julia in your home directory rather than here)
echo When it will be done, launch again this .bat

if not exist "%JULIA_HOME%" goto julia_end

:julia_next
set SYS_PATH=%PATH%
set PATH=%JULIA_HOME%;%SYS_PATH%

set JULIA_EXE=julia.exe
set JULIA=%JULIA_HOME%%JULIA_EXE%

set private_libdir=bin
if not exist "%JULIA_HOME%..\lib\julia\sys.ji" ( ^
echo "Preparing Julia for first launch. This may take a while" && ^
echo "You may see two git related errors. This is completely normal" && ^
cd "%JULIA_HOME%..\share\julia\base" && ^
"%JULIA%" --build "%JULIA_HOME%..\lib\julia\sys0" sysimg.jl && ^
"%JULIA%" --build "%JULIA_HOME%..\lib\julia\sys" -J sys0.ji sysimg.jl && ^
popd && pushd "%cd%" )

echo "julia!"
echo --------------------
echo to install Ijulia for Winpython (the first time) :
echo type 'julia'
echo type in Julia prompt 'Pkg.add("IJulia")'
echo type in Julia prompt 'Pkg.add("PyCall")'
echo type in Julia prompt 'Pkg.add("PyPlot")'
echo type 'Ctrl + 'D' to quit Julia
echo nota : type 'help()' to get help in Julia
echo --------------------
echo if error during build process (July18th, 2014), look there for workaround)
echo "https://github.com/JuliaLang/WinRPM.jl/issues/27#issuecomment-49189546"
echo --------------------
rem (not working as of july 18th, 2014:
rem    https://github.com/JuliaLang/IJulia.jl/issues/206 )
rem echo to enable use of julia from python  (the first time):  
rem echo    launch winpython command prompt
rem echo    cd  ..\settings\.julia\v0.3\IJulia\python
rem echo    python setup.py install
rem echo see http://blog.leahhanson.us/julia-calling-python-calling-julia.html
rem echo --------------------
echo to launch Ijulia type now "Ipython notebook --profile julia"
rem Ipython notebook --profile julia
echo to use julia_magic from Ipython, type "Ipython notebook" instead.
:julia_end
cmd.exe /k
""")

        self.create_batch_script('start_with_r.bat', r"""@echo off
call %~dp0env.bat

rem ******************
rem R part (supposing you install it in \tools\R of winpython)
rem ******************
set tmp_Rdirectory=R
if not exist "%WINPYDIR%\..\tools\%tmp_Rdirectory%\bin" goto r_end

rem  R_HOME for rpy2, R_HOMEBIN for PATH
set R_HOME=%WINPYDIR%\..\tools\%tmp_Rdirectory%\
set R_HOMEbin=%WINPYDIR%\..\tools\%tmp_Rdirectory%\bin

set SYS_PATH=%PATH%
set PATH=%SYS_PATH%;%R_HOMEbin%

echo "r!"
echo "if you want it to be on your winpython icon, update %WINPYDIR%\settings\winpython.ini with"
echo "PATH=%path%"
echo " "
echo to launch Ipython with R, type now "Ipython notebook"
rem Ipython notebook

:r_end

cmd.exe /k
""")
        # Prepare a live patch on python (shame we need it) to have mingw64ok
        patch_distutils = ""
        if self.py_arch == "win-amd64":
            patch_distutils = r"""
%~dp0Find_And_replace.vbs "%WINPYDIR%\Lib\distutils\cygwinccompiler.py" "-O -W" "-O -DMS_WIN64 -W"

set WINPYXX=%WINPYVER:~0,1%%WINPYVER:~2,1%

rem Python 3.3+ case
set WINPYMSVCR=libmsvcr100.a
set WINPYSPEC=specs100

rem Python2.7 case
IF "%WINPYXX%"=="27" set WINPYMSVCR=libmsvcr90.a
IF "%WINPYXX%"=="27" set WINPYSPEC=specs90

cd %WINPYDIR%
copy  /Y ..\tools\mingw32\x86_64-w64-mingw32\lib\%WINPYMSVCR%  libs\%WINPYMSVCR%
copy  /Y ..\tools\mingw32\lib\gcc\x86_64-w64-mingw32\4.8.2\%WINPYSPEC% ..\tools\mingw32\lib\gcc\x86_64-w64-mingw32\4.8.2\specs

REM generate python.34 import file

..\tools\mingw32\bin\gendef.exe python%WINPYXX%.dll
..\tools\mingw32\bin\dlltool -D python%WINPYXX%.dll -d python%WINPYXX%.def -l libpython%WINPYXX%.dll.a
move /Y libpython%WINPYXX%.dll.a libs
del python%WINPYXX%.def
"""

        self.create_batch_script('Find_And_replace.vbs', r"""
' from http://stackoverflow.com/questions/15291341/
'             a-batch-file-to-read-a-file-and-replace-a-string-with-a-new-one

If WScript.Arguments.Count <> 3 then
  WScript.Echo "usage: Find_And_replace.vbs filename word_to_find replace_with "
  WScript.Quit
end If

FindAndReplace WScript.Arguments.Item(0), WScript.Arguments.Item(1), WScript.Arguments.Item(2)
'WScript.Echo "Operation Complete"

function FindAndReplace(strFilename, strFind, strReplace)
    Set inputFile = CreateObject("Scripting.FileSystemObject").OpenTextFile(strFilename, 1)
    strInputFile = inputFile.ReadAll
    inputFile.Close
    Set inputFile = Nothing
    result_text = Replace(strInputFile, strFind, strReplace)
    if result <> strInputFile then
        Set outputFile = CreateObject("Scripting.FileSystemObject").OpenTextFile(strFilename,2,true)
        outputFile.Write result_text
        outputFile.Close
        Set outputFile = Nothing
    end if
end function
""")

        self.create_batch_script('make_cython_use_mingw.bat', r"""@echo off
call %~dp0env.bat

rem ******************
rem mingw part (supposing you install it in \tools\mingw32)
rem ******************
set tmp_mingwdirectory=mingw32
if not exist "%WINPYDIR%\..\tools\%tmp_mingwdirectory%\bin" goto mingw_end

""" + patch_distutils +
r"""
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

goto mingw_success

:mingw_end
echo "%WINPYDIR%\..\tools\%tmp_mingwdirectory%\bin" not found

:mingw_success
rem pause

""")

        self.create_batch_script('make_cython_use_vc.bat', """@echo off
set pydistutils_cfg=%WINPYDIR%\..\settings\pydistutils.cfg
echo [config]>%pydistutils_cfg%
        """)

        self.create_batch_script('cmd.bat', r"""@echo off
call %~dp0env.bat
cmd.exe /k""")
        self.create_python_batch('python.bat', '')
        self.create_python_batch('spyder.bat', 'spyder', workdir='Scripts')
        self.create_python_batch('spyder_light.bat', 'spyder',
                                 workdir='Scripts', options='--light')
        self.create_python_batch('register_python.bat', 'register_python',
                                 workdir='Scripts')
        self.create_batch_script('register_python_for_all.bat',
                                 r"""@echo off
call %~dp0env.bat
call %~dp0register_python.bat --all""")
        self.create_python_batch('wpcp.bat', 'wpcp', workdir='Scripts')
        self.create_python_batch('pyqt_demo.bat', 'qtdemo.pyw',
                     workdir=r'Lib\site-packages\PyQt4\examples\demos\qtdemo')

        # pre-run wingw batch
        print('now pre-running extra mingw')
        filepath = osp.join(self.winpydir, 'scripts', 'make_cython_use_mingw.bat')
        p = subprocess.Popen(filepath, shell=True, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()

        self._print_done()

    def make(self, remove_existing=True):
        """Make WinPython distribution in target directory from the installers
        located in instdir

        remove_existing=True: (default) install all from scratch
        remove_existing=False: only for test purpose (launchers/scripts)"""
        if self.simulation:
            print("WARNING: this is just a simulation!", file=sys.stderr)

        self.python_fname = self.get_package_fname(
                            r'python-([0-9\.rc]*)(\.amd64)?\.msi')
        self.python_name = osp.basename(self.python_fname)[:-4]
        distname = 'win%s' % self.python_name
        vlst = re.match(r'winpython-([0-9\.]*)', distname
                        ).groups()[0].split('.')
        self.python_version = '.'.join(vlst[:2])
        self.python_fullversion = '.'.join(vlst[:3])

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
            self._install_required_packages()
            self._install_all_other_packages()
            if not self.simulation:
                self._copy_dev_tools()
        if not self.simulation:
            self._create_launchers()
            self._create_batch_scripts()

        if remove_existing and not self.simulation:
            self._print("Cleaning up distribution")
            self.distribution.clean_up()
            self._print_done()

        # Writing package index
        self._print("Writing package index")
        fname = osp.join(self.winpydir, os.pardir,
                         'WinPython-%s.txt' % self.winpyver)
        open(fname, 'w').write(self.package_index_wiki)
        # Copy to winpython/changelogs
        shutil.copyfile(fname, osp.join(CHANGELOGS_DIR, osp.basename(fname)))
        self._print_done()

        # Writing changelog
        self._print("Writing changelog")
        diff.write_changelog(self.winpyver, rootdir=self.rootdir)
        self._print_done()


def rebuild_winpython(basedir=None, verbose=False, archis=(32, 64)):
    """Rebuild winpython package from source"""
    basedir = basedir if basedir is not None else utils.BASE_DIR
    for architecture in archis:
        suffix = '.win32' if architecture == 32 else '.win-amd64'
        packdir = osp.join(basedir, 'packages' + suffix)
        for name in os.listdir(packdir):
            if name.startswith('winpython-') and name.endswith('.exe'):
                os.remove(osp.join(packdir, name))
        utils.build_wininst(osp.dirname(__file__), copy_to=packdir,
                            architecture=architecture, verbose=verbose)


def make_winpython(build_number, release_level, architecture,
                   basedir=None, verbose=False, remove_existing=True,
                   create_installer=True, simulation=False, rootdir=None,
                   install_options=None):
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
    packdir = osp.join(basedir, 'packages' + suffix)
    assert osp.isdir(packdir)
    srcdir = osp.join(basedir, 'packages.src')
    assert osp.isdir(srcdir)
    builddir = osp.join(basedir, 'build')
    if not osp.isdir(builddir):
        os.mkdir(builddir)
    toolsdir1 = osp.join(basedir, 'tools')
    assert osp.isdir(toolsdir1)
    toolsdirs = [toolsdir1]
    toolsdir2 = osp.join(basedir, 'tools' + suffix)
    if osp.isdir(toolsdir2):
        toolsdirs.append(toolsdir2)
    dist = WinPythonDistribution(build_number, release_level,
                                 builddir, packdir, srcdir, toolsdirs,
                                 verbose=verbose, simulation=simulation,
                                 rootdir=rootdir,
                                 install_options=install_options)
    dist.make(remove_existing=remove_existing)
    if create_installer and not simulation:
        dist.create_installer()
    return dist


def make_all(build_number, release_level, pyver,
             rootdir=None, simulation=False, create_installer=True,
             verbose=False, remove_existing=True, archis=(32, 64),
             install_options=['--no-deps']):
    """Make WinPython for both 32 and 64bit architectures:

    make_all(build_number, release_level, pyver, rootdir, simulation=False,
             create_installer=True, verbose=False, remove_existing=True)

    `build_number`: build number [int]
    `release_level`: release level (e.g. 'beta1', '') [str]
    `pyver`: Python version (X.Y format) [str]
    `rootdir`: [str] if None, WINPYTHONROOTDIR env var must be set
    (rootdir: root directory containing 'basedir27', 'basedir33', etc.)
    """ + utils.ROOTDIR_DOC
    basedir = utils.get_basedir(pyver, rootdir=rootdir)
    rebuild_winpython(basedir=basedir, archis=archis)
    for architecture in archis:
        make_winpython(build_number, release_level, architecture, basedir,
                       verbose, remove_existing, create_installer, simulation,
                       rootdir=rootdir, install_options=install_options)


if __name__ == '__main__':
    # DO create only what version at a time
    # You may have to manually delete previous build\winpython-.. directory

    #make_all(1, '', pyver='3.4', rootdir=r'D:\Winpython',
    #         verbose=False, archis=(32, ))
    make_all(1, '', pyver='3.4', rootdir=r'D:\Winpython',
              verbose=False, archis=(64, ))
    #make_all(2, '', pyver='3.3', rootdir=r'D:\Winpython',
    #          verbose=False, archis=(32, ))
    #make_all(2, '', pyver='3.3', rootdir=r'D:\Winpython',
    #          verbose=False, archis=(64, ))
    # make_all(2, '', pyver='2.7', rootdir=r'D:\Winpython',
    #          verbose=False, archis=(32, ))
    #make_all(2, '', pyver='2.7', rootdir=r'D:\Winpython',
    #         verbose=False, archis=(64, ))
