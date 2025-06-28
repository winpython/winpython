# -*- coding: utf-8 -*-
#
# associate.py = Register a Python distribution
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

import sys
import os
from pathlib import Path
import importlib.util
import winreg
from . import utils
from argparse import ArgumentParser

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

# --- Helper functions for Registry ---

def _set_reg_value(root, key_path, name, value, reg_type=winreg.REG_SZ, verbose=False):
    """Helper to create key and set a registry value using CreateKeyEx."""
    rootkey_name = "HKEY_CURRENT_USER" if root == winreg.HKEY_CURRENT_USER else "HKEY_LOCAL_MACHINE"
    if verbose:
        print(f"{rootkey_name}\\{key_path}\\{name if name  else ''}:{value}")
    try:
        # Use CreateKeyEx with context manager for automatic closing
        with winreg.CreateKeyEx(root, key_path, 0, winreg.KEY_WRITE) as key:
             winreg.SetValueEx(key, name, 0, reg_type, value)
    except OSError as e:
         print(f"Error creating/setting registry value {rootkey_name}\\{key_path}\\{name}: {e}", file=sys.stderr)

def _delete_reg_key(root, key_path, verbose=False):
    """Helper to delete a registry key, ignoring if not found."""
    rootkey_name = "HKEY_CURRENT_USER" if root == winreg.HKEY_CURRENT_USER else "HKEY_LOCAL_MACHINE"
    if verbose:
        print(f"{rootkey_name}\\{key_path}")
    try:
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
        remove_winpython_start_menu_folder(current=current)
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
            shortcut_name = str(Path(create_winpython_start_menu_folder(current=current)) / bname) + '.lnk'
            data.append(
                (
                    str(Path(wpdir) / name), # Target executable path
                    bname, # Description/Name
                    shortcut_name, # Shortcut file path
                )
            )
    return data

# --- PythonCore entries (PEP-0514 and WinPython specific) ---


def register_in_registery(target, current=True, reg_type=winreg.REG_SZ, verbose=True) -> tuple[list[any], ...]:
    """Register in Windows (like regedit)"""

    # --- Constants ---
    DROP_HANDLER_CLSID = "{60254CA5-953B-11CF-8C96-00AA00B8708C}"

    # --- CONFIG ---
    target_path = Path(target).resolve()
    python_exe = str(target_path / "python.exe")
    pythonw_exe = str(target_path / "pythonw.exe")
    spyder_exe = str(target_path.parent / "Spyder.exe")
    icon_py = str(target_path / "DLLs" / "py.ico")
    icon_pyc = str(target_path / "DLLs" / "pyc.ico")
    idle_path = str(target_path / "Lib" / "idlelib" / "idle.pyw")
    doc_path = str(target_path / "Doc" / "html" / "index.html")
    python_infos = utils.get_python_infos(target)  # ('3.11', 64)
    short_version = python_infos[0]  # e.g., '3.11'
    version = utils.get_python_long_version(target) # e.g., '3.11.5'
    arch = f'{python_infos[1]}bit' # e.g., '64bit'
    display = f"Python {version} ({arch})"

    permanent_entries = [] # key_path, name, value
    dynamic_entries = []  # key_path, name, value
    core_entries = []  # key_path, name, value
    lost_entries = [] # intermediate keys to remove later
    # --- File associations ---
    ext_map = {".py": "Python.File", ".pyw": "Python.NoConFile", ".pyc": "Python.CompiledFile"}
    ext_label = {".py": "Python File", ".pyw": "Python File (no console)", ".pyc": "Compiled Python File"}
    for ext, ftype in ext_map.items():
        permanent_entries.append((f"Software\\Classes\\{ext}", None, ftype))
        if ext in (".py", ".pyw"):
           permanent_entries.append((f"Software\\Classes\\{ext}", "Content Type", "text/plain"))

    # --- Descriptions, Icons, DropHandlers ---
    for ext, ftype in ext_map.items():
        dynamic_entries.append((f"Software\\Classes\\{ftype}", None, ext_label[ext]))
        dynamic_entries.append((f"Software\\Classes\\{ftype}\\DefaultIcon", None, icon_py if "Compiled" not in ftype else icon_pyc))
        dynamic_entries.append((f"Software\\Classes\\{ftype}\\shellex\\DropHandler", None, DROP_HANDLER_CLSID))
        lost_entries.append((f"Software\\Classes\\{ftype}\\shellex", None, None))

    # --- Shell commands ---
    for ext, ftype in ext_map.items():
        dynamic_entries.append((f"Software\\Classes\\{ftype}\\shell\\open\\command", None, f'''"{pythonw_exe if ftype=='Python.NoConFile' else python_exe}" "%1" %*'''))
        lost_entries.append((f"Software\\Classes\\{ftype}\\shell\\open", None, None))
        lost_entries.append((f"Software\\Classes\\{ftype}\\shell", None, None))

    dynamic_entries.append((rf"Software\Classes\Python.File\shell\Edit with IDLE\command", None, f'"{pythonw_exe}" "{idle_path}" -n -e "%1"'))
    dynamic_entries.append((rf"Software\Classes\Python.NoConFile\shell\Edit with IDLE\command", None, f'"{pythonw_exe}" "{idle_path}" -n -e "%1"'))
    lost_entries.append((rf"Software\Classes\Python.File\shell\Edit with IDLE", None, None))
    lost_entries.append((rf"Software\Classes\Python.NoConFile\shell\Edit with IDLE", None, None))

    if Path(spyder_exe).exists():
        dynamic_entries.append((rf"Software\Classes\Python.File\shell\Edit with Spyder\command", None, f'"{spyder_exe}" "%1" -w "%w"'))
        dynamic_entries.append((rf"Software\Classes\Python.NoConFile\shell\Edit with Spyder\command", None, f'"{spyder_exe}" "%1" -w "%w"'))
        lost_entries.append((rf"Software\Classes\Python.File\shell\Edit with Spyder", None, None))
        lost_entries.append((rf"Software\Classes\Python.NoConFile\shell\Edit with Spyder", None, None))

    # --- WinPython Core registry entries (PEP 514 style) ---
    base = f"Software\\Python\\WinPython\\{short_version}"
    core_entries.append((base, "DisplayName", display))
    core_entries.append((base, "SupportUrl", "https://winpython.github.io"))
    core_entries.append((base, "SysVersion", short_version))
    core_entries.append((base, "SysArchitecture", arch))
    core_entries.append((base, "Version", version))

    core_entries.append((f"{base}\\InstallPath", None, str(target)))
    core_entries.append((f"{base}\\InstallPath", "ExecutablePath", python_exe))
    core_entries.append((f"{base}\\InstallPath", "WindowedExecutablePath", pythonw_exe))
    core_entries.append((f"{base}\\InstallPath\\InstallGroup", None, f"Python {short_version}"))

    core_entries.append((f"{base}\\Modules", None, ""))
    core_entries.append((f"{base}\\PythonPath", None, f"{target}\\Lib;{target}\\DLLs"))
    core_entries.append((f"{base}\\Help\\Main Python Documentation", None, doc_path))
    lost_entries.append((f"{base}\\Help", None, None))
    lost_entries.append((f"Software\\Python\\WinPython", None, None))

    return permanent_entries, dynamic_entries, core_entries, lost_entries

# --- Main Register/Unregister Functions ---

def register(target, current=True, reg_type=winreg.REG_SZ, verbose=True):
    """Register a Python distribution in Windows registry and create Start Menu shortcuts"""
    root = winreg.HKEY_CURRENT_USER if current else winreg.HKEY_LOCAL_MACHINE
    has_pywin32 = _has_pywin32()

    if verbose:
        print(f'Creating WinPython registry entries for {target}')

    permanent_entries, dynamic_entries,  core_entries, lost_entries = register_in_registery(target)
    # Set  registry entries for given target 
    for key_path, name, value in permanent_entries + dynamic_entries + core_entries:
         _set_reg_value(root, key_path, name, value, verbose=verbose)
         
    # Create start menu entries
    if has_pywin32:
        if verbose:
            print(f'Creating WinPython menu for all icons in {target.parent}')
        for path, desc, fname in _get_shortcut_data(target, current=current, has_pywin32=True):
            try:
                create_shortcut(path, desc, fname, verbose=verbose)
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
   
    permanent_entries, dynamic_entries,  core_entries , lost_entries = register_in_registery(target)

    # List of keys to attempt to delete, ordered from most specific to general
    keys_to_delete = sorted(list(set(key_path for   key_path , name, value  in  (dynamic_entries +  core_entries + lost_entries))), key=len, reverse=True)

    rootkey_name = "HKEY_CURRENT_USER" if root == winreg.HKEY_CURRENT_USER else "HKEY_LOCAL_MACHINE"
    for key_path in keys_to_delete:
         _delete_reg_key(root, key_path, verbose=verbose)

    # Remove start menu shortcuts
    if has_pywin32:
        if verbose:
            print(f'Removing WinPython menu for all icons in {target.parent}')
        _remove_start_menu_folder(target, current=current, has_pywin32=True)
        # The original code had commented out code to delete .lnk files individually.
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
