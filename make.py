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
                if osp.isfile(exe):
                    return exe
    else:
        raise RuntimeError("NSIS is not installed on this computer.")

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
                 basedir=None, install_options=None, flavor='', docsdirs=None):
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
        self.basedir = basedir  # added to build from winpython
        self.install_options = install_options
        self.flavor = flavor

    @property
    def package_index_wiki(self):
        """Return Package Index page in Wiki format"""
        installed_tools = []

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
        
        if get_tool_path (r'\tools\SciTE.exe', osp.isfile):
            installed_tools += [('SciTE', '3.3.7')]

        rpath = get_tool_path(self.R_PATH, osp.isdir)
        if rpath is not None:
            rver = utils.get_r_version(rpath)
            installed_tools += [('R', rver)]

        juliapath = get_tool_path(self.JULIA_PATH, osp.isdir)
        if juliapath is not None:
            juliaver = utils.get_julia_version(juliapath)
            installed_tools += [('Julia', juliaver)]

        pandocexe = get_tool_path (r'\tools\pandoc.exe', osp.isfile)
        if pandocexe is not None:
            pandocver = utils.get_pandoc_version(osp.dirname(pandocexe))
            installed_tools += [('Pandoc', pandocver)]


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
                        args=None, workdir=r'$EXEDIR\scripts',
                        launcher='launcher_basic.nsi'):
        """Create exe launcher with NSIS"""
        assert name.endswith('.exe')
        portable_dir = osp.join(osp.dirname(osp.abspath(__file__)), 'portable')
        icon_fname = osp.join(portable_dir, 'icons', icon)
        assert osp.isfile(icon_fname)

        # Customizing NSIS script
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
                ('COMMAND', command),
                ('PARAMETERS', args),
                ('WORKDIR', workdir),
                ('Icon', icon_fname),
                ('OutFile', name)]

        build_nsis(launcher, fname, data)

    def create_python_batch(self, name, script_name,
                            workdir=None, options=None, command=None):
        """Create batch file to run a Python script"""
        if options is None:
            options = ''
        else:
            options = ' ' + options

        if command is None:
            if script_name.endswith('.pyw'):
                command = 'start "%WINPYDIR%\pythonw.exe"'
            else:
                command = '"%WINPYDIR%\python.exe"'
        changedir = ''
        if workdir is not None:
            workdir = (workdir)
            changedir = r"""cd/D %s
""" % workdir
        if script_name:
            script_name = ' ' + script_name
        self.create_batch_script(name, r"""@echo off
call "%~dp0env_for_icons.bat"
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
           if self.winpyver < "3.6":
               # new Python 3.5 trick (https://bugs.python.org/issue23955)
               pyvenv_file = osp.join(self.python_dir, 'pyvenv.cfg')
               open(pyvenv_file, 'w').write('applocal=True\n')
           else:
               # new Python 3.6 trick (https://docs.python.org/3.6/using/windows.html#finding-modules)
               # (on hold since 2017-02-16, http://bugs.python.org/issue29578)
               pypath_file = osp.join(self.python_dir, 'python_onHold._pth')
               open(pypath_file, 'w').write('python36.zip\nDLLs\nLib\n.\nimport site\n')
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
        if not osp.isdir(docsdir):
            os.mkdir(docsdir)
        docsdir = osp.join(self.winpydir, 'notebooks', 'docs')
        if not osp.isdir(docsdir):
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
                             args=r'/k cmd.bat')        
        self.create_launcher('WinPython Powershell Prompt.exe', 'powershell.ico',
                             command='$SYSDIR\cmd.exe',
                             args=r'/k cmd_ps.bat')        
        
        self.create_launcher('WinPython Interpreter.exe', 'python.ico',
                             command='$SYSDIR\cmd.exe',
                             args= r'/k winpython.bat')

        #self.create_launcher('IDLEX (students).exe', 'python.ico',
        #                     command='$SYSDIR\cmd.exe',
        #                     args= r'/k IDLEX_for_student.bat  %*',
        #                     workdir='$EXEDIR\scripts')
        self.create_launcher('IDLEX (Python GUI).exe', 'python.ico',
                             command='wscript.exe',
                             args= r'Noshell.vbs winidlex.bat')

        self.create_launcher('Spyder.exe', 'spyder.ico',
                             command='wscript.exe',
                             args=r'Noshell.vbs winspyder.bat')

        self.create_launcher('Spyder reset.exe', 'spyder_reset.ico',
                             command='wscript.exe',
                             args=r'Noshell.vbs spyder_reset.bat')

        self.create_launcher('WinPython Control Panel.exe', 'winpython.ico',
                             command='wscript.exe',
                             args=r'Noshell.vbs wpcp.bat')

        # Multi-Qt launchers
        self.create_launcher('Qt Designer.exe', 'qtdesigner.ico',
                             command='wscript.exe',
                             args=r'Noshell.vbs qtdesigner.bat')

        self.create_launcher('Qt Linguist.exe', 'qtlinguist.ico',
                             command='wscript.exe',
                             args=r'Noshell.vbs qtlinguist.bat')

        # Jupyter launchers
        self.create_launcher('IPython Qt Console.exe', 'ipython.ico',
                             command='wscript.exe',
                             args=r'Noshell.vbs winqtconsole.bat')

        # this one needs a shell to kill fantom processes
        self.create_launcher('Jupyter Notebook.exe', 'jupyter.ico',
                             command='$SYSDIR\cmd.exe',
                             args=r'/k winipython_notebook.bat')

        self._print_done()

    def _create_batch_scripts_initial(self):
        """Create batch scripts"""
        self._print("Creating batch scripts initial")
        conv = lambda path: ";".join(['%WINPYDIR%\\'+pth for pth in path])
        path = conv(self.prepath) + ";%PATH%;" + conv(self.postpath)

        convps = lambda path: ";".join(["$env:WINPYDIR\\"+pth for pth in path])
        pathps = convps(self.prepath) + ";$env:path;" + convps(self.postpath)

        self.create_batch_script('env.bat', r"""@echo off
set WINPYDIRBASE=%~dp0..
rem get a normalize path
CALL :NORMALIZEPATH "%WINPYDIRBASE%"
set WINPYDIRBASE=%RETVAL%
set RETVAL=

set WINPYDIR=%WINPYDIRBASE%"""+"\\" + self.python_name + r"""

set WINPYVER=""" + self.winpyver + r"""
set HOME=%WINPYDIRBASE%\settings
set WINPYDIRBASE=

set JUPYTER_DATA_DIR=%HOME%
set WINPYARCH=WIN32
if  "%WINPYDIR:~-5%"=="amd64" set WINPYARCH=WIN-AMD64
set FINDDIR=%WINDIR%\system32
echo ;%PATH%; | %FINDDIR%\find.exe /C /I ";%WINPYDIR%\;" >nul
if %ERRORLEVEL% NEQ 0 set PATH=""" + path + r"""

rem force default pyqt5 kit for Spyder if PyQt5 module is there
if exist "%WINPYDIR%\Lib\site-packages\PyQt5\__init__.py" set QT_API=pyqt5

rem ******************
rem handle R if included
rem ******************
if not exist "%WINPYDIR%\..\tools\R\bin" goto r_bad
set R_HOME=%WINPYDIR%\..\tools\R
if     "%WINPYARCH%"=="WIN32" set R_HOMEbin=%R_HOME%\bin\i386
if not "%WINPYARCH%"=="WIN32" set R_HOMEbin=%R_HOME%\bin\x64
:r_bad


rem ******************
rem handle Julia if included
rem ******************
if not exist "%WINPYDIR%\..\tools\Julia\bin" goto julia_bad
set JULIA_HOME=%WINPYDIR%\..\tools\Julia\bin\
set JULIA_EXE=julia.exe
set JULIA=%JULIA_HOME%%JULIA_EXE%
set JULIA_PKGDIR=%WINPYDIR%\..\settings\.julia
:julia_bad

rem ******************
rem WinPython.ini part (removed from nsis)
rem ******************
if not exist "%WINPYDIR%\..\settings" mkdir "%WINPYDIR%\..\settings" 
set winpython_ini=%WINPYDIR%\..\settings\winpython.ini
if not exist "%winpython_ini%" (
    echo [debug]>>"%winpython_ini%"
    echo state = disabled>>"%winpython_ini%"
    echo [environment]>>"%winpython_ini%"
    echo ## <?> Uncomment lines to override environment variables>>"%winpython_ini%"
    echo #HOME = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%>>"%winpython_ini%"
    echo #JUPYTER_DATA_DIR = %%HOME%%>>"%winpython_ini%"
    echo #WINPYWORKDIR = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%\Notebooks>>"%winpython_ini%"
)

rem *****
rem http://stackoverflow.com/questions/1645843/resolve-absolute-path-from-relative-path-and-or-file-name
rem *****
:: ========== FUNCTIONS ==========
EXIT /B

:NORMALIZEPATH
  SET RETVAL=%~dpfn1
  EXIT /B

""")

        self.create_batch_script('WinPython_PS_Prompt.ps1', r"""
###############################
### WinPython_PS_Prompt.ps1 ###
###############################
$0 = $myInvocation.MyCommand.Definition
$dp0 = [System.IO.Path]::GetDirectoryName($0)

$env:WINPYDIRBASE = "$dp0\.."
# get a normalize path
# http://stackoverflow.com/questions/1645843/resolve-absolute-path-from-relative-path-and-or-file-name
$env:WINPYDIRBASE = [System.IO.Path]::GetFullPath( $env:WINPYDIRBASE )

# avoid double_init (will only resize screen)
if (-not ($env:WINPYDIR -eq [System.IO.Path]::GetFullPath( $env:WINPYDIRBASE+"""+'"\\' + self.python_name + '"' + r""")) ) {


$env:WINPYDIR = $env:WINPYDIRBASE+"""+ '"' + '\\' + self.python_name + '"' + r"""


$env:WINPYVER = '""" + self.winpyver + r"""'
$env:HOME = "$env:WINPYDIRBASE\settings"
$env:WINPYDIRBASE = ""
$env:JUPYTER_DATA_DIR = "$env:HOME"
$env:WINPYARCH = 'WIN32'
if ($env:WINPYARCH.subString($env:WINPYARCH.length-5, 5) -eq 'amd64')  {
   $env:WINPYARCH = 'WIN-AMD64' } 


if (-not $env:PATH.ToLower().Contains(";"+ $env:WINPYDIR.ToLower()+ ";"))  {
 $env:PATH = """ + '"' +  pathps + '"' + r""" }

#rem force default pyqt5 kit for Spyder if PyQt5 module is there
if (Test-Path "$env:WINPYDIR\Lib\site-packages\PyQt5\__init__.py") { $env:QT_API = "pyqt5" } 



#####################
### handle R if included
#####################
if (Test-Path "$env:WINPYDIR\..\tools\R\bin") { 
    $env:R_HOME = "$env:WINPYDIR\..\tools\R"
    $env:R_HOMEbin = "$env:R_HOME\bin\x64"
    if ("$env:WINPYARCH" -eq "WIN32") {
        $env:R_HOMEbin = "$env:R_HOME\bin\i386"
    }
}

#####################
### handle Julia if included
#####################
if (Test-Path "$env:WINPYDIR\..\tools\Julia\bin") {
    $env:JULIA_HOME = "$env:WINPYDIR\..\tools\Julia\bin\"
    $env:JULIA_EXE = "julia.exe"
    $env:JULIA = "$env:JULIA_HOME$env:JULIA_EXE"
    $env:JULIA_PKGDIR = "$env:WINPYDIR\..\settings\.julia"
}

#####################
### WinPython.ini part (removed from nsis)
#####################
if (-not (Test-Path "$env:WINPYDIR\..\settings")) { md -Path "$env:WINPYDIR\..\settings" }
$env:winpython_ini = "$env:WINPYDIR\..\settings\winpython.ini"
if (-not (Test-Path $env:winpython_ini)) {
    "[debug]" | Add-Content -Path $env:winpython_ini
    "state = disabled" | Add-Content -Path $env:winpython_ini
    "[environment]" | Add-Content -Path $env:winpython_ini
    "## <?> Uncomment lines to override environment variables" | Add-Content -Path $env:winpython_ini
    "#HOME = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%" | Add-Content -Path $env:winpython_ini
    "#JUPYTER_DATA_DIR = %%HOME%%" | Add-Content -Path $env:winpython_ini
    "#WINPYWORKDIR = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%\Notebooks" | Add-Content -Path $env:winpython_ini
}


} 
###############################
### Set-WindowSize
###############################
Function Set-WindowSize {
Param([int]$x=$host.ui.rawui.windowsize.width,
      [int]$y=$host.ui.rawui.windowsize.heigth,
      [int]$buffer=$host.UI.RawUI.BufferSize.heigth)
    
    $buffersize = new-object System.Management.Automation.Host.Size($x,$buffer)
    $host.UI.RawUI.BufferSize = $buffersize
    $size = New-Object System.Management.Automation.Host.Size($x,$y)
    $host.ui.rawui.WindowSize = $size   
}
# Windows10 yelling at us with 150 40 6000
# no more needed ?
# Set-WindowSize 195 40 6000 

### Colorize to distinguish
#$host.ui.RawUI.BackgroundColor = "DarkBlue"
$host.ui.RawUI.BackgroundColor = "Black"
$host.ui.RawUI.ForegroundColor = "White"

""")

        self.create_batch_script('cmd_ps.bat', r"""@echo off
rem safe bet 
call "%~dp0env_for_icons.bat"
Powershell.exe -Command "& {Start-Process PowerShell.exe -ArgumentList '-ExecutionPolicy RemoteSigned -noexit -File ""%~dp0WinPython_PS_Prompt.ps1""'}"
exit
""")
             
        self.create_batch_script('WinPython_Interpreter_PS.bat', r"""@echo off
rem no safe bet (for comparisons)
Powershell.exe -Command "& {Start-Process PowerShell.exe -ArgumentList '-ExecutionPolicy RemoteSigned -noexit -File ""%~dp0WinPython_PS_Prompt.ps1""'}"
exit
""")
 
        self.create_batch_script('env_for_icons.bat', r"""@echo off
call "%~dp0env.bat"
set WINPYWORKDIR=%~dp0..\Notebooks
FOR /F "delims=" %%i IN ('cscript /nologo "%~dp0WinpythonIni.vbs"') DO set winpythontoexec=%%i
%winpythontoexec%set winpythontoexec=

rem ******************
rem missing student directory part
rem ******************

if not exist "%WINPYWORKDIR%" mkdir "%WINPYWORKDIR%"

if not exist "%HOME%\.spyder-py%WINPYVER:~0,1%"  mkdir "%HOME%\.spyder-py%WINPYVER:~0,1%"
if not exist "%HOME%\.spyder-py%WINPYVER:~0,1%\workingdir" echo %HOME%\Notebooks>"%HOME%\.spyder-py%WINPYVER:~0,1%\workingdir"

rem ******* make cython use mingwpy part *******
if not exist "%WINPYDIR%\..\settings\pydistutils.cfg" goto no_cython
if not exist "%HOME%\pydistutils.cfg" xcopy   "%WINPYDIR%\..\settings\pydistutils.cfg" "%HOME%" 
:no_cython 
""")
      
        self.create_batch_script('Noshell.vbs', 
            r"""
'from http://superuser.com/questions/140047/how-to-run-a-batch-file-without-launching-a-command-window/390129
If WScript.Arguments.Count >= 1 Then
    ReDim arr(WScript.Arguments.Count-1)
    For i = 0 To WScript.Arguments.Count-1
        Arg = WScript.Arguments(i)
        If InStr(Arg, " ") > 0 Then Arg = chr(34) & Arg & chr(34)
      arr(i) = Arg
    Next

    RunCmd = Join(arr)
    CreateObject("Wscript.Shell").Run RunCmd, 0 , True
End If
        """)
        
        self.create_batch_script('WinPythonIni.vbs', 
            r"""
Set colArgs = WScript.Arguments
If colArgs.Count> 0 Then 
  Filename=colArgs(0) 
else 
  Filename="..\settings\winpython.ini"
end if
my_lines = Split(GetFile(FileName) & vbNewLine , vbNewLine )
segment = "environment"
txt=""
Set objWSH =  CreateObject("WScript.Shell")
For each l in my_lines
    if left(l, 1)="[" then
        segment=split(mid(l, 2, 999) & "]","]")(0)
    ElseIf left(l, 1) <> "#" and instr(l, "=")>0  then
        data = Split(l & "=", "=")
        if segment="debug" and trim(data(0))="state" then data(0)= "WINPYDEBUG"
        if segment="environment" or segment= "debug" then 
            txt= txt & "set " & rtrim(data(0)) & "=" & translate(ltrim(data(1))) & "&& "
            objWSH.Environment("PROCESS").Item(rtrim(data(0))) = translate(ltrim(data(1)))
        end if
        if segment="debug" and trim(data(0))="state" then txt= txt & "set WINPYDEBUG=" & trim(data(1)) & "&&"
    End If
Next
wscript.echo txt


Function GetFile(ByVal FileName)
    Set FS = CreateObject("Scripting.FileSystemObject")
    If Left(FileName,3)="..\" then FileName = FS.GetParentFolderName(FS.GetParentFolderName(Wscript.ScriptFullName)) & mid(FileName,3,9999)
    If Left(FileName,3)=".\" then FileName = FS.GetParentFolderName(FS.GetParentFolderName(Wscript.ScriptFullName)) & mid(FileName,3,9999)
    On Error Resume Next
    GetFile = FS.OpenTextFile(FileName).ReadAll
End Function

Function translate(line)
    set dos = objWSH.Environment("PROCESS")
    tab = Split(line & "%", "%")
    for i = 1 to Ubound(tab) step 2   
       if tab(i)& "" <> "" and dos.Item(tab(i)) & "" <> "" then tab(i) =  dos.Item(tab(i))
    next
    translate =  Join(tab, "") 
end function
        """)

    def _create_batch_scripts(self):
        """Create batch scripts"""
        self._print("Creating batch scripts")
        self.create_batch_script('readme.txt',
r"""These batch files are required to run WinPython icons.

These files should help the user writing his/her own
specific batch file to call Python scripts inside WinPython.
The environment variables are set-up in 'env_.bat' and 'env_for_icons.bat'.""")
        conv = lambda path: ";".join(['%WINPYDIR%\\'+pth for pth in path])
        path = conv(self.prepath) + ";%PATH%;" + conv(self.postpath)


        self.create_batch_script('make_cython_use_mingw.bat', r"""@echo off
call "%~dp0env.bat"

rem ******************
rem mingw part
rem ******************

set pydistutils_cfg=%WINPYDIR%\..\settings\pydistutils.cfg

set tmp_blank=
echo [config]>"%pydistutils_cfg%"
echo compiler=mingw32>>"%pydistutils_cfg%"

echo [build]>>"%pydistutils_cfg%"
echo compiler=mingw32>>"%pydistutils_cfg%"

echo [build_ext]>>"%pydistutils_cfg%"
echo compiler=mingw32>>"%pydistutils_cfg%"

echo cython has been set to use mingw32
echo to remove this, remove file "%pydistutils_cfg%"

rem pause

""")

        self.create_batch_script('make_cython_use_vc.bat', r"""@echo off
call "%~dp0env.bat"
set pydistutils_cfg=%WINPYDIR%\..\settings\pydistutils.cfg
echo [config]>%pydistutils_cfg%
        """)

        self.create_batch_script('make_winpython_movable.bat',r"""@echo off
call "%~dp0env.bat"
echo patch pip and current launchers for move

"%WINPYDIR%\python.exe" -c "from winpython import wppm;dist=wppm.Distribution(r'%WINPYDIR%');dist.patch_standard_packages('pip', to_movable=True)"
pause
        """)

        self.create_batch_script('make_winpython_fix.bat',r"""@echo off
call "%~dp0env.bat"
echo patch pip and current launchers for non-move

"%WINPYDIR%\python.exe" -c "from winpython import wppm;dist=wppm.Distribution(r'%WINPYDIR%');dist.patch_standard_packages('pip', to_movable=False)"
pause
        """)

        self.create_batch_script('make_working_directory_be_not_winpython.bat', r"""@echo off
set winpython_ini=%~dp0..\\settings\winpython.ini
echo [debug]>"%winpython_ini%"
echo state = disabled>>"%winpython_ini%"
echo [environment]>>"%winpython_ini%"
echo ## <?> Uncomment lines to override environment variables>>"%winpython_ini%"
echo HOME = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%\settings>>"%winpython_ini%"
echo JUPYTER_DATA_DIR = %%HOME%%>>"%winpython_ini%"
echo WINPYWORKDIR = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%\Notebooks>>"%winpython_ini%"
""")

        self.create_batch_script('make_working_directory_be_winpython.bat', r"""@echo off
set winpython_ini=%~dp0..\\settings\winpython.ini
echo [debug]>"%winpython_ini%"
echo state = disabled>>"%winpython_ini%"
echo [environment]>>"%winpython_ini%"
echo ## <?> Uncomment lines to override environment variables>>"%winpython_ini%"
echo #HOME = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%\settings>>"%winpython_ini%"
echo #JUPYTER_DATA_DIR = %%HOME%%>>"%winpython_ini%"
echo #WINPYWORKDIR = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%\Notebooks>>"%winpython_ini%"
""")

        self.create_batch_script('cmd.bat', r"""@echo off
call "%~dp0env_for_icons.bat"
cmd.exe /k""")
       
        self.create_batch_script('python.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
rem backward compatibility for  python command-line users
"%WINPYDIR%\python.exe"  %*
""")                
        self.create_batch_script('winpython.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR%"
rem backward compatibility for non-ptpython users
if exist "%WINPYDIR%\scripts\ptpython.exe" (
    "%WINPYDIR%\scripts\ptpython.exe" %*
) else (
    "%WINPYDIR%\python.exe"  %*
)
""")                

        self.create_batch_script('idlex.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
rem backward compatibility for non-IDLEX users
if exist "%WINPYDIR%\scripts\idlex.pyw" (
    "%WINPYDIR%\python.exe" "%WINPYDIR%\scripts\idlex.pyw" %*
) else (
    "%WINPYDIR%\python.exe" "%WINPYDIR%\Lib\idlelib\idle.pyw" %*
)
""")

        self.create_batch_script('winidlex.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR%"
rem backward compatibility for non-IDLEX users
if exist "%WINPYDIR%\scripts\idlex.pyw" (
    "%WINPYDIR%\python.exe" "%WINPYDIR%\scripts\idlex.pyw" %*
) else (
    "%WINPYDIR%\python.exe" "%WINPYDIR%\Lib\idlelib\idle.pyw" %*
)
""")
        self.create_batch_script('spyder.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR%"
if exist "%WINPYDIR%\scripts\spyder3.exe" (
   "%WINPYDIR%\scripts\spyder3.exe" %*
) else (
   "%WINPYDIR%\scripts\spyder.exe" %*
)   
""")
        self.create_batch_script('winspyder.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR%"
if exist "%WINPYDIR%\scripts\spyder3.exe" (
   "%WINPYDIR%\scripts\spyder3.exe" %*
) else (
   "%WINPYDIR%\scripts\spyder.exe" %*
) 
""")

        self.create_batch_script('spyder_reset.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR%"
if exist "%WINPYDIR%\scripts\spyder3.exe" (
    "%WINPYDIR%\scripts\spyder3.exe" --reset %*
) else (
    "%WINPYDIR%\scripts\spyder.exe" --reset %*
)
""")

        self.create_batch_script('ipython_notebook.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR%"
"%WINPYDIR%\scripts\jupyter-notebook.exe" %*
""")

        self.create_batch_script('winipython_notebook.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR%"
"%WINPYDIR%\scripts\jupyter-notebook.exe" %*
""")

        self.create_batch_script('qtconsole.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR%"
"%WINPYDIR%\scripts\jupyter-qtconsole.exe" %*
""")
 

        self.create_batch_script('winqtconsole.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR%"
"%WINPYDIR%\scripts\jupyter-qtconsole.exe" %*
""")
 
        self.create_batch_script('qtdemo.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR%"
if exist "%WINPYDIR%\Lib\site-packages\PyQt5\examples\qtdemo\qtdemo.py" (
  "%WINPYDIR%\python.exe" "%WINPYDIR%\Lib\site-packages\PyQt5\examples\qtdemo\qtdemo.py"
)  
if exist "%WINPYDIR%\Lib\site-packages\PyQt4\examples\demos\qtdemo\qtdemo.pyw" (
  "%WINPYDIR%\pythonw.exe" "%WINPYDIR%\Lib\site-packages\PyQt4\examples\demos\qtdemo\qtdemo.pyw"
)
""")

        self.create_batch_script('qtdesigner.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR%"
if "%QT_API%"=="pyqt5" (
    "%WINPYDIR%\Lib\site-packages\PyQt5\designer.exe" %*
) else (
    "%WINPYDIR%\Lib\site-packages\PyQt4\designer.exe" %*
)
""")

        self.create_batch_script('qtassistant.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR%"
if "%QT_API%"=="pyqt5" (
    "%WINPYDIR%\Lib\site-packages\PyQt5\assistant.exe" %*
) else (
    "%WINPYDIR%\Lib\site-packages\PyQt4\assistant.exe" %*
)
""")        

        self.create_batch_script('qtlinguist.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR%"
if "%QT_API%"=="pyqt5" (
    cd/D "%WINPYDIR%\Lib\site-packages\PyQt5"
    "%WINPYDIR%\Lib\site-packages\PyQt5\linguist.exe" %*
) else (
    cd/D "%WINPYDIR%\Lib\site-packages\PyQt4"
    "%WINPYDIR%\Lib\site-packages\PyQt4\linguist.exe" %*
)
""")        
        
        self.create_python_batch('register_python.bat', 'register_python',
                                 workdir=r'"%WINPYDIR%\Scripts"')
        self.create_batch_script('register_python_for_all.bat',
                                 r"""@echo off
call "%~dp0env.bat"
call "%~dp0register_python.bat" --all""")

        self.create_batch_script('wpcp.bat',r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR%"
"%WINPYDIR%\python.exe" -m winpython.controlpanel %*
""")

        #self.create_python_batch('wpcp.bat', '-m winpython.controlpanel',
        #                         workdir=r'"%WINPYDIR%\Scripts"')

        self.create_batch_script('upgrade_pip.bat', r"""@echo off
call "%~dp0env.bat"
echo this will upgrade pip with latest version, then patch it for WinPython portability ok ?
pause
"%WINPYDIR%\python.exe" -m pip install --upgrade pip
"%WINPYDIR%\python.exe" -c "from winpython import wppm;dist=wppm.Distribution(r'%WINPYDIR%');dist.patch_standard_packages('pip', to_movable=True)
pause
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

    def make(self, remove_existing=True, requirements=None, my_winpydir=None):  #, find_links=None):
        """Make WinPython distribution in target directory from the installers
        located in wheeldir

        remove_existing=True: (default) install all from scratch
        remove_existing=False: only for test purpose (launchers/scripts)
        requirements=file(s) of requirements (separated by space if several)"""
        if self.simulation:
            print("WARNING: this is just a simulation!", file=sys.stderr)

        self.python_fname = self.get_package_fname(
                            r'python-([0-9\.rcb]*)((\.|\-)amd64)?\.(msi|zip)')
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
        if my_winpydir is None:        
            self.winpydir = osp.join(self.target, distname)  
        else: 
            self.winpydir = osp.join(self.target, my_winpydir)
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
                # launchers at the beginning
                self._create_launchers()


            # pre-patch current pip (until default python has pip 8.0.3)
            self.distribution.patch_standard_packages('pip')
            # not forced update of pip (FIRST) and setuptools here
            for req in ('pip', 'setuptools'):   
                actions = ["install","--upgrade", req]
                if self.install_options is not None:
                    actions += self.install_options
                print("piping %s" % ' '.join(actions))
                self._print("piping %s" % ' '.join(actions))
                self.distribution.do_pip_action(actions)
                self.distribution.patch_standard_packages(req)
                
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

        if remove_existing and not self.simulation:
            self._print("Cleaning up distribution")
            self.distribution.clean_up()
            self._print_done()

        # Writing package index
        self._print("Writing package index")
        # winpyver2 = need the version without build part
        self.winpyver2 = '%s.%s' % (self.python_fullversion, self.build_number)
        fname = osp.join(self.winpydir, os.pardir,
                         'WinPython%s-%s.md' % (self.flavor, self.winpyver2))
        open(fname, 'w').write(self.package_index_wiki)
        # Copy to winpython/changelogs
        shutil.copyfile(fname, osp.join(CHANGELOGS_DIR, osp.basename(fname)))
        self._print_done()

        # Writing changelog
        self._print("Writing changelog")
        diff.write_changelog(self.winpyver2, basedir=self.basedir,
                             flavor=self.flavor, release_level=self.release_level)
        self._print_done()


def rebuild_winpython(basedir=None, verbose=False, architecture=64, targetdir=None):
    """Rebuild winpython package from source"""
    basedir = basedir if basedir is not None else utils.BASE_DIR
    suffix = '.win32' if architecture == 32 else '.win-amd64'
    if targetdir is not None:
        packdir = targetdir
    else:
        packdir = osp.join(basedir, 'packages' + suffix)
    for name in os.listdir(packdir):
        if name.startswith('winpython-') and name.endswith(('.exe', '.whl')):
            os.remove(osp.join(packdir, name))
    utils.build_wininst(osp.dirname(osp.abspath(__file__)), copy_to=packdir,
                        architecture=architecture, verbose=verbose, installer='bdist_wheel')


def transform_in_list(list_in, list_type=None):
    """Transform a 'String or List' in List"""
    if list_in is None:
        list_in = ''
    if not list_in == list(list_in):
            list_in = list_in.split()
    if list_type:
        print(list_type, list_in) 
    return list_in


def make_all(build_number, release_level, pyver, architecture,
                   basedir, verbose=False, remove_existing=True,
                   create_installer=True, simulation=False,
                   install_options=['--no-index'], flavor='', requirements=None,
                   find_links=None, source_dirs=None, toolsdirs=None,
                   docsdirs=None):
    """Make WinPython distribution, for a given base directory and
    architecture:

    make_winpython(build_number, release_level, architecture,
                   basedir=None, verbose=False, remove_existing=True,
                   create_installer=True, simulation=False)

    `build_number`: build number [int]
    `release_level`: release level (e.g. 'beta1', '') [str]
    `pyver`: python version ('3.4' or 3.5')
    `architecture`: [int] (32 or 64)
    `basedir`: where will be created  tmp_wheel dir. and Winpython-xyz dir.
    """ + utils.ROOTDIR_DOC
    
    if basedir is None:
        basedir = utils.BASE_DIR

    assert basedir is not None, "The *basedir* directory must be specified"
    assert architecture in (32, 64)
    utils.print_box("Making WinPython %dbits" % architecture)

    # Create Build director, where Winpython will be constructed
    builddir = osp.join(basedir, 'build' + flavor)
    if not osp.isdir(builddir):
        os.mkdir(builddir)

    # Create 1 wheel directory to receive all packages whished  for build
    wheeldir = osp.join(builddir, 'wheels_tmp_%s' % architecture)
    if osp.isdir(wheeldir):
        shutil.rmtree(wheeldir, onerror=utils.onerror)
    os.mkdir(wheeldir)

    # Rebuild Winpython in this wheel dir
    rebuild_winpython(basedir=basedir, architecture=architecture, targetdir=wheeldir)

    #  Copy Every package directory to the wheel directory

    # Optional pre-defined source_dirs
    source_dirs = transform_in_list(source_dirs, 'source_dirs=')

    for m in list(set(source_dirs)):
        if osp.isdir(m):
            src_files = os.listdir(m)
            for file_name in src_files:
                full_file_name = os.path.join(m, file_name)
                shutil.copy(full_file_name, wheeldir)

    # Optional pre-defined toolsdirs
    toolsdirs = transform_in_list(toolsdirs, 'toolsdirs=')

    # Optional pre-defined toolsdirs
    docsdirs = transform_in_list(docsdirs, 'docsdirs=')

    # install_options = ['--no-index', '--pre', '--find-links=%s' % wheeldir]
    install_options = transform_in_list(install_options, 'install_options')
        
    find_links = transform_in_list(find_links, 'find_links')

    find_list = ['--find-links=%s' % l for l in find_links +[wheeldir]]
    dist = WinPythonDistribution(build_number, release_level,
                                 builddir, wheeldir, toolsdirs,
                                 verbose=verbose, simulation=simulation,
                                 basedir=basedir,
                                 install_options=install_options + find_list,
                                 flavor=flavor, docsdirs=docsdirs)
    # define a pre-defined winpydir, instead of having to guess
    my_winpydir = ('winpython-' + ('%s' % architecture) +'bit-' + pyver +
     '.x.' + ('%s' %build_number) )  # + flavor + release_level)   
    
    dist.make(remove_existing=remove_existing, requirements=requirements,
              my_winpydir=my_winpydir)
    #          ,find_links=osp.join(basedir, 'packages.srcreq'))
    if create_installer and not simulation:
        dist.create_installer()
    return dist


if __name__ == '__main__':
    # DO create only one version at a time
    # You may have to manually delete previous build\winpython-.. directory

    make_all(1, release_level='build3', pyver='3.4', basedir=r'D:\Winpython\basedir34', verbose=True,
             architecture=64, flavor='Barebone',
             requirements=r'D:\Winpython\basedir34\barebone_requirements.txt',
             install_options=r'--no-index --pre --trusted-host=None',
             find_links=r'D:\Winpython\packages.srcreq',
             source_dirs=r'D:\WinPython\basedir34\packages.src D:\WinPython\basedir34\packages.win-amd64',
             toolsdirs=r'D:\WinPython\basedir34\Tools.Slim',
             docsdirs=r'D:\WinPython\basedir34\docs.Slim'
)
