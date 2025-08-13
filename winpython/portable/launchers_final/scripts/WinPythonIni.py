
# Prepares a dynamic list of variables settings from a .ini file
import os
import sys
import subprocess
from pathlib import Path

winpython_inidefault = r'''
[debug]
state = disabled
[env.bat]
#PYTHONPATHz = %WINPYDIR%;%WINPYDIR%\Lib;%WINPYDIR%\DLLs
#see https://github.com/winpython/winpython/issues/839
#USERPROFILE = %HOME%
#PYTHONUTF8=1 creates issues in "movable" patching
SPYDER_CONFDIR = %HOME%\settings\.spyder-py3
JUPYTER_DATA_DIR = %HOME%
JUPYTER_CONFIG_DIR = %WINPYDIR%\etc\jupyter
JUPYTER_CONFIG_PATH = %WINPYDIR%\etc\jupyter
[inactive_environment_per_user]
## <?> changing this segment to [active_environment_per_user] makes this segment of lines active or not
HOME = %HOMEDRIVE%%HOMEPATH%\Documents\WinPython%WINPYVER%\settings
USERPROFILE = %HOME%
JUPYTER_DATA_DIR = %HOME%
WINPYWORKDIR = %HOMEDRIVE%%HOMEPATH%\Documents\WinPython%WINPYVER%\Notebooks
[inactive_environment_common]
## <?> changing this segment to [inactive_environment_common] makes this segment of lines active
USERPROFILE = %HOME%
[environment]
## <?> Uncomment lines to override environment variables
#SPYDER_CONFDIR = %HOME%\settings\.spyder-py3
#JUPYTERLAB_SETTINGS_DIR = %HOME%\.jupyter\lab
#JUPYTERLAB_WORKSPACES_DIR = %HOME%\.jupyter\lab\workspaces
#R_HOME=%WINPYDIRBASE%\t\R
#R_HOMEbin=%R_HOME%\bin\x64
#JULIA_HOME=%WINPYDIRBASE%\t\Julia\bin\
#JULIA_EXE=julia.exe
#JULIA=%JULIA_HOME%%JULIA_EXE%
#JULIA_PKGDIR=%WINPYDIRBASE%\settings\.julia
#QT_PLUGIN_PATH=%WINPYDIR%\Lib\site-packages\pyqt5_tools\Qt\plugins
'''

def get_file(file_name):
    if file_name.startswith("..\\"):
        file_name = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_name[3:])
    elif file_name.startswith(".\\"):
        file_name = os.path.join(os.path.dirname(__file__), file_name[2:])
    try:
        with open(file_name, 'r') as file:
           return file.read()
    except FileNotFoundError:
        if file_name.endswith("winpython.ini"):
            os.makedirs(Path(file_name).parent, exist_ok=True)
            with open(file_name, 'w') as file:
                file.write(winpython_inidefault)
            return winpython_inidefault

def translate(line, env):
    parts = line.split('%')
    for i in range(1, len(parts), 2):
        if parts[i] in env:
            parts[i] = env[parts[i]]
    return ''.join(parts)

def main():
    import sys
    args = sys.argv[:]
    env = os.environ.copy() # later_version: env = os.environ
    my_lines = []
    # before env.ini (we replay just in case)
    env['WINPYthon_subdirectory_name'] = WINPYthon_subdirectory_name = env.get('WINPYthon_subdirectory_name', 'python')
    my_lines += [f"WINPYthon_subdirectory_name={WINPYthon_subdirectory_name}"]
    env['WINPYthon_exe'] = WINPYthon_exe =  env.get('WINPYthon_exe', 'python.exe')
    my_lines += [f"WINPYthon_exe={WINPYthon_exe}"]

    # bypassing env.bat for env.ini
    if (env_ini_file := Path(__file__).parent /  "env.ini").is_file():
        my_lines = get_file(str(env_ini_file)).splitlines() + my_lines
        for l in my_lines:
            if "=" in l:
                var , value = l.split("=")
                env[var.strip()] = value.strip()

    # env.bat things transfered to WinpythonIni.py
    env['WINPYDIRBASE'] = WINPYDIRBASE = Path(env.get('WINPYDIRBASE', Path(__file__).parent.parent)).resolve()
    my_lines += [f"WINPYDIRBASE={WINPYDIRBASE}"]
    env["WINPYDIR"] = WINPYDIR = Path(env.get('WINPYDIR',WINPYDIRBASE / 'WINPYthon_subdirectory_name'))
    my_lines += [f"WINPYDIR={WINPYDIR}"]
    env["PYTHON"] = PYTHON = Path(env.get('PYTHON', WINPYDIR / WINPYthon_exe))
    my_lines += [f"PYTHON={PYTHON}"]
    env["HOME"] = HOME = env.get("HOME",  WINPYDIRBASE / 'settings'")
    my_lines += [f"HOME={HOME}"]

    if (WINPYDIR / "Lib" / "site-package" / "PyQt5" / "__init__.py").is_file():
         my_lines += ["QT_API=pyqt5"]
    if (PYPANDOC_PANDOC := WINPYDIRBASE / "t" / "pandoc.exe").is_file():
         my_lines += [f"PYPANDOC_PANDOC={PYPANDOC_PANDOC}"]

    path_me = f"{WINPYDIR};{WINPYDIR / 'Scripts'};{WINPYDIR / ".." /'t'};{WINPYDIR / ".." / 'n'}"
    if not path_me in env.get('PATH', ''):
        my_lines += [f"PATH={path_me}{env.get('PATH', '')}"]

    # theorical option: a "winpython.ini" file as an initial parameter
    if len(args) >=2 and args[1].endswith("winpython.ini"):
        file_name = args[1] 
        args = args[1:]
    else:
        file_name = "..\\settings\\winpython.ini"

    # env_for_icons.bat default directory logic transfered to WinpythonIni.py

    env['WINPYWORKDIR'] = WINPYWORKDIR = WINPYDIRBASE / "Notebooks"
    my_lines += [f"WINPYWORKDIR={WINPYWORKDIR}"]

    # supposing winpython.ini is given the %* parameters to apply in python the [tricky] change of directory logic
    # if a file or directory is in %1 parameter, and current directory is not the icon nor scripts, we use that directory to define WINPYWORKDIR1
    WINPYWORKDIR1 = WINPYWORKDIR
    if len(args) >=2:
        if Path(args[1:1]).isfile():
            WINPYWORKDIR1 = Path(args[1:1]).parent
        if Path(args[1:1]).isdir():
            WINPYWORKDIR1 = Path(args[1:1])
        
    # if WinPython launched from another directory than icon origin, it's not a Drag&Drop so keep current directory
    CD_directory = Path(os.getcwd())
    dp0_directory = Path(__file__).parent
    if  CD_directory != dp0_directory and  CD_directory / "scripts" != dp0_directory:
        WINPYWORKDIR1 = CD_directory
    env['WINPYWORKDIR'] = WINPYWORKDIR1
    my_lines += [f"WINPYWORKDIR1={WINPYWORKDIR1}"]

    # classic WinpythonIni.py actions: digesting winpython.ini file
    my_lines += get_file(file_name).splitlines()

    segment = "environment"
    txt = ""

    # default directories (from .bat)
    os.makedirs(Path(env['WINPYDIRBASE']) / 'settings' / 'Appdata' / 'Roaming', exist_ok=True)

    # default qt.conf for Qt directories
    qt_conf='''echo [Paths]
    echo Prefix = .
    echo Binaries = .
    '''

    pathlist = [Path(env['WINPYDIR']) / 'Lib' / 'site-packages' / i for i in ('PyQt5', 'PyQt6', 'Pyside6')]
    for p in pathlist:
        if p.is_dir():
            if not (p / 'qt.conf').is_file():
                with open(p / 'qt.conf', 'w') as file:
                    file.write(qt_conf)
    
    # setting both the variable if downard, and the associated list if upward
    for l in my_lines:
        if l.startswith("["):
            segment = l[1:].split("]")[0]
        elif not l.startswith("#") and "=" in l:
            data = l.split("=", 1)
            if segment == "debug" and data[0].strip() == "state":
                data[0] = "WINPYDEBUG"
            if segment in ["env.bat", "environment", "debug", "active_environment_per_user", "active_environment_common"]:
                txt += f"{data[0].strip()}={translate(data[1].strip(), env)}"
                env[data[0].strip()] = translate(data[1].strip(), env)
            if segment == "debug" and data[0].strip() == "state":
                txt += f"WINPYDEBUG={data[1].strip()}"

    # create potential directory need
    for i in ('HOME', 'WINPYWORKDIR', 'WINPYWORKDIR1'):
        if i in env:
            os.makedirs(Path(env[i]), exist_ok=True)

    # Including env_for_icons.bat stuff after WinpythonIni.py actions
    spyder_workdir_specfile = Path(env['HOME']) / f".spyder-py{sys.version_info[0]}" / "workingdir"
    if not spyder_workdir_specfile.exists(): 
        os.makedirs(spyder_workdir_specfile.parent, exist_ok=True)
        with open(spyder_workdir_specfile, 'w') as file:
            file.write(f"{Path(env['HOME']) / "Notebooks"}")

    # output to push change upward
    for l in self.output_lines:
        print(rf"set {l}" , end="&&")

    # later_version:
    # p = subprocess.Popen(["start", "cmd", "/k", "set"], shell = True)
    # p.wait()    # I can wait until finished (although it too finishes after start finishes)

if __name__ == "__main__":
    main()
        