# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Copyright © 2014-2024+  The Winpython development team https://github.com/winpython/
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
WinPython build script
Created on Sun Aug 12 11:17:50 2012
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from winpython import wppm, utils
# Local imports
import diff

CHANGELOGS_DIR = Path(__file__).parent / "changelogs"
PORTABLE_DIR = Path(__file__).parent / "portable"

assert CHANGELOGS_DIR.is_dir(), f"Changelogs directory not found: {CHANGELOGS_DIR}"
assert PORTABLE_DIR.is_dir(), f"Portable directory not found: {PORTABLE_DIR}"


def find_7zip_executable() -> str:
    """
    Locates the 7-Zip executable (7z.exe) in common installation directories.

    Raises:
        RuntimeError: If 7-Zip executable is not found.

    Returns:
        str: Path to the 7-Zip executable.
    """
    program_files_dirs = [
        Path(r"C:\Program Files"),
        Path(r"C:\Program Files (x86)"),
        Path(sys.prefix).parent.parent / "7-Zip",
    ]
    for base_dir in program_files_dirs:
        for subdir in [".", "App"]:
            exe_path = base_dir / subdir / "7-Zip" / "7z.exe"
            if exe_path.is_file():
                return str(exe_path)
    raise RuntimeError("7ZIP is not installed on this computer.")


def replace_lines_in_file(filepath: Path, replacements: list[tuple[str, str]]):
    """
    Replaces lines in a file that start with a given prefix.

    Args:
        filepath: Path to the file to modify.
        replacements: A list of tuples, where each tuple contains:
            - The prefix of the line to replace (str).
            - The new text for the line (str).
    """
    lines: list[str] = []
    with open(filepath, "r") as f:
        lines = f.readlines()

    updated_lines = list(lines)  # Create a mutable copy

    for index, line in enumerate(lines):
        for prefix, new_text in replacements:
            start_prefix = prefix
            if prefix not in ("Icon", "OutFile") and not prefix.startswith("!"):
                start_prefix = "set " + prefix
            if line.startswith(start_prefix + "="):
                updated_lines[index] = f"{start_prefix}={new_text}\n"

    with open(filepath, "w") as f:
        f.writelines(updated_lines)
    print(f"Updated 7-zip script: {filepath}")


def build_installer_7zip(
    script_template_path: Path, output_script_path: Path, replacements: list[tuple[str, str]]
):
    """
    Creates a 7-Zip installer script by copying a template and applying text replacements.

    Args:
        script_template_path: Path to the template 7-Zip script (.bat file).
        output_script_path: Path to save the generated 7-Zip script.
        replacements: A list of tuples for text replacements (prefix, new_text).
    """
    sevenzip_exe = find_7zip_executable()
    shutil.copy(script_template_path, output_script_path)

    # Standard replacements for all 7zip scripts
    data = [
        ("PORTABLE_DIR", str(PORTABLE_DIR)),
        ("SEVENZIP_EXE", sevenzip_exe),
    ] + replacements

    replace_lines_in_file(output_script_path, data)

    try:
        # Execute the generated 7-Zip script
        command = f'"{output_script_path}"'
        print(f"Executing 7-Zip script: {command}")
        subprocess.run(
            command, shell=True, check=True, stderr=sys.stderr, stdout=sys.stderr
            # with stdout=sys.stdout, we would not  see 7zip compressing
        )  # Use subprocess.run for better error handling
    except subprocess.CalledProcessError as e:
        print(f"Error executing 7-Zip script: {e}", file=sys.stderr)


class WinPythonDistributionBuilder:
    """
    Builds a WinPython distribution.
    """

    NODEJS_PATH_REL = r"\n"  # Relative path within WinPython dir

    def __init__(
        self,
        build_number: int,
        release_level: str,
        target_dir: Path,
        wheels_dir: Path,
        tools_dirs: list[Path] = None,
        docs_dirs: list[Path] = None,
        verbose: bool = False,
        base_dir: Path = None,
        install_options: list[str] = None,
        flavor: str = "",
    ):
        """
        Initializes the WinPythonDistributionBuilder.

        Args:
            build_number: The build number (integer).
            release_level: The release level (e.g., "beta", "").
            target_dir: The base directory where WinPython will be created.
            wheels_dir: Directory containing wheel files for packages.
            tools_dirs: List of directories containing development tools to include.
            docs_dirs: List of directories containing documentation to include.
            verbose: Enable verbose output.
            base_dir: Base directory for building (optional, for relative paths).
            install_options: Additional pip install options.
            flavor: WinPython flavor (e.g., "Barebone").
        """
        self.build_number = build_number
        self.release_level = release_level
        self.target_dir = Path(target_dir)  # Ensure Path object
        self.wheels_dir = Path(wheels_dir)  # Ensure Path object
        self.tools_dirs = tools_dirs or []
        self.docs_dirs = docs_dirs or []
        self.verbose = verbose
        self.winpy_dir: Path | None = None  # Will be set during build
        self.distribution: wppm.Distribution | None = None # Will be set during build
        self.base_dir = base_dir
        self.install_options = install_options or []
        self.flavor = flavor
        self.python_zip_file: Path = self._get_python_zip_file()
        self.python_name = self.python_zip_file.stem  # Filename without extension
        self.python_dir_name = "python"  # Standardized Python directory name

    def _get_python_zip_file(self) -> Path:
        """
        Finds the Python zip file in the wheels directory.

        Returns:
            Path: Path to the Python zip file.
        Raises:
            RuntimeError: if no python zip file is found
        """
        patterns = [
            r"(pypy3|python-)([0-9]|[a-zA-Z]|.)*.zip",  # PyPy pattern
            r"python-([0-9\.rcba]*)((\.|\-)amd64)?\.(zip|zip)",  # Standard Python pattern
        ]
        for pattern in patterns:
            for filename in os.listdir(self.wheels_dir):
                if re.match(pattern, filename):
                    return self.wheels_dir / filename
        raise RuntimeError(f"Could not find Python zip package in {self.wheels_dir}")

    @property
    def package_index_markdown(self) -> str:
        """
        Generates a Markdown formatted package index page.

        Returns:
            str: Markdown content for the package index.
        """
        installed_tools_md = self._get_installed_tools_markdown()
        installed_packages_md = self._get_installed_packages_markdown()
        python_description = "Python programming language with standard library"

        return f"""## WinPython {self.winpyver2 + self.flavor}

The following packages are included in WinPython-{self.architecture_bits}bit v{self.winpyver2 + self.flavor} {self.release_level}.

<details>

### Tools

Name | Version | Description
-----|---------|------------
{installed_tools_md}

### Python packages

Name | Version | Description
-----|---------|------------
[Python](http://www.python.org/) | {self.python_full_version} | {python_description}
{installed_packages_md}

</details>
"""
    def _get_installed_tools_markdown(self) -> str:
        """Generates Markdown for installed tools section in package index."""
        installed_tools = []

        def get_tool_path(rel_path):
            path = self.winpy_dir / rel_path if self.winpy_dir else None
            return path if path and (path.is_file() or path.is_dir()) else None

        nodejs_path = get_tool_path(self.NODEJS_PATH_REL)
        if nodejs_path:
            node_version = utils.get_nodejs_version(str(nodejs_path))
            installed_tools.append(("Nodejs", node_version))
            npm_version = utils.get_npmjs_version(str(nodejs_path))
            installed_tools.append(("npmjs", npm_version))

        pandoc_exe = get_tool_path(r"\t\pandoc.exe")
        if pandoc_exe:
            pandoc_version = utils.get_pandoc_version(str(pandoc_exe.parent))
            installed_tools.append(("Pandoc", pandoc_version))

        vscode_exe = get_tool_path(r"\t\VSCode\Code.exe")
        if vscode_exe:
            vscode_version = utils.getFileProperties(str(vscode_exe))["FileVersion"]
            installed_tools.append(("VSCode", vscode_version))

        tool_lines = []
        for name, version in installed_tools:
            metadata = utils.get_package_metadata("tools.ini", name)
            url, description = metadata["url"], metadata["description"]
            tool_lines.append(f"[{name}]({url}) | {version} | {description}")
        return "\n".join(tool_lines)

    def _get_installed_packages_markdown(self) -> str:
        """Generates Markdown for installed packages section in package index."""
        if self.distribution is None:
            return "" # Distribution not initialized yet.
        self.installed_packages = self.distribution.get_installed_packages(update=True)
        package_lines = [
            f"[{pkg.name}]({pkg.url}) | {pkg.version} | {pkg.description}"
            for pkg in sorted(self.installed_packages, key=lambda p: p.name.lower())
        ]
        return "\n".join(package_lines)


    @property
    def winpython_version_name(self) -> str:
        """Returns the full WinPython version string."""
        return f"{self.python_full_version}.{self.build_number}{self.flavor}{self.release_level}"

    @property
    def python_full_version(self) -> str:
        """
        Retrieves the Python full version string from the distribution.
        Will be set after _extract_python is called and distribution is initialized.
        """
        if self.distribution is None:
            return "0.0.0" # Placeholder before initialization
        return utils.get_python_long_version(self.distribution.target)


    @property
    def python_executable_dir(self) -> str:
        """Returns the directory containing the Python executable."""
        python_path_dir = self.winpy_dir / self.python_dir_name if self.winpy_dir else None
        if python_path_dir and python_path_dir.is_dir():
            return str(python_path_dir)
        else:
            python_path_exe = self.winpy_dir / self.python_name if self.winpy_dir else None # Fallback for older structure
            return str(python_path_exe) if python_path_exe else ""

    @property
    def architecture_bits(self) -> int:
        """Returns the architecture (32 or 64 bits) of the distribution."""
        if self.distribution:
            return self.distribution.architecture
        return 64 # Default to 64 if distribution is not initialized yet

    @property
    def pre_path_entries(self) -> list[str]:
        """Returns a list of PATH entries to prepend to the environment."""
        return [
            r"Lib\site-packages\PyQt5",
            "",  # Python root directory
            "DLLs",
            "Scripts",
            r"..\t",
            r".." + self.NODEJS_PATH_REL,
        ]

    @property
    def post_path_entries(self) -> list[str]:
        """Returns a list of PATH entries to append to the environment."""
        return []

    @property
    def tools_directories(self) -> list[Path]:
        """Returns the list of tools directories to include."""
        return self.tools_dirs

    @property
    def docs_directories(self) -> list[Path]:
        """Returns the list of documentation directories to include."""
        default_docs_dir = Path(__file__).resolve().parent / "docs"
        if default_docs_dir.is_dir():
            return [default_docs_dir] + self.docs_dirs
        return self.docs_dirs

    def create_batch_script(self, name: str, contents: str, replacements: list[tuple[str, str]] = None):
        """
        Creates a batch script in the WinPython scripts directory.

        Args:
            name: The name of the batch script file.
            contents: The contents of the batch script.
            replacements: A list of tuples for text replacements in the content.
        """
        script_dir = self.winpy_dir / "scripts" if self.winpy_dir else None
        if not script_dir:
            print("Warning: WinPython directory not set, cannot create batch script.")
            return
        script_dir.mkdir(parents=True, exist_ok=True)
        final_contents = contents
        if replacements:
            for old_text, new_text in replacements:
                final_contents = final_contents.replace(old_text, new_text)
        script_path = script_dir / name
        with open(script_path, "w") as f:
            f.write(final_contents)
        print(f"Created batch script: {script_path}")

    def create_python_launcher_batch(
        self,
        name: str,
        script_name: str,
        working_dir: str = None,
        options: str = None,
        command: str = None,
    ):
        """
        Creates a batch file to launch a Python script within the WinPython environment.

        Args:
            name: The name of the batch file.
            script_name: The name of the Python script to execute.
            working_dir: Optional working directory for the script.
            options: Optional command-line options for the script.
            command: Optional command to execute python, defaults to python.exe or pythonw.exe
        """
        options_str = f" {options}" if options else ""
        if command is None:
            command = '"%WINPYDIR%\\pythonw.exe"' if script_name.endswith(".pyw") else '"%WINPYDIR%\\python.exe"'
        change_dir_cmd = f"cd /D {working_dir}\n" if working_dir else ""
        script_name_str = f" {script_name}" if script_name else ""
        batch_content = f"""@echo off
call "%~dp0env_for_icons.bat"
{change_dir_cmd}{command}{script_name_str}{options_str} %*"""
        self.create_batch_script(name, batch_content)

    def create_installer_7zip(self, installer_type: str = ".exe"):
        """
        Creates a WinPython installer using 7-Zip.

        Args:
            installer_type: Type of installer to create (".exe", ".7z", ".zip").
        """
        self._print_action(f"Creating WinPython installer ({installer_type})")
        template_name = "installer_7zip.bat"
        output_name = "installer_7zip-tmp.bat" # temp file to avoid overwriting template
        if installer_type not in [".exe", ".7z", ".zip"]:
            print(f"Warning: Unsupported installer type '{installer_type}'. Defaulting to .exe")
            installer_type = ".exe"

        replacements = [
            ("DISTDIR", str(self.winpy_dir)),
            ("ARCH", str(self.architecture_bits)),
            ("VERSION", f"{self.python_full_version}.{self.build_number}{self.flavor}"),
            (
                "VERSION_INSTALL",
                f'{self.python_full_version.replace(".", "")}{self.build_number}',
            ),
            ("RELEASELEVEL", self.release_level),
            ("INSTALLER_OPTION", installer_type), # Pass installer type as option to bat script
        ]

        build_installer_7zip(
            PORTABLE_DIR / template_name,
            PORTABLE_DIR / output_name,
            replacements
        )
        self._print_action_done()


    def _print_action(self, text: str):
        """Prints an action message with progress indicator."""
        if self.verbose:
            utils.print_box(text)
        else:
            print(f"{text}... ", end="", flush=True)

    def _print_action_done(self):
        """Prints "OK" to indicate action completion."""
        if not self.verbose:
            print("OK")

    def _extract_python_archive(self):
        """Extracts the Python zip archive to create the base Python environment."""
        self._print_action("Extracting Python archive")
        utils.extract_archive(
            str(self.python_zip_file),
            targetdir=str(self.winpy_dir), # Extract directly to winpy_dir
        )
        self._print_action_done()
        # Relocate to /python subfolder if needed (for newer structure) #2024-12-22 to /python
        python_target_dir = self.winpy_dir / self.python_dir_name
        if self.python_dir_name != self.python_name and not python_target_dir.is_dir():
            os.rename(self.winpy_dir / self.python_name, python_target_dir)


    def _copy_tools(self):
        """Copies development tools to the WinPython 't' directory."""
        tools_target_dir = self.winpy_dir / "t"
        self._print_action(f"Copying tools to {tools_target_dir}")
        tools_target_dir.mkdir(parents=True, exist_ok=True)
        for source_dir in self.tools_directories:
            if not source_dir.is_dir():
                print(f"Warning: Tools directory not found: {source_dir}")
                continue
            for item_name in os.listdir(source_dir):
                source_item = source_dir / item_name
                target_item = tools_target_dir / item_name
                copy_func = shutil.copytree if source_item.is_dir() else shutil.copy2
                try:
                    copy_func(source_item, target_item)
                    if self.verbose:
                        print(f"  Copied: {source_item} -> {target_item}")
                except Exception as e:
                    print(f"Error copying {source_item} to {target_item}: {e}")

        # Special handling for Node.js to move it up one level
        nodejs_current_dir = tools_target_dir / "n"
        nodejs_target_dir = self.winpy_dir / self.NODEJS_PATH_REL
        if nodejs_current_dir != nodejs_target_dir and nodejs_current_dir.is_dir():
            try:
                shutil.move(nodejs_current_dir, nodejs_target_dir)
            except Exception as e:
                print(f"Error moving Node.js directory: {e}")

        self._print_action_done()


    def _copy_documentation(self):
        """Copies documentation files to the WinPython 'docs' directory."""
        docs_target_dir = self.winpy_dir / "notebooks" / "docs"
        self._print_action(f"Copying documentation to {docs_target_dir}")
        docs_target_dir.mkdir(parents=True, exist_ok=True)
        for source_dir in self.docs_directories:
            if not source_dir.is_dir():
                print(f"Warning: Documentation directory not found: {source_dir}")
                continue
            for item_name in os.listdir(source_dir):
                source_item = source_dir / item_name
                target_item = docs_target_dir / item_name
                copy_func = shutil.copytree if source_item.is_dir() else shutil.copy2
                try:
                    copy_func(source_item, target_item)
                    if self.verbose:
                        print(f"  Copied: {source_item} -> {target_item}")
                except Exception as e:
                    print(f"Error copying {source_item} to {target_item}: {e}")
        self._print_action_done()


    def _copy_launchers(self):
        """Copies pre-made launchers to the WinPython directory."""
        self._print_action("Creating launchers")
        launchers_source_dir = PORTABLE_DIR / "launchers_final"
        for item in launchers_source_dir.rglob('*.exe'):
            shutil.copy2(item, self.winpy_dir)
            if self.verbose:
                print(f"  Copied launcher: {item.name} -> {self.winpy_dir}")
        for item in launchers_source_dir.rglob('licence*.*'):
            shutil.copy2(item, self.winpy_dir)
        self._print_action_done()

    def _copy_default_scripts(self):
        """Copies launchers and defeult scripts."""
        self._print_action("copying pre-made scripts")
        origin = PORTABLE_DIR / "scripts"
        destination = self.winpy_dir / "scripts"
        for item in origin.rglob('*.*'):
            shutil.copy2(item, destination)
            if self.verbose:
                print(f"  Copied : {item.name} -> {destination}")

    def _create_initial_batch_scripts(self):
        """Creates initial batch scripts, including environment setup."""
        self._print_action("Creating initial batch scripts")

        path_entries_str = ";".join([rf"%WINPYDIR%\{pth}" for pth in self.pre_path_entries])
        full_path_env_var = f"{path_entries_str};%PATH%;" + ";".join([rf"%WINPYDIR%\{pth}" for pth in self.post_path_entries])

        path_entries_ps_str = ";".join([rf"$env:WINPYDIR\\{pth}" for pth in self.pre_path_entries])
        full_path_ps_env_var = f"{path_entries_ps_str};$env:path;" + ";".join([rf"$env:WINPYDIR\\{pth}" for pth in self.post_path_entries])

        # Replacements for batch scripts (PyPy compatibility)
        exe_name = self.distribution.short_exe if self.distribution else "python.exe" # default to python.exe if distribution is not yet set
        batch_replacements = [
            (r"DIR%\\python.exe", rf"DIR%\\{exe_name}"),
            (r"DIR%\\PYTHON.EXE", rf"DIR%\\{exe_name}"),
        ]
        if self.distribution and (Path(self.distribution.target) / r"lib-python\3\idlelib").is_dir():
            batch_replacements.append((r"\Lib\idlelib", r"\lib-python\3\idlelib"))


        env_bat_content = f"""@echo off
set WINPYDIRBASE=%~dp0..

rem get a normalized path
set WINPYDIRBASETMP=%~dp0..
pushd %WINPYDIRBASETMP%
set WINPYDIRBASE=%__CD__%
if "%WINPYDIRBASE:~-1%"=="\\" set WINPYDIRBASE=%WINPYDIRBASE:~0,-1%
set WINPYDIRBASETMP=
popd

set WINPYDIR=%WINPYDIRBASE%\\{self.python_dir_name}
rem 2019-08-25 pyjulia needs absolutely a variable PYTHON=%WINPYDIR%\\python.exe
set PYTHON=%WINPYDIR%\\python.exe
set PYTHONPATHz=%WINPYDIR%;%WINPYDIR%\\Lib;%WINPYDIR%\\DLLs
set WINPYVER={self.winpython_version_name}

rem 2023-02-12 utf-8 on console to avoid pip crash
rem see https://github.com/pypa/pip/issues/11798#issuecomment-1427069681
set PYTHONIOENCODING=utf-8
rem set PYTHONUTF8=1 creates issues in "movable" patching

set HOME=%WINPYDIRBASE%\\settings
rem see https://github.com/winpython/winpython/issues/839
rem set USERPROFILE=%HOME%
set JUPYTER_DATA_DIR=%HOME%
set JUPYTER_CONFIG_DIR=%WINPYDIR%\\etc\\jupyter
set JUPYTER_CONFIG_PATH=%WINPYDIR%\\etc\\jupyter
set FINDDIR=%WINDIR%\\system32

rem Remove all double quotes
set PATH_CLEANED=%PATH:"=%
echo ";%PATH_CLEANED%;" | %FINDDIR%\\find.exe /C /I ";%WINPYDIR%\\;" >nul
if %ERRORLEVEL% NEQ 0 (
   set "PATH={full_path_env_var}"
   cd .
)
set PATH_CLEANED=

rem force default pyqt5 kit for Spyder if PyQt5 module is there
if exist "%WINPYDIR%\\Lib\\site-packages\\PyQt5\\__init__.py" set QT_API=pyqt5
"""
        self.create_batch_script("env.bat", env_bat_content, replacements=batch_replacements)


        ps1_content = r"""### WinPython_PS_Prompt.ps1 ###
$0 = $myInvocation.MyCommand.Definition
$dp0 = [System.IO.Path]::GetDirectoryName($0)
# $env:PYTHONUTF8 = 1 would create issues in "movable" patching
$env:WINPYDIRBASE = "$dp0\.."
# get a normalize path
# http://stackoverflow.com/questions/1645843/resolve-absolute-path-from-relative-path-and-or-file-name
$env:WINPYDIRBASE = [System.IO.Path]::GetFullPath( $env:WINPYDIRBASE )

# avoid double_init (will only resize screen)
if (-not ($env:WINPYDIR -eq [System.IO.Path]::GetFullPath( $env:WINPYDIRBASE+""" + '"\\' + self.python_dir_name + '"' + r""")) ) {
$env:WINPYDIR = $env:WINPYDIRBASE+""" + '"\\' + self.python_dir_name + '"' + r"""
# 2019-08-25 pyjulia needs absolutely a variable PYTHON=%WINPYDIR%python.exe
$env:PYTHON = "%WINPYDIR%\python.exe"
$env:PYTHONPATHz = "%WINPYDIR%;%WINPYDIR%\Lib;%WINPYDIR%\DLLs"

$env:WINPYVER = '""" + self.winpython_version_name + r"""'
# rem 2023-02-12 try utf-8 on console
# rem see https://github.com/pypa/pip/issues/11798#issuecomment-1427069681
$env:PYTHONIOENCODING = "utf-8"

$env:HOME = "$env:WINPYDIRBASE\settings"

# rem read https://github.com/winpython/winpython/issues/839
# $env:USERPROFILE = "$env:HOME"

$env:WINPYDIRBASE = ""
$env:JUPYTER_DATA_DIR = "$env:HOME"

if (-not $env:PATH.ToLower().Contains(";"+ $env:WINPYDIR.ToLower()+ ";"))  {
 $env:PATH = """ + '"' + full_path_ps_env_var + '"' + r""" }

#rem force default pyqt5 kit for Spyder if PyQt5 module is there
if (Test-Path "$env:WINPYDIR\Lib\site-packages\PyQt5\__init__.py") { $env:QT_API = "pyqt5" } 

# PyQt5 qt.conf creation and winpython.ini creation done via Winpythonini.py (called per env_for_icons.bat for now)
# Start-Process -FilePath $env:PYTHON -ArgumentList ($env:WINPYDIRBASE + '\scripts\WinPythonIni.py')


### Set-WindowSize

Function Set-WindowSize {
Param([int]$x=$host.ui.rawui.windowsize.width,
      [int]$y=$host.ui.rawui.windowsize.heigth,
      [int]$buffer=$host.UI.RawUI.BufferSize.heigth)
    $buffersize = new-object System.Management.Automation.Host.Size($x,$buffer)
    $host.UI.RawUI.BufferSize = $buffersize
    $size = New-Object System.Management.Automation.Host.Size($x,$y)
    $host.ui.rawui.WindowSize = $size
}
# Windows10 yelling at us with 150 40 6000
# Set-WindowSize 195 40 6000 

### Colorize to distinguish
$host.ui.RawUI.BackgroundColor = "Black"
$host.ui.RawUI.ForegroundColor = "White"
}
"""
        self.create_batch_script("WinPython_PS_Prompt.ps1", ps1_content, replacements=batch_replacements)

        self._print_action_done()


    def _create_standard_batch_scripts(self):
        """Creates standard WinPython batch scripts for various actions."""
        self._print_action("Creating standard batch scripts")

        exe_name = self.distribution.short_exe if self.distribution else "python.exe"
        batch_replacements = [
            (r"DIR%\\python.exe", rf"DIR%\\{exe_name}"),
            (r"DIR%\\PYTHON.EXE", rf"DIR%\\{exe_name}"),
        ]
        if self.distribution and (Path(self.distribution.target) / r"lib-python\3\idlelib").is_dir():
            batch_replacements.append((r"\Lib\idlelib", r"\lib-python\3\idlelib"))

        self.create_batch_script("readme.txt", """These batch files are required to run WinPython icons.
These files should help the user writing his/her own
The environment variables are set-up in 'env.bat' and 'env_for_icons.bat'.""",
        )

        for ini_patch_script in [
            ("make_working_directory_be_not_winpython.bat", "[active_environment", "[inactive_environment", "[inactive_environment_per_user]", "[active_environment_per_user]"),
            ("make_working_directory_be_winpython.bat", "[active_environment", "[inactive_environment"),
            ("make_working_directory_and_userprofile_be_winpython.bat", "[active_environment", "[inactive_environment", "[inactive_environment_common]", "[active_environment_common]")
            ]:
            name, patch1_start, patch1_end, *patch2 = ini_patch_script
            content = f"""call "%~dp0env_for_icons.bat"
"%PYTHON%" -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%~dp0..\\settings\winpython.ini', '{patch1_start}', '{patch1_end}' )"
"""
            if patch2:
                content += f""""%PYTHON%" -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%~dp0..\\settings\winpython.ini', '{patch2[0]}', '{patch2[1]}' )" """
            self.create_batch_script(name, content)

        self._print_action_done()


    def build(self, remove_existing: bool = True, requirements=None, winpy_dirname: str = None):
        """Make WinPython distribution in target directory from the installers
        located in wheels_dir

        remove_existing=True: (default) install all from scratch
        remove_existing=False: for complementary purposes (create installers)
        requirements=file(s) of requirements (separated by space if several)"""
        python_zip_filename = self.python_zip_file.name
        print(f"Building WinPython with Python archive: {python_zip_filename}")

        if winpy_dirname is None:
            raise RuntimeError("WinPython base directory to create is undefined") 
        else:
            self.winpy_dir = self.target_dir / winpy_dirname # Create/re-create the WinPython base directory
        self._print_action(f"Creating WinPython {self.winpy_dir} base directory")
        if self.winpy_dir.is_dir() and remove_existing:
            try:
                shutil.rmtree(self.winpy_dir, onexc=utils.onerror)
            except TypeError: # before 3.12
                shutil.rmtree(self.winpy_dir, onerror=utils.onerror)    
        os.makedirs(self.winpy_dir, exist_ok=True)    
        if remove_existing:
            # preventive re-Creation of settings directory
            # (necessary if user is starting an application with a batch)
            (self.winpy_dir / "settings" / "AppData" / "Roaming").mkdir(parents=True, exist_ok=True) # Ensure settings dir exists
            self._extract_python_archive()

        self._print_action_done()
        self.distribution = wppm.Distribution(
            self.python_executable_dir,
            verbose=self.verbose,
            indent=True,
        )

        if remove_existing:
            self._create_initial_batch_scripts()
            self._copy_default_scripts()
            self._create_standard_batch_scripts()
            self._copy_launchers()

            utils.python_execmodule("ensurepip", self.distribution.target) # Ensure pip is installed for PyPy
            self.distribution.patch_standard_packages("pip")

            # Upgrade essential packages
            essential_packages = ["pip", "setuptools", "wheel", "winpython"]
            for package_name in essential_packages:
                actions = ["install", "--upgrade", "--pre", package_name] + self.install_options
                print(f"Piping: {' '.join(actions)}")
                self._print_action(f"Piping: {' '.join(actions)}")
                self.distribution.do_pip_action(actions)
                self.distribution.patch_standard_packages(package_name)

            self._copy_tools()
            self._copy_documentation()

            if requirements:
                if not list(requirements) == requirements:
                    requirements = requirements.split()
                for req in requirements:
                    actions = ["install", "-r", req]
                    if self.install_options is not None:
                        actions += self.install_options
                    print(f"piping {' '.join(actions)}")
                    self._print_action(f"piping {' '.join(actions)}")
                    self.distribution.do_pip_action(actions)

            self.distribution.patch_standard_packages()

            self._print_action("Cleaning up distribution")
            self.distribution.clean_up()
            self._print_action_done()
        # Writing package index
        self._print_action("Writing package index")
        # winpyver2 = the version without build part but with self.distribution.architecture
        self.winpyver2 = f"{self.python_full_version}.{self.build_number}"
        fname = str(
            self.winpy_dir.parent
            / (
                f"WinPython{self.flavor}-"
                + f"{self.distribution.architecture}bit-"
                + f"{self.winpyver2}.md"
            )
        )
        open(fname, "w", encoding='utf-8').write(self.package_index_markdown)
        # Copy to winpython/changelogs

        shutil.copyfile(
            fname,
            str(Path(CHANGELOGS_DIR) / Path(fname).name),
        )
        self._print_action_done()

        # Writing changelog
        self._print_action("Writing changelog")
        diff.write_changelog(
            self.winpyver2,
            basedir=self.base_dir,
            flavor=self.flavor,
            release_level=self.release_level,
            architecture=self.distribution.architecture,
        )
        self._print_action_done()


def rebuild_winpython_package(source_dir: Path, target_dir: Path, architecture: int = 64, verbose: bool = False):
    """Rebuilds the winpython package from source using flit."""
    for filename in os.listdir(target_dir):
        if filename.startswith("winpython-") and filename.endswith((".exe", ".whl", ".gz")):
            os.remove(Path(target_dir) / filename)

    utils.buildflit_wininst(
        str(source_dir),
        copy_to=str(target_dir),
        verbose=verbose,
    )


def _parse_list_argument(arg_value: str | list[str]) -> list[str]:
    """Parses a string or list argument into a list of strings."""
    if arg_value is None:
        return []
    if isinstance(arg_value, str):
        return arg_value.split()
    return list(arg_value) # Ensure it's a list if already a list-like object


def make_all(
    build_number: int,
    release_level: str,
    pyver: str,
    architecture: int,
    basedir: Path,
    verbose: bool = False,
    remove_existing: bool = True,
    create_installer: str = "True",
    install_options=["--no-index"],
    flavor: str = "",
    requirements: str | list[Path] = None,
    find_links: str | list[Path] = None,
    source_dirs: Path = None,
    toolsdirs: str | list[Path] = None,
    docsdirs: str | list[Path] = None,
    python_target_release: str = None, # e.g. "37101" for 3.7.10
):
    """Make WinPython distribution, for a given base directory and
    architecture:
    `build_number`: build number [int]
    `release_level`: release level (e.g. 'beta1', '') [str]
    `pyver`: python version ('3.4' or 3.5')
    `architecture`: [int] (32 or 64)
    `basedir`: where will be created tmp_wheel and Winpython build
              r'D:\Winpython\basedir34'.
    `requirements`: the package list for pip r'D:\requirements.txt',
    `install_options`: pip options r'--no-index --pre --trusted-host=None',
    `find_links`: package directories r'D:\Winpython\packages.srcreq',
    `source_dirs`: the python.zip + rebuilt winpython wheel package directory,
    `toolsdirs`: r'D:\WinPython\basedir34\t.Slim',
    `docsdirs`: r'D:\WinPython\basedir34\docs.Slim'"""

    assert basedir is not None, "The *basedir* directory must be specified"
    assert architecture in (32, 64)
    utils.print_box(
        f"Making WinPython {architecture}bits"
        + f" at {Path(basedir) / ('bu' + flavor)}"
    )

    # Create Build director, where Winpython will be constructed
    builddir = str(Path(basedir) / ("bu" + flavor))
    os.makedirs(Path(builddir), exist_ok=True)    
    # use source_dirs as the directory to re-build Winpython wheel
    wheels_dir = source_dirs

    # Rebuild WinPython package
    winpython_source_dir = Path(__file__).resolve().parent
    rebuild_winpython_package(
        source_dir=winpython_source_dir,
        target_dir=wheels_dir,
        architecture=architecture,
        verbose=verbose,
    )

    # Parse list arguments
    tools_dirs_list = _parse_list_argument(toolsdirs)
    docs_dirs_list = _parse_list_argument(docsdirs)
    install_options_list = _parse_list_argument(install_options)
    find_links_dirs_list = _parse_list_argument(find_links)
    requirements_files_list = [Path(f) for f in _parse_list_argument(requirements) if f] # ensure Path objects

    find_links_options = [f"--find-links={link}" for link in find_links_dirs_list + [wheels_dir]]
    builder = WinPythonDistributionBuilder(
        build_number,
        release_level,
        builddir,
        wheels_dir=wheels_dir,
        tools_dirs=[Path(d) for d in tools_dirs_list],
        docs_dirs=[Path(d) for d in docs_dirs_list],
        verbose=verbose,
        base_dir=basedir,
        install_options=install_options_list + find_links_options,
        flavor=flavor,
    )
    # define a pre-defined winpydir, instead of having to guess

    # extract the python subversion to get WPy64-3671b1
    my_x = "".join(builder.python_name.replace(".amd64", "").split(".")[-2:-1])
    while not my_x.isdigit() and len(my_x) > 0:
        my_x = my_x[:-1]
    # simplify for PyPy
    if not python_target_release == None:
        winpy_dirname = (
            "WPy"
            + f"{architecture}"
            + "-"
            + python_target_release
            + ""
            + f"{build_number}"
        ) + release_level
    # + flavor
    else:
        winpy_dirname = (
            "WPy"
            + f"{architecture}"
            + "-"
            + pyver.replace(".", "")
            + ""
            + my_x
            + ""
            + f"{build_number}"
        ) + release_level
    # + flavor

    builder.build(
        remove_existing=remove_existing,
        requirements=requirements_files_list,
        winpy_dirname=winpy_dirname,
    )
    if str(create_installer).lower() != "false":
        if ".zip" in str(create_installer).lower():
            builder.create_installer_7zip(".zip")
        if ".7z" in str(create_installer).lower():
            builder.create_installer_7zip(".7z")
        if "7zip" in str(create_installer).lower():
            builder.create_installer_7zip(".exe")

    return builder


if __name__ == "__main__":
    # DO create only one version at a time
    # You may have to manually delete previous build\winpython-.. directory

    make_all(
        1,
        release_level="build3",
        pyver="3.4",
        basedir=r"D:\Winpython\basedir34",
        verbose=True,
        architecture=64,
        flavor="Barebone",
        requirements=r"D:\Winpython\basedir34\barebone_requirements.txt",
        install_options=r"--no-index --pre --trusted-host=None",
        find_links=r"D:\Winpython\packages.srcreq",
        source_dirs=r"D:\WinPython\basedir34\packages.win-amd64",
        toolsdirs=r"D:\WinPython\basedir34\t.Slim",
        docsdirs=r"D:\WinPython\basedir34\docs.Slim",
    )