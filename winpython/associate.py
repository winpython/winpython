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

from guidata.py3compat import winreg

# Local imports
from winpython import utils


def register(target, current=True):
    """Register a Python distribution in Windows registry"""
    root = winreg.HKEY_CURRENT_USER if current else winreg.HKEY_LOCAL_MACHINE

    # Extensions
    winreg.SetValueEx(winreg.CreateKey(root, r"Software\Classes\.py"),
                      "", 0, winreg.REG_SZ, "Python.File")
    winreg.SetValueEx(winreg.CreateKey(root, r"Software\Classes\.pyw"),
                      "", 0, winreg.REG_SZ, "Python.NoConFile")
    winreg.SetValueEx(winreg.CreateKey(root, r"Software\Classes\.pyc"),
                      "", 0, winreg.REG_SZ, "Python.CompiledFile")
    winreg.SetValueEx(winreg.CreateKey(root, r"Software\Classes\.pyo"),
                      "", 0, winreg.REG_SZ, "Python.CompiledFile")

    # MIME types
    winreg.SetValueEx(winreg.CreateKey(root, r"Software\Classes\.py"),
                      "Content Type", 0, winreg.REG_SZ, "text/plain")
    winreg.SetValueEx(winreg.CreateKey(root, r"Software\Classes\.pyw"),
                      "Content Type", 0, winreg.REG_SZ, "text/plain")

    # Verbs
    python = osp.abspath(osp.join(target, 'python.exe'))
    pythonw = osp.abspath(osp.join(target, 'pythonw.exe'))
    pat = r"Software\Classes\Python.%sFile\shell\%s\command"
    winreg.SetValueEx(winreg.CreateKey(root, pat % ("", "open")),
                      "", 0, winreg.REG_SZ, '"%s" "%%1" %%*' % python)
    winreg.SetValueEx(winreg.CreateKey(root, pat % ("NoCon", "open")),
                      "", 0, winreg.REG_SZ, '"%s" "%%1" %%*' % pythonw)
    winreg.SetValueEx(winreg.CreateKey(root, pat % ("Compiled", "open")),
                      "", 0, winreg.REG_SZ, '"%s" "%%1" %%*' % python)
    ewi = "Edit with IDLE"
    winreg.SetValueEx(winreg.CreateKey(root, pat % ("", ewi)),
                      "", 0, winreg.REG_SZ,
                      '"%s" "%s\Lib\idlelib\idle.pyw" -n -e "%%1"'
                      % (pythonw, target))
    winreg.SetValueEx(winreg.CreateKey(root, pat % ("NoCon", ewi)),
                      "", 0, winreg.REG_SZ,
                      '"%s" "%s\Lib\idlelib\idle.pyw" -n -e "%%1"'
                      % (pythonw, target))
    
    # Icons
    dlls = osp.join(target, 'DLLs')
    pat2 = r"Software\Classes\Python.%sFile\DefaultIcon"
    winreg.SetValueEx(winreg.CreateKey(root, pat2 % ""),
                      "", 0, winreg.REG_SZ, r'%s\py.ico' % dlls)
    winreg.SetValueEx(winreg.CreateKey(root, pat2 % "NoCon"),
                      "", 0, winreg.REG_SZ, r'%s\py.ico' % dlls)
    winreg.SetValueEx(winreg.CreateKey(root, pat2 % "Compiled"),
                      "", 0, winreg.REG_SZ, r'%s\pyc.ico' % dlls)
    
    # Descriptions
    pat3 = r"Software\Classes\Python.%sFile"
    winreg.SetValueEx(winreg.CreateKey(root, pat3 % ""),
                      "", 0, winreg.REG_SZ, "Python File")
    winreg.SetValueEx(winreg.CreateKey(root, pat3 % "NoCon"),
                      "", 0, winreg.REG_SZ, "Python File (no console)")
    winreg.SetValueEx(winreg.CreateKey(root, pat3 % "Compiled"),
                      "", 0, winreg.REG_SZ, "Compiled Python File")

    # Register the Python ActiveX Scripting client (requires pywin32)
    axscript = osp.join(target, 'Lib', 'site-packages', 'win32comext',
                        'axscript', 'client', 'pyscript.py')
    if osp.isfile(axscript):
        subprocess.call('"%s" "%s"' % (python, axscript), cwd=target)
    else:
        print('Unable to register ActiveX: please install pywin32',
              file=sys.stderr)

    # Create start menu entries for all WinPython launchers
    wpgroup = utils.create_winpython_start_menu_folder(current=current)
    wpdir = osp.join(target, os.pardir)
    for name in os.listdir(wpdir):
        bname, ext = osp.splitext(name)
        if ext == '.exe':
            utils.create_shortcut(osp.join(wpdir, name), bname,
                                  osp.join(wpgroup, bname))


if __name__ == '__main__':
    register(sys.prefix)
