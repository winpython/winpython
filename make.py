# -*- coding: utf-8 -*-
#
# WinPython build script
# Copyright © 2012 Pierre Raybaut
# Copyright © 2014-2025+ The Winpython development team https://github.com/winpython/
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

import os
import re
import shutil
from pathlib import Path
from wppm import wppm, utils

PORTABLE_DIRECTORY = Path(__file__).parent / "portable"
assert PORTABLE_DIRECTORY.is_dir(), f"Portable directory not found: {PORTABLE_DIRECTORY}"

def copy_items(source_directories: list[Path], target_directory: Path, verbose: bool = False):
    """Copies items from source directories to the target directory."""
    target_directory.mkdir(parents=True, exist_ok=True)
    for source_dir in source_directories:
        if not source_dir.is_dir():
            print(f"Warning: Source directory not found: {source_dir}")
            continue
        for source_item in source_dir.iterdir():
            target_item = target_directory / source_item.name
            copy_function = shutil.copytree if source_item.is_dir() else shutil.copy2
            try:
                copy_function(source_item, target_item)
                if verbose:
                    print(f"Copied: {source_item} -> {target_item}")
            except Exception as e:
                print(f"Error copying {source_item} to {target_item}: {e}")

def parse_list_argument(argument_value: str | list[str], separator=" ") -> list[str]:
    """Parse a separated list argument into a list of strings."""
    if not argument_value: return []
    return argument_value.split(separator) if isinstance(argument_value, str) else list(argument_value)

class WinPythonDistributionBuilder:
    """Builds a WinPython distribution."""

    def __init__(self, build_number: int, release_level: str, target_directory: Path, wheels_directory: Path,
                 tools_directories: list[Path] = None, verbose: bool = False,
                 flavor: str = ""):
        """
        Initializes the WinPythonDistributionBuilder.
        Args:
            build_number: The build number (integer).
            release_level: The release level (e.g., "beta", "").
            target_directory: The base directory below which WinPython will be created.
            wheels_directory: Directory containing wheel files for packages.
            tools_directories: List of directories containing development tools to include.
            verbose: Enable verbose output.
            flavor: WinPython flavor (e.g., "Barebone").
        """
        self.build_number = build_number
        self.release_level = release_level
        self.target_directory = Path(target_directory)
        self.wheels_directory = Path(wheels_directory)
        self.tools_directories = tools_directories or []
        self.verbose = verbose
        self.winpython_directory: Path | None = None
        self.distribution: wppm.Distribution | None = None
        self.flavor = flavor
        self.python_zip_file: Path = self._get_python_zip_file()
        self.python_name = self.python_zip_file.stem
        self.python_directory_name = "python"

    def _get_python_zip_file(self) -> Path:
        """Finds the Python .zip file in the wheels directory."""
        for source_item in self.wheels_directory.iterdir():
            if re.match(r"(pypy3|python-).*\.zip", source_item.name):
                return source_item
        raise RuntimeError(f"Could not find Python zip package in {self.wheels_directory}")

    @property
    def winpython_version_name(self) -> str:
        """Returns the full WinPython version string."""
        return f"{self.python_full_version}.{self.build_number}{self.flavor}{self.release_level}"

    @property
    def python_full_version(self) -> str:
        """Retrieves the Python full version string from the distribution."""
        return utils.get_python_long_version(self.distribution.target) if self.distribution else "0.0.0"

    def _print_action(self, text: str):
        """Prints an action message with progress indicator."""
        utils.print_box(text) if self.verbose else print(f"{text}...", end="", flush=True)

    def _extract_python_archive(self):
        """Extracts the Python zip archive to create the base Python environment."""
        self._print_action("Extracting Python archive")
        utils.extract_archive(self.python_zip_file, self.winpython_directory)
        # Relocate to /python subfolder if needed (for newer structure) #2024-12-22 to /python
        expected_python_directory = self.winpython_directory / self.python_directory_name
        if self.python_directory_name != self.python_name and not expected_python_directory.is_dir():
            os.rename(self.winpython_directory / self.python_name, expected_python_directory)

    def _copy_essential_files(self):
        """Copies pre-made objects"""
        self._print_action("Copying launchers")
        copy_items([PORTABLE_DIRECTORY / "launchers_final"], self.winpython_directory, self.verbose)

        tools_target_directory = self.winpython_directory / "t"
        self._print_action(f"Copying tools to {tools_target_directory}")
        copy_items(self.tools_directories, tools_target_directory, self.verbose)

    def _create_env_config(self):
        """Creates environment setup"""
        self._print_action("Creating env.ini environment setup")
        executable_name = self.distribution.short_exe if self.distribution else "python.exe"
        config = {
            "WINPYthon_exe": executable_name,
            "WINPYthon_subdirectory_name": self.python_directory_name,
            "WINPYVER": self.winpython_version_name,
            "WINPYVER2": f"{self.python_full_version}.{self.build_number}",
            "WINPYFLAVOR": self.flavor,
            "WINPYARCH": self.distribution.architecture if self.distribution else 64,
        }
        env_path = self.winpython_directory / "scripts" / "env.ini"
        env_path.parent.mkdir(parents=True, exist_ok=True)
        self._print_action(f"Creating env.ini environment {env_path}")
        env_path.write_text("\n".join(f"{k}={v}" for k, v in config.items()))

    def build(self, winpy_dir: Path = None):
        """Make or finalise WinPython distribution in the target directory"""
        print(f"Building WinPython with Python archive: {self.python_zip_file.name}")
        self.winpython_directory = Path(winpy_dir)
        self._print_action(f"Creating WinPython {self.winpython_directory} base directory")
        if self.winpython_directory.is_dir() and len(self.winpython_directory.parts)>=4:
            shutil.rmtree(self.winpython_directory)
        # preventive re-Creation of settings directory
        (self.winpython_directory / "settings" / "AppData" / "Roaming").mkdir(parents=True, exist_ok=True)

        self._extract_python_archive()
        self.distribution = wppm.Distribution(self.winpython_directory / self.python_directory_name, verbose=self.verbose)
        self._copy_essential_files()
        self._create_env_config()

def make_all(build_number: int, release_level: str, basedir_wpy: Path = None,
             verbose: bool = False,
             flavor: str = "",
             source_dirs: Path = None, toolsdirs: str | list[Path] = None,
):
    """
    Make a WinPython distribution for a given set of parameters:
    Args:
        build_number: build number [int]
        release_level: release level (e.g. 'beta1', '') [str]
        basedir_wpy:  top directory of the build (c:\...\Wpy...)
        verbose: Enable verbose output (bool).
        flavor: WinPython flavor (str).
        source_dirs: the python.zip
        toolsdirs: Directory with development tools r'D:\WinPython\basedir34\t.Slim'
    """
    assert basedir_wpy is not None, "The *winpython_dirname* directory must be specified"

    tools_directories = [Path(d) for d in parse_list_argument(toolsdirs, ",")]
    winpy_dir = Path(basedir_wpy)
    utils.print_box(f"Making WinPython at {winpy_dir}")
    os.makedirs(winpy_dir, exist_ok=True)

    builder = WinPythonDistributionBuilder(
        build_number, release_level, winpy_dir.parent, wheels_directory=source_dirs,
        tools_directories=tools_directories,
        verbose=verbose, flavor=flavor
    )
    builder.build(winpy_dir)

if __name__ == "__main__":
    make_all(
        build_number=1,
        release_level="b3",
        basedir_wpy=r"D:\WinPython\bd314\budot\WPy64-31401b3",
        verbose=True,
        flavor="dot",
        source_dirs=r"D:\WinPython\bd314\packages.win-amd64",
        toolsdirs=r"D:\WinPython\bd314\t.Slim",
    )
