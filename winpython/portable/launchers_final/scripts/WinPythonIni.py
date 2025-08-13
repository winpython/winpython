import os
import sys
from pathlib import Path

winpython_inidefault = r'''
[debug]
state = disabled
[env.bat]
#see https://github.com/winpython/winpython/issues/839
#USERPROFILE = %HOME%
SPYDER_CONFDIR = %HOME%\settings\.spyder-py3
JUPYTER_DATA_DIR = %HOME%
JUPYTER_CONFIG_DIR = %WINPYDIR%\etc\jupyter
JUPYTER_CONFIG_PATH = %WINPYDIR%\etc\jupyter
[inactive_environment_per_user]
## <?> changing this segment to [active_environment_per_user] makes this segment of lines active
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
#JULIA_HOME=%WINPYDIRBASE%\t\Julia\bin\
#JULIA_EXE=julia.exe
#JULIA=%JULIA_HOME%%JULIA_EXE%
#JULIA_PKGDIR=%WINPYDIRBASE%\settings\.julia
#QT_PLUGIN_PATH=%WINPYDIR%\Lib\site-packages\pyqt5_tools\Qt\plugins
'''

class WinPythonEnv:
    editable_sections = {
        "env.ini", "environment", "debug",
        "active_environment_per_user", "active_environment_common"
    }
    
    def __init__(self, args=None):
        self.args = args[:] if args is not None else sys.argv[1:]
        self.env = dict(os.environ)
        self._initialize_paths()
        self.output_lines = []
        # in case 1st parameter is a different WinPython.ini
        if self.args and self.args[0].endswith("winpython.ini"):
            self.winpython_ini = Path(self.args[0])
            self.args = self.args[1:]
        else:
            self.winpython_ini = self.winpy_base / "settings" / "winpython.ini"
    def _initialize_paths(self):
        """we do what env.bat was doing"""
        self.winpy_base = Path(Path(__file__).parent.parent).resolve()
        self.home_dir = Path(self.winpy_base / 'settings') 
        self.winpy_dir = Path(sys.executable).parent
        self.python_exe = Path(sys.executable) 

    def get_file(self, file_path: Path, default_content=None) -> str:
        if not file_path.exists() and default_content:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(default_content)
        return file_path.read_text(encoding='utf-8')

    def translate_vars(self, value: str) -> str:
        """Replace %VAR% patterns with environment values."""
        parts = value.split('%')
        for i in range(1, len(parts), 2):
            parts[i] = self.env.get(parts[i], parts[i])
        return ''.join(parts)

    def parse_ini_lines(self, lines):
        """Parse ini lines and update environment variables."""
        section = "env.ini"
        for line in map(str.strip, lines):
            if not line or line.startswith("#"):
                continue
            if line.startswith("["):
                section = line.strip("[]")
                continue
            if "=" in line:
                key, val = map(str.strip, line.split("=", 1))
                val = self.translate_vars(val)
                if section == "debug" and key == "state":
                    key = "WINPYDEBUG"
                if section in self.editable_sections:
                    self.env[key] = val
                    self.output_lines.append(f"{key}={val}")

    def setup_qt_conf(self):
        """Create qt.conf files if missing for Qt-based packages."""
        qt_conf_text = "[Paths]\nPrefix = .\nBinaries = .\n"
        for subpkg in ("PyQt5", "PyQt6", "Pyside6"):
            pkg_path = self.winpy_dir / "Lib" / "site-packages" / subpkg
            if pkg_path.exists() and not (pkg_path / "qt.conf").exists():
                (pkg_path / "qt.conf").write_text(qt_conf_text)


    def setup_paths(self):
        lines = [
            f"WINPYDIRBASE={self.winpy_base}",
            f"WINPYDIR={self.winpy_dir}",
            f"PYTHON={self.python_exe}",
            f"HOME={self.home_dir}",
            f"WINPYWORKDIR={self.winpy_base / "Notebooks"}",
        ]
        if (self.winpy_dir / "Lib" / "site-packages" / "PyQt5" / "__init__.py").is_file():
            lines.append("QT_API=pyqt5")
        pandoc = self.winpy_base / "t" / "pandoc.exe"
        if pandoc.is_file():
            lines.append(f"PYPANDOC_PANDOC={pandoc}")
        path_extra = f"{self.winpy_dir};{self.winpy_dir / 'Scripts'};{self.winpy_dir/ ".." / 't'};{self.winpy_dir / ".." / 'n'};"
        if path_extra not in self.env.get('PATH', ''):
            lines.append(f"PATH={path_extra}{self.env.get('PATH', '')}")
        return lines


    def ensure_dirs(self):
        for key in ('HOME', 'WINPYWORKDIR', 'WINPYWORKDIR1'):
            Path(self.env.get(key, self.home_dir)).mkdir(parents=True, exist_ok=True)
        spyder_workdir = Path(self.env['HOME']) / f".spyder-py{sys.version_info[0]}" / "workingdir"
        if not spyder_workdir.exists():
            spyder_workdir.parent.mkdir(parents=True, exist_ok=True)
            spyder_workdir.write_text(str(self.home_dir / "Notebooks"))

    def determine_winpyworkdir1(self):
        """Replicates original WINPYWORKDIR1 argument/path rules."""
        winpyworkdir1 = Path(self.env['WINPYWORKDIR'])
        if len(self.args) >= 1:
            arg_path = Path(self.args[0])
            if arg_path.is_file():
                winpyworkdir1 = arg_path.parent
            elif arg_path.is_dir():
                winpyworkdir1 = arg_path
        # If cwd differs from script dir (and not under 'scripts'), use cwd
        cd_dir = Path(os.getcwd())
        script_dir = Path(__file__).parent
        if cd_dir != script_dir and cd_dir / "scripts" != script_dir:
            winpyworkdir1 = cd_dir
        self.env['WINPYWORKDIR1'] = str(winpyworkdir1)
        self.output_lines.append(f"WINPYWORKDIR1={winpyworkdir1}")

    def run(self):
       #  env.ini
        env_ini_file = Path(__file__).parent /  "env.ini" 
        if env_ini_file.is_file():
            ini_content = self.get_file(env_ini_file)
            self.parse_ini_lines(ini_content.splitlines())
        # Set up variables and paths
        self.parse_ini_lines(self.setup_paths())
        # WINPYWORKDIR1 logic here
        self.determine_winpyworkdir1()
        # Load and parse ini files
        ini_content = self.get_file(self.winpython_ini, winpython_inidefault)
        
        self.parse_ini_lines(ini_content.splitlines())
        # Ensure directories exist
        self.ensure_dirs()
        # Setup Qt conf files
        self.setup_qt_conf()
        
        for l in self.output_lines:
            print(rf"set {l}" , end="&&")
        # later_version ?
        # p = subprocess.Popen(["start", "cmd", "/k", "set"], shell = True)

if __name__ == "__main__":
    WinPythonEnv().run()
