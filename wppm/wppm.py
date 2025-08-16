# -*- coding: utf-8 -*-
#
# WinPython Package Manager
# Copyright © 2012 Pierre Raybaut
# Copyright © 2014-2025+ The Winpython development team https://github.com/winpython/
# Licensed under the terms of the MIT License
# (see wppm/__init__.py for details)

import os
import re
import sys
import shutil
import subprocess
import json
from pathlib import Path
from argparse import ArgumentParser, RawTextHelpFormatter
from . import utils, piptree, associate, diff, __version__
from . import wheelhouse as wh
from operator import itemgetter
# Workaround for installing PyVISA on Windows from source:
os.environ["HOME"] = os.environ["USERPROFILE"]

class Package:
    """Standardize a Package from filename or pip list."""
    def __init__(self, fname: str, suggested_summary: str = None):
        self.fname = fname
        self.description = (utils.sum_up(suggested_summary) if suggested_summary else "").strip()
        self.name, self.version = fname, '?.?.?'
        if fname.lower().endswith((".zip", ".tar.gz", ".whl")):
            bname = Path(self.fname).name # e.g., "sqlite_bro-1.0.0..."
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
        self.target = target or str(Path(sys.executable).parent) # Default target more explicit
        self.verbose = verbose
        self.pip = None
        self.to_be_removed = []
        self.version, self.architecture = utils.get_python_infos(self.target)
        self.python_exe = utils.get_python_executable(self.target)
        self.short_exe = Path(self.python_exe).name
        self.wheelhouse = Path(self.target).parent / "wheelhouse"

    def create_file(self, package, name, dstdir, contents):
        """Generate data file -- path is relative to distribution root dir"""
        dst = Path(dstdir) / name
        if self.verbose:
            print(f"create:  {dst}")
        full_dst = Path(self.target) / dst
        with open(full_dst, "w") as fd:
            fd.write(contents)
        package.files.append(str(dst))

    def get_installed_packages(self, update: bool = False) -> list[Package]:
        """Return installed packages."""
        if str(Path(sys.executable).parent) == self.target:
            self.pip = piptree.PipData()
        else:
            self.pip = piptree.PipData(utils.get_python_executable(self.target))
        pip_list = self.pip.pip_list(full=True)
        return [Package(f"{i[0].replace('-', '_').lower()}-{i[1]}-py3-none-any.whl", suggested_summary=i[2]) for i in pip_list]

    def render_markdown_for_list(self, title, items):
        """Generates a Markdown section; name, url, version, summary"""
        md = f"### {title}\n\n"
        md += "Name | Version | Description\n"
        md += "-----|---------|------------\n"
        for name, url, version, summary in sorted(items, key=lambda p: (p[0].lower(), p[2])):
            md += f"[{name}]({url}) | {version} | {summary}\n"
        md += "\n"
        return md
    
    def generate_package_index_markdown(self, python_executable_directory: str|None = None, winpyver2: str|None = None,
                                         flavor: str|None = None, architecture_bits: int|None = None
                                         , release_level: str|None = None, wheeldir: str|None = None) -> str:
        """Generates a Markdown formatted package index page."""
        my_ver , my_arch = utils.get_python_infos(python_executable_directory or self.target)
        my_winpyver2 = winpyver2 or os.getenv("WINPYVER2","")
        my_winpyver2 = my_winpyver2 if my_winpyver2 != "" else my_ver
        my_flavor = flavor or os.getenv("WINPYFLAVOR", "")
        my_release_level = release_level or  os.getenv("WINPYVER", "").replace(my_winpyver2+my_flavor, "")

        tools_list = utils.get_installed_tools(utils.get_python_executable(python_executable_directory))
        package_list = [(pkg.name, pkg.url, pkg.version, pkg.description) for pkg in self.get_installed_packages()]
        wheelhouse_list = []
        my_wheeldir = Path(wheeldir) if wheeldir else self.wheelhouse / 'included.wheels'
        if my_wheeldir.is_dir():
            wheelhouse_list = [(name, f"https://pypi.org/project/{name}", version, utils.sum_up(summary))
               for name, version, summary in wh.list_packages_with_metadata(str(my_wheeldir)) ]

        return f"""## WinPython {my_winpyver2 + my_flavor}

The following packages are included in WinPython-{my_arch}bit v{my_winpyver2 + my_flavor} {my_release_level}.


{self.render_markdown_for_list("Tools", tools_list)}
{self.render_markdown_for_list("Python packages", package_list)}
{self.render_markdown_for_list("WheelHouse packages", wheelhouse_list)}
"""

    def find_package(self, name: str) -> Package | None:
        """Find installed package by name."""
        for pack in self.get_installed_packages():
            if utils.normalize(pack.name) == utils.normalize(name):
                return pack

    def patch_all_shebang(self, to_movable: bool = True, max_exe_size: int = 999999, targetdir: str = ""):
        """Make all python launchers relative."""
        for ffname in Path(self.target).glob("Scripts/*.exe"):
            if ffname.stat().st_size <= max_exe_size:
                utils.patch_shebang_line(ffname, to_movable=to_movable, targetdir=targetdir)
        for ffname in Path(self.target).glob("Scripts/*.py"):
            utils.patch_shebang_line_py(ffname, to_movable=to_movable, targetdir=targetdir)

    def install(self, package: Package, install_options: list[str] = None):
        """Install package in distribution."""
        if package.fname.endswith((".whl", ".tar.gz", ".zip")) or (
            ' ' not in package.fname and ';' not in package.fname and len(package.fname) >1): # Check extension with tuple
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
            the_place = Path(self.target) / "lib" / "site-packages" / "pip" / "_vendor" / "distlib" / "scripts.py"
            sheb_fix = " executable = get_executable()"
            sheb_mov1 = " executable = os.path.join(os.path.basename(get_executable()))"
            sheb_mov2 = " executable = os.path.join('..',os.path.basename(get_executable()))"
            if to_movable:
                utils.patch_sourcefile(the_place, sheb_fix, sheb_mov1)
                utils.patch_sourcefile(the_place, sheb_mov2, sheb_mov1)
            else:
                utils.patch_sourcefile(the_place, sheb_mov1, sheb_fix)
                utils.patch_sourcefile(the_place, sheb_mov2, sheb_fix)

            # create movable launchers for previous package installations
            self.patch_all_shebang(to_movable=to_movable)
        if package_name.lower() in ("", "spyder"):
            # spyder don't goes on internet without you ask
            utils.patch_sourcefile(
                Path(self.target) / "lib" / "site-packages" / "spyder" / "config" / "main.py",
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

    registerWinPythonHelp = f"Register WinPython: associate file extensions, icons and context menu with this WinPython"
    unregisterWinPythonHelp = f"Unregister WinPython: de-associate file extensions, icons and context menu from this WinPython"
    parser = ArgumentParser(prog="wppm",
        description=f"WinPython Package Manager: handle a WinPython Distribution and its packages ({__version__})",
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument("fname", metavar="package(s) or lockfile", nargs="*", default=[""], type=str, help="optional package names, wheels, or lockfile")
    parser.add_argument("-v", "--verbose", action="store_true", help="show more details on packages and actions")
    parser.add_argument( "--register", dest="registerWinPython", action="store_true", help=registerWinPythonHelp)
    parser.add_argument("--unregister", dest="unregisterWinPython", action="store_true", help=unregisterWinPythonHelp)
    parser.add_argument("--fix", action="store_true", help="make WinPython fix")
    parser.add_argument("--movable", action="store_true", help="make WinPython movable")
    parser.add_argument("-ws", dest="wheelsource", default=None, type=str, help="wheels location, '.' = WheelHouse): wppm pylock.toml -ws source_of_wheels, wppm -ls -ws .")
    parser.add_argument("-wd", dest="wheeldrain" , default=None, type=str, help="wheels destination: wppm pylock.toml -wd destination_of_wheels")
    parser.add_argument("-ls", "--list", action="store_true", help="list installed packages matching [optional] expression: wppm -ls, wppm -ls pand")
    parser.add_argument("-lsa", dest="all", action="store_true",help=f"list details of packages matching [optional]  expression: wppm -lsa pandas -l1")
    parser.add_argument("-md", dest="markdown", action="store_true",help=f"markdown summary of the installation")
    parser.add_argument("-p",dest="pipdown",action="store_true",help="show Package dependencies of the given package[option], [.]=all: wppm -p pandas[.]")
    parser.add_argument("-r", dest="pipup", action="store_true", help=f"show Reverse (!= constraining) dependancies of the given package[option]: wppm -r pytest![test]")
    parser.add_argument("-l", dest="levels", type=int, default=-1, help="show 'LEVELS' levels of dependencies (with -p, -r): wppm -p pandas -l1")
    parser.add_argument("-t", dest="target", default=sys.prefix, help=f'path to target Python distribution (default: "{sys.prefix}")')
    parser.add_argument("-i", "--install", action="store_true", help="install a given package wheel or pylock file (use pip for more features)")
    parser.add_argument("-u", "--uninstall", action="store_true", help="uninstall package  (use pip for more features)")

    args = parser.parse_args()
    targetpython = None
    if args.target and args.target != sys.prefix:
        targetpython = args.target if args.target.lower().endswith('.exe') else str(Path(args.target) / 'python.exe')
    if args.wheelsource == ".": # play in default WheelHouse
        if utils.is_python_distribution(args.target):
            dist = Distribution(args.target)
            args.wheelsource = dist.wheelhouse / 'included.wheels'
    if args.install and args.uninstall:
        raise RuntimeError("Incompatible arguments: --install and --uninstall")
    if args.registerWinPython and args.unregisterWinPython:
        raise RuntimeError("Incompatible arguments: --install and --uninstall")
    if args.pipdown:
        pip = piptree.PipData(targetpython, args.wheelsource)
        for args_fname in args.fname:
            pack, extra, *other = (args_fname + "[").replace("]", "[").split("[")
            print(pip.down(pack, extra, args.levels if args.levels>0 else 2, verbose=args.verbose))
        sys.exit()
    elif args.pipup:
        pip = piptree.PipData(targetpython, args.wheelsource)
        for args_fname in args.fname:
            pack, extra, *other = (args_fname + "[").replace("]", "[").split("[")
            print(pip.up(pack, extra, args.levels if args.levels>=0 else 1, verbose=args.verbose))
        sys.exit()
    elif args.list:
        pip = piptree.PipData(targetpython, args.wheelsource)
        todo= []
        for args_fname in args.fname:
            todo += [l for l in pip.pip_list(full=True) if bool(re.search(args_fname, l[0]))]
        todo  = sorted(set(todo)) #, key=lambda p: (p[0].lower(), p[2])
        titles = [['Package', 'Version', 'Summary'], ['_' * max(x, 6) for x in utils.columns_width(todo)]]
        listed = utils.formatted_list(titles + todo, max_width=70)
        for p in listed:
            print(*p)
        sys.exit()
    elif args.all:
        pip = piptree.PipData(targetpython, args.wheelsource)
        for args_fname in args.fname:
            todo = [l for l in pip.pip_list(full=True) if bool(re.search(args_fname, l[0]))]
            for l in sorted(set(todo)):
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
            associate.unregister(dist.target, verbose=args.verbose)
            sys.exit()
    if utils.is_python_distribution(args.target):
        dist = Distribution(args.target, verbose=True)
        cmd_fix = rf"from wppm import wppm;dist=wppm.Distribution(r'{dist.target}');dist.patch_standard_packages('pip', to_movable=False)"
        cmd_mov = rf"from wppm import wppm;dist=wppm.Distribution(r'{dist.target}');dist.patch_standard_packages('pip', to_movable=True)"
        if args.fix:
            # dist.patch_standard_packages('pip', to_movable=False)  # would fail on wppm.exe
            p = subprocess.Popen(["start", "cmd", "/k",dist.python_exe, "-c" , cmd_fix], shell = True,  cwd=dist.target)
            sys.exit()
        if args.movable:
            p = subprocess.Popen(["start", "cmd", "/k",dist.python_exe, "-c" , cmd_mov], shell = True,  cwd=dist.target)
            sys.exit()
        if args.markdown:
            default = dist.generate_package_index_markdown()
            if args.wheelsource:
                compare = dist.generate_package_index_markdown(wheeldir = args.wheelsource)
                print(diff.compare_markdown_sections(default, compare,'python', 'wheelhouse', 'installed', 'wheelhouse')) 
            else:
                print(default)
            sys.exit()
        if not args.install and not args.uninstall and args.fname[0].endswith(".toml"):
            args.install = True  # for Drag & Drop of .toml (and not wheel)
        if args.fname[0] == "" or (not args.install and not args.uninstall):
                parser.print_help()
                sys.exit()
        else:
            try:
               for args_fname in args.fname:
                    filename = Path(args_fname).name
                    install_from_wheelhouse = ["--no-index", "--trusted-host=None", f"--find-links={dist.wheelhouse / 'included.wheels'}"]
                    if filename.split('.')[0] == "pylock" and filename.split('.')[-1] == 'toml':
                        print(' a lock file !', args_fname, dist.target)
                        wh.get_pylock_wheels(dist.wheelhouse, Path(args_fname), args.wheelsource, args.wheeldrain)
                        sys.exit()
                    if args.uninstall:
                        package = dist.find_package(args_fname)
                        dist.uninstall(package)
                    elif args.install:
                        package = Package(args_fname)
                        if args.install:
                            dist.install(package, install_options=install_from_wheelhouse)
            except NotImplementedError:
                raise RuntimeError("Package is not (yet) supported by WPPM")
    else:
        raise OSError(f"Invalid Python distribution {args.target}")


if __name__ == "__main__":
    main()