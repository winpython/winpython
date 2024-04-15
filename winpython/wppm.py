# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
WinPython Package Manager

Created on Fri Aug 03 14:32:26 2012
"""

import os
from pathlib import Path
import shutil
import re
import sys
import subprocess
import json

# Local imports
from winpython import utils
from winpython.config import DATA_PATH
import configparser as cp

# from former wppm separate script launcher
import textwrap
from argparse import ArgumentParser, HelpFormatter, RawTextHelpFormatter

from winpython import piptree

# import information reader
# importlib_metadata before Python 3.8
try:
    from importlib import metadata as metadata  # Python-3.8

    metadata = metadata.metadata
except:
    try:
        from importlib_metadata import metadata  # <Python-3.8
    except:
        metadata = None  # nothing available
# Workaround for installing PyVISA on Windows from source:
os.environ["HOME"] = os.environ["USERPROFILE"]

# pep503 defines normalized package names: www.python.org/dev/peps/pep-0503
def normalize(name):
    """return normalized (unique) name of a package"""
    return re.sub(r"[-_.]+", "-", name).lower()


def get_official_description(name):
    """Extract package Summary description from pypi.org"""
    from winpython import utils

    this = normalize(name)
    this_len = len(this)
    pip_ask = ["pip", "search", this, "--retries", "0"]
    if len(this) < 2:  # don't ask stupid things
        return ""
    try:
        #  .run work when .popen fails when no internet
        pip_res = (utils.exec_run_cmd(pip_ask) + "\n").splitlines()
        pip_filter = [
            l
            for l in pip_res
            if this + " (" == normalize(l[:this_len]) + l[this_len : this_len + 2]
        ]
        pip_desc = (pip_filter[0][len(this) + 1 :]).split(" - ", 1)[1]
        return pip_desc.replace("://", " ")
    except:
        return ""


def get_package_metadata(database, name, gotoWWW=False, update=False):
    """Extract infos (description, url) from the local database"""
    # Note: we could use the PyPI database but this has been written on
    # machine which is not connected to the internet
    # we store only  normalized names now (PEP 503)
    db = cp.ConfigParser()
    try:
        db.read_file(open(str(Path(DATA_PATH) / database), encoding = 'utf-8'))
    except:
        db.read_file(open(str(Path(DATA_PATH) / database)))
    my_metadata = dict(
        description="",
        url="https://pypi.org/project/" + name,
    )
    for key in my_metadata:
        # wheel replace '-' per '_' in key
        for name2 in (name, normalize(name)):
            try:
                my_metadata[key] = db.get(name2, key)
                break
            except (cp.NoSectionError, cp.NoOptionError):
                pass
    db_desc = my_metadata.get("description")

    if my_metadata.get("description") == "" and metadata:
        # nothing in package.ini, we look in our installed packages
        try:
            my_metadata["description"] = (
                metadata(name)["Summary"] + "\n"
            ).splitlines()[0]
        except:
            pass
    if my_metadata["description"] == "" and gotoWWW:
        # still nothing, try look on pypi
        the_official = get_official_description(name)
        if the_official != "":
            my_metadata["description"] = the_official
    if update == True and db_desc == "" and my_metadata["description"] != "":
        # we add new findings in our packgages.ini list, if it's required
        try:
            db[normalize(name)] = {}
            db[normalize(name)]["description"] = my_metadata["description"]
            with open(str(Path(DATA_PATH) / database), "w",  encoding='UTF-8') as configfile:
                db.write(configfile)
        except:
            pass
    return my_metadata


class BasePackage(object):
    def __init__(self, fname):
        self.fname = fname
        self.name = None
        self.version = None
        self.architecture = None
        self.pyversion = None
        self.description = None
        self.url = None

    def __str__(self):
        text = f"{self.name} {self.version}"
        pytext = ""
        if self.pyversion is not None:
            pytext = f" for Python {self.pyversion}"
        if self.architecture is not None:
            if not pytext:
                pytext = " for Python"
            pytext += f" {self.architecture}bits"
        text += f"{pytext}\n{self.description}\nWebsite: {self.url}\n[{Path(self.fname).name}]"
        return text

    def is_compatible_with(self, distribution):
        """Return True if package is compatible with distribution in terms of
        architecture and Python version (if applyable)"""
        iscomp = True
        if self.architecture is not None:
            # Source distributions (not yet supported though)
            iscomp = iscomp and self.architecture == distribution.architecture
        if self.pyversion is not None:
            # Non-pure Python package
            iscomp = iscomp and self.pyversion == distribution.version
        return iscomp

    def extract_optional_infos(self, update=False, suggested_summary=None):
        """Extract package optional infos (description, url)
        from the package database"""
        metadata = get_package_metadata("packages.ini", self.name, True, update=update)
        for key, value in list(metadata.items()):
            setattr(self, key, value)
        if suggested_summary and suggested_summary!="":
            setattr(self, 'description',suggested_summary)


class Package(BasePackage):
    def __init__(self, fname, update=False, suggested_summary=None):
        BasePackage.__init__(self, fname)
        self.files = []
        self.extract_infos()
        self.extract_optional_infos(update=update,suggested_summary=suggested_summary)

    def extract_infos(self):
        """Extract package infos (name, version, architecture)
        from filename (installer basename)"""
        bname = Path(self.fname).name
        if bname.endswith(("32.whl", "64.whl")):
            # {name}[-{bloat}]-{version}-{python tag}-{abi tag}-{platform tag}.whl
            # ['sounddevice','0.3.5','py2.py3.cp34.cp35','none','win32']
            # PyQt5-5.7.1-5.7.1-cp34.cp35.cp36-none-win_amd64.whl
            bname2 = bname[:-4].split("-")
            self.name = bname2[0]
            self.version = "-".join(list(bname2[1:-3]))
            self.pywheel, abi, arch = bname2[-3:]
            self.pyversion = None  # Let's ignore this  self.pywheel
            # wheel arch is 'win32' or 'win_amd64'
            self.architecture = 32 if arch == "win32" else 64
            return
        elif bname.endswith((".zip", ".tar.gz", ".whl")):
            # distutils sdist
            infos = utils.get_source_package_infos(bname)
            if infos is not None:
                self.name, self.version = infos
                return
        raise NotImplementedError(f"Not supported package type {bname}")


class WininstPackage(BasePackage):
    def __init__(self, fname, distribution):
        BasePackage.__init__(self, fname)
        self.logname = None
        self.distribution = distribution
        self.architecture = distribution.architecture
        self.pyversion = distribution.version
        self.extract_infos()
        self.extract_optional_infos()

    def extract_infos(self):
        """Extract package infos (name, version, architecture)"""
        match = re.match(r"Remove([a-zA-Z0-9\-\_\.]*)\.exe", self.fname)
        if match is None:
            return
        self.name = match.groups()[0]
        self.logname = f"{self.name}-wininst.log"
        fd = open(
            str(Path(self.distribution.target) / self.logname),
            "U",
        )
        searchtxt = "DisplayName="
        for line in fd.readlines():
            pos = line.find(searchtxt)
            if pos != -1:
                break
        else:
            return
        fd.close()
        match = re.match(
            r"Python %s %s-([0-9\.]*)" % (self.pyversion, self.name),
            line[pos + len(searchtxt) :],
        )
        if match is None:
            return
        self.version = match.groups()[0]

    def uninstall(self):
        """Uninstall package"""
        subprocess.call(
            [self.fname, "-u", self.logname],
            cwd=self.distribution.target,
        )


class Distribution(object):
    def __init__(self, target=None, verbose=False, indent=False):
        self.target = target
        self.verbose = verbose
        self.indent = indent
        self.pip = None

        # if no target path given, take the current python interpreter one
        if self.target is None:
            self.target = os.path.dirname(sys.executable)
        self.to_be_removed = []  # list of directories to be removed later

        self.version, self.architecture = utils.get_python_infos(target)
        # name of the exe (python.exe or pypy3;exe)
        self.short_exe = Path(utils.get_python_executable(self.target)).name

    def clean_up(self):
        """Remove directories which couldn't be removed when building"""
        for path in self.to_be_removed:
            try:
                shutil.rmtree(path, onerror=utils.onerror)
            except WindowsError:
                print(
                    f"Directory {path} could not be removed",
                    file=sys.stderr,
                )

    def remove_directory(self, path):
        """Try to remove directory -- on WindowsError, remove it later"""
        try:
            shutil.rmtree(path)
        except WindowsError:
            self.to_be_removed.append(path)

    def copy_files(
        self,
        package,
        targetdir,
        srcdir,
        dstdir,
        create_bat_files=False,
    ):
        """Add copy task"""
        srcdir = str(Path(targetdir) / srcdir)
        if not Path(srcdir).is_dir():
            return
        offset = len(srcdir) + len(os.pathsep)
        for dirpath, dirnames, filenames in os.walk(srcdir):
            for dname in dirnames:
                t_dname = str(Path(dirpath) / dname)[offset:]
                src = str(Path(srcdir) / t_dname)
                dst = str(Path(dstdir) / t_dname)
                if self.verbose:
                    print(f"mkdir: {dst}")
                full_dst = str(Path(self.target) / dst)
                if not Path(full_dst).exists():
                    os.mkdir(full_dst)
                package.files.append(dst)
            for fname in filenames:
                t_fname = str(Path(dirpath) / fname)[offset:]
                src = str(Path(srcdir) / t_fname)
                if dirpath.endswith("_system32"):
                    # Files that should be copied in %WINDIR%\system32
                    dst = fname
                else:
                    dst = str(Path(dstdir) / t_fname)
                if self.verbose:
                    print(f"file:  {dst}")
                full_dst = str(Path(self.target) / dst)
                shutil.move(src, full_dst)
                package.files.append(dst)
                name, ext = Path(dst).stem, Path(dst).suffix
                if create_bat_files and ext in ("", ".py"):
                    dst = name + ".bat"
                    if self.verbose:
                        print(f"file:  {dst}")
                    full_dst = str(Path(self.target) / dst)
                    fd = open(full_dst, "w")
                    fd.write(
                        """@echo off
python "%~dpn0"""
                        + ext
                        + """" %*"""
                    )
                    fd.close()
                    package.files.append(dst)

    def create_file(self, package, name, dstdir, contents):
        """Generate data file -- path is relative to distribution root dir"""
        dst = str(Path(dstdir) / name)
        if self.verbose:
            print(f"create:  {dst}")
        full_dst = str(Path(self.target) / dst)
        open(full_dst, "w").write(contents)
        package.files.append(dst)

    def get_installed_packages(self, update=False):
        """Return installed packages"""

        # Include package installed via pip (not via WPPM)
        wppm = []
        try:  # we try to use also 'pip inspect' via piptree (work for pip>= 22.2)
            if str(Path(sys.executable).parent) == self.target:
                self.pip = piptree.pipdata()
            else:
                self.pip = piptree.pipdata(Target=utils.get_python_executable(self.target))
            pip_list = self.pip.pip_list()
        except:
            # if failure back to pip list (will use packages.ini for names)
            cmdx = [
                utils.get_python_executable(self.target),  # PyPy !
                "-m",
                "pip",
                "list",
            ]
            pip_list_raw = utils.exec_run_cmd(cmdx).splitlines()
            # pip list gives 2 lines of titles to ignore
            pip_list = [l.split() for l in pip_list_raw[2:]]

        # create pip package list
        wppm = [
            Package(
                f"{i[0].replace('-', '_').lower()}-{i[1]}-py3-none-any.whl",
                update=update,
                suggested_summary=self.pip.summary(i[0]) if self.pip else None
            )
            for i in pip_list
        ]
        return sorted(wppm, key=lambda tup: tup.name.lower())

    def find_package(self, name):
        """Find installed package"""
        for pack in self.get_installed_packages():
            if normalize(pack.name) == normalize(name):
                return pack

    def uninstall_existing(self, package):
        """Uninstall existing package (or package name)"""
        if isinstance(package, str):
            pack = self.find_package(package)
        else:
            pack = self.find_package(package.name)
        if pack is not None:
            self.uninstall(pack)

    def patch_all_shebang(
        self,
        to_movable=True,
        max_exe_size=999999,
        targetdir="",
    ):
        """make all python launchers relatives"""
        import glob
        import os

        for ffname in glob.glob(r"%s\Scripts\*.exe" % self.target):
            size = os.path.getsize(ffname)
            if size <= max_exe_size:
                utils.patch_shebang_line(
                    ffname,
                    to_movable=to_movable,
                    targetdir=targetdir,
                )
        for ffname in glob.glob(r"%s\Scripts\*.py" % self.target):
            utils.patch_shebang_line_py(
                ffname,
                to_movable=to_movable,
                targetdir=targetdir,
            )

    def install(self, package, install_options=None):
        """Install package in distribution"""
        assert package.is_compatible_with(self)

        # wheel addition
        if package.fname.endswith((".whl", ".tar.gz", ".zip")):
            self.install_bdist_direct(package, install_options=install_options)
        self.handle_specific_packages(package)
        # minimal post-install actions
        self.patch_standard_packages(package.name)

    def do_pip_action(self, actions=None, install_options=None):
        """Do pip action in a distribution"""
        my_list = install_options
        if my_list is None:
            my_list = []
        my_actions = actions
        if my_actions is None:
            my_actions = []
        executing = str(Path(self.target).parent / "scripts" / "env.bat")
        if Path(executing).is_file():
            complement = [
                r"&&",
                "cd",
                "/D",
                self.target,
                r"&&",
                utils.get_python_executable(self.target),
                # Before PyPy: osp.join(self.target, 'python.exe')
            ]
            complement += ["-m", "pip"]
        else:
            executing = utils.get_python_executable(self.target)
            # Before PyPy: osp.join(self.target, 'python.exe')
            complement = ["-m", "pip"]
        try:
            fname = utils.do_script(
                this_script=None,
                python_exe=executing,
                architecture=self.architecture,
                verbose=self.verbose,
                install_options=complement + my_actions + my_list,
            )
        except RuntimeError:
            if not self.verbose:
                print("Failed!")
                raise

    def patch_standard_packages(self, package_name="", to_movable=True):
        """patch Winpython packages in need"""
        import filecmp

        # Adpating to PyPy
        if "pypy3" in Path(utils.get_python_executable(self.target)).name:
            site_package_place = "\\site-packages\\"
        else:
            site_package_place = "\\Lib\\site-packages\\"
        # 'pywin32' minimal post-install (pywin32_postinstall.py do too much)
        if package_name.lower() == "pywin32" or package_name == "":
            origin = self.target + site_package_place + "pywin32_system32"

            destin = self.target
            if Path(origin).is_dir():
                for name in os.listdir(origin):
                    here, there = (
                        str(Path(origin) / name),
                        str(Path(destin) / name),
                    )
                    if not Path(there).exists() or not filecmp.cmp(here, there):
                        shutil.copyfile(here, there)
        # 'pip' to do movable launchers (around line 100) !!!!
        # rational: https://github.com/pypa/pip/issues/2328
        if package_name.lower() == "pip" or package_name == "":
            # ensure pip will create movable launchers
            # sheb_mov1 = classic way up to WinPython 2016-01
            # sheb_mov2 = tried  way, but doesn't work for pip (at least)
            sheb_fix = " executable = get_executable()"
            sheb_mov1 = " executable = os.path.join(os.path.basename(get_executable()))"
            sheb_mov2 = (
                " executable = os.path.join('..',os.path.basename(get_executable()))"
            )

            # Adpating to PyPy
            the_place = site_package_place + r"pip\_vendor\distlib\scripts.py"
            print(the_place)
            if to_movable:
                utils.patch_sourcefile(
                    self.target + the_place,
                    sheb_fix,
                    sheb_mov1,
                )
                utils.patch_sourcefile(
                    self.target + the_place,
                    sheb_mov2,
                    sheb_mov1,
                )
            else:
                utils.patch_sourcefile(
                    self.target + the_place,
                    sheb_mov1,
                    sheb_fix,
                )
                utils.patch_sourcefile(
                    self.target + the_place,
                    sheb_mov2,
                    sheb_fix,
                )
            # ensure pip wheel will register relative PATH in 'RECORD' files
            # will be in standard pip 8.0.3
            utils.patch_sourcefile(
                self.target + (site_package_place + r"pip\wheel.py"),
                " writer.writerow((f, h, l))",
                " writer.writerow((normpath(f, lib_dir), h, l))",
            )

            # create movable launchers for previous package installations
            self.patch_all_shebang(to_movable=to_movable)
        if package_name.lower() == "spyder" or package_name == "":
            # spyder don't goes on internet without I ask
            utils.patch_sourcefile(
                self.target + (site_package_place + r"spyderlib\config\main.py"),
                "'check_updates_on_startup': True,",
                "'check_updates_on_startup': False,",
            )
            utils.patch_sourcefile(
                self.target + (site_package_place + r"spyder\config\main.py"),
                "'check_updates_on_startup': True,",
                "'check_updates_on_startup': False,",
            )
        # workaround bad installers
        if package_name.lower() == "numba":
            self.create_pybat(["numba"])
        else:
            self.create_pybat(package_name.lower())

    def create_pybat(
        self,
        names="",
        contents=r"""@echo off
..\python "%~dpn0" %*""",
    ):
        """Create launcher batch script when missing"""

        scriptpy = str(Path(self.target) / "Scripts")  # std Scripts of python

        # PyPy has no initial Scipts directory
        if not Path(scriptpy).is_dir():
            os.mkdir(scriptpy)
        if not list(names) == names:
            my_list = [
                f for f in os.listdir(scriptpy) if "." not in f and f.startswith(names)
            ]
        else:
            my_list = names
        for name in my_list:
            if Path(scriptpy).is_dir() and (Path(scriptpy) / name).is_file():
                if (
                    not (Path(scriptpy) / (name + ".exe")).is_file()
                    and not (Path(scriptpy) / (name + ".bat")).is_file()
                ):
                    fd = open(
                        str(Path(scriptpy) / (name + ".bat")),
                        "w",
                    )
                    fd.write(contents)
                    fd.close()

    def handle_specific_packages(self, package):
        """Packages requiring additional configuration"""
        if package.name.lower() in (
            "pyqt4",
            "pyqt5",
            "pyside2",
        ):
            # Qt configuration file (where to find Qt)
            name = "qt.conf"
            contents = """[Paths]
Prefix = .
Binaries = ."""
            self.create_file(
                package,
                name,
                str(Path("Lib") / "site-packages" / package.name),
                contents,
            )
            self.create_file(
                package,
                name,
                ".",
                contents.replace(
                    ".",
                    f"./Lib/site-packages/{package.name}",
                ),
            )
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
            tmp_string = tmp_string.replace("python.exe", my_exec)

            self.create_file(
                package,
                f"pyuic{package.name[-1]}.bat",
                "Scripts",
                tmp_string.replace("package.name", package.name),
            )
            # Adding missing __init__.py files (fixes Issue 8)
            uic_path = str(Path("Lib") / "site-packages" / package.name / "uic")
            for dirname in ("Loader", "port_v2", "port_v3"):
                self.create_file(
                    package,
                    "__init__.py",
                    str(Path(uic_path) / dirname),
                    "",
                )

    def _print(self, package, action):
        """Print package-related action text (e.g. 'Installing')
        indicating progress"""
        text = " ".join([action, package.name, package.version])
        if self.verbose:
            utils.print_box(text)
        else:
            if self.indent:
                text = (" " * 4) + text
            print(text + "...", end=" ")

    def _print_done(self):
        """Print OK at the end of a process"""
        if not self.verbose:
            print("OK")

    def uninstall(self, package):
        """Uninstall package from distribution"""
        self._print(package, "Uninstalling")
        if not package.name == "pip":
            # trick to get true target (if not current)
            this_executable_path = self.target
            this_exec = utils.get_python_executable(self.target)  # PyPy !
            subprocess.call(
                [
                    this_exec,
                    "-m",
                    "pip",
                    "uninstall",
                    package.name,
                    "-y",
                ],
                cwd=this_executable_path,
            )
            # no more legacy, no package are installed by old non-pip means
        self._print_done()

    def install_bdist_direct(self, package, install_options=None):
        """Install a package directly !"""
        self._print(
            package,
            f"Installing {package.fname.split('.')[-1]}",
        )
        try:
            fname = utils.direct_pip_install(
                package.fname,
                python_exe=utils.get_python_executable(self.target),  # PyPy !
                architecture=self.architecture,
                verbose=self.verbose,
                install_options=install_options,
            )
        except RuntimeError:
            if not self.verbose:
                print("Failed!")
                raise
        package = Package(fname)
        self._print_done()

    def install_script(self, script, install_options=None):
        try:
            fname = utils.do_script(
                script,
                python_exe=utils.get_python_executable(self.target),  # PyPy3 !
                architecture=self.architecture,
                verbose=self.verbose,
                install_options=install_options,
            )
        except RuntimeError:
            if not self.verbose:
                print("Failed!")
                raise


def main(test=False):
    if test:
        sbdir = str(Path(__file__).parents[0].parent.parent.parent / "sandbox")
        tmpdir = str(Path(sbdir) / "tobedeleted")

        fname = str(Path(sbdir) / "VTK-5.10.0-Qt-4.7.4.win32-py2.7.exe")
        print(Package(fname))
        sys.exit()
        target = str(
            Path(utils.BASE_DIR) / "build" / "winpython-2.7.3" / "python-2.7.3"
        )
        fname = str(Path(utils.BASE_DIR) / "packages.src" / "docutils-0.9.1.tar.gz")

        dist = Distribution(target, verbose=True)
        pack = Package(fname)
        print(pack.description)
        # dist.install(pack)
        # dist.uninstall(pack)
    else:
        bold = "\033[1m"
        unbold = "\033[0m"
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
            help=f"list packages matching the given [optionnal] package expression: {unbold}wppm -ls{unbold}, {unbold}wppm -ls pand{unbold}",
        )   
        parser.add_argument(
            "-p",
            dest="pipdown",
            action="store_const",
            const=True,
            default=False,
            help=f"show Package dependancies of the given package[option]: {unbold}wppm -p pandas[test]{unbold}",
        )
        parser.add_argument(
            "-r",
            dest="pipup",
            action="store_const",
            const=True,
            default=False,
            help=f"show Reverse dependancies of the given package[option]: {unbold}wppm -r pytest[test]{unbold}",
        )
        parser.add_argument(
            "-l",
            dest="levels",
            type=int,
            default=2,
            help=f"show 'LEVELS' levels of dependancies of the package, default is 2: {unbold}wppm -p pandas -l1{unbold}",
        )
        parser.add_argument(
            "-lsa",
            dest="all",
            action="store_const",
            const=True,
            default=False,
            help=f"list details of package names matching given regular expression: {unbold}wppm -lsa pandas -l1{unbold}",
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
        if args.target and not args.target==sys.prefix:
            targetpython = args.target if args.target[-4:] == '.exe' else str(Path(args.target) / 'python.exe')
            # print(targetpython.resolve() to check)
        if args.install and args.uninstall:
            raise RuntimeError("Incompatible arguments: --install and --uninstall")
        if args.registerWinPython and args.unregisterWinPython:
            raise RuntimeError("Incompatible arguments: --install and --uninstall")
        if args.pipdown:
            pip = piptree.pipdata(Target=targetpython)
            pack, extra, *other = (args.fname + "[").replace("]", "[").split("[")
            pip.down(pack, extra, args.levels, verbose=args.verbose)
            sys.exit()
        elif args.pipup:
            pip = piptree.pipdata(Target=targetpython)
            pack, extra, *other = (args.fname + "[").replace("]", "[").split("[")
            pip.up(pack, extra, args.levels, verbose=args.verbose)
            sys.exit()
        elif args.list:
            pip = piptree.pipdata(Target=targetpython)
            todo = [l for l in pip.pip_list(full=True) if bool(re.search(args.fname, l[0])) ]
            titles = [['Package', 'Version', 'Summary'],['_' * max(x, 6) for x in utils.columns_width(todo)]] 
            listed = utils.formatted_list(titles + todo)
            for p in listed:
                print(*p)
            sys.exit()
        elif args.all:
            pip = piptree.pipdata(Target=targetpython)
            todo = [l for l in pip.pip_list(full=True) if bool(re.search(args.fname, l[0])) ]
            for l in todo:
                # print(pip.distro[l[0]])
                title = f"**  Package: {l[0]}  **"
                print("\n"+"*"*len(title), f"\n{title}", "\n"+"*"*len(title) )
                for key, value in pip.raw[l[0]].items():
                    rawtext=json.dumps(value, indent=2)
                    lines = [l for l in rawtext.split(r"\n") if len(l.strip()) > 2]
                    if key.lower() != 'description' or args.verbose==True:
                        print(f"{key}: ","\n".join(lines).replace('"', ""))
            sys.exit()            
        if args.registerWinPython:
            print(registerWinPythonHelp)
            if utils.is_python_distribution(args.target):
                dist = Distribution(args.target)
            else:
                raise WindowsError(f"Invalid Python distribution {args.target}")
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
                raise WindowsError(f"Invalid Python distribution {args.target}")
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
                raise IOError(f"File not found: {args.fname}")
        if utils.is_python_distribution(args.target):
            dist = Distribution(args.target)
            try:
                if args.uninstall:
                    package = dist.find_package(args.fname)
                    dist.uninstall(package)
                else:
                    package = Package(args.fname)
                    if args.install and package.is_compatible_with(dist):
                        dist.install(package)
                    else:
                        raise RuntimeError(
                            "Package is not compatible with Python "
                            f"{dist.version} {dist.architecture}bit"
                        )
            except NotImplementedError:
                raise RuntimeError("Package is not (yet) supported by WPPM")
        else:
            raise WindowsError(f"Invalid Python distribution {args.target}")


if __name__ == "__main__":
    main()