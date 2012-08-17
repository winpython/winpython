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
def  _init_target_dir(targetdir, fname):
    if targetdir is None:
        targetdir = fname[:-4]
    else:
        targetdir = osp.join(targetdir, osp.basename(fname)[:-4])
        if not osp.isdir(targetdir):
            os.mkdir(targetdir)
    return targetdir

def extract_msi(fname, targetdir=None, verbose=False):
    '''Extract .msi installer to the directory of the same name    
    msiexec.exe /a "python-%PYVER%%PYARC%.msi" /qn TARGETDIR="%PYDIR%"'''
    targetdir = _init_target_dir(targetdir, fname)
    extract = 'msiexec.exe'
    assert is_program_installed(extract)
    bname = osp.basename(fname)
    args = ['/a', '%s' % bname]
    if not verbose:
        args += ['/qn']
    args += ['TARGETDIR=%s' % targetdir]
    subprocess.call([extract]+args, cwd=osp.dirname(fname))
    return targetdir

def extract_exe(fname, targetdir=None, verbose=False):
    '''Extract .exe archive to the directory of the same name    
    7z x -o"%1" -aos "%1.exe"'''
    targetdir = _init_target_dir(targetdir, fname)
    extract = '7z.exe'
    assert is_program_installed(extract)
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


if __name__ == '__main__':
    print_box("Test")
    import sys
    dname = sys.prefix
    print dname+':', '\n', get_python_infos(dname)
    dname = r'E:\winpython\sandbox\python-2.7.3'
    print dname+':', '\n', get_python_infos(dname)
    
    sbdir = osp.join(osp.dirname(__file__),
                     os.pardir, os.pardir, os.pardir, 'sandbox')
    tmpdir = osp.join(sbdir, 'tobedeleted')
    print extract_exe(osp.join(sbdir, 'winpython-0.1dev.win-amd64.exe'),
                      tmpdir, verbose=False)
    #extract_exe(osp.join(tmpdir, 'PyQwt-5.2.0-py2.6-x64-pyqt4.8.6-numpy1.6.1-1.exe'))
    #extract_exe(osp.join(tmpdir, 'PyQt-Py2.7-x64-gpl-4.8.6-1.exe'))
