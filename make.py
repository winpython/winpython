# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Copyright © 2014-2024+  The Winpython development team https://github.com/winpython/
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
WinPython build script
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

# Define constant paths for clarity
CHANGELOGS_DIRECTORY = Path(__file__).parent / "changelogs"
PORTABLE_DIRECTORY = Path(__file__).parent / "portable"

# Ensure necessary directories exist at the start
assert CHANGELOGS_DIRECTORY.is_dir(), f"Changelogs directory not found: {CHANGELOGS_DIRECTORY}"
assert PORTABLE_DIRECTORY.is_dir(), f"Portable directory not found: {PORTABLE_DIRECTORY}"


def find_7zip_executable() -> str:
    """Locates the 7-Zip executable (7z.exe)."""
    possible_program_files = [
        Path(r"C:\Program Files"),
        Path(r"C:\Program Files (x86)"),
        Path(sys.prefix).parent.parent / "7-Zip",
    ]
    for base_dir in possible_program_files:
        for subdir in [".", "App"]:
            executable_path = base_dir / subdir / "7-Zip" / "7z.exe"
            if executable_path.is_file():
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
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        return

    updated_lines = list(lines)  # Create a mutable copy

    for index, line in enumerate(lines):
        for prefix, new_text in replacements:
            start_prefix = prefix
            if prefix not in ("Icon", "OutFile") and not prefix.startswith("!"):
                start_prefix = "set " + prefix
            if line.startswith(start_prefix + "="):
                updated_lines[index] = f"{start_prefix}={new_text}\n"

    try:
        with open(filepath, "w") as f:
            f.writelines(updated_lines)
        print(f"Updated 7-zip script: {filepath}")
    except Exception as e:
        print(f"Error writing to file {filepath}: {e}")


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
    sevenzip_executable = find_7zip_executable()
    shutil.copy(script_template_path, output_script_path)

    # Standard replacements for all 7zip scripts
    data_to_replace = [
        ("PORTABLE_DIR", str(PORTABLE_DIRECTORY)),
        ("SEVENZIP_EXE", sevenzip_executable),
    ] + replacements

    replace_lines_in_file(output_script_path, data_to_replace)

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


def _copy_items(source_directories: list[Path], target_directory: Path, verbose: bool = False):
    """Copies items from source directories to the target directory."""

    target_directory.mkdir(parents=True, exist_ok=True)
    for source_dir in source_directories:
        if not source_dir.is_dir():
            print(f"Warning: Source directory not found: {source_dir}")
            continue
        for item_name in os.listdir(source_dir):
            source_item = source_dir / item_name
            target_item = target_directory / item_name
            copy_function = shutil.copytree if source_item.is_dir() else shutil.copy2
            try:
                copy_function(source_item, target_item)
                if verbose:
                    print(f"  Copied: {source_item} -> {target_item}")
            except Exception as e:
                print(f"Error copying {source_item} to {target_item}: {e}")


def _parse_list_argument(argument_value: str | list[str], separator=" ") -> list[str]:
    """Parse a separated list argument into a list of strings."""
    if argument_value is None:
        return []
    if isinstance(argument_value, str):
        return argument_value.split(separator)
    return list(argument_value)


class WinPythonDistributionBuilder:
    """Builds a WinPython distribution."""

    NODEJS_RELATIVE_PATH = r"\n"  # Relative path within WinPython dir

    def __init__(
        self,
        build_number: int,
        release_level: str,
        target_directory: Path,
        wheels_directory: Path,
        tools_directories: list[Path] = None,
        documentation_directories: list[Path] = None,
        verbose: bool = False,
        base_directory: Path = None,
        install_options: list[str] = None,
        flavor: str = "",
    ):
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
        self.target_directory = Path(target_directory)  # Ensure Path object
        self.wheels_directory = Path(wheels_directory)  # Ensure Path object
        self.tools_directories = tools_directories or []
        self.documentation_directories = documentation_directories or []
        self.verbose = verbose
        self.winpython_directory: Path | None = None  # Will be set during build
        self.distribution: wppm.Distribution | None = None  # Will be set during build
        self.base_directory = base_directory
        self.install_options = install_options or []
        self.flavor = flavor
        self.python_zip_file: Path = self._get_python_zip_file()
        self.python_name = self.python_zip_file.stem  # Filename without extension
        self.python_dir_name = "python"  # Standardized Python directory name

    def _get_python_zip_file(self) -> Path:
        """Finds the Python .zip file in the wheels directory."""
        patterns = [
            r"(pypy3|python-)([0-9]|[a-zA-Z]|.)*.zip",  # PyPy pattern
            r"python-([0-9\.rcba]*)((\.|\-)amd64)?\.(zip|zip)",  # Standard Python pattern
        ]
        for pattern in patterns:
            for filename in os.listdir(self.wheels_directory):
                if re.match(pattern, filename):
                    return self.wheels_directory / filename
        raise RuntimeError(f"Could not find Python zip package in {self.wheels_directory}")

    @property
    def package_index_markdown(self) -> str:
        """
        Generates a Markdown formatted package index page.

        Returns:
            str: Markdown content for the package index.
        """
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

        def get_tool_path(rel_path):
            path = self.winpython_directory / rel_path if self.winpython_directory else None
            return path if path and (path.is_file() or path.is_dir()) else None

        nodejs_path = get_tool_path(self.NODEJS_RELATIVE_PATH)
        if nodejs_path:
            node_version = utils.get_nodejs_version(str(nodejs_path))
            installed_tools.append(("Nodejs", node_version))
            npm_version = utils.get_npmjs_version(str(nodejs_path))
            installed_tools.append(("npmjs", npm_version))

        pandoc_executable = get_tool_path(r"\t\pandoc.exe")
        if pandoc_executable:
            pandoc_version = utils.get_pandoc_version(str(pandoc_executable.parent))
            installed_tools.append(("Pandoc", pandoc_version))

        vscode_executable = get_tool_path(r"\t\VSCode\Code.exe")
        if vscode_executable:
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
            return "0.0.0"  # Placeholder before initialization
        return utils.get_python_long_version(self.distribution.target)

    @property
    def python_executable_dir(self) -> str:
        """Returns the directory containing the Python executable."""
        python_path_dir = self.winpython_directory / self.python_dir_name if self.winpython_directory else None
        if python_path_dir and python_path_dir.is_dir():
            return str(python_path_dir)
        else:
            python_path_exe = self.winpython_directory / self.python_name if self.winpython_directory else None # Fallback for older structure
            return str(python_path_exe) if python_path_exe else ""

    @property
    def architecture_bits(self) -> int:
        """Returns the architecture (32 or 64 bits) of the distribution."""
        if self.distribution:
            return self.distribution.architecture
        return 64  # Default to 64 if distribution is not initialized yet

    @property
    def pre_path_entries(self) -> list[str]:
        """Returns a list of PATH entries to prepend to the environment."""
        return [
            r"Lib\site-packages\PyQt5",
            "",  # Python root directory
            "DLLs",
            "Scripts",
            r"..\t",
            r".." + self.NODEJS_RELATIVE_PATH,
        ]

    @property
    def docs_directories(self) -> list[Path]:
        """Returns the list of documentation directories to include."""
        default_docs_dir = Path(__file__).resolve().parent / "docs"
        if default_docs_dir.is_dir():
            return [default_docs_dir] + self.documentation_directories
        return self.documentation_directories

    def create_batch_script(self, name: str, contents: str, replacements: list[tuple[str, str]] = None):
        """
        Creates a batch script in the WinPython scripts directory.

        Args:
            name: The name of the batch script file.
            contents: The contents of the batch script.
            replacements: A list of tuples for text replacements in the content.
        """
        script_dir = self.winpython_directory / "scripts" if self.winpython_directory else None
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


    def create_installer_7zip(self, installer_type: str = ".exe"):
        """
        Creates a WinPython installer using 7-Zip.

        Args: installer_type: Type of installer to create (".exe", ".7z", ".zip").
        """
        self._print_action(f"Creating WinPython installer ({installer_type})")
        template_name = "installer_7zip.bat"
        output_name = "installer_7zip-tmp.bat"  # temp file to avoid overwriting template
        if installer_type not in [".exe", ".7z", ".zip"]:
            print(f"Warning: Unsupported installer type '{installer_type}'. Defaulting to .exe")
            installer_type = ".exe"

        replacements = [
            ("DISTDIR", str(self.winpython_directory)),
            ("ARCH", str(self.architecture_bits)),
            ("VERSION", f"{self.python_full_version}.{self.build_number}{self.flavor}"),
            ("VERSION_INSTALL", f'{self.python_full_version.replace(".", "")}{self.build_number}'),
            ("RELEASELEVEL", self.release_level),
            ("INSTALLER_OPTION", installer_type),  # Pass installer type as option to bat script
        ]

        build_installer_7zip(
            PORTABLE_DIRECTORY / template_name,
            PORTABLE_DIRECTORY / output_name,
            replacements
        )

    def _print_action(self, text: str):
        """Prints an action message with progress indicator."""
        if self.verbose:
            utils.print_box(text)
        else:
            print(f"{text}... ", end="", flush=True)

    def _extract_python_archive(self):
        """Extracts the Python zip archive to create the base Python environment."""
        self._print_action("Extracting Python archive")
        utils.extract_archive(
            str(self.python_zip_file),
            targetdir=str(self.winpython_directory),  # Extract directly to winpython_directory
        )
        # Relocate to /python subfolder if needed (for newer structure) #2024-12-22 to /python
        python_target_dir = self.winpython_directory / self.python_dir_name
        if self.python_dir_name != self.python_name and not python_target_dir.is_dir():
            os.rename(self.winpython_directory / self.python_name, python_target_dir)

    def _copy_tools(self):
        """Copies development tools to the WinPython 't' directory."""
        tools_target_dir = self.winpython_directory / "t"
        self._print_action(f"Copying tools to {tools_target_dir}")
        _copy_items(self.tools_directories, tools_target_dir, self.verbose)

        # Special handling for Node.js to move it up one level
        nodejs_current_dir = tools_target_dir / "n"
        nodejs_target_dir = self.winpython_directory / self.NODEJS_RELATIVE_PATH
        if nodejs_current_dir != nodejs_target_dir and nodejs_current_dir.is_dir():
            try:
                shutil.move(nodejs_current_dir, nodejs_target_dir)
            except Exception as e:
                print(f"Error moving Node.js directory: {e}")

    def _copy_documentation(self):
        """Copies documentation files to the WinPython 'docs' directory."""
        docs_target_dir = self.winpython_directory / "notebooks" / "docs"
        self._print_action(f"Copying documentation to {docs_target_dir}")
        _copy_items(self.docs_directories, docs_target_dir, self.verbose)
 
    def _copy_launchers(self):
        """Copies pre-made launchers to the WinPython directory."""
        self._print_action("Creating launchers")
        _copy_items([PORTABLE_DIRECTORY / "launchers_final"], self.winpython_directory, self.verbose)

    def _copy_default_scripts(self):
        """Copies launchers and defeult scripts."""
        self._print_action("copying pre-made scripts")
        _copy_items([PORTABLE_DIRECTORY / "scripts"], self.winpython_directory / "scripts", self.verbose)
    
    def _create_initial_batch_scripts(self):
        """Creates initial batch scripts, including environment setup."""
        self._print_action("Creating initial batch scripts")

        path_entries_str = ";".join([rf"%WINPYDIR%\{pth}" for pth in self.pre_path_entries])
        full_path_env_var = f"{path_entries_str};%PATH%"

        path_entries_ps_str = ";".join([rf"$env:WINPYDIR\\{pth}" for pth in self.pre_path_entries])
        full_path_ps_env_var = f"{path_entries_ps_str};$env:path"

        # Replacements for batch scripts (PyPy compatibility)
        exe_name = self.distribution.short_exe if self.distribution else "python.exe" # default to python.exe if distribution is not yet set

        destination = self.winpython_directory / "scripts"
        for specials in ('env.bat', 'WinPython_PS_Prompt.ps1'):
            destspe=str(destination / specials)
            print('destspe:', destspe)
            utils.patch_sourcefile(destspe,'{self.python_dir_name}', self.python_dir_name)
            utils.patch_sourcefile(destspe,'{self.winpython_version_name}', self.winpython_version_name)
            utils.patch_sourcefile(destspe,'{full_path_env_var}', full_path_env_var)
            utils.patch_sourcefile(destspe,'{full_path_ps_env_var}', full_path_ps_env_var)


    def build(self, rebuild: bool = True, requirements=None, winpy_dirname: str = None):
        """Make WinPython distribution in target directory from the installers
        located in wheels_directory

        rebuild=True: (default) install all from scratch
        rebuild=False: for complementary purposes (create installers)
        requirements=file(s) of requirements (separated by space if several)"""
        python_zip_filename = self.python_zip_file.name
        print(f"Building WinPython with Python archive: {python_zip_filename}")

        if winpy_dirname is None:
            raise RuntimeError("WinPython base directory to create is undefined")
        else:
            self.winpython_directory = self.target_directory / winpy_dirname  # Create/re-create the WinPython base directory
        self._print_action(f"Creating WinPython {self.winpython_directory} base directory")
        if self.winpython_directory.is_dir() and rebuild:
            try:
                shutil.rmtree(self.winpython_directory, onexc=utils.onerror)
            except TypeError:  # before 3.12
                shutil.rmtree(self.winpython_directory, onerror=utils.onerror)
        os.makedirs(self.winpython_directory, exist_ok=True)
        if rebuild:
            # preventive re-Creation of settings directory
            # (necessary if user is starting an application with a batch)
            (self.winpython_directory / "settings" / "AppData" / "Roaming").mkdir(parents=True, exist_ok=True)  # Ensure settings dir exists
            self._extract_python_archive()

        self.distribution = wppm.Distribution(
            self.python_executable_dir,
            verbose=self.verbose,
            indent=True,
        )

        if rebuild:
            self._copy_default_scripts()
            self._create_initial_batch_scripts()
            self._copy_launchers()
            self._copy_tools()
            self._copy_documentation()

            utils.python_execmodule("ensurepip", self.distribution.target)  # Ensure pip is installed for PyPy
            self.distribution.patch_standard_packages("pip")

            # Upgrade essential packages
            essential_packages = ["pip", "setuptools", "wheel", "winpython"]
            for package_name in essential_packages:
                actions = ["install", "--upgrade", "--pre", package_name] + self.install_options
                print(f"Piping: {' '.join(actions)}")
                self._print_action(f"Piping: {' '.join(actions)}")
                self.distribution.do_pip_action(actions)
                self.distribution.patch_standard_packages(package_name)

            if requirements:
                if not isinstance(requirements, list):
                    requirements = requirements.split(",")
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
        # Writing package index
        self._print_action("Writing package index")
        # winpyver2 = the version without build part but with self.distribution.architecture
        self.winpyver2 = f"{self.python_full_version}.{self.build_number}"
        fname = str(self.winpython_directory.parent / f"WinPython{self.flavor}-{self.distribution.architecture}bit-{self.winpyver2}.md")
        open(fname, "w", encoding='utf-8').write(self.package_index_markdown)

        # Copy to winpython/changelogs
        shutil.copyfile(fname, str(Path(CHANGELOGS_DIRECTORY) / Path(fname).name))

        # Writing changelog
        self._print_action("Writing changelog")
        diff.write_changelog(
            self.winpyver2,
            basedir=self.base_directory,
            flavor=self.flavor,
            release_level=self.release_level,
            architecture=self.distribution.architecture,
        )


def rebuild_winpython_package(source_dir: Path, target_directory: Path, architecture: int = 64, verbose: bool = False):
    """Rebuilds the winpython package from source using flit."""
    for filename in os.listdir(target_directory):
        if filename.startswith("winpython-") and filename.endswith((".exe", ".whl", ".gz")):
            os.remove(Path(target_directory) / filename)
    utils.buildflit_wininst(source_dir, copy_to=target_directory, verbose=verbose)


def make_all(
    build_number: int,
    release_level: str,
    pyver: str,
    architecture: int,
    basedir: Path,
    verbose: bool = False,
    rebuild: bool = True,
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

    # Parse list arguments
    tools_dirs_list = _parse_list_argument(toolsdirs, ",")
    docs_dirs_list = _parse_list_argument(docsdirs, ",")
    install_options_list = _parse_list_argument(install_options, " ")
    find_links_dirs_list = _parse_list_argument(find_links, ",")
    requirements_files_list = [Path(f) for f in _parse_list_argument(requirements, ",") if f] # ensure Path objects
    find_links_options = [f"--find-links={link}" for link in find_links_dirs_list + [source_dirs]]
    builddir = str(Path(basedir) / ("bu" + flavor))

    if rebuild:
        # Rebuild Winpython Wheel Package
        utils.print_box(f"Making WinPython {architecture}bits at {Path(basedir) / ('bu' + flavor)}")
        os.makedirs(Path(builddir), exist_ok=True)    
        # use source_dirs as the directory to re-build Winpython wheel
        winpython_source_dir = Path(__file__).resolve().parent
        rebuild_winpython_package(winpython_source_dir, source_dirs, architecture, verbose)

    builder = WinPythonDistributionBuilder(
        build_number,
        release_level,
        builddir,
        wheels_directory=source_dirs,
        tools_directories=[Path(d) for d in tools_dirs_list],
        documentation_directories=[Path(d) for d in docs_dirs_list],
        verbose=verbose,
        base_directory=basedir,
        install_options=install_options_list + find_links_options,
        flavor=flavor,
    )
    # define the directory where to create the distro
    my_x = "".join(builder.python_name.replace(".amd64", "").split(".")[-2:-1])
    while not my_x.isdigit() and len(my_x) > 0:
        my_x = my_x[:-1]
    # simplify for PyPy
    if not python_target_release == None:
        winpy_dirname = f"WPy{architecture}-{python_target_release}{build_number}{release_level}"
    else:
        winpy_dirname = f"WPy{architecture}-{pyver.replace('.', '')}{my_x}{build_number}{release_level}"

    builder.build(
        rebuild=rebuild,
        requirements=requirements_files_list,
        winpy_dirname=winpy_dirname,
    )
    if ".zip" in str(create_installer).lower():
        builder.create_installer_7zip(".zip")
    if ".7z" in str(create_installer).lower():
        builder.create_installer_7zip(".7z")
    if "7zip" in str(create_installer).lower():
        builder.create_installer_7zip(".exe")


if __name__ == "__main__":
    # DO create only one version at a time
    # You may have to manually delete previous build\winpython-.. directory

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