# -*- coding: utf-8 -*-
"""
WinPython Package Manager

Created on Fri Aug 03 14:32:26 2012
"""

import os
import os.path as osp
import subprocess
import shutil
import cPickle
import re
import sys

# Local imports
from winpython import utils

#==============================================================================
# Extract functions
#==============================================================================
def extract_msi(fname, targetdir=None):
    '''Extract .msi installer to the directory of the same name    
    msiexec.exe /a "python-%PYVER%%PYARC%.msi" /qn TARGETDIR="%PYDIR%"'''
    extract = 'msiexec.exe'
    assert utils.is_program_installed(extract)
    bname = osp.basename(fname)
    args = ['/a', '%s' % bname, '/qn', 'TARGETDIR=%s' % fname[:-4]]
    subprocess.call([extract]+args, cwd=osp.dirname(fname))
    if targetdir is not None:
        shutil.move(fname[:-4], osp.join(targetdir, bname[:-4]))


def extract_exe(fname, targetdir=None):
    '''Extract .exe archive to the directory of the same name    
    7z x -o"%1" -aos "%1.exe"'''
    extract = '7z.exe'
    assert utils.is_program_installed(extract)
    bname = osp.basename(fname)
    args = ['x', '-o%s' % bname[:-4], '-aos', bname]
    subprocess.call([extract]+args, cwd=osp.dirname(fname))
    if targetdir is not None:
        shutil.move(fname[:-4], osp.join(targetdir, bname[:-4]))


#==============================================================================
# Package and Distribution classes
#==============================================================================

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
            match = re.match(r'([a-zA-Z0-9\-\_]*)-([0-9\.]*[a-z]*).(win32|win\-amd64)(-py([0-9\.]*))?(-setup)?\.exe', bname)
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
        #elif bname.endswith(('.zip', '.tar.gz')):
            ## distutils sdist
            #match = re.match(r'([a-zA-Z0-9\-\_]*)-([0-9\.]*[a-z]*).(zip|tar\.gz)', bname)
            #if match is not None:
                #self.name, self.version = match.groups()[:2]
                #return
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
    
    def print_action(self, action):
        """Print action text (e.g. 'Installing') indicating progress"""
        text = " ".join([action, self.name, self.version])
        utils.print_box(text)
        

class Distribution(object):
    NSIS_PACKAGES = ('PyQt', 'PyQwt')  # known NSIS packages
    def __init__(self, target):
        self.target = target
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
    
    def copy_files(self, package, srcdir, dstdir, create_bat_files=False):
        """Add copy task"""
        srcdir = osp.join(package.fname[:-4], srcdir)
        if not osp.isdir(srcdir):
            return
        offset = len(srcdir)+len(os.pathsep)
        for dirpath, dirnames, filenames in os.walk(srcdir):
            for dname in dirnames:
                t_dname = osp.join(dirpath, dname)[offset:]
                src = osp.join(srcdir, t_dname)
                dst = osp.join(dstdir, t_dname)
                full_dst = osp.join(self.target, dst)
                print "mkdir:", dst
                if not osp.exists(full_dst):
                    os.mkdir(full_dst)
                package.folders.append(dst)
            for fname in filenames:
                t_fname = osp.join(dirpath, fname)[offset:]
                src = osp.join(srcdir, t_fname)
                dst = osp.join(dstdir, t_fname)
                full_dst = osp.join(self.target, dst)
                print "file:", dst
                shutil.copyfile(src, full_dst)
                package.files.append(dst)
                name, ext = osp.splitext(dst)
                if create_bat_files and ext in ('', '.py'):
                    dst = name + '.bat'
                    full_dst = osp.join(self.target, dst)
                    print "file:", dst
                    fd = file(full_dst, 'w')
                    fd.write("""@echo off
python "%~dpn0""" + ext + """" %*""")
                    fd.close()
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
        self.uninstall_existing(package)
        bname = osp.basename(package.fname)
        if bname.endswith('.exe'):
            if bname.startswith(self.NSIS_PACKAGES):
                self.install_nsis_package(package)
            else:
                self.install_bdist_wininst(package)
        elif bname.endswith('.msi'):
            self.install_bdist_msi(package)
        elif bname.endswith(('.tar.gz', '.zip')):
            self.install_sdist(package)
        package.save_log(self.logdir)
    
    def uninstall(self, package):
        """Uninstall package from distribution"""
        package.print_action("Uninstalling")
        package.load_log(self.logdir)
        for fname in reversed(package.files):
            print "remove:", fname
            path = osp.join(self.target, fname)
            os.remove(path)
            if fname.endswith('.py'):
                for suffix in ('c', 'o'):
                    if osp.exists(path+suffix):
                        os.remove(path+suffix)
        for dname in reversed(package.folders):
            try:
                print "rmdir:", dname
                os.rmdir(osp.join(self.target, dname))
            except OSError:
                pass

    def install_bdist_wininst(self, package):
        """Install a distutils package built with the bdist_wininst option
        (binary distribution, .exe file)"""
        package.print_action("Extracting")
        extract_exe(package.fname)
        package.print_action("Installing")
        self.copy_files(package, 'PURELIB', osp.join('Lib', 'site-packages'))
        self.copy_files(package, 'PLATLIB', osp.join('Lib', 'site-packages'))
        self.copy_files(package, 'SCRIPTS', 'Scripts', create_bat_files=True)
        self.copy_files(package, 'DLLs', 'DLLs')
        self.copy_files(package, 'DATA', '.')
        self.remove_directory(package.fname[:-4])

    def install_bdist_msi(self, package):
        """Install a distutils package built with the bdist_msi option
        (binary distribution, .msi file)"""
        raise NotImplementedError
        package.print_action("Extracting")
        extract_msi(package.fname)
        self.remove_directory(package.fname[:-4])

    def install_sdist(self, package):
        """Install a distutils package built with the sdist option
        (source distribution, .tar.gz or .zip file)"""
        raise NotImplementedError

    def install_nsis_package(self, package):
        """Install a Python package built with NSIS (e.g. PyQt or PyQwt)
        (binary distribution, .exe file)"""
        bname = osp.basename(package.fname)
        assert bname.startswith(self.NSIS_PACKAGES)
        package.print_action("Extracting")
        extract_exe(package.fname)
        package.print_action("Installing")
        self.copy_files(package, 'Lib', 'Lib')
        if bname.startswith('PyQt'):
            # PyQt4
            outdir = osp.join('Lib', 'site-packages', 'PyQt4')
        else:
            # Qwt5
            outdir = osp.join('Lib', 'site-packages', 'PyQt4', 'Qwt5')
        self.copy_files(package, '$_OUTDIR', outdir)
        self.remove_directory(package.fname[:-4])


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
    #fname = osp.join(sbdir, 'Cython-0.16.win-amd64-py2.7.exe')
    fname = osp.join(sbdir, 'pylzma-0.4.4dev.win-amd64-py2.7.exe')
    fname = osp.join(sbdir, 'cx_Freeze-4.3.win-amd64-py2.6.exe')
    target =osp.join(sbdir, 'winpython-2.7.3.amd64', 'python-2.7.3.amd64')
    #extract_exe(fname)
    #extract_msi(osp.join(tmpdir, 'python-2.7.3.amd64.msi'))
    #extract_exe(osp.join(tmpdir, 'PyQwt-5.2.0-py2.6-x64-pyqt4.8.6-numpy1.6.1-1.exe'))
    #extract_exe(osp.join(tmpdir, 'PyQt-Py2.7-x64-gpl-4.8.6-1.exe'))

    dist = Distribution(target)
    pack = Package(fname)
    #dist.install(pack)
    #dist.uninstall(pack)
