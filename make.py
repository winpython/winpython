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
from pathlib import Path
import re
import subprocess
import shutil
import sys

# Local imports
from winpython import wppm, utils
import diff


CHANGELOGS_DIR = str(Path(__file__).parent / "changelogs")
assert Path(CHANGELOGS_DIR).is_dir()


def get_drives():
  """
  This function retrieves a list of existing drives on a Windows system.

  Returns:
      list: A list of drive letters (e.g., ['C:', 'D:'])
  """
  if hasattr(os, 'listdrives'):  # For Python 3.12 and above
    return os.listdrives()
  else:
    drives = [f"{d}:\\" for d in os.environ.get('HOMEDRIVE', '').split("\\") if d]
    return drives


def get_nsis_exe():
    """Return NSIS executable"""
    localdir = str(Path(sys.prefix).parent.parent)
    for drive in get_drives():
        for dirname in (
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            drive + r"PortableApps\NSISPortableANSI",
            drive + r"PortableApps\NSISPortable",
            str(Path(localdir) / "NSISPortableANSI"),
            str(Path(localdir) / "NSISPortable"),
        ):
            for subdirname in (".", "App"):
                exe = str(Path(dirname) / subdirname / "NSIS" / "makensis.exe")
                if Path(exe).is_file():
                    return exe
    else:
        raise RuntimeError("NSIS is not installed on this computer.")


def get_7zip_exe():
    """Return 7zip executable"""
    localdir = str(Path(sys.prefix).parent.parent)
    for drive in get_drives():
        for dirname in (
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            str(Path(localdir) / "7-Zip"),
        ):
            for subdirname in (".", "App"):
                exe = str(Path(dirname) / subdirname / "7-Zip" / "7z.exe")
                if Path(exe).is_file():
                    return exe
    else:
        raise RuntimeError("7ZIP is not installed on this computer.")


def replace_in_nsis_file(fname, data):
    """Replace text in line starting with *start*, from this position:
    data is a list of (start, text) tuples"""
    fd = open(fname, "U")
    lines = fd.readlines()
    fd.close()
    for idx, line in enumerate(lines):
        for start, text in data:
            if start not in (
                "Icon",
                "OutFile",
            ) and not start.startswith("!"):
                start = "!define " + start
            if line.startswith(start + " "):
                lines[idx] = line[: len(start) + 1] + f'"{text}"' + "\n"
    fd = open(fname, "w")
    fd.writelines(lines)
    print("iss for ", fname, "is", lines)
    fd.close()


def replace_in_7zip_file(fname, data):
    """Replace text in line starting with *start*, from this position:
    data is a list of (start, text) tuples"""
    fd = open(fname, "U")
    lines = fd.readlines()
    fd.close()
    for idx, line in enumerate(lines):
        for start, text in data:
            if start not in (
                "Icon",
                "OutFile",
            ) and not start.startswith("!"):
                start = "set " + start
            if line.startswith(start + "="):
                lines[idx] = line[: len(start) + 1] + f"{text}" + "\n"
    fd = open(fname, "w")
    fd.writelines(lines)
    print("7-zip for ", fname, "is", lines)
    fd.close()


def build_nsis(srcname, dstname, data):
    """Build NSIS script"""
    NSIS_EXE = get_nsis_exe()  # NSIS Compiler
    portable_dir = str(Path(__file__).resolve().parent / "portable")
    shutil.copy(str(Path(portable_dir) / srcname), dstname)
    data = [
        (
            "!addincludedir",
            str(Path(portable_dir) / "include"),
        )
    ] + list(data)
    replace_in_nsis_file(dstname, data)
    try:
        retcode = subprocess.call(
            f'"{NSIS_EXE}" -V2 "{dstname}"',
            shell=True,
            stdout=sys.stderr,
        )
        if retcode < 0:
            print(
                "Child was terminated by signal",
                -retcode,
                file=sys.stderr,
            )
    except OSError as e:
        print("Execution failed:", e, file=sys.stderr)
    os.remove(dstname)


def build_shimmy_launcher(launcher_name, command, icon_path, mkshim_program='mkshim400.py', workdir=''):
    """Build .exe launcher with mkshim_program and pywin32"""

    # define where is mkshim
    mkshim_program = str(Path(__file__).resolve().parent / mkshim_program)
    python_program = utils.get_python_executable()

    # Create the executable using mkshim.py or mkshim240.py
    mkshim_command = f'{python_program} "{mkshim_program}" -f "{launcher_name}" -c "{command}"'
    if workdir !='': # V03 of shim: we can handle an optional sub-directory
        mkshim_command += f' --subdir "{workdir}"'
    # Embed the icon, if provided
    if Path(icon_path).is_file():
        mkshim_command += f' --i "{icon_path}"'
    print(f"Building .exe launcher with {mkshim_program}:", mkshim_command)
    subprocess.run(mkshim_command, shell=True)


def build_7zip(srcname, dstname, data):
    """7-Zip Setup Script"""
    SEVENZIP_EXE = get_7zip_exe()
    portable_dir = str(Path(__file__).resolve().parent / "portable")
    shutil.copy(str(Path(portable_dir) / srcname), dstname)
    data = [
        ("PORTABLE_DIR", portable_dir),
        ("SEVENZIP_EXE", SEVENZIP_EXE),
    ] + list(data)
    replace_in_7zip_file(dstname, data)
    try:
        # insted of a 7zip command line, we launch a script that does it
        # retcode = subprocess.call(f'"{SEVENZIP_EXE}"  "{dstname}"'),
        retcode = subprocess.call(
            f'"{dstname}"  ',
            shell=True,
            stdout=sys.stderr,
        )
        if retcode < 0:
            print(
                "Child was terminated by signal",
                -retcode,
                file=sys.stderr,
            )
    except OSError as e:
        print("Execution failed:", e, file=sys.stderr)
    # os.remove(dstname)


class WinPythonDistribution(object):
    """WinPython distribution"""

    JULIA_PATH = r"\t\Julia\bin"
    NODEJS_PATH = r"\n"  # r'\t\n'

    def __init__(
        self,
        build_number,
        release_level,
        target,
        wheeldir,
        toolsdirs=None,
        verbose=False,
        simulation=False,
        basedir=None,
        install_options=None,
        flavor="",
        docsdirs=None,
    ):
        assert isinstance(build_number, int)
        assert isinstance(release_level, str)
        self.build_number = build_number
        self.release_level = release_level
        self.target = target
        self.wheeldir = wheeldir
        if toolsdirs is None:
            toolsdirs = []
        self._toolsdirs = toolsdirs
        if docsdirs is None:
            docsdirs = []
        self._docsdirs = docsdirs
        self.verbose = verbose
        self.winpydir = None  # new WinPython BaseDirectory
        self.distribution = None
        self.installed_packages = []
        self.simulation = simulation
        self.basedir = basedir  # added to build from winpython
        self.install_options = install_options
        self.flavor = flavor

        # python_fname = the .zip of the python interpreter PyPy !
        try:  # PyPy
            self.python_fname = self.get_package_fname(
                r"(pypy3|python-)([0-9]|[a-zA-Z]|.)*.zip"
            )
        except:  # normal Python
            self.python_fname = self.get_package_fname(
                r"python-([0-9\.rcba]*)((\.|\-)amd64)?\.(zip|zip)"
            )
        self.python_name = Path(self.python_fname).name[:-4]
        self.distname = "winUNKNOWN"
        self.python_fullversion = "winUNKNOWN"

    @property
    def package_index_wiki(self):
        """Return Package Index page in Wiki format"""
        installed_tools = []

        def get_tool_path_file(relpath):
            if self.simulation:
                for dirname in self.toolsdirs:
                    path = dirname + relpath.replace(r"\t", "")
                    if Path(path).is_file():
                        return path
            else:
                path = self.winpydir + relpath
                if Path(path).is_file():
                    return path

        def get_tool_path_dir(relpath):
            if self.simulation:
                for dirname in self.toolsdirs:
                    path = dirname + relpath.replace(r"\t", "")
                    if Path(path).is_dir():
                        return path
            else:
                path = self.winpydir + relpath
                if Path(path).is_dir():
                    return path

        if get_tool_path_file(r"\t\SciTE.exe"):
            installed_tools += [("SciTE", "3.3.7")]
        juliapath = get_tool_path_dir(self.JULIA_PATH)
        if juliapath is not None:
            juliaver = utils.get_julia_version(juliapath)
            installed_tools += [("Julia", juliaver)]
        nodepath = get_tool_path_dir(self.NODEJS_PATH)
        if nodepath is not None:
            nodever = utils.get_nodejs_version(nodepath)
            installed_tools += [("Nodejs", nodever)]
            npmver = utils.get_npmjs_version(nodepath)
            installed_tools += [("npmjs", npmver)]
        pandocexe = get_tool_path_file(r"\t\pandoc.exe")
        if pandocexe is not None:
            pandocver = utils.get_pandoc_version(str(Path(pandocexe).parent))
            installed_tools += [("Pandoc", pandocver)]
        vscodeexe = get_tool_path_file(r"\t\VSCode\Code.exe")
        if vscodeexe is not None:
            installed_tools += [
                ("VSCode", utils.getFileProperties(vscodeexe)["FileVersion"])
            ]
        tools = []
        for name, ver in installed_tools:
            metadata = utils.get_package_metadata("tools.ini", name)
            url, desc = (
                metadata["url"],
                metadata["description"],
            )
            tools += [f"[{name}]({url}) | {ver} | {desc}"]
        # get all packages installed in the changelog, whatever the method
        self.installed_packages = self.distribution.get_installed_packages(update=True)

        packages = [
            f"[{pack.name}]({pack.url}) | {pack.version} | {pack.description}"
            for pack in sorted(
                self.installed_packages,
                key=lambda p: p.name.lower(),
            )
        ]
        python_desc = "Python programming language with standard library"
        tools_f = "\n".join(tools)
        packages_f = "\n".join(packages)
        return (
            f"""## WinPython {self.winpyver2 + self.flavor} 

The following packages are included in WinPython-{self.winpy_arch}bit v{self.winpyver2+self.flavor} {self.release_level}.

<details>

### Tools

Name | Version | Description
-----|---------|------------
{tools_f}

### Python packages

Name | Version | Description
-----|---------|------------
[Python](http://www.python.org/) | {self.python_fullversion} | {python_desc}
{packages_f}"""
            + "\n\n</details>\n"
        )

    # @property makes self.winpyver becomes a call to self.winpyver()
    @property
    def winpyver(self):
        """Return WinPython version (with flavor and release level!)"""
        return f"{self.python_fullversion}.{self.build_number}{self.flavor}{self.release_level}"

    @property
    def python_dir(self):
        """Return Python dirname (full path) of the target distribution"""
        return str(Path(self.winpydir) / self.python_name)  # python.exe path

    @property
    def winpy_arch(self):
        """Return WinPython architecture"""
        return f"{self.distribution.architecture}"

    @property
    def py_arch(self):
        """Return distribution architecture, in Python distutils format:
        win-amd64 or win32"""
        if self.distribution.architecture == 64:
            return "win-amd64"
        else:
            return "win32"

    @property
    def prepath(self):
        """Return PATH contents to be prepend to the environment variable"""
        path = [
            r"Lib\site-packages\PyQt5",
            "",  # Python root directory
            "DLLs",
            "Scripts",
            r"..\t",
        ]
        path += [r".." + self.JULIA_PATH]

        path += [r".." + self.NODEJS_PATH]

        return path

    @property
    def postpath(self):
        """Return PATH contents to be append to the environment variable"""
        path = []
        return path

    @property
    def toolsdirs(self):
        """Return tools directory list"""
        # formerly was joining prepared tool dir + the one of building env..
        return [] + self._toolsdirs

    @property
    def docsdirs(self):
        """Return docs directory list"""
        if (Path(__file__).resolve().parent / "docs").is_dir():
            return [str(Path(__file__).resolve().parent / "docs")] + self._docsdirs
        else:
            return self._docsdirs

    def get_package_fname(self, pattern):
        """Get package matching pattern in wheeldir"""
        path = self.wheeldir
        for fname in os.listdir(path):
            match = re.match(pattern, fname)
            if match is not None or pattern == fname:
                return str((Path(path) / fname).resolve())
        else:
            raise RuntimeError(f"Could not find required package matching {pattern}")

    def create_batch_script(self, name, contents, do_changes=None):
        """Create batch script %WINPYDIR%/name"""
        scriptdir = str(Path(self.winpydir) / "scripts")
        if not Path(scriptdir).is_dir():
            os.mkdir(scriptdir)
        print("dochanges for %s %", name, do_changes)
        # live patch pypy3
        contents_final = contents
        if do_changes != None:
            for i in do_changes:
                contents_final = contents_final.replace(i[0], i[1])
        fd = open(str(Path(scriptdir) / name), "w")
        fd.write(contents_final)
        fd.close()

    def create_launcher_shimmy(
        self,
        name,
        icon,
        command=None,
        args=None,
        workdir=r"",  # ".\script" to go to sub-directory of the icon
        mkshim_program="mkshim400.py", # to force another one
    ):
        """Create an exe launcher with mkshim.py"""
        assert name.endswith(".exe")
        portable_dir = str(Path(__file__).resolve().parent / "portable")
        icon_fname = str(Path(portable_dir) / "icons" / icon)
        assert Path(icon_fname).is_file()

        # prepare mkshim.py script
        #  $env:WINPYDIRICONS variable give the icons directory
        if command is None:
            if args is not None and ".pyw" in args:
                command = "${WINPYDIR}\pythonw.exe" #not used
            else:
                command = "${WINPYDIR}\python.exe"  #not used
        iconlauncherfullname= str(Path(self.winpydir) / name)
        true_command = command.replace(r"$SYSDIR\cmd.exe","cmd.exe")+ " " + args
        build_shimmy_launcher(iconlauncherfullname, true_command, icon_fname, mkshim_program=mkshim_program, workdir=workdir)
        
    def create_launcher(
        self,
        name,
        icon,
        command=None,
        args=None,
        workdir=r"$EXEDIR\scripts",
        launcher="launcher_basic.nsi",
    ):
        """Create exe launcher with NSIS"""
        assert name.endswith(".exe")
        portable_dir = str(Path(__file__).resolve().parent / "portable")
        icon_fname = str(Path(portable_dir) / "icons" / icon)
        assert Path(icon_fname).is_file()

        # Customizing NSIS script
        if command is None:
            if args is not None and ".pyw" in args:
                command = "${WINPYDIR}\pythonw.exe"
            else:
                command = "${WINPYDIR}\python.exe"
        if args is None:
            args = ""
        if workdir is None:
            workdir = ""
        fname = str(Path(self.winpydir) / (Path(name).stem + ".nsi"))

        data = [
            ("WINPYDIR", f"$EXEDIR\{self.python_name}"),
            ("WINPYVER", self.winpyver),
            ("COMMAND", command),
            ("PARAMETERS", args),
            ("WORKDIR", workdir),
            ("Icon", icon_fname),
            ("OutFile", name),
        ]

        build_nsis(launcher, fname, data)

    def create_python_batch(
        self,
        name,
        script_name,
        workdir=None,
        options=None,
        command=None,
    ):
        """Create batch file to run a Python script"""
        if options is None:
            options = ""
        else:
            options = " " + options
        if command is None:
            if script_name.endswith(".pyw"):
                command = 'start "%WINPYDIR%\pythonw.exe"'
            else:
                command = '"%WINPYDIR%\python.exe"'
        changedir = ""
        if workdir is not None:
            workdir = workdir
            changedir = (
                r"""cd/D %s
"""
                % workdir
            )
        if script_name != "":
            script_name = " " + script_name
        self.create_batch_script(
            name,
            r"""@echo off
call "%~dp0env_for_icons.bat"
"""
            + changedir
            + command
            + script_name
            + options
            + " %*",
        )


    def create_installer_7zip(self, installer_option=""):
        """Create installer with 7-ZIP"""
        self._print("Creating WinPython installer 7-ZIP")
        portable_dir = str(Path(__file__).resolve().parent / "portable")
        fname = str(Path(portable_dir) / "installer_7zip-tmp.bat")
        data = (
            ("DISTDIR", self.winpydir),
            ("ARCH", self.winpy_arch),
            (
                "VERSION",
                f"{self.python_fullversion}.{self.build_number}{self.flavor}",
            ),
            (
                "VERSION_INSTALL",
                f'{self.python_fullversion.replace(".", "")}' + f"{self.build_number}",
            ),
            ("RELEASELEVEL", self.release_level),
        )
        data += (("INSTALLER_OPTION", installer_option),)
        build_7zip("installer_7zip.bat", fname, data)
        self._print_done()

    def _print(self, text):
        """Print action text indicating progress"""
        if self.verbose:
            utils.print_box(text)
        else:
            print(text + "...", end=" ")

    def _print_done(self):
        """Print OK at the end of a process"""
        if not self.verbose:
            print("OK")

    def _extract_python(self):
        """Extracting Python installer, creating distribution object"""
        self._print("Extracting Python .zip version")
        utils.extract_archive(
            self.python_fname,
            targetdir=self.python_dir + r"\..",
        )
        self._print_done()

    def _copy_dev_tools(self):
        """Copy dev tools"""
        self._print(f"Copying tools from {self.toolsdirs} to {self.winpydir}/t")
        toolsdir = str(Path(self.winpydir) / "t")
        os.mkdir(toolsdir)
        for dirname in [
            ok_dir for ok_dir in self.toolsdirs if Path(ok_dir).is_dir()
        ]:  # the ones in the make.py script environment
            for name in os.listdir(dirname):
                path = str(Path(dirname) / name)
                copy = shutil.copytree if Path(path).is_dir() else shutil.copyfile
                if self.verbose:
                    print(path + " --> " + str(Path(toolsdir) / name))
                copy(path, str(Path(toolsdir) / name))
        self._print_done()
        # move node higher
        nodejs_current = str(Path(toolsdir) / "n")
        nodejs_target = self.winpydir + self.NODEJS_PATH
        if nodejs_current != nodejs_target and Path(nodejs_current).is_dir():
            shutil.move(nodejs_current, nodejs_target)

    def _copy_dev_docs(self):
        """Copy dev docs"""
        docsdir = str(Path(self.winpydir) / "notebooks")
        self._print(f"Copying Noteebook docs from {self.docsdirs} to {docsdir}")
        if not Path(docsdir).is_dir():
            os.mkdir(docsdir)
        docsdir = str(Path(self.winpydir) / "notebooks" / "docs")
        if not Path(docsdir).is_dir():
            os.mkdir(docsdir)
        for dirname in self.docsdirs:
            for name in os.listdir(dirname):
                path = str(Path(dirname) / name)
                copy = shutil.copytree if Path(path).is_dir() else shutil.copyfile
                copy(path, str(Path(docsdir) / name))
                if self.verbose:
                    print(path + " --> " + str(Path(docsdir) / name))
        self._print_done()

    def _create_launchers(self):
        """Create launchers"""

        self._print("Creating launchers")

        self.create_launcher_shimmy(
            "WinPython Command Prompt.exe",
            "cmd.ico",
            command=".\\cmd.bat",
            args=r"",
            workdir=r".\scripts"
        )
        
        self.create_launcher_shimmy(
            "WinPython Powershell Prompt.exe",
            "powershell.ico",
            command="Powershell.exe",
            args=r"start-process -WindowStyle Hidden -FilePath ([dollar]ENV:WINPYDIRICONS + '\scripts\cmd_ps.bat')",
        )

        #self.create_launcher_shimmy(
        #    "WinPython Terminal.exe",
        #    "terminal.ico",
        #    command="Powershell.exe",
        #    args=r"start-process -WindowStyle Hidden './scripts/WinPython_Terminal.bat",
        #)

        self.create_launcher_shimmy(
            "WinPython Interpreter.exe",
            "python.ico",
            command=".\\winpython.bat",
            args=r"",
            workdir=r".\scripts"
        )

        self.create_launcher_shimmy(
            "IDLE (Python GUI).exe",
            "python.ico",
            command="Powershell.exe",
            args=r"start-process -WindowStyle Hidden -FilePath ([dollar]ENV:WINPYDIRICONS + '\scripts\winidle.bat')",
        )

        self.create_launcher_shimmy(
            "Spyder.exe",
            "spyder.ico",
            command="Powershell.exe",
            args=r"start-process -WindowStyle Hidden -FilePath ([dollar]ENV:WINPYDIRICONS + '\scripts\winspyder.bat')",
        )

        self.create_launcher_shimmy(
            "Spyder reset.exe",
            "spyder_reset.ico",
            command="Powershell.exe",
            args=r"start-process -WindowStyle Hidden -FilePath ([dollar]ENV:WINPYDIRICONS + '\scripts\spyder_reset.bat')",
            #args=r"start-process -WindowStyle Hidden './scripts/spyder_reset.bat",
        )

        self.create_launcher_shimmy(
            "WinPython Control Panel.exe",
            "winpython.ico",
            command=".\\wpcp.bat",
            args=r"",
            workdir=r".\scripts"
        )

        # Jupyter launchers

        # this one needs a shell to kill fantom processes
        self.create_launcher_shimmy(
            "Jupyter Notebook.exe",
            "jupyter.ico",
            command="winipython_notebook.bat",
            args=r"",
            workdir=r".\scripts"
        )

        self.create_launcher_shimmy(
            "Jupyter Lab.exe",
            "jupyter.ico",
            command="winjupyter_lab.bat",
            args=r"",
            workdir=r".\scripts"
        )

        self.create_launcher_shimmy(
            "VS Code.exe",
            "code.ico",
            command="winvscode.bat",
            args=r"",
            workdir=r".\scripts"
        )

        self._print_done()

    def _create_batch_scripts_initial(self):
        """Create batch scripts"""
        self._print("Creating batch scripts initial")
        conv = lambda path: ";".join(["%WINPYDIR%\\" + pth for pth in path])
        path = conv(self.prepath) + ";%PATH%;" + conv(self.postpath)

        convps = lambda path: ";".join(["$env:WINPYDIR\\" + pth for pth in path])
        pathps = convps(self.prepath) + ";$env:path;" + convps(self.postpath)

        # PyPy3
        shorty = self.distribution.short_exe
        changes = (
            (r"DIR%\python.exe", r"DIR%" + "\\" + shorty),
            (r"DIR%\PYTHON.EXE", r"DIR%" + "\\" + shorty),
        )
        if (Path(self.distribution.target) / r"lib-python\3\idlelib").is_dir():
            changes += ((r"\Lib\idlelib", r"\lib-python\3\idlelib"),)
        self.create_batch_script(
            "env.bat",
            r"""@echo off
set WINPYDIRBASE=%~dp0..
rem set PYTHONUTF8=1 would create issues in "movable" patching
rem get a normalize path
set WINPYDIRBASETMP=%~dp0..
pushd %WINPYDIRBASETMP%
set WINPYDIRBASE=%__CD__%
if "%WINPYDIRBASE:~-1%"=="\" set WINPYDIRBASE=%WINPYDIRBASE:~0,-1%
set WINPYDIRBASETMP=
popd

set WINPYDIR=%WINPYDIRBASE%"""
            + "\\"
            + self.python_name
            + r"""
rem 2019-08-25 pyjulia needs absolutely a variable PYTHON=%WINPYDIR%python.exe
set PYTHON=%WINPYDIR%\python.exe
set PYTHONPATHz=%WINPYDIR%;%WINPYDIR%\Lib;%WINPYDIR%\DLLs
set WINPYVER="""
            + self.winpyver
            + r"""
rem 2023-02-12 try utf-8 on console
rem see https://github.com/pypa/pip/issues/11798#issuecomment-1427069681
set PYTHONIOENCODING=utf-8

set HOME=%WINPYDIRBASE%\settings
rem read https://github.com/winpython/winpython/issues/839
rem set USERPROFILE=%HOME%
rem set WINPYDIRBASE=
set JUPYTER_DATA_DIR=%HOME%
set JUPYTER_CONFIG_DIR=%WINPYDIR%\etc\jupyter
set JUPYTER_CONFIG_PATH=%WINPYDIR%\etc\jupyter
set WINPYARCH=WIN32
if  "%WINPYDIR:~-5%"=="amd64" set WINPYARCH=WIN-AMD64
set FINDDIR=%WINDIR%\system32
echo ";%PATH%;" | %FINDDIR%\find.exe /C /I ";%WINPYDIR%\;" >nul
if %ERRORLEVEL% NEQ 0 (
   set "PATH="""
            + path
            + r""""
   cd .
)         

rem force default pyqt5 kit for Spyder if PyQt5 module is there
if exist "%WINPYDIR%\Lib\site-packages\PyQt5\__init__.py" set QT_API=pyqt5


rem ******************
rem handle PyQt5 if included
rem ******************
set tmp_pyz=%WINPYDIR%\Lib\site-packages\PyQt5
if not exist "%tmp_pyz%" goto pyqt5_conf_exist
set tmp_pyz=%tmp_pyz%\qt.conf
if not exist "%tmp_pyz%" (
    echo [Paths]
    echo Prefix = .
    echo Binaries = .
)>> "%tmp_pyz%"
:pyqt5_conf_exist


rem ******************
rem WinPython.ini part (removed from nsis)
rem ******************
if not exist "%WINPYDIRBASE%\settings" mkdir "%WINPYDIRBASE%\settings" 
if not exist "%WINPYDIRBASE%\settings\AppData" mkdir "%WINPYDIRBASE%\settings\AppData" 
if not exist "%WINPYDIRBASE%\settings\AppData\Roaming" mkdir "%WINPYDIRBASE%\settings\AppData\Roaming" 
set winpython_ini=%WINPYDIRBASE%\settings\winpython.ini
if not exist "%winpython_ini%" (
    echo [debug]
    echo state = disabled
    echo [environment]
    echo ## <?> Uncomment lines to override environment variables
    echo #HOME = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%
    echo #USERPROFILE = %%HOME%%
    echo #JUPYTER_DATA_DIR = %%HOME%%
    echo #JUPYTERLAB_SETTINGS_DIR = %%HOME%%\.jupyter\lab
    echo #JUPYTERLAB_WORKSPACES_DIR = %%HOME%%\.jupyter\lab\workspaces
    echo #WINPYWORKDIR = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%\Notebooks
    echo #R_HOME=%%WINPYDIRBASE%%\t\R
    echo #R_HOMEbin=%%R_HOME%%\bin\x64
    echo #JULIA_HOME=%%WINPYDIRBASE%%\t\Julia\bin\
    echo #JULIA_EXE=julia.exe
    echo #JULIA=%%JULIA_HOME%%%%JULIA_EXE%%
    echo #JULIA_PKGDIR=%%WINPYDIRBASE%%\settings\.julia
    echo #QT_PLUGIN_PATH=%%WINPYDIR%%\Lib\site-packages\pyqt5_tools\Qt\plugins
)>> "%winpython_ini%"

""",
            do_changes=changes,
        )

        self.create_batch_script(
            "WinPython_PS_Prompt.ps1",
            r"""
###############################
### WinPython_PS_Prompt.ps1 ###
###############################
$0 = $myInvocation.MyCommand.Definition
$dp0 = [System.IO.Path]::GetDirectoryName($0)
# $env:PYTHONUTF8 = 1 would create issues in "movable" patching
$env:WINPYDIRBASE = "$dp0\.."
# get a normalize path
# http://stackoverflow.com/questions/1645843/resolve-absolute-path-from-relative-path-and-or-file-name
$env:WINPYDIRBASE = [System.IO.Path]::GetFullPath( $env:WINPYDIRBASE )

# avoid double_init (will only resize screen)
if (-not ($env:WINPYDIR -eq [System.IO.Path]::GetFullPath( $env:WINPYDIRBASE+"""
            + '"\\'
            + self.python_name
            + '"'
            + r""")) ) {


$env:WINPYDIR = $env:WINPYDIRBASE+"""
            + '"'
            + "\\"
            + self.python_name
            + '"'
            + r"""
# 2019-08-25 pyjulia needs absolutely a variable PYTHON=%WINPYDIR%python.exe
$env:PYTHON = "%WINPYDIR%\python.exe"
$env:PYTHONPATHz = "%WINPYDIR%;%WINPYDIR%\Lib;%WINPYDIR%\DLLs"


$env:WINPYVER = '"""
            + self.winpyver
            + r"""'
# rem 2023-02-12 try utf-8 on console
# rem see https://github.com/pypa/pip/issues/11798#issuecomment-1427069681
$env:PYTHONIOENCODING = "utf-8"

$env:HOME = "$env:WINPYDIRBASE\settings"

# rem read https://github.com/winpython/winpython/issues/839
# $env:USERPROFILE = "$env:HOME"

$env:WINPYDIRBASE = ""
$env:JUPYTER_DATA_DIR = "$env:HOME"
$env:WINPYARCH = 'WIN32'
if ($env:WINPYARCH.subString($env:WINPYARCH.length-5, 5) -eq 'amd64')  {
   $env:WINPYARCH = 'WIN-AMD64' } 


if (-not $env:PATH.ToLower().Contains(";"+ $env:WINPYDIR.ToLower()+ ";"))  {
 $env:PATH = """
            + '"'
            + pathps
            + '"'
            + r""" }

#rem force default pyqt5 kit for Spyder if PyQt5 module is there
if (Test-Path "$env:WINPYDIR\Lib\site-packages\PyQt5\__init__.py") { $env:QT_API = "pyqt5" } 


#####################
### handle PyQt5 if included
#####################
$env:tmp_pyz = "$env:WINPYDIR\Lib\site-packages\PyQt5"
if (Test-Path "$env:tmp_pyz") {
   $env:tmp_pyz = "$env:tmp_pyz\qt.conf"
   if (-not (Test-Path "$env:tmp_pyz")) {
      "[Paths]"| Add-Content -Path $env:tmp_pyz
      "Prefix = ."| Add-Content -Path $env:tmp_pyz
      "Binaries = ."| Add-Content -Path $env:tmp_pyz
   }
}


#####################
### WinPython.ini part (removed from nsis)
#####################
if (-not (Test-Path "$env:WINPYDIR\..\settings")) { md -Path "$env:WINPYDIR\..\settings" }
if (-not (Test-Path "$env:WINPYDIR\..\settings\AppData")) { md -Path "$env:WINPYDIR\..\settings\AppData" }
if (-not (Test-Path "$env:WINPYDIR\..\settings\AppData\Roaming")) { md -Path "$env:WINPYDIR\..\settings\AppData\Roaming" }
$env:winpython_ini = "$env:WINPYDIR\..\settings\winpython.ini"
if (-not (Test-Path $env:winpython_ini)) {
    "[debug]" | Add-Content -Path $env:winpython_ini
    "state = disabled" | Add-Content -Path $env:winpython_ini
    "[environment]" | Add-Content -Path $env:winpython_ini
    "## <?> Uncomment lines to override environment variables" | Add-Content -Path $env:winpython_ini
    "#HOME = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%" | Add-Content -Path $env:winpython_ini
    "#USERPROFILE = %%HOME%%" | Add-Content -Path $env:winpython_ini
    "#JUPYTER_DATA_DIR = %%HOME%%" | Add-Content -Path $env:winpython_ini
    "#JUPYTERLAB_SETTINGS_DIR = %%HOME%%\.jupyter\lab" | Add-Content -Path $env:winpython_ini
    "#JUPYTERLAB_WORKSPACES_DIR = %%HOME%%\.jupyter\lab\workspaces" | Add-Content -Path $env:winpython_ini
    "#WINPYWORKDIR = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%\Notebooks" | Add-Content -Path $env:winpython_ini
    "#R_HOME=%%WINPYDIRBASE%%\t\R" | Add-Content -Path $env:winpython_ini
    "#R_HOMEbin=%%R_HOME%%\bin\x64" | Add-Content -Path $env:winpython_ini
    "#JULIA_HOME=%%WINPYDIRBASE%%\t\Julia\bin\" | Add-Content -Path $env:winpython_ini
    "#JULIA_EXE=julia.exe" | Add-Content -Path $env:winpython_ini
    "#JULIA=%%JULIA_HOME%%%%JULIA_EXE%%" | Add-Content -Path $env:winpython_ini
    "#JULIA_PKGDIR=%%WINPYDIRBASE%%\settings\.julia" | Add-Content -Path $env:winpython_ini
    "#QT_PLUGIN_PATH=%%WINPYDIR%%\Lib\site-packages\pyqt5_tools\Qt\plugins" | Add-Content -Path $env:winpython_ini
}


} 
###############################
### Set-WindowSize
###############################
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
# no more needed ?
# Set-WindowSize 195 40 6000 

### Colorize to distinguish
#$host.ui.RawUI.BackgroundColor = "DarkBlue"
$host.ui.RawUI.BackgroundColor = "Black"
$host.ui.RawUI.ForegroundColor = "White"

""",
            do_changes=changes,
        )

        self.create_batch_script(
            "cmd_ps.bat",
            r"""@echo off
rem safe bet 
call "%~dp0env_for_icons.bat"
Powershell.exe -Command "& {Start-Process PowerShell.exe -ArgumentList '-ExecutionPolicy RemoteSigned -noexit -File ""%~dp0WinPython_PS_Prompt.ps1""'}"
exit
""",
            do_changes=changes,
        )

        self.create_batch_script(
            "WinPython_Interpreter_PS.bat",
            r"""@echo off
rem no safe bet (for comparisons)
Powershell.exe -Command "& {Start-Process PowerShell.exe -ArgumentList '-ExecutionPolicy RemoteSigned -noexit -File ""%~dp0WinPython_PS_Prompt.ps1""'}"
exit
""",
            do_changes=changes,
        )

        self.create_batch_script(
            "env_for_icons.bat",
            r"""@echo off
call "%~dp0env.bat"
set WINPYWORKDIR=%WINPYDIRBASE%\Notebooks

rem default is as before: Winpython ..\Notebooks
set WINPYWORKDIR1=%WINPYWORKDIR%

rem if we have a file or directory in %1 parameter, we use that directory 
if not "%~1"=="" (
   if exist "%~1" (
      if exist "%~1\" (
         rem echo it is a directory %~1
	     set WINPYWORKDIR1=%~1
	  ) else (
	  rem echo  it is a file %~1, so we take the directory %~dp1
	  set WINPYWORKDIR1=%~dp1
	  )
   )
) else (
rem if it is launched from another directory than icon origin , we keep it that one echo %__CD__%
if not "%__CD__%"=="%~dp0" if not "%__CD__%scripts\"=="%~dp0" set  WINPYWORKDIR1="%__CD__%"
)
rem remove potential doublequote
set WINPYWORKDIR1=%WINPYWORKDIR1:"=%
rem remove some potential last \
if "%WINPYWORKDIR1:~-1%"=="\" set WINPYWORKDIR1=%WINPYWORKDIR1:~0,-1%

FOR /F "delims=" %%i IN ('cscript /nologo "%~dp0WinpythonIni.vbs"') DO set winpythontoexec=%%i
%winpythontoexec%set winpythontoexec=

rem 2024-08-18: we go initial directory WINPYWORKDIR if no direction and we are on icon directory
rem old NSIS launcher is  by default at icon\scripts level
if  "%__CD__%scripts\"=="%~dp0"  if "%WINPYWORKDIR1%"=="%WINPYDIRBASE%\Notebooks"  cd/D %WINPYWORKDIR1%
rem new shimmy launcher is by default at icon level
if  "%__CD__%"=="%~dp0"  if "%WINPYWORKDIR1%"=="%WINPYDIRBASE%\Notebooks"  cd/D %WINPYWORKDIR1%


rem ******************
rem missing student directory part
rem ******************

if not exist "%WINPYWORKDIR%" mkdir "%WINPYWORKDIR%"

if not exist "%HOME%\.spyder-py%WINPYVER:~0,1%"  mkdir "%HOME%\.spyder-py%WINPYVER:~0,1%"
if not exist "%HOME%\.spyder-py%WINPYVER:~0,1%\workingdir" echo %HOME%\Notebooks>"%HOME%\.spyder-py%WINPYVER:~0,1%\workingdir"

rem ******* make cython use mingwpy part *******
if not exist "%WINPYDIRBASE%\settings\pydistutils.cfg" goto no_cython
if not exist "%HOME%\pydistutils.cfg" xcopy   "%WINPYDIRBASE%\settings\pydistutils.cfg" "%HOME%" 
:no_cython 
""",
            do_changes=changes,
        )

        self.create_batch_script(
            "Noshell.vbs",
            r"""
'from http://superuser.com/questions/140047/how-to-run-a-batch-file-without-launching-a-command-window/390129
If WScript.Arguments.Count >= 1 Then
    ReDim arr(WScript.Arguments.Count-1)
    For i = 0 To WScript.Arguments.Count-1
        Arg = WScript.Arguments(i)
        If InStr(Arg, " ") > 0 or InStr(Arg, "&") > 0 Then Arg = chr(34) & Arg & chr(34)
      arr(i) = Arg
    Next

    RunCmd = Join(arr)
    CreateObject("Wscript.Shell").Run RunCmd, 0 , True
End If
        """,
        )

        self.create_batch_script(
            "WinPythonIni.vbs",
            r"""
Set colArgs = WScript.Arguments
If colArgs.Count> 0 Then 
  Filename=colArgs(0) 
else 
  Filename="..\settings\winpython.ini"
end if
my_lines = Split(GetFile(FileName) & vbNewLine , vbNewLine )
segment = "environment"
txt=""
Set objWSH =  CreateObject("WScript.Shell")
For each l in my_lines
    if left(l, 1)="[" then
        segment=split(mid(l, 2, 999) & "]","]")(0)
    ElseIf left(l, 1) <> "#" and instr(l, "=")>0  then
        data = Split(l & "=", "=")
        if segment="debug" and trim(data(0))="state" then data(0)= "WINPYDEBUG"
        if segment="environment" or segment= "debug" then 
            txt= txt & "set " & rtrim(data(0)) & "=" & translate(ltrim(data(1))) & "&& "
            objWSH.Environment("PROCESS").Item(rtrim(data(0))) = translate(ltrim(data(1)))
        end if
        if segment="debug" and trim(data(0))="state" then txt= txt & "set WINPYDEBUG=" & trim(data(1)) & "&&"
    End If
Next
wscript.echo txt


Function GetFile(ByVal FileName)
    Set FS = CreateObject("Scripting.FileSystemObject")
    If Left(FileName,3)="..\" then FileName = FS.GetParentFolderName(FS.GetParentFolderName(Wscript.ScriptFullName)) & mid(FileName,3,9999)
    If Left(FileName,3)=".\" then FileName = FS.GetParentFolderName(FS.GetParentFolderName(Wscript.ScriptFullName)) & mid(FileName,3,9999)
    On Error Resume Next
    GetFile = FS.OpenTextFile(FileName).ReadAll
End Function

Function translate(line)
    set dos = objWSH.Environment("PROCESS")
    tab = Split(line & "%", "%")
    for i = 1 to Ubound(tab) step 2   
       if tab(i)& "" <> "" and dos.Item(tab(i)) & "" <> "" then tab(i) =  dos.Item(tab(i))
    next
    translate =  Join(tab, "") 
end function
        """,
        )

    def _create_batch_scripts(self):
        """Create batch scripts"""
        self._print("Creating batch scripts")

        # PyPy3
        shorty = self.distribution.short_exe
        changes = (
            (r"DIR%\python.exe", r"DIR%" + "\\" + shorty),
            (r"DIR%\PYTHON.EXE", r"DIR%" + "\\" + shorty),
        )
        if (Path(self.distribution.target) / r"lib-python\3\idlelib").is_dir():
            changes += ((r"\Lib\idlelib", r"\lib-python\3\idlelib"),)
        self.create_batch_script(
            "readme.txt",
            r"""These batch files are required to run WinPython icons.

These files should help the user writing his/her own
specific batch file to call Python scripts inside WinPython.
The environment variables are set-up in 'env_.bat' and 'env_for_icons.bat'.""",
        )

        self.create_batch_script(
            "make_winpython_movable.bat",
            r"""@echo off
call "%~dp0env.bat"
echo patch pip and current launchers for move

"%WINPYDIR%\python.exe" -c "from winpython import wppm;dist=wppm.Distribution(r'%WINPYDIR%');dist.patch_standard_packages('pip', to_movable=True)"
pause
        """,
            do_changes=changes,
        )

        self.create_batch_script(
            "make_winpython_fix.bat",
            r"""@echo off
call "%~dp0env.bat"
echo patch pip and current launchers for non-move

"%WINPYDIR%\python.exe" -c "from winpython import wppm;dist=wppm.Distribution(r'%WINPYDIR%');dist.patch_standard_packages('pip', to_movable=False)"
pause
        """,
            do_changes=changes,
        )

        self.create_batch_script(
            "make_working_directory_be_not_winpython.bat",
            r"""@echo off
set winpython_ini=%~dp0..\\settings\winpython.ini
(
    echo [debug]
    echo state = disabled
    echo [environment]
    echo ## <?> Uncomment lines to override environment variables
    echo HOME = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%\settings
    echo USERPROFILE = %%HOME%%
    echo JUPYTER_DATA_DIR = %%HOME%%
    echo #JUPYTERLAB_SETTINGS_DIR = %%HOME%%\.jupyter\lab
    echo #JUPYTERLAB_WORKSPACES_DIR = %%HOME%%\.jupyter\lab\workspaces
    echo WINPYWORKDIR = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%\Notebooks
) > "%winpython_ini%"
    call "%~dp0env_for_icons.bat"
    mkdir %HOMEDRIVE%%HOMEPATH%\Documents\WinPython%WINPYVER%\settings
    mkdir %HOMEDRIVE%%HOMEPATH%\Documents\WinPython%WINPYVER%\settings\AppData
    mkdir %HOMEDRIVE%%HOMEPATH%\Documents\WinPython%WINPYVER%\settings\AppData\Roaming
""",
        )

        self.create_batch_script(
            "make_working_directory_be_winpython.bat",
            r"""@echo off
set winpython_ini=%~dp0..\\settings\winpython.ini
(
    echo [debug]
    echo state = disabled
    echo [environment]
    echo ## <?> Uncomment lines to override environment variables
    echo #HOME = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%\settings
    echo #USERPROFILE = %%HOME%%
    echo #JUPYTER_DATA_DIR = %%HOME%%
    echo #JUPYTERLAB_SETTINGS_DIR = %%HOME%%\.jupyter\lab
    echo #JUPYTERLAB_WORKSPACES_DIR = %%HOME%%\.jupyter\lab\workspaces
    echo #WINPYWORKDIR = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%\Notebooks
) > "%winpython_ini%"
""",
        )

        self.create_batch_script(
            "make_working_directory_and_userprofile_be_winpython.bat",
            r"""@echo off
set winpython_ini=%~dp0..\\settings\winpython.ini
(
    echo [debug]
    echo state = disabled
    echo [environment]
    echo ## <?> Uncomment lines to override environment variables
    echo #HOME = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%\settings
    echo USERPROFILE = %%HOME%%
    echo #JUPYTER_DATA_DIR = %%HOME%%
    echo #JUPYTERLAB_SETTINGS_DIR = %%HOME%%\.jupyter\lab
    echo #JUPYTERLAB_WORKSPACES_DIR = %%HOME%%\.jupyter\lab\workspaces
    echo #WINPYWORKDIR = %%HOMEDRIVE%%%%HOMEPATH%%\Documents\WinPython%%WINPYVER%%\Notebooks
) > "%winpython_ini%"
""",
        )

        self.create_batch_script(
            "cmd.bat",
            r"""@echo off
call "%~dp0env_for_icons.bat"
if not "%WINPYWORKDIR%"=="%WINPYWORKDIR1%" cd %WINPYWORKDIR1%
cmd.exe /k""",
        )

        self.create_batch_script(
            "WinPython_Terminal.bat",
            r"""@echo off
rem call "%~dp0env_for_icons.bat"
rem if not "%WINPYWORKDIR%"=="%WINPYWORKDIR1%" cd %WINPYWORKDIR1%
rem "%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\wt.exe"
Powershell.exe -Command "& {Start-Process PowerShell.exe -ArgumentList '-ExecutionPolicy RemoteSigned -noexit -File ""%~dp0WinPython_PS_Prompt.ps1""'}"
exit
""",
        )

        self.create_batch_script(
            "python.bat",
            r"""@echo off
call "%~dp0env_for_icons.bat"
rem backward compatibility for  python command-line users
if not "%WINPYWORKDIR%"=="%WINPYWORKDIR1%" cd %WINPYWORKDIR1%
"%WINPYDIR%\python.exe"  %*
""",
            do_changes=changes,
        )

        self.create_batch_script(
            "winpython.bat",
            r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR1%"
rem backward compatibility for non-ptpython users
if exist "%WINPYDIR%\scripts\ptpython.exe" (
    "%WINPYDIR%\scripts\ptpython.exe" %*
) else (
    "%WINPYDIR%\python.exe"  %*
)
""",
            do_changes=changes,
        )

        self.create_batch_script(
            "winidle.bat",
            r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR1%"
"%WINPYDIR%\python.exe" "%WINPYDIR%\Lib\idlelib\idle.pyw" %*
""",
            do_changes=changes,
        )

        self.create_batch_script(
            "winspyder.bat",
            r"""@echo off
call "%~dp0env_for_icons.bat"
rem cd/D "%WINPYWORKDIR%"
if exist "%WINPYDIR%\scripts\spyder3.exe" (
   "%WINPYDIR%\scripts\spyder3.exe" %* -w "%WINPYWORKDIR1%"
) else (
   "%WINPYDIR%\scripts\spyder.exe" %* -w "%WINPYWORKDIR1%"
)  
""",
        )

        self.create_batch_script(
            "spyder_reset.bat",
            r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR1%"
if exist "%WINPYDIR%\scripts\spyder3.exe" (
    "%WINPYDIR%\scripts\spyder3.exe" --reset %*
) else (
    "%WINPYDIR%\scripts\spyder.exe" --reset %*
)
""",
        )

        self.create_batch_script(
            "winipython_notebook.bat",
            r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR1%"
"%WINPYDIR%\scripts\jupyter-notebook.exe" %*
""",
        )

        self.create_batch_script(
            "winjupyter_lab.bat",
            r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR1%"
"%WINPYDIR%\scripts\jupyter-lab.exe" %*
""",
        )

        self.create_batch_script(
            "winqtconsole.bat",
            r"""@echo off
call "%~dp0env_for_icons.bat"
cd/D "%WINPYWORKDIR1%"
"%WINPYDIR%\scripts\jupyter-qtconsole.exe" %*
""",
        )

        self.create_python_batch(
            "register_python.bat",
            r'"%WINPYDIR%\Lib\site-packages\winpython\register_python.py"',
            workdir=r'"%WINPYDIR%\Scripts"',
        )

        self.create_python_batch(
            "unregister_python.bat",
            r'"%WINPYDIR%\Lib\site-packages\winpython\unregister_python.py"',
            workdir=r'"%WINPYDIR%\Scripts"',
        )

        self.create_batch_script(
            "register_python_for_all.bat",
            r"""@echo off
call "%~dp0env.bat"
call "%~dp0register_python.bat" --all""",
        )

        self.create_batch_script(
            "unregister_python_for_all.bat",
            r"""@echo off
call "%~dp0env.bat"
call "%~dp0unregister_python.bat" --all""",
        )

        self.create_batch_script(
            "wpcp.bat",
            r"""@echo off
call "%~dp0env_for_icons.bat"
rem cd/D "%WINPYWORKDIR1%"
rem "%WINPYDIR%\python.exe" -m winpython.controlpanel %*
if not "%WINPYWORKDIR%"=="%WINPYWORKDIR1%" cd/d %WINPYWORKDIR1%
cmd.exe /k "echo wppm & wppm"
""",
            do_changes=changes,
        )

        self.create_batch_script(
            "upgrade_pip.bat",
            r"""@echo off
call "%~dp0env.bat"
echo this will upgrade pip with latest version, then patch it for WinPython portability ok ?
pause
"%WINPYDIR%\python.exe" -m pip install --upgrade pip
"%WINPYDIR%\python.exe" -c "from winpython import wppm;dist=wppm.Distribution(r'%WINPYDIR%');dist.patch_standard_packages('pip', to_movable=True)
pause
""",
            do_changes=changes,
        )

        
        self.create_batch_script(  # virtual environment mimicking
            "activate.bat",
            r"""@echo off
call "%~dp0env.bat"  %*
""",
        )

        self.create_batch_script(
            "winvscode.bat",
            r"""@echo off
rem launcher for VScode
call "%~dp0env_for_icons.bat"
rem cd/D "%WINPYWORKDIR1%"
if exist "%WINPYDIR%\..\t\vscode\code.exe" (
    "%WINPYDIR%\..\t\vscode\code.exe" %*
) else (
if exist "%LOCALAPPDATA%\Programs\Microsoft VS Code\code.exe" (
    "%LOCALAPPDATA%\Programs\Microsoft VS Code\code.exe"  %*
) else (
    "code.exe" %*
))

""",
        )
        


    def _run_complement_batch_scripts(self, this_batch="run_complement.bat"):
        """tools\..\run_complement.bat for final complements"""
        print(f"now {this_batch} in tooldirs\..")
        for post_complement in list(
            set([str(Path(s).parent) for s in self._toolsdirs])
        ):
            filepath = str(Path(post_complement) / this_batch)
            if Path(filepath).is_file():
                print(f'launch "{filepath}"  for  "{self.winpydir}"')
                self._print(f'launch "{filepath}"  for  "{self.winpydir}" !')
                try:
                    retcode = subprocess.call(
                        f'"{filepath}"   "{self.winpydir}"',
                        shell=True,
                        stdout=sys.stderr,
                    )
                    if retcode < 0:
                        print(
                            "Child was terminated by signal",
                            -retcode,
                            file=sys.stderr,
                        )
                        self._print(
                            "Child was terminated by signal ! ",
                            -retcode,
                            file=sys.stderr,
                        )
                except OSError as e:
                    print(
                        "Execution failed:",
                        e,
                        file=sys.stderr,
                    )
                    self._print(
                        "Execution failed !:",
                        e,
                        file=sys.stderr,
                    )
        self._print_done()

    def make(
        self,
        remove_existing=True,
        requirements=None,
        my_winpydir=None,
    ):  # , find_links=None):
        """Make WinPython distribution in target directory from the installers
        located in wheeldir

        remove_existing=True: (default) install all from scratch
        remove_existing=False: only for test purpose (launchers/scripts)
        requirements=file(s) of requirements (separated by space if several)"""
        if self.simulation:
            print(
                "WARNING: this is just a simulation!",
                file=sys.stderr,
            )
        print(
            self.python_fname,
            self.python_name,
            self.distname,
            self.python_fullversion,  # PyPy to delete or move
        )
        if my_winpydir is None:
            self.winpydir = str(Path(self.target) / self.distname)  # PyPy to delete
        else:
            self.winpydir = str(
                Path(self.target) / my_winpydir
            )  # Create/re-create the WinPython base directory
        self._print(f"Creating WinPython {my_winpydir} base directory")
        if Path(self.winpydir).is_dir() and remove_existing and not self.simulation:
            shutil.rmtree(self.winpydir, onexc=utils.onerror)
        if not Path(self.winpydir).is_dir():
            os.mkdir(self.winpydir)
        if remove_existing and not self.simulation:
            # Create settings directory
            # (only necessary if user is starting an application with a batch
            #  scripts before using an executable launcher, because the latter
            #  is creating the directory automatically)
            os.mkdir(str(Path(self.winpydir) / "settings"))
            os.mkdir(str(Path(self.winpydir) / "settings" / "AppData"))
            os.mkdir(str(Path(self.winpydir) / "settings" / "AppData" / "Roaming"))
        self._print_done()

        if remove_existing and not self.simulation:
            self._extract_python()  # unzip Python interpreter
        self.distribution = wppm.Distribution(
            self.python_dir,
            verbose=self.verbose,
            indent=True,
        )

        # PyPy: get Fullversion from the executable
        self.python_fullversion = utils.get_python_long_version(
            self.distribution.target
        )

        # PyPY: Assert that WinPython version and real python version do match
        self._print(
            f"Python version{self.python_fullversion.replace('.','')}"
            + f"\nDistro Name {self.distribution.target}"
        )
        assert self.python_fullversion.replace(".", "") in self.distribution.target, (
            "Distro Directory doesn't match the Python version it ships"
            + f"\nPython version: {self.python_fullversion.replace('.','')}"
            + f"\nDistro Name: {self.distribution.target}"
        )

        if remove_existing:
            if not self.simulation:
                # self._add_msvc_files()  # replaced per msvc_runtime package
                self._create_batch_scripts_initial()
                self._create_batch_scripts()
                # always create all launchers (as long as it is NSIS-based)
                self._create_launchers()
            # pre-patch current pip (until default python has pip 8.0.3)

            # PyPY must ensure pip
            # "pypy3.exe -m ensurepip"
            utils.python_execmodule("ensurepip", self.distribution.target)

            self.distribution.patch_standard_packages("pip")
            # not forced update of pip (FIRST) and setuptools here
            for req in ("pip", "setuptools", "wheel", "winpython"):
                actions = ["install", "--upgrade", "--pre", req]
                if self.install_options is not None:
                    actions += self.install_options
                print(f"piping {' '.join(actions)}")
                self._print(f"piping {' '.join(actions)}")
                self.distribution.do_pip_action(actions)
                self.distribution.patch_standard_packages(req)
            # no more directory base package install: use requirements.txt
            # 2019-05-03 removed self._install_all_other_packages()
            print("self.simulation zz", self.simulation)
            if not self.simulation:
                self._copy_dev_tools()
                self._copy_dev_docs()
        if not self.simulation:

            if requirements:
                if not list(requirements) == requirements:
                    requirements = requirements.split()
                for req in requirements:
                    actions = ["install", "-r", req]
                    if self.install_options is not None:
                        actions += self.install_options
                    print(f"piping {' '.join(actions)}")
                    self._print(f"piping {' '.join(actions)}")
                    self.distribution.do_pip_action(actions)
                    # actions=["install","-r", req, "--no-index",
                    #         "--trusted-host=None"]+ links,
                    #         install_options=None)
            self._run_complement_batch_scripts()
            self.distribution.patch_standard_packages()
        if remove_existing and not self.simulation:
            self._print("Cleaning up distribution")
            self.distribution.clean_up()
            self._print_done()
        # Writing package index
        self._print("Writing package index")
        # winpyver2 = need the version without build part
        # but with self.distribution.architecture
        self.winpyver2 = f"{self.python_fullversion}.{self.build_number}"
        fname = str(
            Path(self.winpydir).parent
            / (
                f"WinPython{self.flavor}-"
                + f"{self.distribution.architecture}bit-"
                + f"{self.winpyver2}.md"
            )
        )
        open(fname, "w", encoding='utf-8').write(self.package_index_wiki)
        # Copy to winpython/changelogs
        shutil.copyfile(
            fname,
            str(Path(CHANGELOGS_DIR) / Path(fname).name),
        )
        self._print_done()

        # Writing changelog
        self._print("Writing changelog")
        diff.write_changelog(
            self.winpyver2,
            basedir=self.basedir,
            flavor=self.flavor,
            release_level=self.release_level,
            architecture=self.distribution.architecture,
        )
        self._print_done()


def rebuild_winpython(basedir, targetdir, architecture=64, verbose=False):
    """Rebuild winpython package from source"""
    basedir = basedir
    packdir = targetdir
    for name in os.listdir(packdir):
        if name.startswith("winpython-") and name.endswith((".exe", ".whl", ".gz")):
            os.remove(str(Path(packdir) / name))
    #  utils.build_wininst is replaced per flit 2023-02-27
    utils.buildflit_wininst(
        str(Path(__file__).resolve().parent),
        copy_to=packdir,
        verbose=verbose,
    )


def transform_in_list(list_in, list_type=None):
    """Transform a 'String or List' in List"""
    if list_in is None:
        list_in = ""
    if not list_in == list(list_in):
        list_in = list_in.split()
    if list_type:
        print(list_type, list_in)
    return list_in


def make_all(
    build_number,
    release_level,
    pyver,
    architecture,
    basedir,
    verbose=False,
    remove_existing=True,
    create_installer=True,
    simulation=False,
    install_options=["--no-index"],
    flavor="",
    requirements=None,
    find_links=None,
    source_dirs=None,
    toolsdirs=None,
    docsdirs=None,
    python_target_release=None,  # 37101 for 3.7.10
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
    if not Path(builddir).is_dir():
        os.mkdir(builddir)
    # use source_dirs as the directory to re-build Winpython wheel
    wheeldir = source_dirs

    # Rebuild Winpython in this wheel dir
    rebuild_winpython(
        basedir=basedir,
        targetdir=wheeldir,
        architecture=architecture,
    )

    # Optional pre-defined toolsdirs
    toolsdirs = transform_in_list(toolsdirs, "toolsdirs=")

    # Optional pre-defined toolsdirs
    print("docsdirs input", docsdirs)
    docsdirs = transform_in_list(docsdirs, "docsdirs=")
    print("docsdirs output", docsdirs)

    # install_options = ['--no-index', '--pre', f'--find-links={wheeldir)']
    install_options = transform_in_list(install_options, "install_options")

    find_links = transform_in_list(find_links, "find_links")

    find_list = [f"--find-links={l}" for l in find_links + [wheeldir]]
    dist = WinPythonDistribution(
        build_number,
        release_level,
        builddir,
        wheeldir,
        toolsdirs,
        verbose=verbose,
        simulation=simulation,
        basedir=basedir,
        install_options=install_options + find_list,
        flavor=flavor,
        docsdirs=docsdirs,
    )
    # define a pre-defined winpydir, instead of having to guess

    # extract the python subversion to get WPy64-3671b1
    my_x = "".join(dist.python_fname.replace(".amd64", "").split(".")[-2:-1])
    while not my_x.isdigit() and len(my_x) > 0:
        my_x = my_x[:-1]
    # simplify for PyPy
    if not python_target_release == None:
        my_winpydir = (
            "WPy"
            + f"{architecture}"
            + "-"
            + python_target_release
            + ""
            + f"{build_number}"
        ) + release_level
    # + flavor
    else:
        my_winpydir = (
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

    dist.make(
        remove_existing=remove_existing,
        requirements=requirements,
        my_winpydir=my_winpydir,
    )
    #          ,find_links=osp.join(basedir, 'packages.srcreq'))
    if str(create_installer).lower() != "false" and not simulation:
        if "7zip" in str(create_installer).lower():
            dist.create_installer_7zip(".exe")  # 7-zip (no licence splash screen)
        if ".7z" in str(create_installer).lower():
            dist.create_installer_7zip(".7z")  # 7-zip (no licence splash screen)
        if ".zip" in str(create_installer).lower():
            dist.create_installer_7zip(".zip")  # 7-zip (no licence splash screen)
    return dist


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
