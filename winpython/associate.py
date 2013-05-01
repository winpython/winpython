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
KEY_C0 = KEY_C % r"Python.%sFile\shell\%s"
KEY_C1 = KEY_C0 + r"\command"
KEY_I = KEY_C % r"Python.%sFile\DefaultIcon"
KEY_D = KEY_C % r"Python.%sFile"
EWI = "Edit with IDLE"
EWS = "Edit with Spyder"


def _get_shortcut_data(target, current=True):
    wpgroup = utils.create_winpython_start_menu_folder(current=current)
    wpdir = osp.join(target, os.pardir)
    data = []
    for name in os.listdir(wpdir):
        bname, ext = osp.splitext(name)
        if ext == '.exe':
            data.append( (osp.join(wpdir, name),
                          bname,
                          osp.join(wpgroup, bname)) )
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
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C1 % ("", "open")),
                      "", 0, winreg.REG_SZ, '"%s" "%%1" %%*' % python)
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C1 % ("NoCon", "open")),
                      "", 0, winreg.REG_SZ, '"%s" "%%1" %%*' % pythonw)
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C1 % ("Compiled", "open")),
                      "", 0, winreg.REG_SZ, '"%s" "%%1" %%*' % python)
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C1 % ("", EWI)),
                      "", 0, winreg.REG_SZ,
                      '"%s" "%s\Lib\idlelib\idle.pyw" -n -e "%%1"'
                      % (pythonw, target))
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C1 % ("NoCon", EWI)),
                      "", 0, winreg.REG_SZ,
                      '"%s" "%s\Lib\idlelib\idle.pyw" -n -e "%%1"'
                      % (pythonw, target))
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C1 % ("", EWS)),
                      "", 0, winreg.REG_SZ,
                      '"%s" "%s\Scripts\spyder" "%%1"' % (pythonw, target))
    winreg.SetValueEx(winreg.CreateKey(root, KEY_C1 % ("NoCon", EWS)),
                      "", 0, winreg.REG_SZ,
                      '"%s" "%s\Scripts\spyder" "%%1"' % (pythonw, target))
    
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
    for key in (
                # Icons
                KEY_I % "NoCon", KEY_I % "Compiled", KEY_I % "",
                # Edit with IDLE
                KEY_C1 % ("", EWI), KEY_C1 % ("NoCon", EWI),
                KEY_C0 % ("", EWI), KEY_C0 % ("NoCon", EWI),
                # Edit with Spyder
                KEY_C1 % ("", EWS), KEY_C1 % ("NoCon", EWS),
                KEY_C0 % ("", EWS), KEY_C0 % ("NoCon", EWS),
                # Verbs
                KEY_C1 % ("", "open"), KEY_C1 % ("NoCon", "open"),
                KEY_C1 % ("Compiled", "open"),
                # Descriptions
                KEY_D % "NoCon", KEY_D % "Compiled", KEY_D % "",
                # Parent key
                KEY_C,
                ):
        try:
            winreg.DeleteKey(root, key)
        except WindowsError:
            rootkey = 'HKEY_CURRENT_USER' if current else 'HKEY_LOCAL_MACHINE'
            raise WindowsError(r'Unable to remove %s\%s' % (rootkey, key))
    
    # Start menu shortcuts
    for path, desc, fname in _get_shortcut_data(target, current=current):
        os.remove(fname)


if __name__ == '__main__':
    register(sys.prefix)
    unregister(sys.prefix)
