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


def get_nsis_exe():
    """Return NSIS executable"""
    drive = __file__[:3]
    for dirname in (r'C:\Program Files', r'C:\Program Files (x86)',
                    drive+r'PortableApps\NSISPortableANSI',
                    drive+r'PortableApps\NSISPortable',
                    drive+r'PortableApps\PortableApps\NSISPortableANSI',
                    drive+r'PortableApps\PortableApps\NSISPortable',
                ):
        for subdirname in ('.', 'App'):
            exe = osp.join(dirname, subdirname, 'NSIS', 'makensis.exe')
            if osp.isfile(exe):
                return exe
    else:
        raise RuntimeError, "NSIS is not installed on this computer."

NSIS_EXE = get_nsis_exe()


def replace_in_nsis_file(fname, data):
    """Replace text in line starting with *start*, from this position:
    data is a list of (start, text) tuples"""
    fd = open(fname, 'U')
    lines = fd.readlines()
    fd.close()
    for idx, line in enumerate(lines):
        for start, text in data:
            if start not in ('Icon', 'OutFile'):
                start = '!define ' + start
            if line.startswith(start):
                lines[idx] = line[:len(start)+1] + ('"%s"' % text) + '\n'
    fd = open(fname, 'w')
    fd.writelines(lines)
    fd.close()


class WinPythonDistribution(object):
    """WinPython distribution"""
    def __init__(self, target, instdir, verbose=False):
        self.target = target
        self.instdir = instdir
        self.verbose = verbose
        self.version = None
        self.fullversion = None
        self.winpydir = None
        self.python_name = None
        self.distribution = None
        self.installed_packages = []

    @property
    def ms_arch(self):
        """Return distribution architecture, in Microsoft format: x86/x64"""
        return 'x64' if 'amd64' in self.python_name else 'x86'
        
    @property
    def py_arch(self):
        """Return distribution architecture, in Python distutils format:
        win-amd64 or win32"""
        return 'win-amd64' if 'amd64' in self.python_name else 'win32'
    
    @property
    def prepath(self):
        """Return PATH contents to be prepend to the environment variable"""
        return [r"Lib\site-packages\PyQt4"]
    
    @property
    def postpath(self):
        """Return PATH contents to be append to the environment variable"""
        return ["", "DLLs", "Scripts",
                r"..\tools", r"..\tools\gnuwin32\bin",
                r"..\tools\TortoiseHg-%s" % self.ms_arch]
        
    def get_package_fname(self, pattern):
        """Get package matching pattern in instdir"""
        for fname in os.listdir(self.instdir):
            match = re.match(pattern, fname)
            if match is not None:
                return osp.abspath(osp.join(self.instdir, fname))
        else:
            raise RuntimeError, 'Could not found required package matching %s' % pattern
    
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
    
    def create_launcher(self, name, icon,
                        command=None, args=None, workdir=None):
        """Create exe launcher with NSIS"""
        assert name.endswith('.exe')
        portable_dir = osp.join(osp.dirname(__file__), 'portable')
        icon_fname = osp.join(portable_dir, 'icons', icon)
        assert osp.isfile(icon_fname)
        fname = osp.join(self.winpydir, osp.splitext(name)[0]+'.nsi')
        shutil.copy(osp.join(portable_dir, 'launcher.nsi'), fname)
        
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
        replace_in_nsis_file(fname,
                        (('WINPYDIR', '$EXEDIR\%s' % self.python_name),
                         ('COMMAND', command),
                         ('PARAMETERS', args),
                         ('WORKDIR', workdir),
                         ('PREPATH', prepath),
                         ('POSTPATH', postpath),
                         ('Icon', icon_fname),
                         ('OutFile', name),
                        ))
        
        try:
            retcode = subprocess.call('"%s" -V2 %s' % (NSIS_EXE, fname),
                                      shell=True)
            if retcode < 0:
                print >>sys.stderr, "Child was terminated by signal", -retcode
        except OSError, e:
            print >>sys.stderr, "Execution failed:", e
        os.remove(fname)

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

    def make(self):
        """Make WinPython distribution in target directory from the installers 
        located in instdir"""
        python_fname = self.get_package_fname(
                                    r'python-([0-9\.]*)(\.amd64)?\.msi')
        self.python_name = python_name = osp.basename(python_fname)[:-4]
        distname = 'win%s' % python_name
        vlst = re.match(r'winpython-([0-9\.]*)', distname
                        ).groups()[0].split('.')
        self.version = '.'.join(vlst[:2])
        self.fullversion = '.'.join(vlst[:3])

        # Create the WinPython base directory
        self._print("Creating WinPython base directory")
        self.winpydir = osp.join(self.target, distname)
        if osp.isdir(self.winpydir):
            shutil.rmtree(self.winpydir)
        os.mkdir(self.winpydir)
        self._print_done()

        # Extracting Python installer, creating distribution object
        self._print("Extracting Python installer")
        utils.extract_msi(python_fname, targetdir=self.winpydir)
        self.installed_packages.append(python_fname)
        pydir = osp.join(self.winpydir, python_name)
        os.remove(osp.join(pydir, osp.basename(python_fname)))
        self.distribution = wppm.Distribution(pydir, verbose=self.verbose,
                                              indent=True)
        os.mkdir(osp.join(pydir, 'Scripts'))
        self._print_done()
        
        # Adding Microsoft Visual Studio 2008 DLLs and manifest
        print("Adding Microsoft Visual C++ 2008 DLLs with manifest""")
        for fname in disthelpers.get_visual_studio_dlls(
                                architecture=self.distribution.architecture,
                                python_version=self.distribution.version):
            shutil.copy(fname, pydir)

        # Installing required packages
        print("Installing required packages")
        self.install_package('pywin32-([0-9\.]*[a-z]*).%s-py%s.exe'
                             % (self.py_arch, self.version))
        self.install_package('winpython-([0-9\.]*[a-z]*).%s(-py%s)?.exe'
                             % (self.py_arch, self.version))
        self.install_package('spyder(lib)?-([0-9\.]*[a-z]*).%s(-py%s)?.exe'
                             % (self.py_arch, self.version))
        self.install_package(pattern='PyQt-Py%s-%s-gpl-([0-9\.\-]*).exe'
                                     % (self.version, self.ms_arch))
        self.install_package(
                    pattern='PyQwt-([0-9\.]*)-py%s-%s-([a-z0-9\.\-]*).exe'
                            % (self.version, self.ms_arch))
        
        # Try to install all other packages in instdir
        print("Installing other packages")
        for fname in os.listdir(self.instdir):
            try:
                self.install_package(fname)
            except NotImplementedError:
                pass
        
        # Copy dev tools
        self._print("Copying tools")
        shutil.copytree(osp.join(osp.dirname(__file__), 'tools'),
                        osp.join(self.winpydir, 'tools'))
        self._print_done()
        
        #XXX: the USERPROFILE environment variable redirection do not work 
        # with TortoiseHg (and maybe other programs)... but, why?
        ## Creating settings directory
        #os.mkdir(osp.join(self.winpydir, 'settings'))

        # Create launchers
        self._print("Creating launchers")
        self.create_launcher('cmd.exe', 'cmd.ico', command='$SYSDIR\cmd.exe',
                             args='/k', workdir='${WINPYDIR}')
        self.create_launcher('python.exe', 'python.ico')
        self.create_launcher('Spyder.exe', 'spyder.ico',
                             args='spyder',
                             workdir='${WINPYDIR}\Scripts')
        self.create_launcher('Spyder_Light.exe', 'spyder_light.ico',
                             args='spyder --light',
                             workdir='${WINPYDIR}\Scripts')
        self.create_launcher('WPPM.exe', 'winpython.ico',
                             args='wppmgui',
                             workdir='${WINPYDIR}\Scripts')
        self.create_launcher('PyQtdemo.exe', 'qt.ico', args='qtdemo.pyw',
           workdir='${WINPYDIR}\Lib\site-packages\PyQt4\examples\demos\qtdemo')
        thg = r'\tools\TortoiseHg-%s\thg.exe' % self.ms_arch
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

        # Create batch scripts
        print("Creating batch scripts")
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
set WINPYDIR=%~dp0..\\""" + python_name + r"""
set PATH=""" + path)
        #self.create_batch_script('env.bat', """@echo off
#set WINPYDIR=%~dp0..\\""" + python_name + r"""
#set USERPROFILE=%WINPYDIR%\..\settings
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

        self._print("Cleaning up distribution")
        self.distribution.clean_up()
        self._print_done()
        
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
    

if __name__ == '__main__':
    sbdir = osp.join(osp.dirname(__file__), os.pardir, 'sandbox')
    sbdir = r'D:\Pierre'
    wpdir = osp.join(sbdir, 'maketest')
    instdir = osp.join(sbdir, 'installers')
    if not osp.isdir(wpdir):
        os.mkdir(wpdir)
    dist = WinPythonDistribution(wpdir, instdir, verbose=False)
    dist.make()
