# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
WinPython Package Manager

Created on Fri Aug 03 14:32:26 2012
"""

from __future__ import print_function

import os
import os.path as osp
import shutil
import cPickle
import re
import sys
import atexit

# Local imports
from winpython import utils

# Workaround for installing PyVISA on Windows from source:
os.environ['HOME'] = os.environ['USERPROFILE']


class Package(object):
    def __init__(self, fname):
        self.fname = fname

        self.files = []
        self.folders = []
        
        # Package informations extracted from installer filename
        self.name = None
        self.version = None
        self.architecture = None
        self.pyversion = None
        self.extract_infos()
    
    def is_compatible_with(self, distribution):
        """Return True if package is compatible with distribution in terms of
        architecture and Python version (if applyable)"""
        iscomp = True
        if self.architecture is not None:
            # Source distributions (not yet supported though)
            iscomp = iscomp and self.architecture == distribution.architecture
        if self.pyversion is not None:
            # Non-pure Python package
            iscomp = iscomp and self.pyversion == distribution.version
        return iscomp

    def extract_infos(self):
        """Extract package infos (name, version, architecture)
        from filename (installer basename)"""
        bname = osp.basename(self.fname)
        if bname.endswith('.exe'):
            # distutils bdist_wininst
            match = re.match(utils.WININST_PATTERN, bname)
            if match is not None:
                self.name, self.version, arch, _t1, self.pyversion, _t2 = match.groups()
                self.architecture = 32 if arch == 'win32' else 64
                return
            # NSIS
            pat = r'([a-zA-Z0-9\-\_]*)-Py([0-9\.]*)-x(64|32)-gpl-([0-9\.\-]*[a-z]*)\.exe'
            match = re.match(pat, bname)
            if match is not None:
                self.name, self.pyversion, arch, self.version = match.groups()
                self.architecture = int(arch)
                return
            match = re.match(r'([a-zA-Z0-9\-\_]*)-([0-9\.]*[a-z]*)-py([0-9\.]*)-x(64|32)-([a-z0-9\.\-]*).exe', bname)
            if match is not None:
                self.name, self.version, self.pyversion, arch, _pyqt = match.groups()
                self.architecture = int(arch)
                return
        elif bname.endswith(('.zip', '.tar.gz')):
            # distutils sdist
            infos = utils.get_source_package_infos(bname)
            if infos is not None:
                self.name, self.version = infos
                return
        raise NotImplementedError, "Not supported package type %s" % bname

    def logpath(self, logdir):
        """Return full log path"""
        return osp.join(logdir, osp.basename(self.fname+'.log'))
    
    def save_log(self, logdir):
        """Save log (pickle)"""
        log = [self.files, self.folders]
        try:
            cPickle.dump(log, file(self.logpath(logdir), 'w'))
        except (IOError, OSError):
            raise

    def load_log(self, logdir):
        """Load log (pickle)"""
        try:
            log = cPickle.loads(file(self.logpath(logdir), 'U').read())
        except (IOError, OSError):
            raise
        self.files, self.folders = log
    
    def remove_log(self, logdir):
        """Remove log (after uninstalling package)"""
        try:
            os.remove(self.logpath(logdir))
        except WindowsError:
            pass
        

class Distribution(object):
    NSIS_PACKAGES = ('PyQt', 'PyQwt')  # known NSIS packages
    def __init__(self, target, verbose=False, indent=False):
        self.target = target
        self.verbose = verbose
        self.indent = indent
        self.logdir = None
        self.init_log_dir()
        self.to_be_removed = []  # list of directories to be removed later
        self.version, self.architecture = utils.get_python_infos(target)
    
    def clean_up(self):
        """Remove directories which couldn't be removed when building"""
        for path in self.to_be_removed:
            try:
                shutil.rmtree(path)
            except WindowsError:
                print >>sys.stderr, "Directory %s could not be removed" % path
        
    def remove_directory(self, path):
        """Try to remove directory -- on WindowsError, remove it later"""
        try:
            shutil.rmtree(path)
        except WindowsError:
            self.to_be_removed.append(path)

    def init_log_dir(self):
        """Init log path"""
        path = osp.join(self.target, 'Logs')
        if not osp.exists(path):
            os.mkdir(path)
        self.logdir = path
    
    def copy_files(self, package, targetdir,
                   srcdir, dstdir, create_bat_files=False):
        """Add copy task"""
        srcdir = osp.join(targetdir, srcdir)
        if not osp.isdir(srcdir):
            return
        offset = len(srcdir)+len(os.pathsep)
        for dirpath, dirnames, filenames in os.walk(srcdir):
            for dname in dirnames:
                t_dname = osp.join(dirpath, dname)[offset:]
                src = osp.join(srcdir, t_dname)
                dst = osp.join(dstdir, t_dname)
                if self.verbose:
                    print("mkdir: %s" % dst)
                full_dst = osp.join(self.target, dst)
                if not osp.exists(full_dst):
                    os.mkdir(full_dst)
                package.folders.append(dst)
            for fname in filenames:
                t_fname = osp.join(dirpath, fname)[offset:]
                src = osp.join(srcdir, t_fname)
                if dirpath.endswith('_system32'):
                    # Files that should be copied in %WINDIR%\system32
                    dst = fname
                else:
                    dst = osp.join(dstdir, t_fname)
                if self.verbose:
                    print("file:  %s" % dst)
                full_dst = osp.join(self.target, dst)
                shutil.move(src, full_dst)
                package.files.append(dst)
                name, ext = osp.splitext(dst)
                if create_bat_files and ext in ('', '.py'):
                    dst = name + '.bat'
                    if self.verbose:
                        print("file:  %s" % dst)
                    full_dst = osp.join(self.target, dst)
                    fd = file(full_dst, 'w')
                    fd.write("""@echo off
python "%~dpn0""" + ext + """" %*""")
                    fd.close()
                    package.files.append(dst)

    def create_file(self, package, name, dstdir, contents):
        """Generate data file -- path is relative to distribution root dir"""
        dst = osp.join(dstdir, name)
        if self.verbose:
            print("create:  %s" % dst)
        full_dst = osp.join(self.target, dst)
        file(full_dst, 'w').write(contents)
        package.files.append(dst)

    def get_installed_packages(self):
        """Return installed packages"""
        return [Package(logname[:-4]) for logname in os.listdir(self.logdir)]
    
    def find_package(self, name):
        """Find installed package"""
        for pack in self.get_installed_packages():
            if pack.name == name:
                return pack

    def uninstall_existing(self, package):
        """Uninstall existing package"""
        pack = self.find_package(package.name)
        if pack is not None:
            self.uninstall(pack)
    
    def install(self, package):
        """Install package in distribution"""
        assert package.is_compatible_with(self)
        tmp_fname = None
        self.uninstall_existing(package)
        if package.fname.endswith(('.tar.gz', '.zip')):
            self._print(package, "Building")
            try:
                fname = utils.source_to_wininst(package.fname,
                          architecture=self.architecture, verbose=self.verbose)
            except RuntimeError:
                if not self.verbose:
                    print("Failed!")
                raise
            tmp_fname = fname
            package = Package(fname)
            self._print_done()
        bname = osp.basename(package.fname)
        if bname.endswith('.exe'):
            if re.match(r'(' + ('|'.join(self.NSIS_PACKAGES)) + r')-', bname):
                self.install_nsis_package(package)
            else:
                self.install_bdist_wininst(package)
        elif bname.endswith('.msi'):
            self.install_bdist_msi(package)
        self.handle_specific_packages(package)
        package.save_log(self.logdir)
        if tmp_fname is not None:
            os.remove(tmp_fname)

    def handle_specific_packages(self, package):
        """Packages requiring additional configuration"""
        if package.name in ('PyQt', 'PyQt4'):
            name = 'qt.conf'
            contents = """[Paths]
Prefix = .
Binaries = ."""
            self.create_file(package, name,
                         osp.join('Lib', 'site-packages', 'PyQt4'),  contents)
            self.create_file(package, name, '.',
                         contents.replace('.', './Lib/site-packages/PyQt4'))
    
    def _print(self, package, action):
        """Print package-related action text (e.g. 'Installing') 
        indicating progress"""
        text = " ".join([action, package.name, package.version])
        if self.verbose:
            utils.print_box(text)
        else:
            if self.indent:
                text = (' '*4) + text
            print(text + '...', end=" ")
    
    def _print_done(self):
        """Print OK at the end of a process"""
        if not self.verbose:
            print("OK")
    
    def uninstall(self, package):
        """Uninstall package from distribution"""
        self._print(package, "Uninstalling")
        package.load_log(self.logdir)
        for fname in reversed(package.files):
            if self.verbose:
                print("remove: %s" % fname)
            path = osp.join(self.target, fname)
            if osp.exists(path):
                os.remove(path)
            if fname.endswith('.py'):
                for suffix in ('c', 'o'):
                    if osp.exists(path+suffix):
                        os.remove(path+suffix)
        for dname in reversed(package.folders):
            try:
                if self.verbose:
                    print("rmdir:  %s" % fname)
                path = osp.join(self.target, dname)
                if osp.exists(path):
                    os.rmdir(path)
            except OSError:
                pass
        package.remove_log(self.logdir)
        self._print_done()
    
    def install_bdist_wininst(self, package):
        """Install a distutils package built with the bdist_wininst option
        (binary distribution, .exe file)"""
        self._print(package, "Extracting")
        targetdir = utils.extract_exe(package.fname, targetdir=self.target)
        self._print_done()
        
        self._print(package, "Installing")
        self.copy_files(package, targetdir, 'PURELIB',
                        osp.join('Lib', 'site-packages'))
        self.copy_files(package, targetdir, 'PLATLIB',
                        osp.join('Lib', 'site-packages'))
        self.copy_files(package, targetdir, 'SCRIPTS', 'Scripts',
                        create_bat_files=True)
        self.copy_files(package, targetdir, 'DLLs', 'DLLs')
        self.copy_files(package, targetdir, 'DATA', '.')
        self.remove_directory(targetdir)
        self._print_done()

    def install_bdist_msi(self, package):
        """Install a distutils package built with the bdist_msi option
        (binary distribution, .msi file)"""
        raise NotImplementedError
        self._print(package, "Extracting")
        targetdir = utils.extract_msi(package.fname, targetdir=self.target)
        self._print_done()
        self.remove_directory(targetdir)

    def install_nsis_package(self, package):
        """Install a Python package built with NSIS (e.g. PyQt or PyQwt)
        (binary distribution, .exe file)"""
        bname = osp.basename(package.fname)
        assert bname.startswith(self.NSIS_PACKAGES)
        self._print(package, "Extracting")
        targetdir = utils.extract_exe(package.fname, targetdir=self.target)
        self._print_done()

        self._print(package, "Installing")
        self.copy_files(package, targetdir, 'Lib', 'Lib')
        if bname.startswith('PyQt'):
            # PyQt4
            outdir = osp.join('Lib', 'site-packages', 'PyQt4')
        else:
            # Qwt5
            outdir = osp.join('Lib', 'site-packages', 'PyQt4', 'Qwt5')
        self.copy_files(package, targetdir, '$_OUTDIR', outdir)
        self.remove_directory(targetdir)
        self._print_done()


if __name__ == '__main__':
    sbdir = osp.join(osp.dirname(__file__),
                     os.pardir, os.pardir, os.pardir, 'sandbox')
    tmpdir = osp.join(sbdir, 'tobedeleted')
    
    #for fname in os.listdir(sbdir):
        #try:
            #ins = Installation(fname)
            #print fname, '--->', ins.name, ins.version, ins.architecture
        #except NotImplementedError:
            #pass
    
    #fname = osp.join(tmpdir, 'scipy-0.10.1.win-amd64-py2.7.exe')
    fname = osp.join(sbdir, 'Cython-0.16.win-amd64-py2.7.exe')
    #fname = osp.join(sbdir, 'pylzma-0.4.4dev.win-amd64-py2.7.exe')
    #fname = osp.join(sbdir, 'cx_Freeze-4.3.win-amd64-py2.6.exe')
    #fname = osp.join(sbdir, 'PyQtdoc-4.7.2.win-amd64.exe')
    #fname = osp.join(sbdir, 'winpython-0.1dev.win-amd64.exe')
    target =osp.join(sbdir, 'winpython-2.7.3.amd64', 'python-2.7.3.amd64')
    
    target = r'D:\Pierre\build\winpython-2.7.3\python-2.7.3'
    sbdir = r'D:\Pierre\_test'
    fname = osp.join(sbdir, 'xlrd-0.8.0.tar.gz')

    dist = Distribution(target, verbose=False)
    pack = Package(fname)
    dist.install(pack)
    #dist.uninstall(pack)
