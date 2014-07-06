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
import re
import sys
import subprocess

# Local imports
from winpython import utils
from winpython.config import DATA_PATH
from winpython.py3compat import configparser as cp

# Workaround for installing PyVISA on Windows from source:
os.environ['HOME'] = os.environ['USERPROFILE']


def get_package_metadata(database, name):
    """Extract infos (description, url) from the local database"""
    # Note: we could use the PyPI database but this has been written on 
    # machine which is not connected to the internet
    db = cp.ConfigParser()
    db.readfp(open(osp.join(DATA_PATH, database)))
    metadata = dict(description='', url='http://pypi.python.org/pypi/' + name)
    for key in metadata:
        name1 = name.lower()
        for name2 in (name1, name1.split('-')[0]):
            try:
                metadata[key] = db.get(name2, key)
                break
            except (cp.NoSectionError, cp.NoOptionError):
                pass
    return metadata


class BasePackage(object):
    def __init__(self, fname):
        self.fname = fname
        self.name = None
        self.version = None
        self.architecture = None
        self.pyversion = None
        self.description = None
        self.url = None

    def __str__(self):
        text = "%s %s" % (self.name, self.version)
        pytext = ""
        if self.pyversion is not None:
            pytext = " for Python %s" % self.pyversion
        if self.architecture is not None:
            if not pytext:
                pytext = " for Python"
            pytext += " %dbits" % self.architecture
        text += "%s\n%s\nWebsite: %s\n[%s]" % (pytext, self.description,
                                            self.url, osp.basename(self.fname))
        return text
    
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

    def extract_optional_infos(self):
        """Extract package optional infos (description, url)
        from the package database"""
        metadata = get_package_metadata('packages.ini', self.name)
        for key, value in list(metadata.items()):
            setattr(self, key, value)

class Package(BasePackage):
    def __init__(self, fname):
        BasePackage.__init__(self, fname)
        self.files = []
        
        self.extract_infos()
        self.extract_optional_infos()

    def extract_infos(self):
        """Extract package infos (name, version, architecture)
        from filename (installer basename)"""
        bname = osp.basename(self.fname)
        if bname.endswith('.exe'):
            # distutils bdist_wininst
            match = re.match(utils.WININST_PATTERN, bname)
            if match is not None:
                (self.name, self.version,
                 _t0, _qtver, arch, _t1, self.pyversion, _t2) = match.groups()
                self.architecture = 32 if arch == 'win32' else 64
                return
            # NSIS
            pat = r'([a-zA-Z0-9\-\_]*)-Py([0-9\.]*)-x(64|32)-gpl-([0-9\.\-]*[a-z]*)\.exe'
            match = re.match(pat, bname)
            if match is not None:
                self.name, self.pyversion, arch, self.version = match.groups()
                self.architecture = int(arch)
                return
            # NSIS complement to match PyQt4-4.10.4-gpl-Py3.4-Qt4.8.6-x32.exe   
            pat = r'([a-zA-Z0-9\_]*)-([0-9\.]*[a-z]*)-gpl-Py([0-9\.]*)-.*-x(64|32)\.exe'
            match = re.match(pat, bname)
            if match is not None:
                self.name, self.version, self.pyversion, arch  = match.groups()
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
        raise NotImplementedError("Not supported package type %s" % bname)

    def logpath(self, logdir):
        """Return full log path"""
        return osp.join(logdir, osp.basename(self.fname+'.log'))
    
    def save_log(self, logdir):
        """Save log (pickle)"""
        header = ['# WPPM package installation log',
                  '# ',
                  '# Package: %s v%s' % (self.name, self.version),
                  '']
        open(self.logpath(logdir), 'w').write('\n'.join(header + self.files))

    def load_log(self, logdir):
        """Load log (pickle)"""
        try:
            data = open(self.logpath(logdir), 'U').readlines()
        except (IOError, OSError):
            raise
        self.files = []
        for line in data:
            relpath = line.strip()
            if relpath.startswith('#') or len(relpath) == 0:
                continue
            self.files.append(relpath)
    
    def remove_log(self, logdir):
        """Remove log (after uninstalling package)"""
        try:
            os.remove(self.logpath(logdir))
        except WindowsError:
            pass


class WininstPackage(BasePackage):
    def __init__(self, fname, distribution):
        BasePackage.__init__(self, fname)
        self.logname = None
        self.distribution = distribution
        self.architecture = distribution.architecture
        self.pyversion = distribution.version
        self.extract_infos()
        self.extract_optional_infos()

    def extract_infos(self):
        """Extract package infos (name, version, architecture)"""
        match = re.match(r'Remove([a-zA-Z0-9\-\_\.]*)\.exe', self.fname)
        if match is None:
            return
        self.name = match.groups()[0]
        self.logname = '%s-wininst.log' % self.name
        fd = open(osp.join(self.distribution.target, self.logname), 'U')
        searchtxt = 'DisplayName='
        for line in fd.readlines():
            pos = line.find(searchtxt)
            if pos != -1:
                break
        else:
            return
        fd.close()
        match = re.match(r'Python %s %s-([0-9\.]*)'
                         % (self.pyversion, self.name),
                         line[pos+len(searchtxt):])
        if match is None:
            return
        self.version = match.groups()[0]
    
    def uninstall(self):
        """Uninstall package"""
        subprocess.call([self.fname, '-u', self.logname],
                        cwd=self.distribution.target)


class Distribution(object):
    # PyQt module is now like :PyQt4-... 
    NSIS_PACKAGES = ('PyQt4', 'PyQwt')  # known NSIS packages 
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
                shutil.rmtree(path, onerror=utils.onerror)
            except WindowsError:
                print("Directory %s could not be removed" % path,
                      file=sys.stderr)
        
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
                package.files.append(dst)
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
                    fd = open(full_dst, 'w')
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
        open(full_dst, 'w').write(contents)
        package.files.append(dst)

    def get_installed_packages(self):
        """Return installed packages"""
        # Packages installed with WPPM
        wppm = [Package(logname[:-4]) for logname in os.listdir(self.logdir)]
        # Packages installed with distutils wininst
        wininst = []
        for name in os.listdir(self.target):
            if name.startswith('Remove') and name.endswith('.exe'):
                try:
                    pack = WininstPackage(name, self)
                except IOError:
                    continue
                if pack.name is not None and pack.version is not None:
                    wininst.append(pack)
        return wppm + wininst
    
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
                          python_exe=osp.join(self.target, 'python.exe'),
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
            # Qt configuration file (where to find Qt)
            name = 'qt.conf'
            contents = """[Paths]
Prefix = .
Binaries = ."""
            self.create_file(package, name,
                         osp.join('Lib', 'site-packages', 'PyQt4'),  contents)
            self.create_file(package, name, '.',
                         contents.replace('.', './Lib/site-packages/PyQt4'))
            # pyuic script
            self.create_file(package, 'pyuic4.bat', 'Scripts', r'''@echo off
python "%WINPYDIR%\Lib\site-packages\PyQt4\uic\pyuic.py" %1 %2 %3 %4 %5 %6 %7 %8 %9''')
            # Adding missing __init__.py files (fixes Issue 8)
            uic_path = osp.join('Lib', 'site-packages', 'PyQt4', 'uic')
            for dirname in ('Loader', 'port_v2', 'port_v3'):
                self.create_file(package, '__init__.py',
                                 osp.join(uic_path, dirname), '')
    
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
        if isinstance(package, WininstPackage):
            package.uninstall()
        else:
            package.load_log(self.logdir)
            for fname in reversed(package.files):
                path = osp.join(self.target, fname)
                if osp.isfile(path):
                    if self.verbose:
                        print("remove: %s" % fname)
                    os.remove(path)
                    if fname.endswith('.py'):
                        for suffix in ('c', 'o'):
                            if osp.exists(path+suffix):
                                if self.verbose:
                                    print("remove: %s" % (fname+suffix))
                                os.remove(path+suffix)
                elif osp.isdir(path):
                    if self.verbose:
                        print("rmdir:  %s" % fname)
                    pycache = osp.join(path, '__pycache__')
                    if osp.exists(pycache):
                        try:
                            shutil.rmtree(pycache, onerror=utils.onerror)
                            if self.verbose:
                                print("rmtree: %s" % pycache)
                        except WindowsError:
                            print("Directory %s could not be removed"\
                                  % pycache, file=sys.stderr)
                    try:
                        os.rmdir(path)
                    except OSError:
                        if self.verbose:
                            print("unable to remove directory: %s" % fname,
                                  file=sys.stderr)
                else:
                    if self.verbose:
                        print("file not found: %s" % fname, file=sys.stderr)
            package.remove_log(self.logdir)
        self._print_done()
    
    def install_bdist_wininst(self, package):
        """Install a distutils package built with the bdist_wininst option
        (binary distribution, .exe file)"""
        self._print(package, "Extracting")
        targetdir = utils.extract_archive(package.fname)
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
        self._print_done()

    def install_bdist_msi(self, package):
        """Install a distutils package built with the bdist_msi option
        (binary distribution, .msi file)"""
        raise NotImplementedError
        #self._print(package, "Extracting")
        #targetdir = utils.extract_msi(package.fname, targetdir=self.target)
        #self._print_done()

    def install_nsis_package(self, package):
        """Install a Python package built with NSIS (e.g. PyQt or PyQwt)
        (binary distribution, .exe file)"""
        bname = osp.basename(package.fname)
        assert bname.startswith(self.NSIS_PACKAGES)
        self._print(package, "Extracting")
        targetdir = utils.extract_exe(package.fname)
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
    fname = osp.join(sbdir, 'VTK-5.10.0-Qt-4.7.4.win32-py2.7.exe')
    fname = osp.join(sbdir, 'scikits.timeseries-0.91.3.win32-py2.7.exe')
    print(Package(fname))
    sys.exit()
    #fname = osp.join(sbdir, 'pylzma-0.4.4dev.win-amd64-py2.7.exe')
    #fname = osp.join(sbdir, 'cx_Freeze-4.3.win-amd64-py2.6.exe')
    #fname = osp.join(sbdir, 'PyQtdoc-4.7.2.win-amd64.exe')
    #fname = osp.join(sbdir, 'winpython-0.1dev.win-amd64.exe')
    target =osp.join(sbdir, 'winpython-2.7.3.amd64', 'python-2.7.3.amd64')
    
    target = osp.join(utils.BASE_DIR, 'build',
                      'winpython-2.7.3', 'python-2.7.3')
    #fname = osp.join(utils.BASE_DIR, 'packages.src', 'docutils-0.9.1.tar.gz')
    fname = osp.join(utils.BASE_DIR, 'packages.win32',
                     'PyQt-Py2.7-x32-gpl-4.8.6-1.exe')
    fname = osp.join(utils.BASE_DIR, 'packages.win32',
                     'scikits-image-0.6.1.win32-py2.7.exe')

    dist = Distribution(target, verbose=True)
    pack = Package(fname)
    print(pack.description)
    #dist.install(pack)
    #dist.uninstall(pack)
