# -*- coding: utf-8 -*-
#
# associate.py = Register a Python distribution
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

import sys
import os
from pathlib import Path
import platform
import importlib.util
import winreg
from winpython import utils
from argparse import ArgumentParser

# --- Constants ---
KEY_C = r"Software\Classes\%s"
KEY_CP = r"Software\Classes"
KEY_S = r"Software\Python"
KEY_S0 = KEY_S + r"\WinPython" # was PythonCore before PEP-0514
EWI = "Edit with IDLE"
EWS = "Edit with Spyder"
DROP_HANDLER_CLSID = "{60254CA5-953B-11CF-8C96-00AA00B8708C}"

# --- Helper functions for Registry ---

def _set_reg_value(root, key_path, name, value, reg_type=winreg.REG_SZ, verbose=False):
    """Helper to create key and set a registry value using CreateKeyEx."""
    rootkey_name = "HKEY_CURRENT_USER" if root == winreg.HKEY_CURRENT_USER else "HKEY_LOCAL_MACHINE"
    try:
        # Use CreateKeyEx with context manager for automatic closing
        # KEY_WRITE access is needed to set values
        
        if verbose:
            print(f"{rootkey_name}\\{key_path}\\{name if name  else ''}:{value}")
        with winreg.CreateKeyEx(root, key_path, 0, winreg.KEY_WRITE) as key:
             winreg.SetValueEx(key, name, 0, reg_type, value)
    except OSError as e:
         print(f"Error creating/setting registry value {rootkey_name}\\{key_path}\\{name}: {e}", file=sys.stderr)

def _delete_reg_key(root, key_path, verbose=False):
    """Helper to delete a registry key, ignoring if not found."""
    rootkey_name = "HKEY_CURRENT_USER" if root == winreg.HKEY_CURRENT_USER else "HKEY_LOCAL_MACHINE"
    try:
        if verbose:
            print(f"{rootkey_name}\\{key_path}")
        # DeleteKey can only delete keys with no subkeys.
        # For keys with (still) subkeys, use DeleteKeyEx on the parent key if available
        winreg.DeleteKey(root, key_path)
    except FileNotFoundError:
        if verbose:
             print(f"Registry key not found (skipping deletion): {rootkey_name}\\{key_path}")
    except OSError as e: # Catch other potential errors like key not empty
        print(f"Error deleting registry key {rootkey_name}\\{key_path}: {e}", file=sys.stderr)


# --- Helper functions for Start Menu Shortcuts ---

def _has_pywin32():
    """Check if pywin32 (pythoncom) is installed."""
    return importlib.util.find_spec('pythoncom') is not None

def _remove_start_menu_folder(target, current=True, has_pywin32=False):
    "remove menu Folder for target WinPython if pywin32 exists"
    if has_pywin32:
        utils.remove_winpython_start_menu_folder(current=current)
    else:
        print("Skipping start menu removal as pywin32 package is not installed.")

def _get_shortcut_data(target, current=True, has_pywin32=False):
    "get windows menu access data if pywin32 exists, otherwise empty list"
    if not has_pywin32:
        return []
 
    wpdir = str(Path(target).parent)
    data = []
    for name in os.listdir(wpdir):
        bname, ext = Path(name).stem, Path(name).suffix
        if ext.lower() == ".exe":
            # Path for the shortcut file in the start menu folder
            # This depends on utils.create_winpython_start_menu_folder creating the right path
            shortcut_name = str(Path(utils.create_winpython_start_menu_folder(current=current)) / bname) + '.lnk'
            data.append(
                (
                    str(Path(wpdir) / name), # Target executable path
                    bname, # Description/Name
                    shortcut_name, # Shortcut file path
                )
            )
    return data

# --- Registry Entry Definitions ---

# Structure: (key_path, value_name, value, reg_type)
# Use None for value_name to set the default value of the key
REGISTRY_ENTRIES = []

# --- Extensions ---
EXTENSIONS = {
    ".py": "Python.File",
    ".pyw": "Python.NoConFile",
    ".pyc": "Python.CompiledFile",
    ".pyo": "Python.CompiledFile",
}
for ext, file_type in EXTENSIONS.items():
    REGISTRY_ENTRIES.append((KEY_C % ext, None, file_type))

# --- MIME types ---
MIME_TYPES = {
    ".py": "text/plain",
    ".pyw": "text/plain",
}
for ext, mime_type in MIME_TYPES.items():
    REGISTRY_ENTRIES.append((KEY_C % ext, "Content Type", mime_type))

# --- Verbs (Open, Edit with IDLE, Edit with Spyder) ---
# These depend on the python/pythonw/spyder paths
def _get_verb_entries(target):
    python = str((Path(target) / "python.exe").resolve())
    pythonw = str((Path(target) / "pythonw.exe").resolve())
    spyder_exe = str((Path(target).parent / "Spyder.exe").resolve())

    # Command string for Spyder, fallback to script if exe not found
    spyder_cmd = rf'"{spyder_exe}" "%1"' if Path(spyder_exe).is_file() else rf'"{pythonw}" "{target}\Scripts\spyder" "%1"'

    verbs_data = [
        # Open verb
        (rf"{KEY_CP}\Python.File\shell\open\command", None, rf'"{python}" "%1" %*'),
        (rf"{KEY_CP}\Python.NoConFile\shell\open\command", None, rf'"{pythonw}" "%1" %*'),
        (rf"{KEY_CP}\Python.CompiledFile\shell\open\command", None, rf'"{python}" "%1" %*'),
        # Edit with IDLE verb
        (rf"{KEY_CP}\Python.File\shell\{EWI}\command", None, rf'"{pythonw}" "{target}\Lib\idlelib\idle.pyw" -n -e "%1"'),
        (rf"{KEY_CP}\Python.NoConFile\shell\{EWI}\command", None, rf'"{pythonw}" "{target}\Lib\idlelib\idle.pyw" -n -e "%1"'),
        # Edit with Spyder verb
        (rf"{KEY_CP}\Python.File\shell\{EWS}\command", None, spyder_cmd),
        (rf"{KEY_CP}\Python.NoConFile\shell\{EWS}\command", None, spyder_cmd),
    ]
    return verbs_data

# --- Drop support ---
DROP_SUPPORT_FILE_TYPES = ["Python.File", "Python.NoConFile", "Python.CompiledFile"]
for file_type in DROP_SUPPORT_FILE_TYPES:
    REGISTRY_ENTRIES.append((rf"{KEY_C % file_type}\shellex\DropHandler", None, DROP_HANDLER_CLSID))

# --- Icons ---
def _get_icon_entries(target):
    dlls_path = str(Path(target) / "DLLs")
    icon_data = [
        (rf"{KEY_CP}\Python.File\DefaultIcon", None, rf"{dlls_path}\py.ico"),
        (rf"{KEY_CP}\Python.NoConFile\DefaultIcon", None, rf"{dlls_path}\py.ico"),
        (rf"{KEY_CP}\Python.CompiledFile\DefaultIcon", None, rf"{dlls_path}\pyc.ico"),
    ]
    return icon_data

# --- Descriptions ---
DESCRIPTIONS = {
    "Python.File": "Python File",
    "Python.NoConFile": "Python File (no console)",
    "Python.CompiledFile": "Compiled Python File",
}
for file_type, desc in DESCRIPTIONS.items():
    REGISTRY_ENTRIES.append((KEY_C % file_type, None, desc))


# --- PythonCore entries (PEP-0514 and WinPython specific) ---
def _get_pythoncore_entries(target):
    python_infos = utils.get_python_infos(target)  # ('3.11', 64)
    short_version = python_infos[0]  # e.g., '3.11'
    long_version = utils.get_python_long_version(target) # e.g., '3.11.5'

    SupportUrl = "https://winpython.github.io"
    SysArchitecture = f'{python_infos[1]}bit' # e.g., '64bit'
    SysVersion = short_version # e.g., '3.11'
    Version = long_version # e.g., '3.11.5'
    DisplayName = f'Python {Version} ({SysArchitecture})'

    python_exe = str((Path(target) / "python.exe").resolve())
    pythonw_exe = str((Path(target) / "pythonw.exe").resolve())

    core_entries = []

    # Main version key (WinPython\3.11)
    version_key = f"{KEY_S0}\\{short_version}"
    core_entries.extend([
        (version_key, 'DisplayName', DisplayName),
        (version_key, 'SupportUrl', SupportUrl),
        (version_key, 'SysVersion', SysVersion),
        (version_key, 'SysArchitecture', SysArchitecture),
        (version_key, 'Version', Version),
    ])

    # InstallPath key (WinPython\3.11\InstallPath)
    install_path_key = f"{version_key}\\InstallPath"
    core_entries.extend([
        (install_path_key, None, str(Path(target) / '')), # Default value is the install dir
        (install_path_key, 'ExecutablePath', python_exe),
        (install_path_key, 'WindowedExecutablePath', pythonw_exe),
    ])

    # InstallGroup key (WinPython\3.11\InstallPath\InstallGroup)
    core_entries.append((f"{install_path_key}\\InstallGroup", None, f"Python {short_version}"))

    # Modules key (WinPython\3.11\Modules) - seems to be a placeholder key
    core_entries.append((f"{version_key}\\Modules", None, ""))

    # PythonPath key (WinPython\3.11\PythonPath)
    core_entries.append((f"{version_key}\\PythonPath", None, rf"{target}\Lib;{target}\DLLs"))

    # Help key (WinPython\3.11\Help\Main Python Documentation)
    core_entries.append((f"{version_key}\\Help\\Main Python Documentation", None, rf"{target}\Doc\python{long_version}.chm"))

    return core_entries


# --- Main Register/Unregister Functions ---

def register(target, current=True, reg_type=winreg.REG_SZ, verbose=True):
    """Register a Python distribution in Windows registry and create Start Menu shortcuts"""
    root = winreg.HKEY_CURRENT_USER if current else winreg.HKEY_LOCAL_MACHINE
    has_pywin32 = _has_pywin32()

    if verbose:
        print(f'Creating WinPython registry entries for {target}')

    # Set static registry entries
    for key_path, name, value in REGISTRY_ENTRIES:
        _set_reg_value(root, key_path, name, value, verbose=verbose)

    # Set dynamic registry entries (verbs, icons, pythoncore)
    dynamic_entries = []
    dynamic_entries.extend(_get_verb_entries(target))
    dynamic_entries.extend(_get_icon_entries(target))
    dynamic_entries.extend(_get_pythoncore_entries(target))

    for key_path, name, value in dynamic_entries:
         _set_reg_value(root, key_path, name, value)

    # Create start menu entries
    if has_pywin32:
        if verbose:
            print(f'Creating WinPython menu for all icons in {target.parent}')
        for path, desc, fname in _get_shortcut_data(target, current=current, has_pywin32=True):
            try:
                 utils.create_shortcut(path, desc, fname, verbose=verbose)
            except Exception as e:
                 print(f"Error creating shortcut for {desc} at {fname}: {e}", file=sys.stderr)
    else:
        print("Skipping start menu shortcut creation as pywin32 package is needed.")


def unregister(target, current=True, verbose=True):
    """Unregister a Python distribution from Windows registry and remove Start Menu shortcuts"""
    root = winreg.HKEY_CURRENT_USER if current else winreg.HKEY_LOCAL_MACHINE
    has_pywin32 = _has_pywin32()

    if verbose:
         print(f'Removing WinPython registry entries for {target}')

    # List of keys to attempt to delete, ordered from most specific to general
    keys_to_delete = []

    # Add dynamic keys first (helps DeleteKey succeed)
    dynamic_entries = []
    dynamic_entries.extend(_get_verb_entries(target))
    dynamic_entries.extend(_get_icon_entries(target))
    dynamic_entries.extend(_get_pythoncore_entries(target))

    # Collect parent keys from dynamic entries
    dynamic_parent_keys = {entry[0] for entry in dynamic_entries}
    # Add keys from static entries
    static_parent_keys = {entry[0] for entry in REGISTRY_ENTRIES}

    # Combine and add the key templates that might become empty and should be removed
    python_infos = utils.get_python_infos(target)
    short_version = python_infos[0]
    version_key_base = f"{KEY_S0}\\{short_version}"

    # Keys from static REGISTRY_ENTRIES (mostly Class registrations)
    keys_to_delete.extend([
        KEY_C % file_type + rf"\shellex\DropHandler" for file_type in DROP_SUPPORT_FILE_TYPES
    ])
    keys_to_delete.extend([
        KEY_C % file_type + rf"\shellex" for file_type in DROP_SUPPORT_FILE_TYPES
    ])
    #keys_to_delete.extend([
    #     KEY_C % file_type + rf"\DefaultIcon" for file_type in set(EXTENSIONS.values()) # Use values as file types
    #])
    keys_to_delete.extend([
         KEY_C % file_type + rf"\shell\{EWI}\command" for file_type in ["Python.File", "Python.NoConFile"] # Specific types for IDLE verb
    ])
    keys_to_delete.extend([
         KEY_C % file_type + rf"\shell\{EWS}\command" for file_type in ["Python.File", "Python.NoConFile"] # Specific types for Spyder verb
    ])
     # General open command keys (cover all file types)
    keys_to_delete.extend([
         KEY_C % file_type + rf"\shell\open\command" for file_type in ["Python.File", "Python.NoConFile", "Python.CompiledFile"]
    ])


    # Keys from dynamic entries (Verbs, Icons, PythonCore) - add parents
    # Verbs
    keys_to_delete.extend([KEY_C % file_type + rf"\shell\{EWI}" for file_type in ["Python.File", "Python.NoConFile"]])
    keys_to_delete.extend([KEY_C % file_type + rf"\shell\{EWS}" for file_type in ["Python.File", "Python.NoConFile"]])
    keys_to_delete.extend([KEY_C % file_type + rf"\shell\open" for file_type in ["Python.File", "Python.NoConFile", "Python.CompiledFile"]])
    keys_to_delete.extend([KEY_C % file_type + rf"\shell" for file_type in ["Python.File", "Python.NoConFile", "Python.CompiledFile"]]) # Shell parent

    # Icons
    keys_to_delete.extend([KEY_C % file_type + rf"\DefaultIcon" for file_type in set(EXTENSIONS.values())]) # Already added above? Check for duplicates or order
    keys_to_delete.extend([KEY_C % file_type  for file_type in set(EXTENSIONS.values())]) # Parent keys for file types

    # Extensions/Descriptions parents
    # keys_to_delete.extend([KEY_C % ext for ext in EXTENSIONS.keys()]) # e.g., .py, .pyw

    # PythonCore keys (from most specific down to the base)
    keys_to_delete.extend([
        f"{version_key_base}\\InstallPath\\InstallGroup",
        f"{version_key_base}\\InstallPath",
        f"{version_key_base}\\Modules",
        f"{version_key_base}\\PythonPath",
        f"{version_key_base}\\Help\\Main Python Documentation",
        f"{version_key_base}\\Help",
        version_key_base, # e.g., Software\Python\WinPython\3.11
        KEY_S0, # Software\Python\WinPython
        #KEY_S, # Software\Python (only if WinPython key is the only subkey - risky to delete)
    ])

    # Attempt to delete keys
    # Use a set to avoid duplicates, then sort by length descending to try deleting children first
    # (although DeleteKey only works on empty keys anyway, so explicit ordering is clearer)

    for key in keys_to_delete:
         _delete_reg_key(root, key, verbose=verbose)

    # Remove start menu shortcuts
    if has_pywin32:
        if verbose:
            print(f'Removing WinPython menu for all icons in {target.parent}')
        _remove_start_menu_folder(target, current=current, has_pywin32=True)
        # The original code had commented out code to delete .lnk files individually.
        # remove_winpython_start_menu_folder is likely the intended method.
    else:
        print("Skipping start menu removal as pywin32 package is needed.")

if __name__ == "__main__":
    # Ensure we are running from the target WinPython environment
    parser = ArgumentParser(description="Register or Un-register Python file extensions, icons "\
                        "and Windows explorer context menu to this "\
                        "Python distribution.")
    parser.add_argument('--unregister', action="store_true",
                    help='register to all users, requiring administrative '\
                         'privileges (default: register to current user only)')
    parser.add_argument('--all', action="store_true",
                    help='action is to all users, requiring administrative '\
                         'privileges (default: to current user only)')
    args = parser.parse_args()
    expected_target = Path(sys.prefix)
    command = "unregister" if args.unregister else "register"
    users = "all" if args.all else "user"
    print(f"Attempting to {command} the Python environment for {users} at: {expected_target}")

    target_dir = sys.prefix # Or get from arguments
    is_current_user = True # Or get from arguments
    if command == "register":
        register(expected_target, current=not args.all)
    else:
        unregister(expected_target, current=not args.all)
