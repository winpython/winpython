# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
WinPython utilities

Created on Tue Aug 14 14:08:40 2012
"""

from __future__ import print_function

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
import stat
import locale

# Local imports
from winpython.py3compat import winreg


# Development only
TOOLS_DIR = osp.abspath(osp.join(osp.dirname(__file__), os.pardir, 'tools'))
if osp.isdir(TOOLS_DIR):
    os.environ['PATH'] += ';%s' % TOOLS_DIR
ROOT_DIR = os.environ.get('WINPYTHONROOTDIR')
BASE_DIR = os.environ.get('WINPYTHONBASEDIR')

ROOTDIR_DOC = """

    The WinPython root directory (WINPYTHONROOTDIR environment variable which
    may be overriden with the `rootdir` option) contains the following folders:
      * (required) `packages.win32`: contains distutils 32-bit packages
      * (required) `packages.win-amd64`: contains distutils 64-bit packages
      * (optional) `packages.src`: contains distutils source distributions
      * (required) `tools`: contains architecture-independent tools
      * (optional) `tools.win32`: contains 32-bit-specific tools
      * (optional) `tools.win-amd64`: contains 64-bit-specific tools"""


def onerror(function, path, excinfo):
    """Error handler for `shutil.rmtree`.

    If the error is due to an access error (read-only file), it
    attempts to add write permission and then retries.
    If the error is for another reason, it re-raises the error.

    Usage: `shutil.rmtree(path, onerror=onerror)"""
    if not os.access(path, os.W_OK):
        # Is the error an access error?
        os.chmod(path, stat.S_IWUSR)
        function(path)
    else:
        raise


# Exact copy of 'spyderlib.utils.programs.is_program_installed' function
def is_program_installed(basename):
    """Return program absolute path if installed in PATH
    Otherwise, return None"""
    for path in os.environ["PATH"].split(os.pathsep):
        abspath = osp.join(path, basename)
        if osp.isfile(abspath):
            return abspath


# =============================================================================
# Environment variables
# =============================================================================
def get_env(name, current=True):
    """Return HKCU/HKLM environment variable name and value

    For example, get_user_env('PATH') may returns:
    ('Path', u'C:\\Program Files\\Intel\\WiFi\\bin\\')"""
    root = winreg.HKEY_CURRENT_USER if current else winreg.HKEY_LOCAL_MACHINE
    key = winreg.OpenKey(root, "Environment")
    for index in range(0, winreg.QueryInfoKey(key)[1]):
        try:
            value = winreg.EnumValue(key, index)
            if value[0].lower() == name.lower():
                # Return both value[0] and value[1] because value[0] could be
                # different from name (lowercase/uppercase)
                return value[0], value[1]
        except:
            break


def set_env(name, value, current=True):
    """Set HKCU/HKLM environment variables"""
    root = winreg.HKEY_CURRENT_USER if current else winreg.HKEY_LOCAL_MACHINE
    key = winreg.OpenKey(root, "Environment")
    try:
        _x, key_type = winreg.QueryValueEx(key, name)
    except WindowsError:
        key_type = winreg.REG_EXPAND_SZ
    key = winreg.OpenKey(root, "Environment", 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, name, 0, key_type, value)
    from win32gui import SendMessageTimeout
    from win32con import (HWND_BROADCAST, WM_SETTINGCHANGE,
                          SMTO_ABORTIFHUNG)
    SendMessageTimeout(HWND_BROADCAST, WM_SETTINGCHANGE, 0,
                       "Environment", SMTO_ABORTIFHUNG, 5000)


# =============================================================================
# Shortcuts, start menu
# =============================================================================

def get_special_folder_path(path_name):
    """Return special folder path"""
    from win32com.shell import shell, shellcon
    for maybe in """
       CSIDL_COMMON_STARTMENU CSIDL_STARTMENU CSIDL_COMMON_APPDATA
       CSIDL_LOCAL_APPDATA CSIDL_APPDATA CSIDL_COMMON_DESKTOPDIRECTORY
       CSIDL_DESKTOPDIRECTORY CSIDL_COMMON_STARTUP CSIDL_STARTUP
       CSIDL_COMMON_PROGRAMS CSIDL_PROGRAMS CSIDL_PROGRAM_FILES_COMMON
       CSIDL_PROGRAM_FILES CSIDL_FONTS""".split():
        if maybe == path_name:
            csidl = getattr(shellcon, maybe)
            return shell.SHGetSpecialFolderPath(0, csidl, False)
    raise ValueError("%s is an unknown path ID" % (path_name,))


def get_winpython_start_menu_folder(current=True):
    """Return WinPython Start menu shortcuts folder"""
    if current:
        # non-admin install - always goes in this user's start menu.
        folder = get_special_folder_path("CSIDL_PROGRAMS")
    else:
        try:
            folder = get_special_folder_path("CSIDL_COMMON_PROGRAMS")
        except OSError:
            # No CSIDL_COMMON_PROGRAMS on this platform
            folder = get_special_folder_path("CSIDL_PROGRAMS")
    return osp.join(folder, 'WinPython')


def create_winpython_start_menu_folder(current=True):
    """Create WinPython Start menu folder -- remove it if it already exists"""
    path = get_winpython_start_menu_folder(current=current)
    if osp.isdir(path):
        try:
            shutil.rmtree(path, onerror=onerror)
        except WindowsError:
            print("Directory %s could not be removed" % path, file=sys.stderr)
    else:
        os.mkdir(path)
    return path


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
    if not filename.endswith('.lnk'):
        filename += '.lnk'
    ipf.Save(filename, 0)


# =============================================================================
# Misc.
# =============================================================================

def print_box(text):
    """Print text in a box"""
    line0 = "+" + ("-"*(len(text)+2)) + "+"
    line1 = "| " + text + " |"
    print(("\n\n" + "\n".join([line0, line1, line0]) + "\n"))


def is_python_distribution(path):
    """Return True if path is a Python distribution"""
    # XXX: This test could be improved but it seems to be sufficient
    return osp.isfile(osp.join(path, 'python.exe'))\
           and osp.isdir(osp.join(path, 'Lib', 'site-packages'))


# =============================================================================
# Shell, Python queries
# =============================================================================

def decode_fs_string(string):
    """Convert string from file system charset to unicode"""
    charset = sys.getfilesystemencoding()
    if charset is None:
        charset = locale.getpreferredencoding()
    return string.decode(charset)


def exec_shell_cmd(args, path):
    """Execute shell command (*args* is a list of arguments) in *path*"""
    # print " ".join(args)
    process = subprocess.Popen(args, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, cwd=path, shell=True)
    return decode_fs_string(process.stdout.read())


def get_r_version(path):
    """Return version of the R installed in *path*"""
    return exec_shell_cmd('dir ..\README.R*', path).splitlines()[-3].split("-")[-1]


def get_julia_version(path):
    """Return version of the Julia installed in *path*"""
    return exec_shell_cmd('julia.exe -v', path).splitlines()[0].split(" ")[-1]


def get_thg_version(path):
    """Return version of TortoiseHg installed in *path*"""
    txt = exec_shell_cmd('thg version', path).splitlines()[0]
    match = re.match('TortoiseHg Dialogs \(version ([0-9\.]*)\)', txt)
    if match is not None:
        return match.groups()[0]

def get_pandoc_version(path):
    """Return version of the Pandoc executable in *path*"""
    return exec_shell_cmd('pandoc -v', path).splitlines()[0].split(" ")[-1]

def python_query(cmd, path):
    """Execute Python command using the Python interpreter located in *path*"""
    return exec_shell_cmd('python -c "%s"' % cmd, path).splitlines()[0]


def get_python_infos(path):
    """Return (version, architecture) for the Python distribution located in
    *path*. The version number is limited to MAJOR.MINOR, the architecture is
    an integer: 32 or 64"""
    is_64 = python_query('import sys; print(sys.maxsize > 2**32)', path)
    arch = {'True': 64, 'False': 32}.get(is_64, None)
    ver = python_query("import sys; print('%d.%d' % (sys.version_info.major, "
                       "sys.version_info.minor))", path)
    if re.match(r'([0-9]*)\.([0-9]*)', ver) is None:
        ver = None
    return ver, arch


def get_python_long_version(path):
    """Return long version (X.Y.Z) for the Python distribution located in
    *path*"""
    ver = python_query("import sys; print('%d.%d.%d' % "
                       "(sys.version_info.major, sys.version_info.minor,"
                       "sys.version_info.micro))", path)
    if re.match(r'([0-9]*)\.([0-9]*)\.([0-9]*)', ver) is None:
        ver = None
    return ver


# =============================================================================
# Patch chebang line (courtesy of Christoph Gohlke)
# =============================================================================
def patch_shebang_line(fname, pad=b' ', to_movable=True, targetdir=""):
    """Remove absolute path to python.exe in shebang lines, or re-add it"""

    import re
    import sys
    import os
    target_dir = targetdir # movable option
    if to_movable == False:
        target_dir = os.path.abspath(os.path.dirname(fname))
        target_dir = os.path.abspath(os.path.join(target_dir, r'..')) + '\\'

    executable= sys.executable
    if sys.version_info[0] == 2:
        shebang_line = re.compile(r"(#!.*pythonw?\.exe)")  # Python2.7
    else:
        shebang_line = re.compile(b"(#!.*pythonw?\.exe)")  # Python3+
        target_dir = target_dir.encode('utf-8')
    with open(fname, 'rb') as fh:
        initial_content = fh.read()
        fh.close
        fh = None
    content = shebang_line.split(initial_content, maxsplit=1)
    if len(content) != 3:
        return

    exe = os.path.basename(content[1][2:])
    content[1] = b'#!' + target_dir + exe #+ (pad * (len(content[1]) - len(exe) - 2))
    final_content = b''.join(content)
    if initial_content == final_content:
        return
    try:
        with open(fname, 'wb') as fo:
            fo.write(final_content)
            fo.close
            fo = None
            print("patched", fname)
    except Exception:
        print("failed to patch", fname)


# =============================================================================
# Patch shebang line in .py files
# =============================================================================
def patch_shebang_line_py(fname, to_movable=True, targetdir=""):
    """Changes shebang line in '.py' file to relative or absolue path"""
    import fileinput
    import re
    import sys
    
    if sys.version_info[0] == 2:
        # Python 2.x doesn't create .py files for .exe files. So, Moving
        # WinPython doesn't break running executable files.
        return
    if to_movable:
        exec_path = '#!.\python.exe'
    else:
        exec_path = '#!' + sys.executable
    for line in fileinput.input(fname, inplace=True):
        if re.match('^#\!.*python\.exe$', line) is not None:
            print(exec_path)
        else:
            print(line, end='')

# =============================================================================
# Patch sourcefile (instead of forking packages)
# =============================================================================
def patch_sourcefile(fname, in_text, out_text, silent_mode=False):
    """Replace a string in a source file"""
    import io
    if osp.isfile(fname) and not in_text == out_text:
        with io.open(fname, 'r') as fh:
            content = fh.read()
        new_content = content.replace(in_text, out_text)
        if not new_content == content:
            if not silent_mode:
                print("patching ", fname, "from", in_text, "to", out_text)
            with io.open(fname, 'wt') as fh:
                fh.write(new_content)

# =============================================================================
# Patch sourcelines (instead of forking packages)
# =============================================================================
def patch_sourcelines(fname, in_line_start, out_line, endline='\n', silent_mode=False):
    """Replace the middle of lines between in_line_start and endline """
    import io
    import os.path as osp
    if osp.isfile(fname):
        with io.open(fname, 'r') as fh:
            contents = fh.readlines()
            content = "".join(contents)
            for l in range(len(contents)):
                if contents[l].startswith(in_line_start):
                   begining , middle = in_line_start , contents[l][len(in_line_start):]
                   ending = ""
                   if middle.find(endline)>0:
                       ending = endline + endline.join(middle.split(endline)[1:])
                       middle = middle.split(endline)[0]
                   middle = out_line
                   new_line = begining + middle + ending
                   if not new_line == contents[l]:
                       if not silent_mode:
                           print("patching ", fname, " from\n", contents[l], "\nto\n", new_line)
                   contents[l] = new_line
            new_content = "".join(contents)
        if not new_content == content:
            # if not silent_mode:
            #    print("patching ", fname, "from", content, "to", new_content)
            with io.open(fname, 'wt') as fh:
                try:
                    fh.write(new_content)
                except:
                    print("impossible to patch", fname, "from", content,
                          "to", new_content)


# =============================================================================
# Extract functions
# =============================================================================
def _create_temp_dir():
    """Create a temporary directory and remove it at exit"""
    tmpdir = tempfile.mkdtemp(prefix='wppm_')
    atexit.register(lambda path: shutil.rmtree(path, onerror=onerror), tmpdir)
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
    print('fname=%s' % fname)
    print('TARGETDIR=%s' % targetdir)
    # ensure pip if it's not 3.3
    if '-3.3' not in targetdir:
        subprocess.call(
            [r'%s\%s' % (targetdir, 'python.exe'), '-m', 'ensurepip'],
            cwd=osp.dirname(r'%s\%s' % (targetdir, 'pythons.exe')))
        # We patch ensurepip live (shame) !!!!
        # rational: https://github.com/pypa/pip/issues/2328
        import glob
        for fname in glob.glob(r'%s\Scripts\*.exe' % targetdir):
            patch_shebang_line(fname)
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
        retcode = subprocess.call([extract]+args, cwd=osp.dirname(fname))
    else:
        p = subprocess.Popen([extract]+args, cwd=osp.dirname(fname),
                             stdout=subprocess.PIPE)
        p.communicate()
        p.stdout.close()
        retcode = p.returncode
    if retcode != 0:
        raise RuntimeError("Failed to extract %s (return code: %d)"
                           % (fname, retcode))
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
        raise RuntimeError("Unsupported archive filename %s" % fname)
    obj.extractall(path=targetdir)
    return targetdir


WININST_PATTERN = r'([a-zA-Z0-9\-\_]*|[a-zA-Z\-\_\.]*)-([0-9\.\-]*[a-z]*[0-9]?)(-Qt-([0-9\.]+))?.(win32|win\-amd64)(-py([0-9\.]+))?(-setup)?\.exe'

# SOURCE_PATTERN defines what an acceptable source package name is
# As of 2014-09-08 :
#    - the wheel package format is accepte in source directory
#    - the tricky regexp is tuned also to support the odd jolib naming :
#         . joblib-0.8.3_r1-py2.py3-none-any.whl,
#         . joblib-0.8.3-r1.tar.gz

SOURCE_PATTERN = r'([a-zA-Z0-9\-\_\.]*)-([0-9\.\_]*[a-z]*[\-]?[0-9]*)(\.zip|\.tar\.gz|\-(py[2-7]*|py[2-7]*\.py[2-7]*)\-none\-any\.whl)'

# WHEELBIN_PATTERN defines what an acceptable binary wheel package is
# "cp([0-9]*)" to replace per cp(34) for python3.4
# "win32|win\_amd64" to replace per "win\_amd64" for 64bit
WHEELBIN_PATTERN = r'([a-zA-Z0-9\-\_\.]*)-([0-9\.\_]*[a-z0-9\+]*[0-9]?)-cp([0-9]*)\-[0-9|c|o|n|e|p|m]*\-(win32|win\_amd64)\.whl'

def get_source_package_infos(fname):
    """Return a tuple (name, version) of the Python source package"""
    match = re.match(SOURCE_PATTERN, osp.basename(fname).replace("+mkl-","-"))
    if match is not None:
        return match.groups()[:2]

def build_wininst(root, python_exe=None, copy_to=None,
                  architecture=None, verbose=False, installer='bdist_wininst'):
    """Build wininst installer from Python package located in *root*
    and eventually copy it to *copy_to* folder.
    Return wininst installer full path."""
    if python_exe is None:
        python_exe = sys.executable
    assert osp.isfile(python_exe)
    cmd = [python_exe, 'setup.py', 'build']
    if architecture is not None:
        archstr = 'win32' if architecture == 32 else 'win-amd64'
        cmd += ['--plat-name=%s' % archstr]
    cmd += [installer]
    # root = a tmp dir in windows\tmp,
    if verbose:
        subprocess.call(cmd, cwd=root)
    else:
        p = subprocess.Popen(cmd, cwd=root, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        p.communicate()
        p.stdout.close()
        p.stderr.close()
    distdir = osp.join(root, 'dist')
    if not osp.isdir(distdir):
        raise RuntimeError("Build failed: see package README file for further"
                   " details regarding installation requirements.\n\n"
                   "For more concrete debugging infos, please try to build "
                   "the package from the command line:\n"
                   "1. Open a WinPython command prompt\n"
                   "2. Change working directory to the appropriate folder\n"
                   "3. Type `python setup.py build install`")
    pattern = WININST_PATTERN.replace(r'(win32|win\-amd64)', archstr)
    for distname in os.listdir(distdir):
        match = re.match(pattern, distname)
        if match is not None:
            break
        # for wheels (winpython here)
        match = re.match(SOURCE_PATTERN, distname)
        if match is not None:
            break
        match = re.match(WHEELBIN_PATTERN, distname)
        if match is not None:
            break
    else:
        raise RuntimeError("Build failed: not a pure Python package? %s" %
                           distdir)
    src_fname = osp.join(distdir, distname)
    if copy_to is None:
        return src_fname
    else:
        dst_fname = osp.join(copy_to, distname)
        shutil.move(src_fname, dst_fname)
        if verbose:
            print(("Move: %s --> %s" % (src_fname, (dst_fname))))
            # remove tempo dir 'root' no more needed
            shutil.rmtree(root, onerror=onerror)
        return dst_fname


def direct_pip_install(fname, python_exe=None, architecture=None,
                       verbose=False, install_options=None):
    """Direct install via pip !"""
    copy_to = osp.dirname(fname)

    if python_exe is None:
        python_exe = sys.executable
    assert osp.isfile(python_exe)
    myroot = os.path.dirname(python_exe)

    cmd = [python_exe, '-m', 'pip', 'install']
    if install_options:
        cmd += install_options  # typically ['--no-deps']
        print('pip install_options', install_options)
    cmd += [fname]

    if verbose:
        subprocess.call(cmd, cwd=myroot)
    else:
        p = subprocess.Popen(cmd, cwd=myroot, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        the_log = ("%s" % stdout + "\n %s" % stderr)

        if ' not find ' in the_log or ' not found ' in the_log:
            print("Failed to Install: \n %s \n" % fname)
            print("msg: %s" % the_log)
            raise RuntimeError
        p.stdout.close()
        p.stderr.close()
    src_fname = fname
    if copy_to is None:
        return src_fname
    else:
        if verbose:
            print("Installed %s" % src_fname)
        return src_fname


def do_script(this_script, python_exe=None, copy_to=None,
              architecture=None, verbose=False, install_options=None):
    """Execute a script (get-pip typically)"""
    if python_exe is None:
        python_exe = sys.executable
    myroot = os.path.dirname(python_exe)

    # cmd = [python_exe, myroot + r'\Scripts\pip-script.py', 'install']
    cmd = [python_exe]
    if install_options:
        cmd += install_options  # typically ['--no-deps']
        print('script install_options', install_options)
    if this_script:
        cmd += [this_script]
    # print('build_wheel', myroot, cmd)
    print("Executing ", cmd)

    if verbose:
        subprocess.call(cmd, cwd=myroot)
    else:
        p = subprocess.Popen(cmd, cwd=myroot, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        p.communicate()
        p.stdout.close()
        p.stderr.close()
    if verbose:
            print("Executed " % cmd)
    return 'ok'


if __name__ == '__main__':
    thg = get_thg_version(osp.join(BASE_DIR, 'tools', 'tortoisehg'))
    print(("thg version: %r" % thg))

    print_box("Test")
    dname = sys.prefix
    print((dname+':', '\n', get_python_infos(dname)))
    # dname = r'E:\winpython\sandbox\python-2.7.3'
    # print dname+':', '\n', get_python_infos(dname)

    tmpdir = r'D:\Tests\winpython_tests'
    if not osp.isdir(tmpdir):
        os.mkdir(tmpdir)
    print((extract_archive(osp.join(BASE_DIR, 'packages.win-amd64',
                           'winpython-0.3dev.win-amd64.exe'),
                           tmpdir)))
    # extract_exe(osp.join(tmpdir,
    #                      'PyQwt-5.2.0-py2.6-x64-pyqt4.8.6-numpy1.6.1-1.exe'))
    # extract_exe(osp.join(tmpdir, 'PyQt-Py2.7-x64-gpl-4.8.6-1.exe'))

    # path = r'D:\Pierre\_test\xlrd-0.8.0.tar.gz'
    # source_to_wininst(path)
