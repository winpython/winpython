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
from winpython import wppm, utils
# Local import
import diff

# Define constant paths for clarity
CHANGELOGS_DIRECTORY = Path(__file__).parent / "changelogs"
PORTABLE_DIRECTORY = Path(__file__).parent / "portable"

# Ensure necessary directories exist at the start
assert CHANGELOGS_DIRECTORY.is_dir(), f"Changelogs directory not found: {CHANGELOGS_DIRECTORY}"
assert PORTABLE_DIRECTORY.is_dir(), f"Portable directory not found: {PORTABLE_DIRECTORY}"

def find_7zip_executable() -> str:
    """Locates the 7-Zip executable (7z.exe)."""
    possible_program_files = [r"C:\Program Files", r"C:\Program Files (x86)", Path(sys.prefix).parent / "t"]
    for base_dir in possible_program_files:
        if (executable_path := Path(base_dir) / "7-Zip" / "7z.exe").is_file():
            return str(executable_path)
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
    with open(filepath, "r") as f:
        lines = f.readlines()
    updated_lines = lines.copy()  # Create a mutable copy of lines

    for index, line in enumerate(lines):
        for prefix, new_text in replacements:
            start_prefix = f"set {prefix}=" if not prefix.startswith("!") else prefix
            if line.startswith(start_prefix):
                updated_lines[index] = f"{start_prefix}{new_text}\n"

    with open(filepath, "w") as f:
            f.writelines(updated_lines)
    print(f"Updated 7-zip script: {filepath}")

def build_installer_7zip(script_template_path: Path, output_script_path: Path, replacements: list[tuple[str, str]]):
    """
    Creates a 7-Zip installer script by copying a template and applying text replacements.

    Args:
        script_template_path: Path to the template 7-Zip script (.bat file).
        output_script_path: Path to save the generated 7-Zip script.
        replacements: A list of tuples for text replacements (prefix, new_text).
    """
    shutil.copy(script_template_path, output_script_path)

    # Standard replacements for all 7zip scripts
    data_to_replace = [
        ("PORTABLE_DIR", str(PORTABLE_DIRECTORY)),
        ("SEVENZIP_EXE", find_7zip_executable()),
    ] + replacements

    replace_lines_in_file(output_script_path, data_to_replace)

    try:
        # Execute the generated 7-Zip script, with stdout=sys.stderr to see 7zip compressing
        command = f'"{output_script_path}"'
        print(f"Executing 7-Zip script: {command}")
        subprocess.run(command, shell=True, check=True, stderr=sys.stderr, stdout=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error executing 7-Zip script: {e}", file=sys.stderr)

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
    if argument_value is None:
        return []
    if isinstance(argument_value, str):
        return argument_value.split(separator)
    return list(argument_value)

class WinPythonDistributionBuilder:
    """Builds a WinPython distribution."""

    NODEJS_RELATIVE_PATH = "n"  # Relative path within WinPython dir

    def __init__(self, build_number: int, release_level: str, target_directory: Path, wheels_directory: Path,
                 tools_directories: list[Path] = None, documentation_directories: list[Path] = None, verbose: bool = False,
                 base_directory: Path = None, install_options: list[str] = None, flavor: str = ""):
        """
        Initializes the WinPythonDistributionBuilder.

        Args:
            build_number: The build number (integer).
            release_level: The release level (e.g., "beta", "").
            target_directory: The base directory where WinPython will be created.
            wheels_directory: Directory containing wheel files for packages.
            tools_directories: List of directories containing development tools to include.
            documentation_directories: List of directories containing documentation to include.
            verbose: Enable verbose output.
            base_directory: Base directory for building (optional, for relative paths).
            install_options: Additional pip install options.
            flavor: WinPython flavor (e.g., "Barebone").
        """
        self.build_number = build_number
        self.release_level = release_level
        self.target_directory = Path(target_directory)
        self.wheels_directory = Path(wheels_directory)
        self.tools_directories = tools_directories or []
        self.documentation_directories = documentation_directories or []
        self.verbose = verbose
        self.winpython_directory: Path | None = None
        self.distribution: wppm.Distribution | None = None
        self.base_directory = base_directory
        self.install_options = install_options or []
        self.flavor = flavor
        self.python_zip_file: Path = self._get_python_zip_file()
        self.python_name = self.python_zip_file.stem
        self.python_directory_name = "python"

    def _get_python_zip_file(self) -> Path:
        """Finds the Python .zip file in the wheels directory."""
        for source_item in self.wheels_directory.iterdir():
            if re.match("(pypy3|python-)([0-9]|[a-zA-Z]|.)*.zip", source_item.name):
                return source_item
        raise RuntimeError(f"Could not find Python zip package in {self.wheels_directory}")

    @property
    def package_index_markdown(self) -> str:
        """Generates a Markdown formatted package index page."""
        installed_tools_markdown = self._get_installed_tools_markdown()
        installed_packages_markdown = self._get_installed_packages_markdown()
        python_description = "Python programming language with standard library"

        return f"""## WinPython {self.winpyver2 + self.flavor}

The following packages are included in WinPython-{self.architecture_bits}bit v{self.winpyver2 + self.flavor} {self.release_level}.

<details>

### Tools

Name | Version | Description
-----|---------|------------
{installed_tools_markdown}

### Python packages

Name | Version | Description
-----|---------|------------
[Python](http://www.python.org/) | {self.python_full_version} | {python_description}
{installed_packages_markdown}

</details>
"""

    def _get_installed_tools_markdown(self) -> str:
        """Generates Markdown for installed tools section in package index."""
        installed_tools = []

        def get_tool_path(relative_path):
            path = self.winpython_directory / relative_path if self.winpython_directory else None
            return path if path and (path.is_file() or path.is_dir()) else None

        if nodejs_path := get_tool_path(self.NODEJS_RELATIVE_PATH):
            node_version = utils.get_nodejs_version(nodejs_path)
            npm_version = utils.get_npmjs_version(nodejs_path)
            installed_tools += [("Nodejs", node_version), ("npmjs", npm_version)]

        if pandoc_executable := get_tool_path("t/pandoc.exe"):
            pandoc_version = utils.get_pandoc_version(str(pandoc_executable.parent))
            installed_tools.append(("Pandoc", pandoc_version))

        if vscode_executable := get_tool_path("t/VSCode/Code.exe"):
            vscode_version = utils.getFileProperties(str(vscode_executable))["FileVersion"]
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
            return ""  # Distribution not initialized yet.
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
        """Retrieves the Python full version string from the distribution."""
        if self.distribution is None:
            return "0.0.0"  # Placeholder before initialization
        return utils.get_python_long_version(self.distribution.target)

    @property
    def python_executable_directory(self) -> str:
        """Returns the directory containing the Python executable."""
        python_path_directory = self.winpython_directory / self.python_directory_name if self.winpython_directory else None
        if python_path_directory and python_path_directory.is_dir():
            return str(python_path_directory)
        python_path_executable = self.winpython_directory / self.python_name if self.winpython_directory else None
        return str(python_path_executable) if python_path_executable else ""

    @property
    def architecture_bits(self) -> int:
        """Returns the architecture (32 or 64 bits) of the distribution."""
        if self.distribution:
            return self.distribution.architecture
        return 64

    def create_installer_7zip(self, installer_type: str = ".exe"):
        """Creates a WinPython installer using 7-Zip: ".exe", ".7z", ".zip")"""
        self._print_action(f"Creating WinPython installer ({installer_type})")
        template_name = "installer_7zip.bat"
        output_name = "installer_7zip-tmp.bat"
        if installer_type not in [".exe", ".7z", ".zip"]:
            print(f"Warning: Unsupported installer type '{installer_type}'. Defaulting to .exe")
            installer_type = ".exe"

        replacements = [
            ("DISTDIR", str(self.winpython_directory)),
            ("ARCH", str(self.architecture_bits)),
            ("VERSION", f"{self.python_full_version}.{self.build_number}{self.flavor}"),
            ("VERSION_INSTALL", f'{self.python_full_version.replace(".", "")}{self.build_number}'),
            ("RELEASELEVEL", self.release_level),
            ("INSTALLER_OPTION", installer_type),
        ]

        build_installer_7zip(PORTABLE_DIRECTORY / template_name, self.target_directory  / output_name, replacements)

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
        self._print_action("Copying default scripts")
        copy_items([PORTABLE_DIRECTORY / "scripts"], self.winpython_directory / "scripts", self.verbose)

        self._print_action("Copying launchers")
        copy_items([PORTABLE_DIRECTORY / "launchers_final"], self.winpython_directory, self.verbose)

        docs_target_directory = self.winpython_directory / "notebooks" / "docs"
        self._print_action(f"Copying documentation to {docs_target_directory}")
        copy_items(self.documentation_directories, docs_target_directory, self.verbose)

        tools_target_directory = self.winpython_directory / "t"
        self._print_action(f"Copying tools to {tools_target_directory}")
        copy_items(self.tools_directories, tools_target_directory, self.verbose)

        if (nodejs_current_directory := tools_target_directory / "n").is_dir():
            self._print_action(f"moving tools from {nodejs_current_directory} to {tools_target_directory.parent / self.NODEJS_RELATIVE_PATH} ")
            try:
                shutil.move(nodejs_current_directory, tools_target_directory.parent / self.NODEJS_RELATIVE_PATH)
            except Exception as e:
                print(f"Error moving Node.js directory: {e}")

    def _create_initial_batch_scripts(self):
        """Creates initial batch scripts, including environment setup."""
        self._print_action("Creating initial batch scripts")

        # Replacements for batch scripts (PyPy compatibility)
        executable_name = self.distribution.short_exe if self.distribution else "python.exe"  # default to python.exe if distribution is not yet set

        init_variables = [('WINPYthon_exe', executable_name), ('WINPYthon_subdirectory_name', self.python_directory_name), ('WINPYVER', self.winpython_version_name)]
        with open(self.winpython_directory / "scripts" / "env.ini", "w") as f:
            f.writelines([f'{a}={b}\n' for a , b in init_variables])

    def build(self, rebuild: bool = True, requirements_files_list=None, winpy_dirname: str = None):
        """Make or finalise WinPython distribution in the target directory"""
        print(f"Building WinPython with Python archive: {self.python_zip_file.name}")
        if winpy_dirname is None:
            raise RuntimeError("WinPython base directory to create is undefined")
        self.winpython_directory = self.target_directory / winpy_dirname

        if rebuild:
            self._print_action(f"Creating WinPython {self.winpython_directory} base directory")
            if self.winpython_directory.is_dir():
                try:
                    shutil.rmtree(self.winpython_directory, onexc=utils.onerror)
                except TypeError:  # before 3.12
                    shutil.rmtree(self.winpython_directory, onerror=utils.onerror)
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

            essential_packages = ["pip", "setuptools", "wheel", "winpython"]
            for package_name in essential_packages:
                actions = ["install", "--upgrade", "--pre", package_name] + self.install_options
                self._print_action(f"Piping: {' '.join(actions)}")
                self.distribution.do_pip_action(actions)
                self.distribution.patch_standard_packages(package_name)

        if requirements_files_list:
            for req in requirements_files_list:
                actions = ["install", "-r", req]
                if self.install_options is not None:
                    actions += self.install_options
                self._print_action(f"Piping: {' '.join(actions)}")
                self.distribution.do_pip_action(actions)
            self.distribution.patch_standard_packages()

        self._print_action("Cleaning up distribution")
        self.distribution.clean_up()  # still usefull ?
        self._print_action("Writing package index")
        self.winpyver2 = f"{self.python_full_version}.{self.build_number}"
        output_markdown_filename = str(self.winpython_directory.parent / f"WinPython{self.flavor}-{self.distribution.architecture}bit-{self.winpyver2}.md")
        with open(output_markdown_filename, "w", encoding='utf-8') as f:
            f.write(self.package_index_markdown)

        self._print_action("Writing changelog")
        shutil.copyfile(output_markdown_filename, str(Path(CHANGELOGS_DIRECTORY) / Path(output_markdown_filename).name))
        diff.write_changelog(self.winpyver2, None, self.base_directory, self.flavor, self.distribution.architecture)

def rebuild_winpython_package(source_directory: Path, target_directory: Path, architecture: int = 64, verbose: bool = False):
    """Rebuilds the winpython package from source using flit."""
    for filename in os.listdir(target_directory):
        if filename.startswith("winpython-") and filename.endswith((".exe", ".whl", ".gz")):
            os.remove(Path(target_directory) / filename)
    utils.buildflit_wininst(source_directory, copy_to=target_directory, verbose=verbose)

def make_all(build_number: int, release_level: str, pyver: str, architecture: int, basedir: Path,
             verbose: bool = False, rebuild: bool = True, create_installer: str = "True", install_options=["--no-index"],
             flavor: str = "", requirements: str | list[Path] = None, find_links: str | list[Path] = None,
             source_dirs: Path = None, toolsdirs: str | list[Path] = None, docsdirs: str | list[Path] = None,
             python_target_release: str = None, # e.g. "37101" for 3.7.10
):
    """
    Make a WinPython distribution for a given set of parameters:
    Args:
        build_number: build number [int]
        release_level: release level (e.g. 'beta1', '') [str]
        pyver: python version ('3.4' or 3.5')
        architecture: [int] (32 or 64)
        basedir: where to create the build (r'D:\Winpython\basedir34')
        verbose: Enable verbose output (bool).
        rebuild: Whether to rebuild the distribution (bool).
        create_installer: Type of installer to create (str).
        install_options: pip options (r'--no-index --pre --trusted-host=None')
        flavor: WinPython flavor (str).
        requirements: package lists for pip (r'D:\requirements.txt')
        find_links: package directories (r'D:\Winpython\packages.srcreq')
        source_dirs: the python.zip + rebuilt winpython wheel package directory
        toolsdirs: Directory with development tools r'D:\WinPython\basedir34\t.Slim'
        docsdirs: Directory with documentation r'D:\WinPython\basedir34\docs.Slim'
        python_target_release: Target Python release (str).
    """
    assert basedir is not None, "The *basedir* directory must be specified"
    assert architecture in (32, 64)

    tools_dirs_list = parse_list_argument(toolsdirs, ",")
    docs_dirs_list = parse_list_argument(docsdirs, ",")
    install_options_list = parse_list_argument(install_options, " ")
    find_links_dirs_list = parse_list_argument(find_links, ",")
    requirements_files_list = [Path(f) for f in parse_list_argument(requirements, ",") if f]
    find_links_options = [f"--find-links={link}" for link in find_links_dirs_list + [source_dirs]]
    build_directory = str(Path(basedir) / ("bu" + flavor))

    if rebuild:
        utils.print_box(f"Making WinPython {architecture}bits at {Path(basedir) / ('bu' + flavor)}")
        os.makedirs(Path(build_directory), exist_ok=True)
        # use source_dirs as the directory to re-build Winpython wheel
        winpython_source_dir = Path(__file__).resolve().parent
        rebuild_winpython_package(winpython_source_dir, source_dirs, architecture, verbose)

    builder = WinPythonDistributionBuilder(
        build_number, release_level, build_directory, wheels_directory=source_dirs,
        tools_directories=[Path(d) for d in tools_dirs_list],
        documentation_directories=[Path(d) for d in docs_dirs_list],
        verbose=verbose, base_directory=basedir,
        install_options=install_options_list + find_links_options,
        flavor=flavor
    )
    # define the directory where to create the distro
    python_minor_version_str = "".join(builder.python_name.replace(".amd64", "").split(".")[-2:-1])
    while not python_minor_version_str.isdigit() and len(python_minor_version_str) > 0:
        python_minor_version_str = python_minor_version_str[:-1]
    # simplify for PyPy
    if python_target_release is not None:
        winpython_dirname = f"WPy{architecture}-{python_target_release}{build_number}{release_level}"
    else:
        winpython_dirname = f"WPy{architecture}-{pyver.replace('.', '')}{python_minor_version_str}{build_number}{release_level}"

    builder.build(rebuild=rebuild, requirements_files_list=requirements_files_list, winpy_dirname=winpython_dirname)

    if ".zip" in str(create_installer).lower():
        builder.create_installer_7zip(".zip")
    if ".7z" in str(create_installer).lower():
        builder.create_installer_7zip(".7z")
    if "7zip" in str(create_installer).lower():
        builder.create_installer_7zip(".exe")

if __name__ == "__main__":
    # DO create only one Winpython distribution at a time
    make_all(
        build_number=1,
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