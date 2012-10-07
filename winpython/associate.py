# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
Register a Python distribution

Created on Tue Aug 21 21:46:30 2012
"""

import os.path as osp
import _winreg


def register(target, current=True):
    """Register a Python distribution in Windows registry"""
    root = _winreg.HKEY_CURRENT_USER if current else _winreg.HKEY_LOCAL_MACHINE

    # Extensions
    _winreg.SetValueEx(_winreg.CreateKey(root, r"Software\Classes\.py"),
                       "", 0, _winreg.REG_SZ, "Python.File")
    _winreg.SetValueEx(_winreg.CreateKey(root, r"Software\Classes\.pyw"),
                       "", 0, _winreg.REG_SZ, "Python.NoConFile")
    _winreg.SetValueEx(_winreg.CreateKey(root, r"Software\Classes\.pyc"),
                       "", 0, _winreg.REG_SZ, "Python.CompiledFile")
    _winreg.SetValueEx(_winreg.CreateKey(root, r"Software\Classes\.pyo"),
                       "", 0, _winreg.REG_SZ, "Python.CompiledFile")

    # MIME types
    _winreg.SetValueEx(_winreg.CreateKey(root, r"Software\Classes\.py"),
                       "Content Type", 0, _winreg.REG_SZ, "text/plain")
    _winreg.SetValueEx(_winreg.CreateKey(root, r"Software\Classes\.pyw"),
                       "Content Type", 0, _winreg.REG_SZ, "text/plain")

    # Verbs
    python = osp.abspath(osp.join(target, 'python.exe'))
    pythonw = osp.abspath(osp.join(target, 'pythonw.exe'))
    pat = r"Software\Classes\Python.%sFile\shell\%s\command"
    _winreg.SetValueEx(_winreg.CreateKey(root, pat % ("", "open")),
                       "", 0, _winreg.REG_SZ, '"%s" "%%1" %%*' % python)
    _winreg.SetValueEx(_winreg.CreateKey(root, pat % ("NoCon", "open")),
                       "", 0, _winreg.REG_SZ, '"%s" "%%1" %%*' % pythonw)
    _winreg.SetValueEx(_winreg.CreateKey(root, pat % ("Compiled", "open")),
                       "", 0, _winreg.REG_SZ, '"%s" "%%1" %%*' % python)
    ewi = "Edit with IDLE"
    _winreg.SetValueEx(_winreg.CreateKey(root, pat % ("", ewi)),
                       "", 0, _winreg.REG_SZ,
                       '"%s" "%s\Lib\idlelib\idle.pyw" -n -e "%%1"'
                       % (pythonw, target))
    _winreg.SetValueEx(_winreg.CreateKey(root, pat % ("NoCon", ewi)),
                       "", 0, _winreg.REG_SZ,
                       '"%s" "%s\Lib\idlelib\idle.pyw" -n -e "%%1"'
                       % (pythonw, target))
    
    # Icons
    dlls = osp.join(target, 'DLLs')
    pat2 = r"Software\Classes\Python.%sFile\DefaultIcon"
    _winreg.SetValueEx(_winreg.CreateKey(root, pat2 % ""),
                       "", 0, _winreg.REG_SZ, r'%s\py.ico' % dlls)
    _winreg.SetValueEx(_winreg.CreateKey(root, pat2 % "NoCon"),
                       "", 0, _winreg.REG_SZ, r'%s\py.ico' % dlls)
    _winreg.SetValueEx(_winreg.CreateKey(root, pat2 % "Compiled"),
                       "", 0, _winreg.REG_SZ, r'%s\pyc.ico' % dlls)
    
    # Descriptions
    pat3 = r"Software\Classes\Python.%sFile"
    _winreg.SetValueEx(_winreg.CreateKey(root, pat3 % ""),
                       "", 0, _winreg.REG_SZ, "Python File")
    _winreg.SetValueEx(_winreg.CreateKey(root, pat3 % "NoCon"),
                       "", 0, _winreg.REG_SZ, "Python File (no console)")
    _winreg.SetValueEx(_winreg.CreateKey(root, pat3 % "Compiled"),
                       "", 0, _winreg.REG_SZ, "Compiled Python File")


if __name__ == '__main__':
    register(r'D:\Pierre\build\winpython-2.7.3\python-2.7.3')
