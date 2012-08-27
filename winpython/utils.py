# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
WinPython utilities

Created on Tue Aug 14 14:08:40 2012
"""

import os
import os.path as osp
import subprocess
import re
import tarfile
import zipfile
import tempfile
import shutil
import atexit
import sys


# Development only
TOOLS_DIR = osp.abspath(osp.join(osp.dirname(__file__), os.pardir, 'tools'))
if osp.isdir(TOOLS_DIR):
    os.environ['PATH'] += ';%s' % TOOLS_DIR
BASE_DIR = os.environ.get('WINPYTHONBASEDIR')


# Exact copy of 'spyderlib.utils.programs.is_program_installed' function
def is_program_installed(basename):
    """Return program absolute path if installed in PATH
    Otherwise, return None"""
    for path in os.environ["PATH"].split(os.pathsep):
        abspath = osp.join(path, basename)
        if osp.isfile(abspath):
            return abspath


def create_shortcut(path, description, filename,
                    arguments="", workdir="", iconpath="", iconindex=0):
    """Create Windows shortcut (.lnk file)"""
    import pythoncom
    from win32com.shell import shell
    ilink = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None,
                                       pythoncom.CLSCTX_INPROC_SERVER,
                                       shell.IID_IShellLink)
    ilink.SetPath(path)
    ilink.SetDescription(description)
    if arguments:
        ilink.SetArguments(arguments)
    if workdir:
        ilink.SetWorkingDirectory(workdir)
    if iconpath or iconindex:
        ilink.SetIconLocation(iconpath, iconindex)
    # now save it.
    ipf = ilink.QueryInterface(pythoncom.IID_IPersistFile)
    ipf.Save(filename, 0)


def print_box(text):
    """Print text in a box"""
    line0 = "+" + ("-"*(len(text)+2)) + "+"
    line1 = "| " + text + " |"
    print("\n\n" + "\n".join([line0, line1, line0]) + "\n")


def exec_shell_cmd(args, path):
    """Execute shell command (*args* is a list of arguments) in *path*"""
    #print " ".join(args)
    process = subprocess.Popen(args, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, cwd=path, shell=True)
    return process.stdout.read()


def python_query(cmd, path):
    """Execute Python command using the Python interpreter located in *path*"""
    return exec_shell_cmd('python -c "%s"' % cmd, path).splitlines()[0]


def get_python_infos(path):
    """Return (version, architecture) for the Python distribution located in 
    *path*. The version number is limited to MAJOR.MINOR, the architecture is 
    an integer: 32 or 64"""
    is_64 = python_query('import sys; print(sys.maxsize > 2**32)', path)
    arch = {'True': 64, 'False': 32}.get(is_64, None)
    ver = python_query("import sys; print('%d.%d' % (sys.version_info.major, "\
                       "sys.version_info.minor))", path)
    if re.match(r'([0-9]*)\.([0-9]*)', ver) is None:
        ver = None
    return ver, arch


#==============================================================================
# Extract functions
#==============================================================================
def _create_temp_dir():
    """Create a temporary directory and remove it at exit"""
    tmpdir = tempfile.mkdtemp(prefix='wppm_')
    atexit.register(shutil.rmtree, tmpdir)
    return tmpdir

def extract_msi(fname, targetdir=None, verbose=False):
    """Extract .msi installer to a temporary directory (if targetdir 
    is None). Return the temporary directory path"""
    assert fname.endswith('.msi')
    if targetdir is None:
        targetdir = _create_temp_dir()
    extract = 'msiexec.exe'
    bname = osp.basename(fname)
    args = ['/a', '%s' % bname]
    if not verbose:
        args += ['/qn']
    args += ['TARGETDIR=%s' % targetdir]
    subprocess.call([extract]+args, cwd=osp.dirname(fname))
    return targetdir

def extract_exe(fname, targetdir=None, verbose=False):
    """Extract .exe archive to a temporary directory (if targetdir 
    is None). Return the temporary directory path"""
    if targetdir is None:
        targetdir = _create_temp_dir()
    extract = '7z.exe'
    assert is_program_installed(extract),\
           "Required program '%s' was not found" % extract
    bname = osp.basename(fname)
    args = ['x', '-o%s' % targetdir, '-aos', bname]
    if verbose:
        subprocess.call([extract]+args, cwd=osp.dirname(fname))
    else:
        p = subprocess.Popen([extract]+args, cwd=osp.dirname(fname),
                             stdout=subprocess.PIPE)
        p.communicate()
        p.stdout.close()
    return targetdir

def extract_archive(fname, targetdir=None, verbose=False):
    """Extract .zip, .exe (considered to be a zip archive) or .tar.gz archive 
    to a temporary directory (if targetdir is None).
    Return the temporary directory path"""
    if targetdir is None:
        targetdir = _create_temp_dir()
    if osp.splitext(fname)[1] in ('.zip', '.exe'):
        obj = zipfile.ZipFile(fname, mode="r")
    elif fname.endswith('.tar.gz'):
        obj = tarfile.open(fname, mode='r:gz')
    else:
        raise RuntimeError, "Unsupported archive filename %s" % fname
    obj.extractall(path=targetdir)
    return targetdir


WININST_PATTERN = r'([a-zA-Z0-9\-\_]*)-([0-9\.]*[a-z]*).(win32|win\-amd64)(-py([0-9\.]*))?(-setup)?\.exe'
SOURCE_PATTERN = r'([a-zA-Z0-9\-\_]*)-([0-9\.]*[a-z]*).(zip|tar\.gz)'

def get_source_package_infos(fname):
    """Return a tuple (name, version) of the Python source package"""
    match = re.match(SOURCE_PATTERN, osp.basename(fname))
    if match is not None:
        return match.groups()[:2]
    
def source_to_wininst(fname, architecture=None, verbose=False):
    """Extract source archive, build it and create a distutils installer"""
    tmpdir = extract_archive(fname)
    root = osp.join(tmpdir, '%s-%s' % get_source_package_infos(fname))
    assert osp.isdir(root)
    cmd = [sys.executable, 'setup.py', 'build']
    if architecture is not None:
        archstr = 'win32' if architecture == 32 else 'win-amd64'
        cmd += ['--plat-name=%s' % archstr]
    cmd += ['bdist_wininst']
    if verbose:
        subprocess.call(cmd, cwd=root)
    else:
        p = subprocess.Popen(cmd, cwd=root, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        p.communicate()
        p.stdout.close()
        p.stderr.close()
    distdir = osp.join(root, 'dist')
    distname = os.listdir(distdir)[0]
    match = re.match(WININST_PATTERN, distname)
    if match is None:
        raise RuntimeError, "Installation failed: not a pure Python package?"
    else:
        dest_fname = osp.join(osp.dirname(fname), distname)
        shutil.copyfile(osp.join(distdir, distname), dest_fname)
        return dest_fname


if __name__ == '__main__':
    print_box("Test")
    dname = sys.prefix
    print dname+':', '\n', get_python_infos(dname)
    #dname = r'E:\winpython\sandbox\python-2.7.3'
    #print dname+':', '\n', get_python_infos(dname)
    
    tmpdir = r'D:\Tests\winpython_tests'
    if not osp.isdir(tmpdir):
        os.mkdir(tmpdir)
    print extract_archive(osp.join(BASE_DIR, 'packages.win-amd64',
                               'winpython-0.3dev.win-amd64.exe'),
                          tmpdir)
    #extract_exe(osp.join(tmpdir, 'PyQwt-5.2.0-py2.6-x64-pyqt4.8.6-numpy1.6.1-1.exe'))
    #extract_exe(osp.join(tmpdir, 'PyQt-Py2.7-x64-gpl-4.8.6-1.exe'))

#    path = r'D:\Pierre\_test\xlrd-0.8.0.tar.gz'
#    source_to_wininst(path)
