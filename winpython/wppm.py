# -*- coding: utf-8 -*-
#
# WinPython Package Manager
# Copyright © 2012 Pierre Raybaut
# Copyright © 2014-2025+ The Winpython development team https://github.com/winpython/
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

import os
from pathlib import Path
import shutil
import re
import sys
import subprocess
import json
from argparse import ArgumentParser, RawTextHelpFormatter

# Local imports
from winpython import utils, piptree

# Workaround for installing PyVISA on Windows from source:
os.environ["HOME"] = os.environ["USERPROFILE"]

class Package:
    """Standardize a Package from filename or pip list."""
    def __init__(self, fname: str, suggested_summary: str = None):
        self.fname = fname
        self.description = piptree.sum_up(suggested_summary) if suggested_summary else ""
        self.name, self.version = None, None
        if fname.endswith((".zip", ".tar.gz", ".whl")):
            bname = Path(self.fname).name #wheel style name like "sqlite_bro-1.0.0..."
            infos = utils.get_source_package_infos(bname) # get name, version
            if infos:
                self.name, self.version = utils.normalize(infos[0]), infos[1]
        self.url = f"https://pypi.org/project/{self.name}"
        self.files = []

    def __str__(self):
        return f"{self.name} {self.version}\r\n{self.description}\r\nWebsite: {self.url}"


class Distribution:
    """Handles operations on a WinPython distribution."""
    def __init__(self, target: str = None, verbose: bool = False):
        self.target = target or os.path.dirname(sys.executable) # Default target more explicit
        self.verbose = verbose
        self.pip = None
        self.to_be_removed = []
        self.version, self.architecture = utils.get_python_infos(self.target)
        self.short_exe = Path(utils.get_python_executable(self.target)).name

    def clean_up(self):
        """Remove directories that were marked for removal."""
        for path in self.to_be_removed:
            try:
                shutil.rmtree(path, onexc=utils.onerror)
            except OSError as e:
                print(f"Error: Could not remove directory {path}: {e}", file=sys.stderr)

    def remove_directory(self, path: str):
        """Try to remove a directory, add to removal list on failure."""
        try:
            shutil.rmtree(path)
        except OSError:
            self.to_be_removed.append(path)

    def create_file(self, package, name, dstdir, contents):
        """Generate data file -- path is relative to distribution root dir"""
        dst = str(Path(dstdir) / name)
        if self.verbose:
            print(f"create:  {dst}")
        full_dst = str(Path(self.target) / dst)
        with open(full_dst, "w") as fd:
            fd.write(contents)
        package.files.append(dst)

    def get_installed_packages(self, update: bool = False) -> list[Package]:
        """Return installed packages."""

        # Include package installed via pip (not via WPPM)
        wppm = []
        if str(Path(sys.executable).parent) == self.target:
            self.pip = piptree.PipData()
        else:
            self.pip = piptree.PipData(utils.get_python_executable(self.target))
        pip_list = self.pip.pip_list()

        # create pip package list
        wppm = [
            Package(
                f"{i[0].replace('-', '_').lower()}-{i[1]}-py3-none-any.whl", #faking wheel
                suggested_summary=self.pip.summary(i[0]) if self.pip else None
            )
            for i in pip_list
        ]
        return sorted(wppm, key=lambda tup: tup.name.lower())

    def find_package(self, name: str) -> Package | None:
        """Find installed package by name."""
        for pack in self.get_installed_packages():
            if utils.normalize(pack.name) == utils.normalize(name):
                return pack

    def patch_all_shebang(self, to_movable: bool = True, max_exe_size: int = 999999, targetdir: str = ""):
        """Make all python launchers relative."""
        import glob

        for ffname in glob.glob(r"%s\Scripts\*.exe" % self.target):
            size = os.path.getsize(ffname)
            if size <= max_exe_size:
                utils.patch_shebang_line(ffname, to_movable=to_movable, targetdir=targetdir)
        for ffname in glob.glob(r"%s\Scripts\*.py" % self.target):
            utils.patch_shebang_line_py(ffname, to_movable=to_movable, targetdir=targetdir)

    def install(self, package: Package, install_options: list[str] = None): # Type hint install_options
        """Install package in distribution."""
        if package.fname.endswith((".whl", ".tar.gz", ".zip")): # Check extension with tuple
            self.install_bdist_direct(package, install_options=install_options)
        self.handle_specific_packages(package)
        # minimal post-install actions
        self.patch_standard_packages(package.name)

    def do_pip_action(self, actions: list[str] = None, install_options: list[str] = None):
        """Execute pip action in the distribution."""
        my_list = install_options or []
        my_actions = actions or []
        executing = str(Path(self.target).parent / "scripts" / "env.bat")
        if Path(executing).is_file():
            complement = [r"&&", "cd", "/D", self.target, r"&&", utils.get_python_executable(self.target), "-m", "pip"]
        else:
            executing = utils.get_python_executable(self.target)
            complement = ["-m", "pip"]
        try:
            fname = utils.do_script(this_script=None, python_exe=executing, verbose=self.verbose, install_options=complement + my_actions + my_list)
        except RuntimeError as e:
            if not self.verbose:
                print("Failed!")
                raise
            else:
                print(f"Pip action failed with error: {e}") # Print error if verbose

    def patch_standard_packages(self, package_name="", to_movable=True):
        """patch Winpython packages in need"""
        import filecmp

        # 'pywin32' minimal post-install (pywin32_postinstall.py do too much)
        if package_name.lower() in ("", "pywin32"):
            origin = Path(self.target) / "site-packages" / "pywin32_system32"
            destin = Path(self.target)
            if origin.is_dir():
                for name in os.listdir(origin):
                    here, there = origin / name, destin / name
                    if not there.exists() or not filecmp.cmp(here, there):
                        shutil.copyfile(here, there)
        # 'pip' to do movable launchers (around line 100) !!!!
        # rational: https://github.com/pypa/pip/issues/2328
        if package_name.lower() == "pip" or package_name == "":
            # ensure pip will create movable launchers
            # sheb_mov1 = classic way up to WinPython 2016-01
            # sheb_mov2 = tried  way, but doesn't work for pip (at least)
            sheb_fix = " executable = get_executable()"
            sheb_mov1 = " executable = os.path.join(os.path.basename(get_executable()))"
            sheb_mov2 = " executable = os.path.join('..',os.path.basename(get_executable()))"

            the_place = Path(self.target) / "lib" / "site-packages" / "pip" / "_vendor" / "distlib" / "scripts.py"
            print(the_place)
            if to_movable:
                utils.patch_sourcefile(the_place, sheb_fix, sheb_mov1)
                utils.patch_sourcefile(the_place, sheb_mov2, sheb_mov1)
            else:
                utils.patch_sourcefile(the_place, sheb_mov1, sheb_fix)
                utils.patch_sourcefile(the_place, sheb_mov2, sheb_fix)

            # create movable launchers for previous package installations
            self.patch_all_shebang(to_movable=to_movable)
        if package_name.lower() in ("", "spyder"):
            # spyder don't goes on internet without I ask
            utils.patch_sourcefile(
                Path(self.target) / "lib" / "site-packages" / "spyder" / "config" /"main.py",
                "'check_updates_on_startup': True,",
                "'check_updates_on_startup': False,",
            )


    def handle_specific_packages(self, package):
        """Packages requiring additional configuration"""
        if package.name.lower() in ("pyqt4", "pyqt5", "pyside2"):
            # Qt configuration file (where to find Qt)
            name = "qt.conf"
            contents = """[Paths]\nPrefix = .\nBinaries = ."""
            self.create_file(package, name, str(Path("Lib") / "site-packages" / package.name), contents)
            self.create_file(package, name, ".", contents.replace(".", f"./Lib/site-packages/{package.name}"))
            # pyuic script
            if package.name.lower() == "pyqt5":
                # see http://code.activestate.com/lists/python-list/666469/
                tmp_string = r"""@echo off
if "%WINPYDIR%"=="" call "%~dp0..\..\scripts\env.bat"
"%WINPYDIR%\python.exe" -m PyQt5.uic.pyuic %1 %2 %3 %4 %5 %6 %7 %8 %9"""
            else:
                tmp_string = r"""@echo off
if "%WINPYDIR%"=="" call "%~dp0..\..\scripts\env.bat"
"%WINPYDIR%\python.exe" "%WINPYDIR%\Lib\site-packages\package.name\uic\pyuic.py" %1 %2 %3 %4 %5 %6 %7 %8 %9"""
            # PyPy adaption: python.exe or pypy3.exe
            my_exec = Path(utils.get_python_executable(self.target)).name
            tmp_string = tmp_string.replace("python.exe", my_exec).replace("package.name", package.name)
            self.create_file(package, f"pyuic{package.name[-1]}.bat", "Scripts", tmp_string)
            # Adding missing __init__.py files (fixes Issue 8)
            uic_path = str(Path("Lib") / "site-packages" / package.name / "uic")
            for dirname in ("Loader", "port_v2", "port_v3"):
                self.create_file(package, "__init__.py", str(Path(uic_path) / dirname), "")

    def _print(self, package: Package, action: str):
        """Print package-related action text."""
        text = f"{action} {package.name} {package.version}"
        if self.verbose:
            utils.print_box(text)
        else:
            print(f"    {text}...", end=" ")

    def _print_done(self):
        """Print OK at the end of a process"""
        if not self.verbose:
            print("OK")

    def uninstall(self, package):
        """Uninstall package from distribution"""
        self._print(package, "Uninstalling")
        if package.name != "pip":
            # trick to get true target (if not current)
            this_exec = utils.get_python_executable(self.target)  # PyPy !
            subprocess.call([this_exec, "-m", "pip", "uninstall", package.name, "-y"], cwd=self.target)
        self._print_done()

    def install_bdist_direct(self, package, install_options=None):
        """Install a package directly !"""
        self._print(package,f"Installing {package.fname.split('.')[-1]}")
        try:
            fname = utils.direct_pip_install(
                package.fname,
                python_exe=utils.get_python_executable(self.target),  # PyPy !
                verbose=self.verbose,
                install_options=install_options,
            )
        except RuntimeError:
            if not self.verbose:
                print("Failed!")
                raise
        package = Package(fname)
        self._print_done()

def main(test=False):
    if test:
        sbdir = Path(__file__).parents[0].parent.parent.parent / "sandbox"
        tmpdir = sbdir / "tobedeleted"
        fname = sbdir / "VTK-5.10.0-Qt-4.7.4.win32-py2.7.exe")
        print(Package(str(fname)))
        sys.exit()
        target = Path(utils.BASE_DIR) / "build" / "winpython-2.7.3" / "python-2.7.3"
        fname = Path(utils.BASE_DIR) / "packages.src" / "docutils-0.9.1.tar.gz"
        dist = Distribution(str(target), verbose=True)
        pack = Package(str(fname))
        print(pack.description)
        # dist.install(pack)
        # dist.uninstall(pack)
    else:
        registerWinPythonHelp = f"Register distribution: associate file extensions, icons and context menu with this WinPython"
        unregisterWinPythonHelp = f"Unregister distribution: de-associate file extensions, icons and context menu from this WinPython"
        parser = ArgumentParser(
            description="WinPython Package Manager: handle a WinPython Distribution and its packages",
            formatter_class=RawTextHelpFormatter,
        )
        parser.add_argument(
            "fname",
            metavar="package",
            nargs="?",
            default="",
            type=str,
            help="optional package name or package wheel",
        )
        parser.add_argument(
            "--register",
            dest="registerWinPython",
            action="store_const",
            const=True,
            default=False,
            help=registerWinPythonHelp,
        )
        parser.add_argument(
            "--unregister",
            dest="unregisterWinPython",
            action="store_const",
            const=True,
            default=False,
            help=unregisterWinPythonHelp,
        )
        parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_const",
            const=True,
            default=False,
            help="show more details on packages and actions",
        )
        parser.add_argument(
            "-ls",
            "--list",
            dest="list",
            action="store_const",
            const=True,
            default=False,
            help=f"list packages matching the given [optionnal] package expression: wppm -ls, wppm -ls pand",
        )
        parser.add_argument(
            "-p",
            dest="pipdown",
            action="store_const",
            const=True,
            default=False,
            help=f"show Package dependancies of the given package[option]: wppm -p pandas[test]",
        )
        parser.add_argument(
            "-r",
            dest="pipup",
            action="store_const",
            const=True,
            default=False,
            help=f"show Reverse dependancies of the given package[option]: wppm -r pytest[test]",
        )
        parser.add_argument(
            "-l",
            dest="levels",
            type=int,
            default=2,
            help=f"show 'LEVELS' levels of dependancies of the package, default is 2: wppm -p pandas -l1",
        )
        parser.add_argument(
            "-lsa",
            dest="all",
            action="store_const",
            const=True,
            default=False,
            help=f"list details of package names matching given regular expression: wppm -lsa pandas -l1",
        )
        parser.add_argument(
            "-t",
            dest="target",
            default=sys.prefix,
            help=f'path to target Python distribution (default: "{sys.prefix}")',
        )
        parser.add_argument(
            "-i",
            "--install",
            dest="install",
            action="store_const",
            const=True,
            default=False,
            help="install a given package wheel (use pip for more features)",
        )
        parser.add_argument(
            "-u",
            "--uninstall",
            dest="uninstall",
            action="store_const",
            const=True,
            default=False,
            help="uninstall package  (use pip for more features)",
        )
        args = parser.parse_args()
        targetpython = None
        if args.target and args.target != sys.prefix:
            targetpython = args.target if args.target.lower().endswith('.exe') else str(Path(args.target) / 'python.exe')
        if args.install and args.uninstall:
            raise RuntimeError("Incompatible arguments: --install and --uninstall")
        if args.registerWinPython and args.unregisterWinPython:
            raise RuntimeError("Incompatible arguments: --install and --uninstall")
        if args.pipdown:
            pip = piptree.PipData(targetpython)
            pack, extra, *other = (args.fname + "[").replace("]", "[").split("[")
            print(pip.down(pack, extra, args.levels, verbose=args.verbose))
            sys.exit()
        elif args.pipup:
            pip = piptree.PipData(targetpython)
            pack, extra, *other = (args.fname + "[").replace("]", "[").split("[")
            print(pip.up(pack, extra, args.levels, verbose=args.verbose))
            sys.exit()
        elif args.list:
            pip = piptree.PipData(targetpython)
            todo = [l for l in pip.pip_list(full=True) if bool(re.search(args.fname, l[0]))]
            titles = [['Package', 'Version', 'Summary'], ['_' * max(x, 6) for x in utils.columns_width(todo)]]
            listed = utils.formatted_list(titles + todo, max_width=70)
            for p in listed:
                print(*p)
            sys.exit()
        elif args.all:
            pip = piptree.PipData(targetpython)
            todo = [l for l in pip.pip_list(full=True) if bool(re.search(args.fname, l[0]))]
            for l in todo:
                # print(pip.distro[l[0]])
                title = f"**  Package: {l[0]}  **"
                print("\n" + "*" * len(title), f"\n{title}", "\n" + "*" * len(title))
                for key, value in pip.raw[l[0]].items():
                    rawtext = json.dumps(value, indent=2, ensure_ascii=False)
                    lines = [l for l in rawtext.split(r"\n") if len(l.strip()) > 2]
                    if key.lower() != 'description' or args.verbose:
                        print(f"{key}: ", "\n".join(lines).replace('"', ""))
            sys.exit()
        if args.registerWinPython:
            print(registerWinPythonHelp)
            if utils.is_python_distribution(args.target):
                dist = Distribution(args.target)
            else:
                raise OSError(f"Invalid Python distribution {args.target}")
            print(f"registering {args.target}")
            print("continue ? Y/N")
            theAnswer = input()
            if theAnswer == "Y":
                from winpython import associate
                associate.register(dist.target, verbose=args.verbose)
                sys.exit()
        if args.unregisterWinPython:
            print(unregisterWinPythonHelp)
            if utils.is_python_distribution(args.target):
                dist = Distribution(args.target)
            else:
                raise OSError(f"Invalid Python distribution {args.target}")
            print(f"unregistering {args.target}")
            print("continue ? Y/N")
            theAnswer = input()
            if theAnswer == "Y":
                from winpython import associate
                associate.unregister(dist.target, verbose=args.verbose)
                sys.exit()
        elif not args.install and not args.uninstall:
            args.install = True
        if not Path(args.fname).is_file() and args.install:
            if args.fname == "":
                parser.print_help()
                sys.exit()
            else:
                raise FileNotFoundError(f"File not found: {args.fname}")
        if utils.is_python_distribution(args.target):
            dist = Distribution(args.target, verbose=True)
            try:
                if args.uninstall:
                    package = dist.find_package(args.fname)
                    dist.uninstall(package)
                else:
                    package = Package(args.fname)
                    if args.install:
                        dist.install(package)
            except NotImplementedError:
                raise RuntimeError("Package is not (yet) supported by WPPM")
        else:
            raise OSError(f"Invalid Python distribution {args.target}")


if __name__ == "__main__":
    main()