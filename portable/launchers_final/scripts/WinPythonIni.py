
# Prepares a dynamic list of variables settings from a .ini file
import os
import subprocess
from pathlib import Path

winpython_inidefault=r'''
[debug]
state = disabled
[inactive_environment_per_user]
## <?> changing this segment to [active_environment_per_user] makes this segment of lines active or not
HOME = %HOMEDRIVE%%HOMEPATH%\Documents\WinPython%WINPYVER%\settings
USERPROFILE = %HOME%
JUPYTER_DATA_DIR = %HOME%
WINPYWORKDIR = %HOMEDRIVE%%HOMEPATH%\Documents\WinPython%WINPYVER%\Notebooks
[inactive_environment_common]
USERPROFILE = %HOME%
[environment]
## <?> Uncomment lines to override environment variables
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
        if file_name[-3:] == 'ini':
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
    args = sys.argv[1:]
    file_name = args[0] if args else "..\\settings\\winpython.ini"

    my_lines = get_file(file_name).splitlines()
    segment = "environment"
    txt = ""
    env = os.environ.copy() # later_version: env = os.environ

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

    for l in my_lines:
        if l.startswith("["):
            segment = l[1:].split("]")[0]
        elif not l.startswith("#") and "=" in l:
            data = l.split("=", 1)
            if segment == "debug" and data[0].strip() == "state":
                data[0] = "WINPYDEBUG"
            if segment in ["environment", "debug", "active_environment_per_user", "active_environment_common"]:
                txt += f"set {data[0].strip()}={translate(data[1].strip(), env)}&& "
                env[data[0].strip()] = translate(data[1].strip(), env)
            if segment == "debug" and data[0].strip() == "state":
                txt += f"set WINPYDEBUG={data[1].strip()}&&"

    print(txt)

    # set potential directory
    for i in ('HOME', 'WINPYWORKDIR'):
        if i in env:
            os.makedirs(Path(env[i]), exist_ok=True)
    # later_version:
    # p = subprocess.Popen(["start", "cmd", "/k", "set"], shell = True)
    # p.wait()    # I can wait until finished (although it too finishes after start finishes)

if __name__ == "__main__":
    main()
        