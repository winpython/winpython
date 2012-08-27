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
# The batch to exe conversion is abandoned due to false virus detection issues
#==============================================================================
def bat_to_exe(fname, icon):
    """Convert .bat file to .exe using Bat_To_Exe_Converter (www.f2ko.de)"""
    conv = 'Bat_To_Exe_Converter.exe'
    assert fname.endswith('.bat')
    assert icon.endswith('.ico')
    #assert utils.is_program_installed(conv)
    bname = osp.basename(fname)
    args = ['-bat', bname, '-save', bname.replace('.bat', '.exe')]#,
#            '-icon', osp.abspath(icon)]
    print(args)
    subprocess.call([conv]+args, cwd=osp.dirname(fname))

def call_bat_from_exe(batname, targetname, icon):
    """Call .bat file from a generated .exe file
    Executable file is created in .bat file parent directory"""
    assert batname.endswith('.bat')
    assert targetname.endswith('.exe')
    assert icon.endswith('.ico') and osp.isfile(icon)
    exedir = osp.join(osp.dirname(batname), os.pardir)
    exename = osp.join(exedir, targetname)
    tmpbatname = exename.replace('.exe', '-tmp.bat')
    tmpbat = file(tmpbatname, 'w')
    tmpbat.write("""@echo off
call %s""" % osp.relpath(batname, exedir))
    tmpbat.close()
    bat_to_exe(tmpbatname, icon)

def bat_to_exe_test():
    wpdir = osp.join(osp.dirname(__file__), os.pardir, 'sandbox',
                     'winpython-2.7.3.amd64')
    call_bat_from_exe(osp.join(wpdir, 'scripts', 'spyder.bat'), 'Spyder.exe',
                      osp.join(wpdir, 'python-2.7.3.amd64',
                               'Scripts', 'spyder.ico'))


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


class WinPythonDistribution(object):
    """WinPython distribution"""
    def __init__(self, target, instdir, srcdir=None, toolsdirs=None,
                 verbose=False):
        self.target = target
        self.instdir = instdir
        self.srcdir = srcdir
        if toolsdirs is None:
            toolsdirs = []
        self.toolsdirs = toolsdirs
        self.verbose = verbose
        self.version = None
        self.fullversion = None
        self.winpydir = None
        self.python_fname = None
        self.python_name = None
        self.distribution = None
        self.installed_packages = []

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
        path = [r"Lib\site-packages\PyQt4"]
        if self.distribution.architecture == 32:
            path += [r"..\tools\mingw32\bin"]
        return path
    
    @property
    def postpath(self):
        """Return PATH contents to be append to the environment variable"""
        return ["", "DLLs", "Scripts",
                r"..\tools", r"..\tools\gnuwin32\bin", r"..\tools\TortoiseHg"]
        
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
        bname = osp.basename(fname)
        if bname not in self.installed_packages:
            pack = wppm.Package(fname)
            self.distribution.install(pack)
            self.installed_packages.append(bname)

    def create_batch_script(self, name, contents):
        """Create batch script %WINPYDIR%/name"""
        scriptdir = osp.join(self.winpydir, 'scripts')
        if not osp.isdir(scriptdir):
            os.mkdir(scriptdir)
        fd = file(osp.join(scriptdir, name), 'w')
        fd.write(contents)
        fd.close()
    
    def build_nsis(self, srcname, dstname, data):
        """Build NSIS script"""
        portable_dir = osp.join(osp.dirname(__file__), 'portable')
        shutil.copy(osp.join(portable_dir, srcname), dstname)
        data = [('!addincludedir', osp.join(portable_dir, 'include'))
                ] + list(data)
        replace_in_nsis_file(dstname, data)
        try:
            retcode = subprocess.call('"%s" -V2 %s' % (NSIS_EXE, dstname),
                                      shell=True, stdout=sys.stderr)
            if retcode < 0:
                print >>sys.stderr, "Child was terminated by signal", -retcode
        except OSError, e:
            print >>sys.stderr, "Execution failed:", e
        os.remove(dstname)
    
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

        self.build_nsis('launcher.nsi', fname, data)

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

    def create_installer(self, build_number, release_level):
        """Create installer with NSIS"""
        assert isinstance(build_number, int)
        assert isinstance(release_level, str)
        self._print("Creating WinPython installer")
        portable_dir = osp.join(osp.dirname(__file__), 'portable')
        fname = osp.join(portable_dir, 'installer-tmp.nsi')
        data = (('DISTDIR', self.winpydir),
                ('ARCH', self.winpy_arch),
                ('VERSION', '%s.%d' % (self.fullversion, build_number)),
                ('RELEASELEVEL', release_level),)
        self.build_nsis('installer.nsi', fname, data)
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
        self.installed_packages.append(self.python_name)
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
                             % (self.py_arch, self.version))
        self.install_package('winpython-([0-9\.]*[a-z]*).%s(-py%s)?.exe'
                             % (self.py_arch, self.version))
        self.install_package('spyder(lib)?-([0-9\.]*[a-z]*).%s(-py%s)?.exe'
                             % (self.py_arch, self.version))
        self.install_package(pattern='PyQt-Py%s-%s-gpl-([0-9\.\-]*).exe'
                                     % (self.version, self.pyqt_arch))
        self.install_package(
                    pattern='PyQwt-([0-9\.]*)-py%s-%s-([a-z0-9\.\-]*).exe'
                            % (self.version, self.pyqt_arch))
    
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
        for dirname in [osp.join(osp.dirname(__file__), 'tools')
                        ] + self.toolsdirs:
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
        self.create_launcher('cmd.exe', 'cmd.ico', command='$SYSDIR\cmd.exe',
                             args='/k', workdir='${WINPYDIR}')
        self.create_launcher('python.exe', 'python.ico')
        settingspath = osp.join('.spyder2', '.spyder.ini')
        self.create_launcher('Spyder.exe', 'spyder.ico',
                             args='spyder', workdir='${WINPYDIR}\Scripts',
                             settingspath=settingspath)
        self.create_launcher('Spyder_Light.exe', 'spyder_light.ico',
                             args='spyder --light',
                             workdir='${WINPYDIR}\Scripts',
                             settingspath=settingspath)
        self.create_launcher('WPPM.exe', 'winpython.ico',
                             args='wppmgui',
                             workdir='${WINPYDIR}\Scripts')
        self.create_launcher('QtDemo.exe', 'qt.ico', args='qtdemo.pyw',
           workdir=r'${WINPYDIR}\Lib\site-packages\PyQt4\examples\demos\qtdemo')
        self.create_launcher('QtAssistant.exe', 'qtassistant.ico',
                   command=r'${WINPYDIR}\Lib\site-packages\PyQt4\assistant.exe',
                   workdir=r'${WINPYDIR}')
        self.create_launcher('QtDesigner.exe', 'qtdesigner.ico',
                   command=r'${WINPYDIR}\Lib\site-packages\PyQt4\designer.exe',
                   workdir=r'${WINPYDIR}')
        self.create_launcher('QtLinguist.exe', 'qtlinguist.ico',
                   command=r'${WINPYDIR}\Lib\site-packages\PyQt4\linguist.exe',
                   workdir=r'${WINPYDIR}')
        if osp.isfile(osp.join(self.python_dir, 'Scripts', 'ipython.exe')):
            self.create_launcher('IPython.exe', 'ipython.ico',
                             command='${WINPYDIR}\pythonw.exe',
                             args='ipython-script.py qtconsole --pylab=inline',
                             workdir='${WINPYDIR}\Scripts')
        thg = r'\tools\TortoiseHg\thgw.exe'
        if osp.isfile(self.winpydir + thg):
            self.create_launcher('TortoiseHg.exe', 'tortoisehg.ico',
                                 command=r'${WINPYDIR}\..' + thg,
                                 workdir=r'${WINPYDIR}')
        winmerge = r'\tools\WinMerge\WinMerge.exe'
        if osp.isfile(self.winpydir + winmerge):
            self.create_launcher('WinMerge.exe', 'winmerge.ico',
                                 command=r'${WINPYDIR}\..' + winmerge,
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
set HOME=%WINPYDIR%\..\settings
set PATH=""" + path)
        #self.create_batch_script('env.bat', """@echo off
#set WINPYDIR=%~dp0..\\""" + self.python_name + r"""
#set HOME=%WINPYDIR%\..\settings
#set PATH=""" + path)
        self.create_batch_script('cmd.bat', r"""@echo off
call %~dp0env.bat
cmd.exe /k""")
        self.create_python_batch('python.bat', '', '')
        self.create_python_batch('spyder.bat', r'\Scripts', 'spyder')
        self.create_python_batch('spyder_light.bat', r'\Scripts', 'spyder',
                                 options='--light')
        self.create_python_batch('wppm.bat', r'\Scripts', 'wppmgui.pyw')
        self.create_python_batch('pyqt_demo.bat',
             r'\Lib\site-packages\PyQt4\examples\demos\qtdemo', 'qtdemo.pyw')
        self._print_done()

    def make(self, remove_existing=True):
        """Make WinPython distribution in target directory from the installers 
        located in instdir
        
        remove_existing=True: (default) install all from scratch
        remove_existing=False: only for test purpose (launchers/scripts)"""
        self.python_fname = self.get_package_fname(
                                    r'python-([0-9\.]*)(\.amd64)?\.msi')
        self.python_name = osp.basename(self.python_fname)[:-4]
        distname = 'win%s' % self.python_name
        vlst = re.match(r'winpython-([0-9\.]*)', distname
                        ).groups()[0].split('.')
        self.version = '.'.join(vlst[:2])
        self.fullversion = '.'.join(vlst[:3])

        # Create the WinPython base directory
        self._print("Creating WinPython base directory")
        self.winpydir = osp.join(self.target, distname)
        if osp.isdir(self.winpydir) and remove_existing:
            shutil.rmtree(self.winpydir)
        if not osp.isdir(self.winpydir):
            os.mkdir(self.winpydir)
        if remove_existing:
            # Create settings directory
            # (only necessary if user is starting an application with a batch 
            #  scripts before using an executable launcher, because the latter 
            #  is creating the directory automatically)
            os.mkdir(osp.join(self.winpydir, 'settings'))
        self._print_done()

        if remove_existing:
            self._extract_python()
        self.distribution = wppm.Distribution(self.python_dir,
                                          verbose=self.verbose, indent=True)

        if remove_existing:
            self._add_vs2008_files()
            self._install_required_packages()
            self._install_all_other_packages()
            self._copy_dev_tools()
        self._create_launchers()
        self._create_batch_scripts()
        
        if remove_existing:
            self._print("Cleaning up distribution")
            self.distribution.clean_up()
            self._print_done()
            

def make_winpython(architecture, basedir=None,
                   verbose=False, remove_existing=True):
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
    dist = WinPythonDistribution(builddir, packdir, srcdir, toolsdirs,
                                 verbose=verbose)
    dist.make(remove_existing=remove_existing)
    return dist


def make_all(build_number, release_level, basedir=None,
             create_installer=True, verbose=False, remove_existing=True):
    """Make WinPython for both 32 and 64bit architectures"""
    for architecture in (32, 64):
        dist = make_winpython(architecture, basedir, verbose, remove_existing)
        if create_installer:
            dist.create_installer(build_number, release_level)


if __name__ == '__main__':
    #dist = make_winpython(32, remove_existing=True)
#    dist.create_installer(0, 'beta4')
    make_all(0, 'beta4', create_installer=True)
