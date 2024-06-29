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
from pathlib import Path
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
import io
import configparser as cp

# Local imports
import winreg

def get_python_executable(path = None):
    """return the python executable"""
    my_path = sys.executable if path == None else path  # default = current one
    my_path = my_path if Path(my_path).is_dir() else str(Path(my_path).parent)
    exec_py = str(Path(my_path) / 'python.exe')
    exec_pypy = str(Path(my_path) / 'pypy3.exe')  # PyPy !
    # PyPy >=7.3.6 3.8 aligns to python.exe and Lib\site-packages
    python_executable = exec_py if Path(exec_py).is_file() else exec_pypy
    return python_executable

def get_site_packages_path(path = None):
    """return the python site-packages"""
    my_path = sys.executable if path == None else path  # default = current one
    my_path = my_path if Path(my_path).is_dir() else str(Path(my_path).parent)
    site_py = str(Path(my_path) / 'Lib' / 'site-packages')
    site_pypy = str(Path(my_path) / 'site-packages')  # PyPy !!
    site_packages_path = site_pypy if Path(site_pypy).is_dir() else site_py
    return site_packages_path

def onerror(function, path, excinfo):
    """Error handler for `shutil.rmtree`.

    If the error is due to an access error (read-only file), it
    attempts to add write permission and then retries.
    If the error is for another reason, it re-raises the error.

    Usage: `shutil.rmtree(path, onexc=onerror)"""
    if not os.access(path, os.W_OK):
        # Is the error an access error?
        os.chmod(path, stat.S_IWUSR)
        function(path)
    else:
        raise


#==============================================================================
# https://stackoverflow.com/questions/580924/how-to-access-a-files-properties-on-windows
def getFileProperties(fname):
#==============================================================================
    """
    Read all properties of the given file return them as a dictionary.
    """
    import win32api
    propNames = ('Comments', 'InternalName', 'ProductName',
        'CompanyName', 'LegalCopyright', 'ProductVersion',
        'FileDescription', 'LegalTrademarks', 'PrivateBuild',
        'FileVersion', 'OriginalFilename', 'SpecialBuild')

    props = {'FixedFileInfo': None, 'StringFileInfo': None, 'FileVersion': None}

    try:
        # backslash as parm returns dictionary of numeric info corresponding to VS_FIXEDFILEINFO struc
        fixedInfo = win32api.GetFileVersionInfo(fname, '\\')
        props['FixedFileInfo'] = fixedInfo
        props['FileVersion'] = "%d.%d.%d.%d" % (fixedInfo['FileVersionMS'] / 65536,
                fixedInfo['FileVersionMS'] % 65536, fixedInfo['FileVersionLS'] / 65536,
                fixedInfo['FileVersionLS'] % 65536)

        # \VarFileInfo\Translation returns list of available (language, codepage)
        # pairs that can be used to retreive string info. We are using only the first pair.
        lang, codepage = win32api.GetFileVersionInfo(fname, '\\VarFileInfo\\Translation')[0]

        # any other must be of the form \StringfileInfo\%04X%04X\parm_name, middle
        # two are language/codepage pair returned from above

        strInfo = {}
        for propName in propNames:
            strInfoPath = u'\\StringFileInfo\\%04X%04X\\%s' % (lang, codepage, propName)
            ## print str_info
            strInfo[propName] = win32api.GetFileVersionInfo(fname, strInfoPath)

        props['StringFileInfo'] = strInfo
    except:
        pass

    return props
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
            return shell.SHGetSpecialFolderPath(
                0, csidl, False
            )
    raise ValueError(
        f"{path_name} is an unknown path ID"
    )


def get_winpython_start_menu_folder(current=True):
    """Return WinPython Start menu shortcuts folder"""
    if current:
        # non-admin install - always goes in this user's start menu.
        folder = get_special_folder_path("CSIDL_PROGRAMS")
    else:
        try:
            folder = get_special_folder_path(
                "CSIDL_COMMON_PROGRAMS"
            )
        except OSError:
            # No CSIDL_COMMON_PROGRAMS on this platform
            folder = get_special_folder_path(
                "CSIDL_PROGRAMS"
            )
    return str(Path(folder) / 'WinPython')

def remove_winpython_start_menu_folder(current=True):
    """Remove WinPython Start menu folder -- remove it if it already exists"""
    path = get_winpython_start_menu_folder(current=current)
    if Path(path).is_dir():
        try:
            shutil.rmtree(path, onexc=onerror)
        except WindowsError:
            print(
                f"Directory {path} could not be removed",
                file=sys.stderr,
            )

def create_winpython_start_menu_folder(current=True):
    """Create WinPython Start menu folder -- remove it if it already exists"""
    path = get_winpython_start_menu_folder(current=current)
    if Path(path).is_dir():
        try:
            shutil.rmtree(path, onexc=onerror)
        except WindowsError:
            print(
                f"Directory {path} could not be removed",
                file=sys.stderr,
            )
    # create, or re-create !
    os.mkdir(path)
    return path


def create_shortcut(
    path,
    description,
    filename,
    arguments="",
    workdir="",
    iconpath="",
    iconindex=0,
    verbose=True,
):
    """Create Windows shortcut (.lnk file)"""
    import pythoncom
    from win32com.shell import shell

    ilink = pythoncom.CoCreateInstance(
        shell.CLSID_ShellLink,
        None,
        pythoncom.CLSCTX_INPROC_SERVER,
        shell.IID_IShellLink,
    )
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
        print ("a fail !")
        pass


# =============================================================================
# Misc.
# =============================================================================


def print_box(text):
    """Print text in a box"""
    line0 = "+" + ("-" * (len(text) + 2)) + "+"
    line1 = "| " + text + " |"
    print(
        ("\n\n" + "\n".join([line0, line1, line0]) + "\n")
    )


def is_python_distribution(path):
    """Return True if path is a Python distribution"""
    # XXX: This test could be improved but it seems to be sufficient
    has_exec = Path(get_python_executable(path)).is_file()
    has_site = Path(get_site_packages_path(path)).is_dir()    
    return has_exec and has_site


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
    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=path,
        shell=True
    )
    return decode_fs_string(process.stdout.read())

def exec_run_cmd(args, path=None):
    """run a single command (*args* is a list of arguments) in optional *path*"""
    # only applicable to Python-3.5+
    # python-3.7+ allows to replace "stdout and stderr ", per "capture_output=True"
    if path:
        process = subprocess.run(args,
                                capture_output=True,
                                cwd=path, text=True)
        #return  decode_fs_string(process.stdout)
        return  process.stdout
    else:
        process = subprocess.run(args,
                                capture_output=True,
                                cwd=path, text=True)
        #return  decode_fs_string(process.stdout)
        return  process.stdout


def get_r_version(path):
    """Return version of the R installed in *path*"""
    return (
        exec_shell_cmd('dir ..\README.R*', path)
        .splitlines()[-3]
        .split("-")[-1]
    )


def get_julia_version(path):
    """Return version of the Julia installed in *path*"""
    return (
        exec_shell_cmd('julia.exe -v', path)
        .splitlines()[0]
        .split(" ")[-1]
    )


def get_nodejs_version(path):
    """Return version of the Nodejs installed in *path*"""
    return exec_shell_cmd('node -v', path).splitlines()[0]


def get_npmjs_version(path):
    """Return version of the Nodejs installed in *path*"""
    return exec_shell_cmd('npm -v', path).splitlines()[0]


def get_pandoc_version(path):
    """Return version of the Pandoc executable in *path*"""
    return (
        exec_shell_cmd('pandoc -v', path)
        .splitlines()[0]
        .split(" ")[-1]
    )


def python_query(cmd, path):
    """Execute Python command using the Python interpreter located in *path*"""
    the_exe = get_python_executable(path)
    # debug2021-09-12
    # print(f'"{the_exe}" -c "{cmd}"', ' * ',  path)
    return exec_shell_cmd(f'"{the_exe}" -c "{cmd}"', path).splitlines()[0]

def python_execmodule(cmd, path):
    """Execute Python command using the Python interpreter located in *path*"""
    the_exe = get_python_executable(path)
    exec_shell_cmd(f'{the_exe} -m {cmd}', path)


def get_python_infos(path):
    """Return (version, architecture) for the Python distribution located in
    *path*. The version number is limited to MAJOR.MINOR, the architecture is
    an integer: 32 or 64"""
    is_64 = python_query(
        'import sys; print(sys.maxsize > 2**32)', path
    )
    arch = {'True': 64, 'False': 32}.get(is_64, None)
    ver = python_query(
        "import sys;print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        ,
        path,
    )
    if re.match(r'([0-9]*)\.([0-9]*)', ver) is None:
        ver = None
  
    return ver, arch


def get_python_long_version(path):
    """Return long version (X.Y.Z) for the Python distribution located in
    *path*"""
    ver = python_query(
        "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
        ,
        path,
    )
    if (
        re.match(r'([0-9]*)\.([0-9]*)\.([0-9]*)', ver)
        is None
    ):
        ver = None
    return ver


# =============================================================================
# Patch chebang line (courtesy of Christoph Gohlke)
# =============================================================================
def patch_shebang_line(
    fname, pad=b' ', to_movable=True, targetdir=""
):
    """Remove absolute path to python.exe in shebang lines, or re-add it"""

    import re
    import sys
    import os

    target_dir = targetdir  # movable option
    if to_movable == False:
        target_dir = os.path.abspath(os.path.dirname(fname))
        target_dir = (
            os.path.abspath(os.path.join(target_dir, r'..'))
            + '\\'
        )
    executable = sys.executable
    if sys.version_info[0] == 2:
        shebang_line = re.compile(
            r"(#!.*pythonw?\.exe)"
        )  # Python2.7
    else:
        shebang_line = re.compile(
            b"(#!.*pythonw?\.exe)"
        )  # Python3+
        if 'pypy3' in sys.executable:
            shebang_line = re.compile(
            b"(#!.*pypy3w?\.exe)"
        )  # Pypy3+
            
        target_dir = target_dir.encode('utf-8')
    with open(fname, 'rb') as fh:
        initial_content = fh.read()
        fh.close
        fh = None
    content = shebang_line.split(
        initial_content, maxsplit=1
    )
    if len(content) != 3:
        return
    exe = os.path.basename(content[1][2:])
    content[1] = (
        b'#!' + target_dir + exe
    )  # + (pad * (len(content[1]) - len(exe) - 2))
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
def patch_shebang_line_py(
    fname, to_movable=True, targetdir=""
):
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
        if 'pypy3' in sys.executable:  # PyPy !
            exec_path = '#!.\pypy3.exe'
    else:
        exec_path = '#!' + sys.executable
    for line in fileinput.input(fname, inplace=True):
        if re.match('^#\!.*python\.exe$', line) is not None:
            print(exec_path)
        elif re.match('^#\!.*pypy3\.exe$', line) is not None:# PyPy !
            print(exec_path)          
        else:
            print(line, end='')


# =============================================================================
# Guess encoding (shall rather be utf-8 per default)
# =============================================================================
def guess_encoding(csv_file):
    """guess the encoding of the given file"""
    # UTF_8_BOM = "\xEF\xBB\xBF"
    # Python behavior on UTF-16 not great on write, so we drop it
    with io.open(csv_file, "rb") as f:
        data = f.read(5)
    if data.startswith(b"\xEF\xBB\xBF"):  # UTF-8 with a "BOM" (normally no BOM in utf-8)
        return ["utf-8-sig"]
    else:  # in Windows, guessing utf-8 doesn't work, so we have to try
        try:
            with io.open(csv_file, encoding="utf-8") as f:
                preview = f.read(222222)
                return ["utf-8"]
        except:
            return [locale.getdefaultlocale()[1], "utf-8"]
            
# =============================================================================
# Patch sourcefile (instead of forking packages)
# =============================================================================
def patch_sourcefile(
    fname, in_text, out_text, silent_mode=False
):
    """Replace a string in a source file"""
    import io

    if Path(fname).is_file() and not in_text == out_text:
        the_encoding = guess_encoding(fname)[0]
        with io.open(fname, 'r', encoding=the_encoding) as fh:
            content = fh.read()
        new_content = content.replace(in_text, out_text)
        if not new_content == content:
            if not silent_mode:
                print(
                    "patching ",
                    fname,
                    "from",
                    in_text,
                    "to",
                    out_text,
                )
            with io.open(fname, 'wt', encoding=the_encoding) as fh:
                fh.write(new_content)


# =============================================================================
# Patch sourcelines (instead of forking packages)
# =============================================================================
def patch_sourcelines(
    fname,
    in_line_start,
    out_line,
    endline='\n',
    silent_mode=False,
):
    """Replace the middle of lines between in_line_start and endline """
    import io

    if Path(fname).is_file():
        the_encoding = guess_encoding(fname)[0]
        with io.open(fname, 'r', encoding=the_encoding) as fh:
            contents = fh.readlines()
            content = "".join(contents)
            for l in range(len(contents)):
                if contents[l].startswith(in_line_start):
                    begining, middle = (
                        in_line_start,
                        contents[l][len(in_line_start) :],
                    )
                    ending = ""
                    if middle.find(endline) > 0:
                        ending = endline + endline.join(
                            middle.split(endline)[1:]
                        )
                        middle = middle.split(endline)[0]
                    middle = out_line
                    new_line = begining + middle + ending
                    if not new_line == contents[l]:
                        if not silent_mode:
                            print(
                                "patching ",
                                fname,
                                " from\n",
                                contents[l],
                                "\nto\n",
                                new_line,
                            )
                    contents[l] = new_line
            new_content = "".join(contents)
        if not new_content == content:
            # if not silent_mode:
            #    print("patching ", fname, "from", content, "to", new_content)
            with io.open(fname, 'wt', encoding=the_encoding) as fh:
                try:
                    fh.write(new_content)
                except:
                    print(
                        "impossible to patch",
                        fname,
                        "from",
                        content,
                        "to",
                        new_content,
                    )


# =============================================================================
# Extract functions
# =============================================================================
def _create_temp_dir():
    """Create a temporary directory and remove it at exit"""
    tmpdir = tempfile.mkdtemp(prefix='wppm_')
    atexit.register(
        lambda path: shutil.rmtree(path, onexc=onerror),
        tmpdir,
    )
    return tmpdir


def extract_archive(fname, targetdir=None, verbose=False):
    """Extract .zip, .exe (considered to be a zip archive) or .tar.gz archive
    to a temporary directory (if targetdir is None).
    Return the temporary directory path"""
    if targetdir is None:
        targetdir = _create_temp_dir()
    else:
        try:
            os.mkdir(targetdir)
        except:
            pass
    if Path(fname).suffix in ('.zip', '.exe'):
        obj = zipfile.ZipFile(fname, mode="r")
    elif fname.endswith('.tar.gz'):
        obj = tarfile.open(fname, mode='r:gz')
    else:
        raise RuntimeError(
            f"Unsupported archive filename {fname}"
        )
    obj.extractall(path=targetdir)
    return targetdir

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
    if fname[-4:] == '.whl':
        return Path(fname).name.split("-")[:2]
    match = re.match(SOURCE_PATTERN, Path(fname).name)
    if match is not None:
        return match.groups()[:2]


def buildflit_wininst(
    root,
    python_exe=None,
    copy_to=None,
    verbose=False,
):
    """Build Wheel from Python package located in *root*
    with flit"""
    if python_exe is None:
        python_exe = sys.executable
    assert Path(python_exe).is_file()
    cmd = [python_exe, '-m' ,'flit', 'build']

    # root = a tmp dir in windows\tmp,
    if verbose:
        subprocess.call(cmd, cwd=root)
    else:
        p = subprocess.Popen(
            cmd,
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        p.communicate()
        p.stdout.close()
        p.stderr.close()
    distdir = str(Path(root) / 'dist')
    if not Path(distdir).is_dir():
        raise RuntimeError(
            "Build failed: see package README file for further"
            " details regarding installation requirements.\n\n"
            "For more concrete debugging infos, please try to build "
            "the package from the command line:\n"
            "1. Open a WinPython command prompt\n"
            "2. Change working directory to the appropriate folder\n"
            "3. Type `python -m filt build`"
        )

    for distname in os.listdir(distdir):
        # for wheels (winpython here)
        match = re.match(SOURCE_PATTERN, distname)
        if match is not None:
            break
        match = re.match(WHEELBIN_PATTERN, distname)
        if match is not None:
            break
    else:
        raise RuntimeError(
            f"Build failed: not a pure Python package? {distdir}"
        )
    src_fname = str(Path(distdir) / distname)
    if copy_to is None:
        return src_fname
    else:
        dst_fname = str(Path(copy_to) / distname)
        shutil.move(src_fname, dst_fname)
        if verbose:
            print(
                (
                    f"Move: {src_fname} --> {dst_fname}"
                )
            )
            # remove tempo dir 'root' no more needed
            shutil.rmtree(root, onexc=onerror)
        return dst_fname


def direct_pip_install(
    fname,
    python_exe=None,
    verbose=False,
    install_options=None,
):
    """Direct install via python -m pip !"""
    copy_to = str(Path(fname).parent)

    if python_exe is None:
        python_exe = sys.executable
    assert Path(python_exe).is_file()
    myroot = str(Path(python_exe).parent)

    cmd = [python_exe, '-m', 'pip', 'install']
    if install_options:
        cmd += install_options  # typically ['--no-deps']
        print('python -m pip install_options', install_options)
    cmd += [fname]

    if verbose:
        subprocess.call(cmd, cwd=myroot)
    else:
        p = subprocess.Popen(
            cmd,
            cwd=myroot,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()
        the_log = f"{stdout}" + f"\n {stderr}"

        if (
            ' not find ' in the_log
            or ' not found ' in the_log
        ):
            print(f"Failed to Install: \n {fname} \n")
            print(f"msg: {the_log}")
            raise RuntimeError
        p.stdout.close()
        p.stderr.close()
    src_fname = fname
    if copy_to is None:
        return src_fname
    else:
        if verbose:
            print(f"Installed {src_fname}")
        return src_fname


def do_script(
    this_script,
    python_exe=None,
    copy_to=None,
    verbose=False,
    install_options=None,
):
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
        p = subprocess.Popen(
            cmd,
            cwd=myroot,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        p.communicate()
        p.stdout.close()
        p.stderr.close()
    if verbose:
        print("Executed " , cmd)
    return 'ok'

def columns_width(list_of_lists):
        """return the maximum string length of each column of a list of list"""
        if not isinstance(list_of_lists, list):
            return [0]
 
        # Transpose the list of lists using zip
        transposed_lists = list(zip(*list_of_lists))
        # Calculate the maximum width for each column
        column_widths = [max(len(str(item)) for item in sublist) for sublist in transposed_lists]
        return column_widths

def formatted_list(list_of_list, full=False, max_width=70):
        """format a list_of_list to fix length columns"""
        columns_size = columns_width(list_of_list)
        nb_columns = len(columns_size)

        # normalize each columns to columns_size[col] width, in the limit of max_width
        
        zz = [
            list(
                line[col].ljust(columns_size[col])[:max_width] for col in range(nb_columns)
            )
            for line in list_of_list
        ]
        return zz

def normalize(this):
    """apply https://peps.python.org/pep-0503/#normalized-names"""
    return re.sub(r"[-_.]+", "-", this).lower()

def get_package_metadata(database, name, update=False, suggested_summary=None):
    """Extract infos (description, url) from the local database"""
    # for package.ini safety belt
    # Note: we could use the PyPI database but this has been written on
    # machine which is not connected to the internet
    # we store only  normalized names now (PEP 503)
    DATA_PATH = str(Path(sys.modules['winpython'].__file__).parent /'data')
    db = cp.ConfigParser()
    filepath = Path(database) if Path(database).is_absolute() else Path(DATA_PATH) / database
    try:
        db.read_file(open(str(filepath), encoding = 'utf-8'))
    except:
        db.read_file(open(str(filepath)))
    my_metadata = dict(
        description="",
        url="https://pypi.org/project/" + name,
    )
    for key in my_metadata:
        # wheel replace '-' per '_' in key
        for name2 in (name, normalize(name)):
            try:
                my_metadata[key] = db.get(name2, key)
                break
            except (cp.NoSectionError, cp.NoOptionError):
                pass
    db_desc = my_metadata.get("description")

    if my_metadata.get("description") == "" and suggested_summary:
        # nothing in package.ini, we look in our installed packages
        try:
            my_metadata["description"] = (
                suggested_summary + "\n"
            ).splitlines()[0]
        except:
            pass

    if update == True and db_desc == "" and my_metadata["description"] != "":
        # we add new findings in our packgages.ini list, if it's required
        try:
            db[normalize(name)] = {}
            db[normalize(name)]["description"] = my_metadata["description"]
            with open(str(Path(DATA_PATH) / database), "w",  encoding='UTF-8') as configfile:
                db.write(configfile)
        except:
            pass
    return my_metadata


if __name__ == '__main__':

    print_box("Test")
    dname = sys.prefix
    print((dname + ':', '\n', get_python_infos(dname)))
    # dname = r'E:\winpython\sandbox\python-2.7.3'
    # print dname+':', '\n', get_python_infos(dname)

    tmpdir = r'D:\Tests\winpython_tests'
    if not Path(tmpdir).is_dir():
        os.mkdir(tmpdir)
    print(
        (
            extract_archive(
                str(Path(r'D:\WinP\bd37') / 'packages.win-amd64' /
                    'python-3.7.3.amd64.zip'),        
                tmpdir,
            )    
        )
    )
