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
import subprocess
import sys
from pathlib import Path
from wppm import wppm, utils, diff

# Define constant paths for clarity
CHANGELOGS_DIRECTORY = Path(__file__).parent / "changelogs"
PORTABLE_DIRECTORY = Path(__file__).parent / "portable"
NODEJS_RELATIVE_PATH = "n"  # Relative path within WinPython dir

# Ensure necessary directories exist at the start
assert CHANGELOGS_DIRECTORY.is_dir(), f"Changelogs directory not found: {CHANGELOGS_DIRECTORY}"
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
    if not argument_value:
        return []
    return argument_value.split(separator) if isinstance(argument_value, str) else list(argument_value)

class WinPythonDistributionBuilder:
    """Builds a WinPython distribution."""

    def __init__(self, build_number: int, release_level: str, target_directory: Path, wheels_directory: Path,
                 tools_directories: list[Path] = None, verbose: bool = False,
                 install_options: list[str] = None, flavor: str = ""):
        """
        Initializes the WinPythonDistributionBuilder.
        Args:
            build_number: The build number (integer).
            release_level: The release level (e.g., "beta", "").
            target_directory: The base directory below which WinPython will be created.
            wheels_directory: Directory containing wheel files for packages.
            tools_directories: List of directories containing development tools to include.
            verbose: Enable verbose output.
            install_options: Additional pip install options.
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
        self.install_options = install_options or []
        self.flavor = flavor
        self.python_zip_file: Path = self._get_python_zip_file()
        self.python_name = self.python_zip_file.stem
        self.python_directory_name = "python"

    def _get_python_zip_file(self) -> Path:
        """Finds the Python .zip file in the wheels directory."""
        for source_item in self.wheels_directory.iterdir():
            if re.match(r"(pypy3|python-)([0-9]|[a-zA-Z]|.)*.zip", source_item.name):
                return source_item
        raise RuntimeError(f"Could not find Python zip package in {self.wheels_directory}")

    @property
    def package_index_markdown(self) -> str:
        """Generates a Markdown formatted package index page."""
        return self.distribution.generate_package_index_markdown(
        self.python_executable_directory,
        self.winpyver2,
        self.flavor,
        self.architecture_bits,
        self.release_level
    )

    @property
    def winpython_version_name(self) -> str:
        """Returns the full WinPython version string."""
        return f"{self.python_full_version}.{self.build_number}{self.flavor}{self.release_level}"

    @property
    def python_full_version(self) -> str:
        """Retrieves the Python full version string from the distribution."""
        return utils.get_python_long_version(self.distribution.target) if self.distribution else "0.0.0"

    @property
    def python_executable_directory(self) -> str:
        """Returns the directory containing the Python executable."""
        if self.winpython_directory:
            python_path_directory = self.winpython_directory / self.python_directory_name
            return str(python_path_directory) if python_path_directory.is_dir() else str(self.winpython_directory / self.python_name)
        return ""

    @property
    def architecture_bits(self) -> int:
        """Returns the architecture (32 or 64 bits) of the distribution."""
        return self.distribution.architecture if self.distribution else 64

    def create_installer_7zip(self, installer_type: str = "exe", compression= "mx5"):
        """Creates a WinPython installer using 7-Zip: "exe", "7z", "zip")"""
        self._print_action(f"Creating WinPython installer ({installer_type})")
        DISTDIR = self.winpython_directory
        filename_stem = f"Winpython{self.architecture_bits}-{self.python_full_version}.{self.build_number}{self.flavor}{self.release_level}"
        fullfilename = DISTDIR.parent / (filename_stem + "." + installer_type)
        if installer_type not in ["exe", "7z", "zip"]:
            return
        sfx_option = "-sfx7z.sfx" if installer_type == "exe" else ""
        zip_option = "-tzip" if installer_type == "zip" else ""
        compress_level = "mx5" if compression == "" else compression 
        command = f'"{utils.find_7zip_executable()}" {zip_option} -{compress_level} a "{fullfilename}" "{DISTDIR}" {sfx_option}'
        print(f'Executing 7-Zip script: "{command}"')
        try:
            subprocess.run(command, shell=True, check=True, stderr=sys.stderr, stdout=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Error executing 7-Zip script: {e}", file=sys.stderr)

    def _print_action(self, text: str):
        """Prints an action message with progress indicator."""
        if self.verbose:
            utils.print_box(text)
        else:
            print(f"{text}... ", end="", flush=True)

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

    def _create_initial_batch_scripts(self):
        """Creates initial batch scripts, including environment setup."""
        self._print_action("Creating initial batch scripts")
        # Replacements for batch scripts (PyPy compatibility)
        executable_name = self.distribution.short_exe if self.distribution else "python.exe"  # default to python.exe if distribution is not yet set
        init_variables = [('WINPYthon_exe', executable_name), ('WINPYthon_subdirectory_name', self.python_directory_name), ('WINPYVER', self.winpython_version_name)]
        init_variables += [('WINPYVER2', f"{self.python_full_version}.{self.build_number}"), ('WINPYFLAVOR', self.flavor), ('WINPYARCH', self.architecture_bits)]
        with open(self.winpython_directory / "scripts" / "env.ini", "w") as f:
            f.writelines([f'{a}={b}\n' for a, b in init_variables])

    def build(self, rebuild: bool = True, winpy_dir: Path = None):
        """Make or finalise WinPython distribution in the target directory"""
        print(f"Building WinPython with Python archive: {self.python_zip_file.name}")
        if winpy_dir is None:
            raise RuntimeError("WinPython base directory to create is undefined")
        self.winpython_directory = winpy_dir

        if rebuild:
            self._print_action(f"Creating WinPython {self.winpython_directory} base directory")
            if self.winpython_directory.is_dir():
                shutil.rmtree(self.winpython_directory)
            os.makedirs(self.winpython_directory, exist_ok=True)
            # preventive re-Creation of settings directory
            (self.winpython_directory / "settings" / "AppData" / "Roaming").mkdir(parents=True, exist_ok=True)
            self._extract_python_archive()

        self.distribution = wppm.Distribution(self.python_executable_directory, verbose=self.verbose)

        if rebuild:
            self._copy_essential_files()
            self._create_initial_batch_scripts()
            utils.python_execmodule("ensurepip", self.distribution.target)
            self.distribution.patch_standard_packages("pip")
            essential_packages = ["pip", "setuptools", "wheel", "wppm"]
            for package_name in essential_packages:
                actions = ["install", "--upgrade", "--pre", package_name] + self.install_options
                self._print_action(f"Piping: {' '.join(actions)}")
                self.distribution.do_pip_action(actions)
                self.distribution.patch_standard_packages(package_name)

        self._print_action("Writing package index")
        self.winpyver2 = f"{self.python_full_version}.{self.build_number}"
        output_markdown_filename = str(self.winpython_directory.parent / f"WinPython{self.flavor}-{self.distribution.architecture}bit-{self.winpyver2}.md")
        with open(output_markdown_filename, "w", encoding='utf-8') as f:
            f.write(self.package_index_markdown)

        self._print_action("Writing changelog")
        shutil.copyfile(output_markdown_filename, str(Path(CHANGELOGS_DIRECTORY) / Path(output_markdown_filename).name))
        diff.write_changelog(self.winpyver2, None, CHANGELOGS_DIRECTORY, self.flavor, self.distribution.architecture, basedir=self.winpython_directory.parent)

def make_all(build_number: int, release_level: str, basedir_wpy: Path = None,
             verbose: bool = False, rebuild: bool = True, create_installer: str = "True", install_options=["--no-index"],
             flavor: str = "", find_links: str | list[Path] = None,
             source_dirs: Path = None, toolsdirs: str | list[Path] = None,
):
    """
    Make a WinPython distribution for a given set of parameters:
    Args:
        build_number: build number [int]
        release_level: release level (e.g. 'beta1', '') [str]
        basedir_wpy:  top directory of the build (c:\...\Wpy...)
        verbose: Enable verbose output (bool).
        rebuild: Whether to rebuild the distribution (bool).
        create_installer: Type of installer to create (str).
        install_options: pip options (r'--no-index --pre --trusted-host=None')
        flavor: WinPython flavor (str).
        find_links: package directories (r'D:\Winpython\packages.srcreq')
        source_dirs: the python.zip + rebuilt winpython wheel package directory
        toolsdirs: Directory with development tools r'D:\WinPython\basedir34\t.Slim'
    """
    assert basedir_wpy is not None, "The *winpython_dirname* directory must be specified"

    tools_dirs_list = parse_list_argument(toolsdirs, ",")
    install_options_list = parse_list_argument(install_options, " ")
    find_links_dirs_list = parse_list_argument(find_links, ",")
    find_links_options = [f"--find-links={link}" for link in find_links_dirs_list + [source_dirs]]
    winpy_dir = Path(basedir_wpy)

    if rebuild:
        utils.print_box(f"Making WinPython at {winpy_dir}")
        os.makedirs(winpy_dir, exist_ok=True)

    builder = WinPythonDistributionBuilder(
        build_number, release_level, winpy_dir.parent, wheels_directory=source_dirs,
        tools_directories=[Path(d) for d in tools_dirs_list],
        verbose=verbose,
        install_options=install_options_list + find_links_options,
        flavor=flavor
    )

    builder.build(rebuild=rebuild, winpy_dir=winpy_dir)

    for commmand in create_installer.lower().replace("7zip",".exe").split('.'):
        installer_type, compression = (commmand + "-").split("-")[:2]
        builder.create_installer_7zip(installer_type, compression)

if __name__ == "__main__":
    # DO create only one Winpython distribution at a time
    make_all(
        build_number=1,
        release_level="b3",
        basedir_wpy=r"D:\WinPython\bd314\budot\WPy64-31401b3",
        verbose=True,
        flavor="dot",
        install_options=r"--no-index --pre --trusted-host=None",
        find_links=r"D:\Winpython\packages.srcreq",
        source_dirs=r"D:\WinPython\bd314\packages.win-amd64",
        toolsdirs=r"D:\WinPython\bd314\t.Slim",
    )
