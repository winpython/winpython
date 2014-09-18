# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
Register a Python distribution

Created on Tue Aug 21 21:46:30 2012
"""

from __future__ import print_function

import sys
import os
import os.path as osp
import subprocess


# Local imports
from winpython.py3compat import winreg
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
KEY_S0 = KEY_S + r"\PythonCore"
KEY_S1 = KEY_S0 + r"\%s"


def _get_shortcut_data(target, current=True):
    wpgroup = utils.create_winpython_start_menu_folder(current=current)
    wpdir = osp.join(target, os.pardir)
    data = []
    for name in os.listdir(wpdir):
        bname, ext = osp.splitext(name)
        if ext == '.exe':
            data.append((osp.join(wpdir, name),
                         bname,
                         osp.join(wpgroup, bname)))
    return data


def register(target, current=True):
    """Register a Python distribution in Windows registry"""
    root = winreg.HKEY_CURRENT_USER if current else winreg.HKEY_LOCAL_MACHINE

    # Extensions
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C % ".py"),
                      "", 0, winreg.REG_SZ, "Python.File")
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C % ".pyw"),
                      "", 0, winreg.REG_SZ, "Python.NoConFile")
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C % ".pyc"),
                      "", 0, winreg.REG_SZ, "Python.CompiledFile")
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C % ".pyo"),
                      "", 0, winreg.REG_SZ, "Python.CompiledFile")

    # MIME types
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C % ".py"),
                      "Content Type", 0, winreg.REG_SZ, "text/plain")
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C % ".pyw"),
                      "Content Type", 0, winreg.REG_SZ, "text/plain")

    # Verbs
    python = osp.abspath(osp.join(target, 'python.exe'))
    pythonw = osp.abspath(osp.join(target, 'pythonw.exe'))
    spyder = osp.abspath(osp.join(target, os.pardir, 'Spyder.exe'))
    if not osp.isfile(spyder):
        spyder = '%s" "%s\Scripts\spyder' % (pythonw, target)
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C2 % ("", "open")),
                      "", 0, winreg.REG_SZ, '"%s" "%%1" %%*' % python)
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C2 % ("NoCon", "open")),
                      "", 0, winreg.REG_SZ, '"%s" "%%1" %%*' % pythonw)
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C2 % ("Compiled", "open")),
                      "", 0, winreg.REG_SZ, '"%s" "%%1" %%*' % python)
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C2 % ("", EWI)),
                      "", 0, winreg.REG_SZ,
                      '"%s" "%s\Lib\idlelib\idle.pyw" -n -e "%%1"'
                      % (pythonw, target))
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C2 % ("NoCon", EWI)),
                      "", 0, winreg.REG_SZ,
                      '"%s" "%s\Lib\idlelib\idle.pyw" -n -e "%%1"'
                      % (pythonw, target))
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C2 % ("", EWS)),
                      "", 0, winreg.REG_SZ, '"%s" "%%1"' % spyder)
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C2 % ("NoCon", EWS)),
                      "", 0, winreg.REG_SZ, '"%s" "%%1"' % spyder)

    # Drop support
    handler = "{60254CA5-953B-11CF-8C96-00AA00B8708C}"
    for ftype in ("", "NoCon", "Compiled"):
        winreg.SetValueEx(winreg.CreateKey(root, KEY_DROP1 % ftype),
                          "", 0, winreg.REG_SZ, handler)

    # Icons
    dlls = osp.join(target, 'DLLs')
    winreg.SetValueEx(winreg.CreateKey(root, KEY_I % ""),
                      "", 0, winreg.REG_SZ, r'%s\py.ico' % dlls)
    winreg.SetValueEx(winreg.CreateKey(root, KEY_I % "NoCon"),
                      "", 0, winreg.REG_SZ, r'%s\py.ico' % dlls)
    winreg.SetValueEx(winreg.CreateKey(root, KEY_I % "Compiled"),
                      "", 0, winreg.REG_SZ, r'%s\pyc.ico' % dlls)

    # Descriptions
    winreg.SetValueEx(winreg.CreateKey(root, KEY_D % ""),
                      "", 0, winreg.REG_SZ, "Python File")
    winreg.SetValueEx(winreg.CreateKey(root, KEY_D % "NoCon"),
                      "", 0, winreg.REG_SZ, "Python File (no console)")
    winreg.SetValueEx(winreg.CreateKey(root, KEY_D % "Compiled"),
                      "", 0, winreg.REG_SZ, "Compiled Python File")

    # PythonCore entries
    short_version = utils.get_python_infos(target)[0]
    long_version = utils.get_python_long_version(target)
    key_core = (KEY_S1 % short_version) + r'\%s'
    winreg.SetValueEx(winreg.CreateKey(root, key_core % 'InstallPath'),
                      "", 0, winreg.REG_SZ, target)
    winreg.SetValueEx(winreg.CreateKey(root,
                                       key_core % r'InstallPath\InstallGroup'),
                      "", 0, winreg.REG_SZ, "Python %s" % short_version)
    winreg.SetValueEx(winreg.CreateKey(root, key_core % 'Modules'),
                      "", 0, winreg.REG_SZ, "")
    winreg.SetValueEx(winreg.CreateKey(root, key_core % 'PythonPath'),
                      "", 0, winreg.REG_SZ,
                      r"%s\Lib;%s\DLLs" % (target, target))
    winreg.SetValueEx(winreg.CreateKey(root,
                               key_core % r'Help\Main Python Documentation'),
                      "", 0, winreg.REG_SZ,
                      r"%s\Doc\python%s.chm" % (target, long_version))

    # Create start menu entries for all WinPython launchers
    for path, desc, fname in _get_shortcut_data(target, current=current):
        utils.create_shortcut(path, desc, fname)

    # Register the Python ActiveX Scripting client (requires pywin32)
    axscript = osp.join(target, 'Lib', 'site-packages', 'win32comext',
                        'axscript', 'client', 'pyscript.py')
    if osp.isfile(axscript):
        subprocess.call('"%s" "%s"' % (python, axscript), cwd=target)
    else:
        print('Unable to register ActiveX: please install pywin32',
              file=sys.stderr)


def unregister(target, current=True):
    """Unregister a Python distribution in Windows registry"""
    # Registry entries
    root = winreg.HKEY_CURRENT_USER if current else winreg.HKEY_LOCAL_MACHINE
    short_version = utils.get_python_infos(target)[0]
    key_core = (KEY_S1 % short_version) + r'\%s'
    for key in (
                # Drop support
                KEY_DROP1 % "", KEY_DROP1 % "NoCon", KEY_DROP1 % "Compiled",
                KEY_DROP0 % "", KEY_DROP0 % "NoCon", KEY_DROP0 % "Compiled",
                # Icons
                KEY_I % "NoCon", KEY_I % "Compiled", KEY_I % "",
                # Edit with IDLE
                KEY_C2 % ("", EWI), KEY_C2 % ("NoCon", EWI),
                KEY_C1 % ("", EWI), KEY_C1 % ("NoCon", EWI),
                # Edit with Spyder
                KEY_C2 % ("", EWS), KEY_C2 % ("NoCon", EWS),
                KEY_C1 % ("", EWS), KEY_C1 % ("NoCon", EWS),
                # Verbs
                KEY_C2 % ("", "open"),
                KEY_C2 % ("NoCon", "open"),
                KEY_C2 % ("Compiled", "open"),
                KEY_C1 % ("", "open"),
                KEY_C1 % ("NoCon", "open"),
                KEY_C1 % ("Compiled", "open"),
                KEY_C0 % "", KEY_C0 % "NoCon", KEY_C0 % "Compiled",
                # Descriptions
                KEY_D % "NoCon", KEY_D % "Compiled", KEY_D % "",
                # PythonCore
                key_core % r'InstallPath\InstallGroup',
                key_core % 'InstallPath',
                key_core % 'Modules',
                key_core % 'PythonPath',
                key_core % r'Help\Main Python Documentation',
                key_core % 'Help',
                KEY_S1 % short_version, KEY_S0, KEY_S,
                ):
        try:
            print(key)
            winreg.DeleteKey(root, key)
        except WindowsError:
            rootkey = 'HKEY_CURRENT_USER' if current else 'HKEY_LOCAL_MACHINE'
            print(r'Unable to remove %s\%s' % (rootkey, key), file=sys.stderr)

    # Start menu shortcuts
    for path, desc, fname in _get_shortcut_data(target, current=current):
        if osp.exists(fname):
            os.remove(fname)


if __name__ == '__main__':
    register(sys.prefix)
    unregister(sys.prefix)
