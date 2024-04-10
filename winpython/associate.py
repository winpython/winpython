# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
Register a Python distribution

Created on Tue Aug 21 21:46:30 2012
"""

import sys
import os
from pathlib import Path
import platform
import importlib

#  import subprocess


# Local imports
import winreg
from winpython import utils

KEY_C = r"Software\Classes\%s"
KEY_C0 = KEY_C % r"Python.%sFile\shell"
KEY_C1 = KEY_C % r"Python.%sFile\shell\%s"
KEY_C2 = KEY_C1 + r"\command"
KEY_DROP0 = KEY_C % r"Python.%sFile\shellex"
KEY_DROP1 = KEY_C % r"Python.%sFile\shellex\DropHandler"
KEY_I = KEY_C % r"Python.%sFile\DefaultIcon"
KEY_D = KEY_C % r"Python.%sFile"
EWI = "Edit with IDLE"
EWS = "Edit with Spyder"

KEY_S = r"Software\Python"
KEY_S0 = KEY_S + r"\WinPython" # was PythonCore before PEP-0514
KEY_S1 = KEY_S0 + r"\%s"

def _remove_start_menu_folder(target, current=True):
    "remove menu Folder for target WinPython"
    import importlib.util
    win32com_exists = importlib.util.find_spec('win32com') is not None

    # we return nothing if no win32com package
    if win32com_exists:
        utils.remove_winpython_start_menu_folder(current=current)

def _get_shortcut_data(target, current=True):
    "get windows menu access, if win32com exists otherwise nothing"
    import importlib.util
    win32com_exists = importlib.util.find_spec('win32com') is not None

    # we return nothing if no win32com package
    if not win32com_exists:
        return []
    wpgroup = utils.create_winpython_start_menu_folder(current=current)
    wpdir = str(Path(target).parent)
    data = []
    for name in os.listdir(wpdir):
        bname, ext = Path(name).stem, Path(name).suffix
        if ext == ".exe":
            data.append(
                (
                    str(Path(wpdir) / name),
                    bname,
                    str(Path(wpgroup) / bname),
                )
            )
    return data


def register(target, current=True, verbose=True):
    """Register a Python distribution in Windows registry"""
    root = winreg.HKEY_CURRENT_USER if current else winreg.HKEY_LOCAL_MACHINE

    # Creating Registry entries
    if verbose:
        print(f'Creating WinPython registry entries for {target}')
    # Extensions
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_C % ".py"),
        "",
        0,
        winreg.REG_SZ,
        "Python.File",
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_C % ".pyw"),
        "",
        0,
        winreg.REG_SZ,
        "Python.NoConFile",
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_C % ".pyc"),
        "",
        0,
        winreg.REG_SZ,
        "Python.CompiledFile",
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_C % ".pyo"),
        "",
        0,
        winreg.REG_SZ,
        "Python.CompiledFile",
    )

    # MIME types
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_C % ".py"),
        "Content Type",
        0,
        winreg.REG_SZ,
        "text/plain",
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_C % ".pyw"),
        "Content Type",
        0,
        winreg.REG_SZ,
        "text/plain",
    )

    # Verbs
    python = str((Path(target) / "python.exe").resolve())
    pythonw = str((Path(target) / "pythonw.exe").resolve())
    spyder = str((Path(target).parent / "Spyder.exe").resolve())

    if not Path(spyder).is_file():
        spyder = f'{pythonw}" "{target}\Scripts\spyder'
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_C2 % ("", "open")),
        "",
        0,
        winreg.REG_SZ,
        '"%s" "%%1" %%*' % python,
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_C2 % ("NoCon", "open")),
        "",
        0,
        winreg.REG_SZ,
        '"%s" "%%1" %%*' % pythonw,
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_C2 % ("Compiled", "open")),
        "",
        0,
        winreg.REG_SZ,
        '"%s" "%%1" %%*' % python,
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_C2 % ("", EWI)),
        "",
        0,
        winreg.REG_SZ,
        '"%s" "%s\Lib\idlelib\idle.pyw" -n -e "%%1"' % (pythonw, target),
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_C2 % ("NoCon", EWI)),
        "",
        0,
        winreg.REG_SZ,
        '"%s" "%s\Lib\idlelib\idle.pyw" -n -e "%%1"' % (pythonw, target),
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_C2 % ("", EWS)),
        "",
        0,
        winreg.REG_SZ,
        '"%s" "%%1"' % spyder,
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_C2 % ("NoCon", EWS)),
        "",
        0,
        winreg.REG_SZ,
        '"%s" "%%1"' % spyder,
    )

    # Drop support
    handler = "{60254CA5-953B-11CF-8C96-00AA00B8708C}"
    for ftype in ("", "NoCon", "Compiled"):
        winreg.SetValueEx(
            winreg.CreateKey(root, KEY_DROP1 % ftype),
            "",
            0,
            winreg.REG_SZ,
            handler,
        )
    # Icons
    dlls = str(Path(target) / "DLLs")
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_I % ""),
        "",
        0,
        winreg.REG_SZ,
        r"%s\py.ico" % dlls,
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_I % "NoCon"),
        "",
        0,
        winreg.REG_SZ,
        r"%s\py.ico" % dlls,
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_I % "Compiled"),
        "",
        0,
        winreg.REG_SZ,
        r"%s\pyc.ico" % dlls,
    )

    # Descriptions
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_D % ""),
        "",
        0,
        winreg.REG_SZ,
        "Python File",
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_D % "NoCon"),
        "",
        0,
        winreg.REG_SZ,
        "Python File (no console)",
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, KEY_D % "Compiled"),
        "",
        0,
        winreg.REG_SZ,
        "Compiled Python File",
    )

    # PythonCore entries
    python_infos = utils.get_python_infos(target)  #   ('3.11', 64)
    short_version = python_infos[0]  # 3.11 from ('3.11', 64)
    long_version = utils.get_python_long_version(target)  # 3.11.5
    key_core = (KEY_S1 % short_version) + r"\%s"  # Winpython\3.11
    
    # PEP-0514 additions, with standard Python practice
    SupportUrl="https://winpython.github.io"
    SysArchitecture = platform.architecture()[0]  # '64bit'
    SysVersion = '.'.join(platform.python_version_tuple()[:2])  # '3.11' 
    Version = platform.python_version()  # '3.11.5'

    # But keep consistent with past possibilities until more alignement
    SysArchitecture = f'{python_infos[1]}bit' # '64bit'
    SysVersion = short_version
    Version = long_version

    DisplayName = f'Python {Version} ({SysArchitecture})'
    key_short = (KEY_S1 % short_version) # WinPython\3.11
    key_keys={'DisplayName':DisplayName,
               'SupportUrl':SupportUrl,
               'SysVersion':SysVersion,
               'SysArchitecture':SysArchitecture,
               'Version':Version}

    regkey = winreg.CreateKey(root, key_short)
    # see https://www.programcreek.com/python/example/106949/winreg.CreateKey
    # winreg.SetValueEx(key, '', reg.REG_SZ, '')
    for k, v in key_keys.items():
        winreg.SetValueEx(
            regkey,
            k,
            0,
            winreg.REG_SZ,
            v,
        )
    winreg.CloseKey(regkey)    
   
    # pep-0514 additions at InstallPathLevel
    ExecutablePath = python
    WindowedExecutablePath = pythonw
    
    key_short = key_core % "InstallPath" # WinPython\3.11\InstallPath
    key_keys={'ExecutablePath':ExecutablePath,
               'WindowedExecutablePath':WindowedExecutablePath}
    
    regkey = winreg.CreateKey(root, key_core % "InstallPath")
    winreg.SetValueEx(
        regkey,
        "",
        0,
        winreg.REG_SZ,
        target + '\\',
    )
    for k, v in key_keys.items():
        winreg.SetValueEx(
            regkey,
            k,
            0,
            winreg.REG_SZ,
            v,
        )
    winreg.CloseKey(regkey)

    
    
    winreg.SetValueEx(
        winreg.CreateKey(root, key_core % r"InstallPath\InstallGroup"),
        "",
        0,
        winreg.REG_SZ,
        "Python %s" % short_version,
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, key_core % "Modules"),
        "",
        0,
        winreg.REG_SZ,
        "",
    )
    winreg.SetValueEx(
        winreg.CreateKey(root, key_core % "PythonPath"),
        "",
        0,
        winreg.REG_SZ,
        r"%s\Lib;%s\DLLs" % (target, target),
    )
    winreg.SetValueEx(
        winreg.CreateKey(
            root,
            key_core % r"Help\Main Python Documentation",
        ),
        "",
        0,
        winreg.REG_SZ,
        r"%s\Doc\python%s.chm" % (target, long_version),
    )

    # Create start menu entries for all WinPython launchers
    spec = importlib.util.find_spec('pythoncom')
    if verbose and spec is None:
        print(f"Can't create WinPython menu as pywin32 package is not installed")
    if verbose and spec is not None:
        print(f'Creating WinPython menu for all icons in {target}')
    for path, desc, fname in _get_shortcut_data(target, current=current):
        utils.create_shortcut(path, desc, fname, verbose=verbose)


def unregister(target, current=True, verbose=True):
    """Unregister a Python distribution in Windows registry"""
    # Removing Registry entries
    if verbose:
        print(f'Removing WinPython registry entries for {target}')
    root = winreg.HKEY_CURRENT_USER if current else winreg.HKEY_LOCAL_MACHINE
    short_version = utils.get_python_infos(target)[0]
    key_core = (KEY_S1 % short_version) + r"\%s"
    for key in (
        # Drop support
        KEY_DROP1 % "",
        KEY_DROP1 % "NoCon",
        KEY_DROP1 % "Compiled",
        KEY_DROP0 % "",
        KEY_DROP0 % "NoCon",
        KEY_DROP0 % "Compiled",
        # Icons
        KEY_I % "NoCon",
        KEY_I % "Compiled",
        KEY_I % "",
        # Edit with IDLE
        KEY_C2 % ("", EWI),
        KEY_C2 % ("NoCon", EWI),
        KEY_C1 % ("", EWI),
        KEY_C1 % ("NoCon", EWI),
        # Edit with Spyder
        KEY_C2 % ("", EWS),
        KEY_C2 % ("NoCon", EWS),
        KEY_C1 % ("", EWS),
        KEY_C1 % ("NoCon", EWS),
        # Verbs
        KEY_C2 % ("", "open"),
        KEY_C2 % ("NoCon", "open"),
        KEY_C2 % ("Compiled", "open"),
        KEY_C1 % ("", "open"),
        KEY_C1 % ("NoCon", "open"),
        KEY_C1 % ("Compiled", "open"),
        KEY_C0 % "",
        KEY_C0 % "NoCon",
        KEY_C0 % "Compiled",
        # Descriptions
        KEY_D % "NoCon",
        KEY_D % "Compiled",
        KEY_D % "",
        # PythonCore
        key_core % r"InstallPath\InstallGroup",
        key_core % "InstallPath",
        key_core % "Modules",
        key_core % "PythonPath",
        key_core % r"Help\Main Python Documentation",
        key_core % "Help",
        KEY_S1 % short_version,
        KEY_S0,
        KEY_S,
    ):
        try:
            if verbose:
                print(key)
            winreg.DeleteKey(root, key)
        except WindowsError:
            rootkey = "HKEY_CURRENT_USER" if current else "HKEY_LOCAL_MACHINE"
            if verbose:
                print(
                r"Unable to remove %s\%s" % (rootkey, key),
                file=sys.stderr,
            )
    # remove menu shortcuts
    spec = importlib.util.find_spec('pythoncom')
    if verbose and spec is None:
        print(f"Can't remove WinPython menu as pywin32 package is not installed")
    if verbose and spec is not None:
        print(f'Removing WinPython menu for all icons in {target}')
    _remove_start_menu_folder(target, current=current)
    
    #for path, desc, fname in _get_shortcut_data(target, current=current):
    #    if Path(fname).exists():
    #        os.remove(fname)


if __name__ == "__main__":
    register(sys.prefix)
    unregister(sys.prefix)