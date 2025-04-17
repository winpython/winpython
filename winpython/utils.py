# -*- coding: utf-8 -*-
#
# WinPython utilities
# Copyright © 2012 Pierre Raybaut
# Copyright © 2014-2025+ The Winpython development team https://github.com/winpython/
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

import os
import sys
import stat
import shutil
import locale
import tempfile
import subprocess
import configparser as cp
from pathlib import Path
import re
import tarfile
import zipfile
import atexit
import winreg

# SOURCE_PATTERN defines what an acceptable source package name is
SOURCE_PATTERN = r'([a-zA-Z0-9\-\_\.]*)-([0-9\.\_]*[a-z]*[\-]?[0-9]*)(\.zip|\.tar\.gz|\-(py[2-7]*|py[2-7]*\.py[2-7]*)\-none\-any\.whl)'

# WHEELBIN_PATTERN defines what an acceptable binary wheel package is
WHEELBIN_PATTERN = r'([a-zA-Z0-9\-\_\.]*)-([0-9\.\_]*[a-z0-9\+]*[0-9]?)-cp([0-9]*)\-[0-9|c|o|n|e|p|m]*\-(win32|win\_amd64)\.whl'

def get_python_executable(path=None):
    """Return the path to the Python executable."""
    python_path = Path(path) if path else Path(sys.executable)
    base_dir = python_path if python_path.is_dir() else python_path.parent
    python_exe = base_dir / 'python.exe'
    pypy_exe = base_dir / 'pypy3.exe'  # For PyPy
    return str(python_exe if python_exe.is_file() else pypy_exe)

def get_site_packages_path(path=None):
    """Return the path to the Python site-packages directory."""
    python_path = Path(path) if path else Path(sys.executable)
    base_dir = python_path if python_path.is_dir() else python_path.parent
    site_packages = base_dir / 'Lib' / 'site-packages'
    pypy_site_packages = base_dir / 'site-packages'  # For PyPy
    return str(pypy_site_packages if pypy_site_packages.is_dir() else site_packages)

def onerror(function, path, excinfo):
    """Error handler for `shutil.rmtree`."""
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        function(path)
    else:
        raise

def getFileProperties(fname):
    """Read all properties of the given file return them as a dictionary."""
    import win32api
    prop_names = ('ProductName', 'ProductVersion', 'FileDescription', 'FileVersion')
    props = {'FixedFileInfo': None, 'StringFileInfo': None, 'FileVersion': None}

    try:
        fixed_info = win32api.GetFileVersionInfo(fname, '\\')
        props['FixedFileInfo'] = fixed_info
        props['FileVersion'] = "{}.{}.{}.{}".format(
            fixed_info['FileVersionMS'] // 65536,
            fixed_info['FileVersionMS'] % 65536,
            fixed_info['FileVersionLS'] // 65536,
            fixed_info['FileVersionLS'] % 65536
        )
        lang, codepage = win32api.GetFileVersionInfo(fname, '\\VarFileInfo\\Translation')[0]
        props['StringFileInfo'] = {
            prop_name: win32api.GetFileVersionInfo(fname, f'\\StringFileInfo\\{lang:04X}{codepage:04X}\\{prop_name}')
            for prop_name in prop_names
        }
    except:
        pass

    return props

def get_special_folder_path(path_name):
    """Return special folder path."""
    from win32com.shell import shell, shellcon
    try:
        csidl = getattr(shellcon, path_name)
        return shell.SHGetSpecialFolderPath(0, csidl, False)
    except OSError:
        print(f"{path_name} is an unknown path ID")

def get_winpython_start_menu_folder(current=True):
    """Return WinPython Start menu shortcuts folder."""
    folder = get_special_folder_path("CSIDL_PROGRAMS")
    if not current:
        try:
            folder = get_special_folder_path("CSIDL_COMMON_PROGRAMS")
        except OSError:
            pass
    return str(Path(folder) / 'WinPython')

def remove_winpython_start_menu_folder(current=True):
    """Remove WinPython Start menu folder -- remove it if it already exists"""
    path = get_winpython_start_menu_folder(current=current)
    if Path(path).is_dir():
        try:
            shutil.rmtree(path, onexc=onerror)
        except WindowsError:
            print(f"Directory {path} could not be removed", file=sys.stderr)

def create_winpython_start_menu_folder(current=True):
    """Create WinPython Start menu folder."""
    path = get_winpython_start_menu_folder(current=current)
    if Path(path).is_dir():
        try:
            shutil.rmtree(path, onexc=onerror)
        except WindowsError:
            print(f"Directory {path} could not be removed", file=sys.stderr)
    Path(path).mkdir(parents=True, exist_ok=True)
    return path

def create_shortcut(path, description, filename, arguments="", workdir="", iconpath="", iconindex=0, verbose=True):
    """Create Windows shortcut (.lnk file)."""
    import pythoncom
    from win32com.shell import shell
    ilink = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
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
    if verbose:
        print(f'create menu *{filename}*')
    try:
        ipf.Save(filename, 0)
    except:
        print("a fail !")

def print_box(text):
    """Print text in a box"""
    line0 = "+" + ("-" * (len(text) + 2)) + "+"
    line1 = "| " + text + " |"
    print("\n\n" + "\n".join([line0, line1, line0]) + "\n")

def is_python_distribution(path):
    """Return True if path is a Python distribution."""
    has_exec = Path(get_python_executable(path)).is_file()
    has_site = Path(get_site_packages_path(path)).is_dir()
    return has_exec and has_site

def decode_fs_string(string):
    """Convert string from file system charset to unicode."""
    charset = sys.getfilesystemencoding() or locale.getpreferredencoding()
    return string.decode(charset)

def exec_shell_cmd(args, path):
    """Execute shell command (*args* is a list of arguments) in *path*."""
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path, shell=True)
    return decode_fs_string(process.stdout.read())

def exec_run_cmd(args, path=None):
    """Run a single command (*args* is a list of arguments) in optional *path*."""
    process = subprocess.run(args, capture_output=True, cwd=path, text=True)
    return process.stdout

def python_query(cmd, path):
    """Execute Python command using the Python interpreter located in *path*."""
    the_exe = get_python_executable(path)
    return exec_shell_cmd(f'"{the_exe}" -c "{cmd}"', path).splitlines()[0]

def python_execmodule(cmd, path):
    """Execute Python command using the Python interpreter located in *path*."""
    the_exe = get_python_executable(path)
    exec_shell_cmd(f'{the_exe} -m {cmd}', path)

def get_python_infos(path):
    """Return (version, architecture) for the Python distribution located in *path*."""
    is_64 = python_query("import sys; print(sys.maxsize > 2**32)", path)
    arch = {"True": 64, "False": 32}.get(is_64, None)
    ver = python_query("import sys;print(f'{sys.version_info.major}.{sys.version_info.minor}')", path)
    return ver, arch

def get_python_long_version(path):
    """Return long version (X.Y.Z) for the Python distribution located in *path*."""
    ver = python_query("import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')", path)
    return ver if re.match(r"([0-9]*)\.([0-9]*)\.([0-9]*)", ver) else None

def patch_shebang_line(fname, pad=b" ", to_movable=True, targetdir=""):
    """Remove absolute path to python.exe in shebang lines in binary files, or re-add it."""
    target_dir = targetdir if to_movable else os.path.abspath(os.path.join(os.path.dirname(fname), r"..")) + "\\"
    executable = sys.executable
    shebang_line = re.compile(rb"""(#!.*pythonw?\.exe)"?""")  # Python3+
    if "pypy3" in sys.executable:
        shebang_line = re.compile(rb"""(#!.*pypy3w?\.exe)"?""")  # Pypy3+
    target_dir = target_dir.encode("utf-8")

    with open(fname, "rb") as fh:
        initial_content = fh.read()
    content = shebang_line.split(initial_content, maxsplit=1)
    if len(content) != 3:
        return
    exe = os.path.basename(content[1][2:])
    content[1] = b"#!" + target_dir + exe  # + (pad * (len(content[1]) - len(exe) - 2))
    final_content = b"".join(content)
    if initial_content == final_content:
        return
    try:
        with open(fname, "wb") as fo:
            fo.write(final_content)
            print("patched", fname)
    except Exception:
        print("failed to patch", fname)

def patch_shebang_line_py(fname, to_movable=True, targetdir=""):
    """Changes shebang line in '.py' file to relative or absolue path"""
    import fileinput
    exec_path = r'#!.\python.exe' if to_movable else '#!' + sys.executable
    if 'pypy3' in sys.executable:
        exec_path = r'#!.\pypy3.exe' if to_movable else exec_path
    for line in fileinput.input(fname, inplace=True):
        if re.match(r'^#\!.*python\.exe$', line) or re.match(r'^#\!.*pypy3\.exe$', line):
            print(exec_path)
        else:
            print(line, end='')

def guess_encoding(csv_file):
    """guess the encoding of the given file"""
    with open(csv_file, "rb") as f:
        data = f.read(5)
    if data.startswith(b"\xEF\xBB\xBF"):  # UTF-8 with a "BOM" (normally no BOM in utf-8)
        return ["utf-8-sig"]
    try:
        with open(csv_file, encoding="utf-8") as f:
            preview = f.read(222222)
            return ["utf-8"]
    except:
        return [locale.getdefaultlocale()[1], "utf-8"]

def replace_in_file(filepath: Path, replacements: list[tuple[str, str]], filedest: Path = None, verbose=False):
    """
    Replaces strings in a file
    Args:
        filepath: Path to the file to modify.
        replacements: A list of tuples of ('old string 'new string')
        filedest: optional output file, otherwise will be filepath
    """
    the_encoding = guess_encoding(filepath)[0]
    with open(filepath, "r", encoding=the_encoding) as f:
        content = f.read()
    new_content = content
    for old_text, new_text in replacements:
        new_content = new_content.replace(old_text, new_text)
    outfile = filedest if filedest else filepath
    if new_content != content or str(outfile) != str(filepath):
        with open(outfile, "w", encoding=the_encoding) as f:
            f.write(new_content)
        if verbose:
            print(f"patched from {Path(filepath).name} into {outfile} !")

def patch_sourcefile(fname, in_text, out_text, silent_mode=False):
    """Replace a string in a source file."""
    if not silent_mode:
        print(f"patching {fname} from {in_text} to {out_text}")
    if Path(fname).is_file() and in_text != out_text:
        replace_in_file(Path(fname), [(in_text, out_text)])

def extract_archive(fname, targetdir=None, verbose=False):
    """Extract .zip, .exe or .tar.gz archive to a temporary directory.
    Return the temporary directory path"""
    targetdir = targetdir or create_temp_dir()
    Path(targetdir).mkdir(parents=True, exist_ok=True)
    if Path(fname).suffix in ('.zip', '.exe'):
        obj = zipfile.ZipFile(fname, mode="r")
    elif fname.endswith('.tar.gz'):
        obj = tarfile.open(fname, mode='r:gz')
    else:
        raise RuntimeError(f"Unsupported archive filename {fname}")
    obj.extractall(path=targetdir)
    return targetdir

def get_source_package_infos(fname):
    """Return a tuple (name, version) of the Python source package."""
    if fname.endswith('.whl'):
        return Path(fname).name.split("-")[:2]
    match = re.match(SOURCE_PATTERN, Path(fname).name)
    return match.groups()[:2] if match else None

def buildflit_wininst(root, python_exe=None, copy_to=None, verbose=False):
    """Build Wheel from Python package located in *root* with flit."""
    python_exe = python_exe or sys.executable
    cmd = [python_exe, '-m', 'flit', 'build']
    if verbose:
        subprocess.call(cmd, cwd=root)
    else:
        subprocess.Popen(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    distdir = Path(root) / 'dist'
    if not distdir.is_dir():
        raise RuntimeError(
            "Build failed: see package README file for further details regarding installation requirements.\n\n"
            "For more concrete debugging infos, please try to build the package from the command line:\n"
            "1. Open a WinPython command prompt\n"
            "2. Change working directory to the appropriate folder\n"
            "3. Type `python -m flit build`"
        )
    for distname in os.listdir(distdir):
        if re.match(SOURCE_PATTERN, distname) or re.match(WHEELBIN_PATTERN, distname):
            break
    else:
        raise RuntimeError(f"Build failed: not a pure Python package? {distdir}")

    src_fname = distdir / distname
    if copy_to:
        dst_fname = Path(copy_to) / distname
        shutil.move(src_fname, dst_fname)
        if verbose:
            print(f"Move: {src_fname} --> {dst_fname}")

def direct_pip_install(fname, python_exe=None, verbose=False, install_options=None):
    """Direct install via python -m pip !"""
    python_exe = python_exe or sys.executable
    myroot = Path(python_exe).parent
    cmd = [python_exe, "-m", "pip", "install"] + (install_options or []) + [fname]
    if not verbose:
        process = subprocess.Popen(cmd, cwd=myroot, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        the_log = f"{stdout}\n {stderr}"
        if " not find " in the_log or " not found " in the_log:
            print(f"Failed to Install: \n {fname} \n msg: {the_log}")
            raise RuntimeError
        process.stdout.close()
        process.stderr.close()
    else:
        subprocess.call(cmd, cwd=myroot)
        print(f"Installed {fname} via {' '.join(cmd)}")
    return fname

def do_script(this_script, python_exe=None, copy_to=None, verbose=False, install_options=None):
    """Execute a script (get-pip typically)."""
    python_exe = python_exe or sys.executable
    myroot = Path(python_exe).parent
    # cmd = [python_exe, myroot + r'\Scripts\pip-script.py', 'install']
    cmd = [python_exe] + (install_options or []) + ([this_script] if this_script else [])
    print("Executing ", cmd)
    if not verbose:
        subprocess.Popen(cmd, cwd=myroot, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    else:
        subprocess.call(cmd, cwd=myroot)
        print("Executed ", cmd)
    return 'ok'

def columns_width(list_of_lists):
    """Return the maximum string length of each column of a list of lists."""
    if not isinstance(list_of_lists, list):
        return [0]
    return [max(len(str(item)) for item in sublist) for sublist in zip(*list_of_lists)]

def formatted_list(list_of_list, full=False, max_width=70):
    """Format a list_of_list to fixed length columns."""
    columns_size = columns_width(list_of_list)
    columns = range(len(columns_size))
    return [list(line[col].ljust(columns_size[col])[:max_width] for col in columns) for line in list_of_list]

def normalize(this):
    """Apply PEP 503 normalization to the string."""
    return re.sub(r"[-_.]+", "-", this).lower()

if __name__ == '__main__':
    print_box("Test")
    dname = sys.prefix
    print((dname + ':', '\n', get_python_infos(dname)))

    tmpdir = r'D:\Tests\winpython_tests'
    Path(tmpdir).mkdir(parents=True, exist_ok=True)
    print(extract_archive(str(Path(r'D:\WinP\bd37') / 'packages.win-amd64' / 'python-3.7.3.amd64.zip'), tmpdir))
