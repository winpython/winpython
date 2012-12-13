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

from guidata import disthelpers

# Local imports
from winpython import wppm, utils


#==============================================================================
# How to prepare the MinGW package:
#==============================================================================
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


def get_drives():
    """Return all active drives"""
    import win32api
    return win32api.GetLogicalDriveStrings().split('\000')[:-1]

def get_nsis_exe():
    """Return NSIS executable"""
    for drive in get_drives():
        for dirname in (r'C:\Program Files', r'C:\Program Files (x86)',
                        drive+r'PortableApps\NSISPortableANSI',
                        drive+r'PortableApps\NSISPortable',
                    ):
            for subdirname in ('.', 'App'):
                exe = osp.join(dirname, subdirname, 'NSIS', 'makensis.exe')
                include = osp.join(dirname, subdirname, 'NSIS', 'include')
                if osp.isfile(exe) and\
                   osp.isfile(osp.join(include, 'TextReplace.nsh')):
                    return exe
    else:
        raise RuntimeError, "NSIS (with TextReplace plugin) is not installed "\
                            "on this computer."

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
            print >>sys.stderr, "Child was terminated by signal", -retcode
    except OSError, e:
        print >>sys.stderr, "Execution failed:", e
    os.remove(dstname)


class WinPythonDistribution(object):
    """WinPython distribution"""
    THG_PATH = r'\tools\TortoiseHg\thgw.exe'
    WINMERGE_PATH = r'\tools\WinMerge\WinMerge.exe'
    MINGW32_PATH = r'\tools\mingw32\bin'
    
    def __init__(self, build_number, release_level, target, instdir,
                 srcdir=None, toolsdirs=None, verbose=False, simulation=False):
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
    
    @property
    def package_index_wiki(self):
        """Return Package Index page in Wiki format"""
        installed_tools = [('gettext', '0.14.4'), ('SciTE', '3.2.3')]        
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
            tools += ['|| [%s %s] || %s || %s ||' % (url, name, ver, desc)]
        packages = ['|| [%s %s] || %s || %s ||'
                    % (pack.url, pack.name, pack.version, pack.description)
                    for pack in sorted(self.installed_packages,
                                       key=lambda p: p.name.lower())]
        python_desc = 'Python programming language with standard library'
        return """== WinPython %s ==

The following packages are included in WinPython v%s.

=== Tools ===

%s

=== Python packages ===

|| [http://www.python.org/ Python] || %s || %s ||

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
                "DLLs", "Scripts", r"..\tools", r"..\tools\gnuwin32\bin"]
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
            raise RuntimeError,\
                  'Could not found required package matching %s' % pattern
    
    def install_package(self, pattern):
        """Install package matching pattern"""
        fname = self.get_package_fname(pattern)
        if fname not in [p.fname for p in self.installed_packages]:
            pack = wppm.Package(fname)
            if self.simulation:
                self.distribution._print(pack, "Installing")
                self.distribution._print_done()
            else:
                self.distribution.install(pack)
            self.installed_packages.append(pack)

    def create_batch_script(self, name, contents):
        """Create batch script %WINPYDIR%/name"""
        scriptdir = osp.join(self.winpydir, 'scripts')
        if not osp.isdir(scriptdir):
            os.mkdir(scriptdir)
        fd = file(osp.join(scriptdir, name), 'w')
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

    def create_python_batch(self, name, package_dir, script_name,
                            options=None):
        """Create batch file to run a Python script"""
        if options is None:
            options = ''
        else:
            options = ' ' + options
        if script_name.endswith('.pyw'):
            cmd = 'start %WINPYDIR%\pythonw.exe'
        else:
            cmd = '%WINPYDIR%\python.exe'
        if script_name:
            script_name = ' ' + script_name
        self.create_batch_script(name, r"""@echo off
call %~dp0env.bat
cd %WINPYDIR%""" + package_dir + r"""
""" + cmd + script_name + options + " %*")

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
    
    def _add_vs2008_files(self):
        """Adding Microsoft Visual Studio 2008 DLLs and manifest"""
        print("Adding Microsoft Visual C++ 2008 DLLs with manifest""")
        for fname in disthelpers.get_visual_studio_dlls(
                                architecture=self.distribution.architecture,
                                python_version=self.distribution.version):
            shutil.copy(fname, self.python_dir)

    def _install_required_packages(self):
        """Installing required packages"""
        print("Installing required packages")
        self.install_package('pywin32-([0-9\.]*[a-z]*).%s-py%s.exe'
                             % (self.py_arch, self.python_version))
        self.install_package('winpython-([0-9\.]*[a-z]*).%s(-py%s)?.exe'
                             % (self.py_arch, self.python_version))
        self.install_package('spyder(lib)?-([0-9\.]*[a-z]*).%s(-py%s)?.exe'
                             % (self.py_arch, self.python_version))
        self.install_package(pattern='PyQt-Py%s-%s-gpl-([0-9\.\-]*).exe'
                                     % (self.python_version, self.pyqt_arch))
        self.install_package(
                    pattern='PyQwt-([0-9\.]*)-py%s-%s-([a-z0-9\.\-]*).exe'
                            % (self.python_version, self.pyqt_arch))
    
    def _install_all_other_packages(self):
        """Try to install all other packages in instdir"""
        print("Installing other packages")
        for fname in os.listdir(self.srcdir) + os.listdir(self.instdir):
            try:
                self.install_package(fname)
            except NotImplementedError:
                pass
    
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
        self.create_launcher('Command prompt.exe', 'cmd.ico',
                             command='$SYSDIR\cmd.exe',
                             args='/k', workdir='${WINPYDIR}')
        self.create_launcher('Python interpreter.exe', 'python.ico')
        settingspath = osp.join('.spyder2', '.spyder.ini')
        self.create_launcher('Spyder.exe', 'spyder.ico',
                             args='spyder', workdir='${WINPYDIR}\Scripts',
                             settingspath=settingspath)
        self.create_launcher('Spyder (light).exe', 'spyder_light.ico',
                             args='spyder --light',
                             workdir='${WINPYDIR}\Scripts',
                             settingspath=settingspath)
        self.create_launcher('WP Control Panel.exe', 'winpython.ico',
                             args='wpcp', workdir='${WINPYDIR}\Scripts')
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
        if osp.isfile(osp.join(self.python_dir, 'Scripts', 'ipython.exe')):
            self.create_launcher('IPython Qt Console.exe', 'ipython.ico',
                             command='${WINPYDIR}\pythonw.exe',
                             args='ipython-script.py qtconsole --pylab=inline',
                             workdir='${WINPYDIR}\Scripts')
        if osp.isfile(self.winpydir + self.THG_PATH):
            self.create_launcher('TortoiseHg.exe', 'tortoisehg.ico',
                                 command=r'${WINPYDIR}\..'+self.THG_PATH,
                                 workdir=r'${WINPYDIR}')
        if osp.isfile(self.winpydir + self.WINMERGE_PATH):
            self.create_launcher('WinMerge.exe', 'winmerge.ico',
                                 command=r'${WINPYDIR}\..'+self.WINMERGE_PATH,
                                 workdir=r'${WINPYDIR}')
        self._print_done()
    
    def _create_batch_scripts(self):
        """Create batch scripts"""
        self._print("Creating batch scripts")
        self.create_batch_script('readme.txt', \
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
        self.create_batch_script('cmd.bat', r"""@echo off
call %~dp0env.bat
cmd.exe /k""")
        self.create_python_batch('python.bat', '', '')
        self.create_python_batch('spyder.bat', r'\Scripts', 'spyder')
        self.create_python_batch('spyder_light.bat', r'\Scripts', 'spyder',
                                 options='--light')
        self.create_python_batch('register_python.bat',
                                 r'\Scripts', 'register_python')
        self.create_batch_script('register_this_python.bat', r"""@echo off
call %~dp0env.bat
call %~dp0register_python.bat %WINPYDIR%""")
        self.create_batch_script('register_this_python_for_all.bat',
                                 r"""@echo off
call %~dp0env.bat
call %~dp0register_python.bat --all %WINPYDIR%""")
        self.create_python_batch('wpcp.bat', r'\Scripts', 'wpcp')
        self.create_python_batch('pyqt_demo.bat',
             r'\Lib\site-packages\PyQt4\examples\demos\qtdemo', 'qtdemo.pyw')
        self._print_done()

    def make(self, remove_existing=True):
        """Make WinPython distribution in target directory from the installers 
        located in instdir
        
        remove_existing=True: (default) install all from scratch
        remove_existing=False: only for test purpose (launchers/scripts)"""
        if self.simulation:
            print("WARNING: this is just a simulation!", file=sys.stderr)

        self.python_fname = self.get_package_fname(
                                    r'python-([0-9\.]*)(\.amd64)?\.msi')
        self.python_name = osp.basename(self.python_fname)[:-4]
        distname = 'win%s' % self.python_name
        vlst = re.match(r'winpython-([0-9\.]*)', distname
                        ).groups()[0].split('.')
        self.python_version = '.'.join(vlst[:2])
        self.python_fullversion = '.'.join(vlst[:3])

        # Create the WinPython base directory
        self._print("Creating WinPython base directory")
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
                                          verbose=self.verbose, indent=True)

        if remove_existing:
            if not self.simulation:
                self._add_vs2008_files()
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
        fname = osp.join(self.winpydir, os.pardir,
                         'WinPython-%s.txt' % self.winpyver)
        open(fname, 'w').write(self.package_index_wiki)


def rebuild_winpython(basedir=None, verbose=False):
    """Rebuild winpython package from source"""
    basedir = basedir if basedir is not None else utils.BASE_DIR
    for architecture in (32, 64):
        suffix = '.win32' if architecture == 32 else '.win-amd64'
        packdir = osp.join(basedir, 'packages' + suffix)
        for name in os.listdir(packdir):
            if name.startswith('winpython-') and name.endswith('.exe'):
                os.remove(osp.join(packdir, name))
        utils.build_wininst(osp.dirname(__file__), copy_to=packdir,
                            architecture=architecture, verbose=verbose)


def make_winpython(build_number, release_level, architecture,
                   basedir=None, verbose=False, remove_existing=True,
                   create_installer=True, simulation=False):
    """Make WinPython distribution, assuming that the following folders exist
    in *basedir* directory (if basedir is None, the WINPYTHONBASEDIR environ-
    ment variable is assumed to be basedir):
    
      * (required) `packages.win32`: contains distutils 32-bit packages
      * (required) `packages.win-amd64`: contains distutils 64-bit packages
      * (optional) `packages.src`: contains distutils source distributions
      * (required) `tools`: contains architecture-independent tools
      * (optional) `tools.win32`: contains 32-bit-specific tools
      * (optional) `tools.win-amd64`: contains 64-bit-specific tools
    
    architecture: integer (32 or 64)"""
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
                                 verbose=verbose, simulation=simulation)
    dist.make(remove_existing=remove_existing)
    if create_installer and not simulation:
        dist.create_installer()
    return dist


def make_all(build_number, release_level, basedir=None, simulation=False,
             create_installer=True, verbose=False, remove_existing=True):
    """Make WinPython for both 32 and 64bit architectures"""
    for architecture in (64, 32):
        make_winpython(build_number, release_level, architecture,
                       basedir, verbose, remove_existing, create_installer,
                       simulation)


if __name__ == '__main__':
    rebuild_winpython()
    #make_winpython(0, 'rc1', 32,
                   #remove_existing=False, create_installer=False)
    make_all(1, '', simulation=False)#, remove_existing=False, create_installer=False)
