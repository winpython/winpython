# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
WinPython Package Manager

Created on Fri Aug 03 14:32:26 2012
"""

from __future__ import print_function

import os
import os.path as osp
import shutil
import re
import sys
import subprocess

# Local imports
from winpython import utils
from winpython.config import DATA_PATH
from winpython.py3compat import configparser as cp

# from former wppm separate script launcher
from argparse import ArgumentParser
from winpython import py3compat


# Workaround for installing PyVISA on Windows from source:
os.environ['HOME'] = os.environ['USERPROFILE']

# pep503 defines normalized package names: www.python.org/dev/peps/pep-0503
def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def get_package_metadata(database, name):
    """Extract infos (description, url) from the local database"""
    # Note: we could use the PyPI database but this has been written on
    # machine which is not connected to the internet
    db = cp.ConfigParser()
    db.readfp(open(osp.join(DATA_PATH, database)))
    metadata = dict(
        description='',
        url='https://pypi.org/project/' + name,
    )
    for key in metadata:
        name1 = name.lower()
        # wheel replace '-' per '_' in key
        for name2 in (
            name1,
            name1.split('-')[0],
            name1.replace('-', '_'),
            '-'.join(name1.split('_')),
            normalize(name),
        ):
            try:
                metadata[key] = db.get(name2, key)
                break
            except (cp.NoSectionError, cp.NoOptionError):
                pass
    return metadata


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
        text = "%s %s" % (self.name, self.version)
        pytext = ""
        if self.pyversion is not None:
            pytext = " for Python %s" % self.pyversion
        if self.architecture is not None:
            if not pytext:
                pytext = " for Python"
            pytext += " %dbits" % self.architecture
        text += "%s\n%s\nWebsite: %s\n[%s]" % (
            pytext,
            self.description,
            self.url,
            osp.basename(self.fname),
        )
        return text

    def is_compatible_with(self, distribution):
        """Return True if package is compatible with distribution in terms of
        architecture and Python version (if applyable)"""
        iscomp = True
        if self.architecture is not None:
            # Source distributions (not yet supported though)
            iscomp = (
                iscomp
                and self.architecture
                == distribution.architecture
            )
        if self.pyversion is not None:
            # Non-pure Python package
            iscomp = (
                iscomp
                and self.pyversion == distribution.version
            )
        return iscomp

    def extract_optional_infos(self):
        """Extract package optional infos (description, url)
        from the package database"""
        metadata = get_package_metadata(
            'packages.ini', self.name
        )
        for key, value in list(metadata.items()):
            setattr(self, key, value)


class Package(BasePackage):
    def __init__(self, fname):
        BasePackage.__init__(self, fname)
        self.files = []
        self.extract_infos()
        self.extract_optional_infos()

    def extract_infos(self):
        """Extract package infos (name, version, architecture)
        from filename (installer basename)"""
        bname = osp.basename(self.fname)
        if bname.endswith(('32.whl', '64.whl')):
            # {name}[-{bloat}]-{version}-{python tag}-{abi tag}-{platform tag}.whl
            # ['sounddevice','0.3.5','py2.py3.cp34.cp35','none','win32']
            # PyQt5-5.7.1-5.7.1-cp34.cp35.cp36-none-win_amd64.whl
            bname2 = bname[:-4].split("-")
            self.name = bname2[0]
            self.version = '-'.join(list(bname2[1:-3]))
            self.pywheel, abi, arch = bname2[-3:]
            self.pyversion = (
                None
            )  # Let's ignore this  self.pywheel
            # wheel arch is 'win32' or 'win_amd64'
            self.architecture = (
                32 if arch == 'win32' else 64
            )
            return
        elif bname.endswith(('.zip', '.tar.gz', '.whl')):
            # distutils sdist
            infos = utils.get_source_package_infos(bname)
            if infos is not None:
                self.name, self.version = infos
                return
        raise NotImplementedError(
            "Not supported package type %s" % bname
        )


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
        match = re.match(
            r'Remove([a-zA-Z0-9\-\_\.]*)\.exe', self.fname
        )
        if match is None:
            return
        self.name = match.groups()[0]
        self.logname = '%s-wininst.log' % self.name
        fd = open(
            osp.join(
                self.distribution.target, self.logname
            ),
            'U',
        )
        searchtxt = 'DisplayName='
        for line in fd.readlines():
            pos = line.find(searchtxt)
            if pos != -1:
                break
        else:
            return
        fd.close()
        match = re.match(
            r'Python %s %s-([0-9\.]*)'
            % (self.pyversion, self.name),
            line[pos + len(searchtxt) :],
        )
        if match is None:
            return
        self.version = match.groups()[0]

    def uninstall(self):
        """Uninstall package"""
        subprocess.call(
            [self.fname, '-u', self.logname],
            cwd=self.distribution.target,
        )


class Distribution(object):
    def __init__(
        self, target=None, verbose=False, indent=False
    ):
        self.target = target
        self.verbose = verbose
        self.indent = indent

        # if no target path given, take the current python interpreter one
        if self.target is None:
            self.target = os.path.dirname(sys.executable)
        self.to_be_removed = (
            []
        )  # list of directories to be removed later

        self.version, self.architecture = utils.get_python_infos(
            target
        )

    def clean_up(self):
        """Remove directories which couldn't be removed when building"""
        for path in self.to_be_removed:
            try:
                shutil.rmtree(path, onerror=utils.onerror)
            except WindowsError:
                print(
                    "Directory %s could not be removed"
                    % path,
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
        srcdir = osp.join(targetdir, srcdir)
        if not osp.isdir(srcdir):
            return
        offset = len(srcdir) + len(os.pathsep)
        for dirpath, dirnames, filenames in os.walk(srcdir):
            for dname in dirnames:
                t_dname = osp.join(dirpath, dname)[offset:]
                src = osp.join(srcdir, t_dname)
                dst = osp.join(dstdir, t_dname)
                if self.verbose:
                    print("mkdir: %s" % dst)
                full_dst = osp.join(self.target, dst)
                if not osp.exists(full_dst):
                    os.mkdir(full_dst)
                package.files.append(dst)
            for fname in filenames:
                t_fname = osp.join(dirpath, fname)[offset:]
                src = osp.join(srcdir, t_fname)
                if dirpath.endswith('_system32'):
                    # Files that should be copied in %WINDIR%\system32
                    dst = fname
                else:
                    dst = osp.join(dstdir, t_fname)
                if self.verbose:
                    print("file:  %s" % dst)
                full_dst = osp.join(self.target, dst)
                shutil.move(src, full_dst)
                package.files.append(dst)
                name, ext = osp.splitext(dst)
                if create_bat_files and ext in ('', '.py'):
                    dst = name + '.bat'
                    if self.verbose:
                        print("file:  %s" % dst)
                    full_dst = osp.join(self.target, dst)
                    fd = open(full_dst, 'w')
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
        dst = osp.join(dstdir, name)
        if self.verbose:
            print("create:  %s" % dst)
        full_dst = osp.join(self.target, dst)
        open(full_dst, 'w').write(contents)
        package.files.append(dst)

    def get_installed_packages(self):
        """Return installed packages"""

        # Include package installed via pip (not via WPPM)
        wppm = []
        try:
            if (
                os.path.dirname(sys.executable)
                == self.target
            ):
                #  direct way: we interrogate ourself, using official API
                import pkg_resources, imp

                imp.reload(pkg_resources)
                pip_list = [
                    (i.key, i.version)
                    for i in pkg_resources.working_set
                ]
            else:
                #  indirect way: we interrogate something else
                cmdx = [
                    osp.join(self.target, 'python.exe'),
                    '-c',
                    "import pip;from pip._internal.utils.misc import  get_installed_distributions as pip_get_installed_distributions ;print('+!+'.join(['%s@+@%s@+@' % (i.key,i.version)  for i in pip_get_installed_distributions()]))",
                ]
                p = subprocess.Popen(
                    cmdx,
                    shell=True,
                    stdout=subprocess.PIPE,
                    cwd=self.target,
                )
                stdout, stderr = p.communicate()
                start_at = (
                    2 if sys.version_info >= (3, 0) else 0
                )
                pip_list = [
                    line.split("@+@")[:2]
                    for line in ("%s" % stdout)[
                        start_at:
                    ].split("+!+")
                ]
            # there are only Packages installed with pip now
            # create pip package list
            wppm = [
                Package(
                    '%s-%s-py2.py3-none-any.whl'
                    % (i[0].replace('-', '_').lower(), i[1])
                )
                for i in pip_list
            ]
        except:
            pass
        return sorted(
            wppm, key=lambda tup: tup.name.lower()
        )

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

        for ffname in glob.glob(
            r'%s\Scripts\*.exe' % self.target
        ):
            size = os.path.getsize(ffname)
            if size <= max_exe_size:
                utils.patch_shebang_line(
                    ffname,
                    to_movable=to_movable,
                    targetdir=targetdir,
                )
        for ffname in glob.glob(
            r'%s\Scripts\*.py' % self.target
        ):
            utils.patch_shebang_line_py(
                ffname,
                to_movable=to_movable,
                targetdir=targetdir,
            )

    def install(self, package, install_options=None):
        """Install package in distribution"""
        assert package.is_compatible_with(self)

        # wheel addition
        if package.fname.endswith(
            ('.whl', '.tar.gz', '.zip')
        ):
            self.install_bdist_direct(
                package, install_options=install_options
            )
        self.handle_specific_packages(package)
        # minimal post-install actions
        self.patch_standard_packages(package.name)

    def do_pip_action(
        self, actions=None, install_options=None
    ):
        """Do pip action in a distribution"""
        my_list = install_options
        if my_list is None:
            my_list = []
        my_actions = actions
        if my_actions is None:
            my_actions = []
        executing = osp.join(
            self.target, '..', 'scripts', 'env.bat'
        )
        if osp.isfile(executing):
            complement = [
                r'&&',
                'cd',
                '/D',
                self.target,
                r'&&',
                osp.join(self.target, 'python.exe'),
            ]
            complement += ['-m', 'pip']
        else:
            executing = osp.join(self.target, 'python.exe')
            complement = ['-m', 'pip']
        try:
            fname = utils.do_script(
                this_script=None,
                python_exe=executing,
                architecture=self.architecture,
                verbose=self.verbose,
                install_options=complement
                + my_actions
                + my_list,
            )
        except RuntimeError:
            if not self.verbose:
                print("Failed!")
                raise

    def patch_standard_packages(
        self, package_name='', to_movable=True
    ):
        """patch Winpython packages in need"""
        import filecmp

        # 'pywin32' minimal post-install (pywin32_postinstall.py do too much)
        if (
            package_name.lower() == "pywin32"
            or package_name == ''
        ):
            origin = self.target + (
                r"\Lib\site-packages\pywin32_system32"
            )
            destin = self.target
            if osp.isdir(origin):
                for name in os.listdir(origin):
                    here, there = (
                        osp.join(origin, name),
                        osp.join(destin, name),
                    )
                    if not os.path.exists(
                        there
                    ) or not filecmp.cmp(here, there):
                        shutil.copyfile(here, there)
        # 'pip' to do movable launchers (around line 100) !!!!
        # rational: https://github.com/pypa/pip/issues/2328
        if (
            package_name.lower() == "pip"
            or package_name == ''
        ):
            # ensure pip will create movable launchers
            # sheb_mov1 = classic way up to WinPython 2016-01
            # sheb_mov2 = tried  way, but doesn't work for pip (at least)
            sheb_fix = " executable = get_executable()"
            sheb_mov1 = " executable = os.path.join(os.path.basename(get_executable()))"
            sheb_mov2 = " executable = os.path.join('..',os.path.basename(get_executable()))"
            if to_movable:
                utils.patch_sourcefile(
                    self.target
                    + r"\Lib\site-packages\pip\_vendor\distlib\scripts.py",
                    sheb_fix,
                    sheb_mov1,
                )
                utils.patch_sourcefile(
                    self.target
                    + r"\Lib\site-packages\pip\_vendor\distlib\scripts.py",
                    sheb_mov2,
                    sheb_mov1,
                )
            else:
                utils.patch_sourcefile(
                    self.target
                    + r"\Lib\site-packages\pip\_vendor\distlib\scripts.py",
                    sheb_mov1,
                    sheb_fix,
                )
                utils.patch_sourcefile(
                    self.target
                    + r"\Lib\site-packages\pip\_vendor\distlib\scripts.py",
                    sheb_mov2,
                    sheb_fix,
                )
            # ensure pip wheel will register relative PATH in 'RECORD' files
            # will be in standard pip 8.0.3
            utils.patch_sourcefile(
                self.target
                + (r"\Lib\site-packages\pip\wheel.py"),
                " writer.writerow((f, h, l))",
                " writer.writerow((normpath(f, lib_dir), h, l))",
            )

            # create movable launchers for previous package installations
            self.patch_all_shebang(to_movable=to_movable)
        if (
            package_name.lower() == "spyder"
            or package_name == ''
        ):
            # spyder don't goes on internet without I ask
            utils.patch_sourcefile(
                self.target
                + (
                    r"\Lib\site-packages\spyderlib\config\main.py"
                ),
                "'check_updates_on_startup': True,",
                "'check_updates_on_startup': False,",
            )
            utils.patch_sourcefile(
                self.target
                + (
                    r"\Lib\site-packages\spyder\config\main.py"
                ),
                "'check_updates_on_startup': True,",
                "'check_updates_on_startup': False,",
            )
        # workaround bad installers
        if package_name.lower() == "numba":
            self.create_pybat(['numba', 'pycc'])
        else:
            self.create_pybat(package_name.lower())

    def create_pybat(
        self,
        names='',
        contents=r"""@echo off
..\python "%~dpn0" %*""",
    ):
        """Create launcher batch script when missing"""

        scriptpy = osp.join(
            self.target, 'Scripts'
        )  # std Scripts of python
        if not list(names) == names:
            my_list = [
                f
                for f in os.listdir(scriptpy)
                if '.' not in f and f.startswith(names)
            ]
        else:
            my_list = names
        for name in my_list:
            if osp.isdir(scriptpy) and osp.isfile(
                osp.join(scriptpy, name)
            ):
                if not osp.isfile(
                    osp.join(scriptpy, name + '.exe')
                ) and not osp.isfile(
                    osp.join(scriptpy, name + '.bat')
                ):
                    fd = open(
                        osp.join(scriptpy, name + '.bat'),
                        'w',
                    )
                    fd.write(contents)
                    fd.close()

    def handle_specific_packages(self, package):
        """Packages requiring additional configuration"""
        if package.name.lower() in (
            'pyqt4',
            'pyqt5',
            'pyside2',
        ):
            # Qt configuration file (where to find Qt)
            name = 'qt.conf'
            contents = """[Paths]
Prefix = .
Binaries = ."""
            self.create_file(
                package,
                name,
                osp.join(
                    'Lib', 'site-packages', package.name
                ),
                contents,
            )
            self.create_file(
                package,
                name,
                '.',
                contents.replace(
                    '.',
                    './Lib/site-packages/%s' % package.name,
                ),
            )
            # pyuic script
            if package.name.lower() == 'pyqt5':
                # see http://code.activestate.com/lists/python-list/666469/
                tmp_string = r'''@echo off
if "%WINPYDIR%"=="" call "%~dp0..\..\scripts\env.bat"
"%WINPYDIR%\python.exe" -m PyQt5.uic.pyuic %1 %2 %3 %4 %5 %6 %7 %8 %9'''
            else:
                tmp_string = r'''@echo off
if "%WINPYDIR%"=="" call "%~dp0..\..\scripts\env.bat"
"%WINPYDIR%\python.exe" "%WINPYDIR%\Lib\site-packages\package.name\uic\pyuic.py" %1 %2 %3 %4 %5 %6 %7 %8 %9'''
            self.create_file(
                package,
                'pyuic%s.bat' % package.name[-1],
                'Scripts',
                tmp_string.replace(
                    'package.name', package.name
                ),
            )
            # Adding missing __init__.py files (fixes Issue 8)
            uic_path = osp.join(
                'Lib', 'site-packages', package.name, 'uic'
            )
            for dirname in ('Loader', 'port_v2', 'port_v3'):
                self.create_file(
                    package,
                    '__init__.py',
                    osp.join(uic_path, dirname),
                    '',
                )

    def _print(self, package, action):
        """Print package-related action text (e.g. 'Installing')
        indicating progress"""
        text = " ".join(
            [action, package.name, package.version]
        )
        if self.verbose:
            utils.print_box(text)
        else:
            if self.indent:
                text = (' ' * 4) + text
            print(text + '...', end=" ")

    def _print_done(self):
        """Print OK at the end of a process"""
        if not self.verbose:
            print("OK")

    def uninstall(self, package):
        """Uninstall package from distribution"""
        self._print(package, "Uninstalling")
        if not package.name == 'pip':
            # trick to get true target (if not current)
            this_executable_path = self.target
            subprocess.call(
                [
                    this_executable_path + r'\python.exe',
                    '-m',
                    'pip',
                    'uninstall',
                    package.name,
                    '-y',
                ],
                cwd=this_executable_path,
            )
            # no more legacy, no package are installed by old non-pip means
        self._print_done()

    def install_bdist_direct(
        self, package, install_options=None
    ):
        """Install a package directly !"""
        self._print(
            package,
            "Installing %s" % package.fname.split(".")[-1],
        )
        try:
            fname = utils.direct_pip_install(
                package.fname,
                python_exe=osp.join(
                    self.target, 'python.exe'
                ),
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
                python_exe=osp.join(
                    self.target, 'python.exe'
                ),
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
        sbdir = osp.join(
            osp.dirname(__file__),
            os.pardir,
            os.pardir,
            os.pardir,
            'sandbox',
        )
        tmpdir = osp.join(sbdir, 'tobedeleted')

        # fname = osp.join(tmpdir, 'scipy-0.10.1.win-amd64-py2.7.exe')
        fname = osp.join(
            sbdir, 'VTK-5.10.0-Qt-4.7.4.win32-py2.7.exe'
        )
        print(Package(fname))
        sys.exit()
        target = osp.join(
            utils.BASE_DIR,
            'build',
            'winpython-2.7.3',
            'python-2.7.3',
        )
        fname = osp.join(
            utils.BASE_DIR,
            'packages.src',
            'docutils-0.9.1.tar.gz',
        )

        dist = Distribution(target, verbose=True)
        pack = Package(fname)
        print(pack.description)
        # dist.install(pack)
        # dist.uninstall(pack)
    else:

        parser = ArgumentParser(
            description="WinPython Package Manager: install, "
            "uninstall or upgrade Python packages on a Windows "
            "Python distribution like WinPython."
        )
        parser.add_argument(
            'fname',
            metavar='package',
            type=str if py3compat.PY3 else unicode,
            help='path to a Python package',
        )
        parser.add_argument(
            '-t',
            '--target',
            dest='target',
            default=sys.prefix,
            help='path to target Python distribution '
            '(default: "%s")' % sys.prefix,
        )
        parser.add_argument(
            '-i',
            '--install',
            dest='install',
            action='store_const',
            const=True,
            default=False,
            help='install package (this is the default action)',
        )
        parser.add_argument(
            '-u',
            '--uninstall',
            dest='uninstall',
            action='store_const',
            const=True,
            default=False,
            help='uninstall package',
        )
        args = parser.parse_args()

        if args.install and args.uninstall:
            raise RuntimeError(
                "Incompatible arguments: --install and --uninstall"
            )
        if not args.install and not args.uninstall:
            args.install = True
        if not osp.isfile(args.fname) and args.install:
            raise IOError("File not found: %s" % args.fname)
        if utils.is_python_distribution(args.target):
            dist = Distribution(args.target)
            try:
                if args.uninstall:
                    package = dist.find_package(args.fname)
                    dist.uninstall(package)
                else:
                    package = Package(args.fname)
                    if (
                        args.install
                        and package.is_compatible_with(dist)
                    ):
                        dist.install(package)
                    else:
                        raise RuntimeError(
                            "Package is not compatible with Python "
                            "%s %dbit"
                            % (
                                dist.version,
                                dist.architecture,
                            )
                        )
            except NotImplementedError:
                raise RuntimeError(
                    "Package is not (yet) supported by WPPM"
                )
        else:
            raise WindowsError(
                "Invalid Python distribution %s"
                % args.target
            )


if __name__ == '__main__':
    main()
