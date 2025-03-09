@echo off
set WINPYDIRBASE=%~dp0..

rem get a normalized path
set WINPYDIRBASETMP=%~dp0..
pushd %WINPYDIRBASETMP%
set WINPYDIRBASE=%__CD__%
if "%WINPYDIRBASE:~-1%"=="\" set WINPYDIRBASE=%WINPYDIRBASE:~0,-1%
set WINPYDIRBASETMP=
popd

set WINPYDIR=%WINPYDIRBASE%\{self.python_dir_name}
rem 2019-08-25 pyjulia needs absolutely a variable PYTHON=%WINPYDIR%\python.exe
set PYTHON=%WINPYDIR%\python.exe
set PYTHONPATHz=%WINPYDIR%;%WINPYDIR%\Lib;%WINPYDIR%\DLLs
set WINPYVER={self.winpython_version_name}

rem 2023-02-12 utf-8 on console to avoid pip crash
rem see https://github.com/pypa/pip/issues/11798#issuecomment-1427069681
set PYTHONIOENCODING=utf-8
rem set PYTHONUTF8=1 creates issues in "movable" patching

set HOME=%WINPYDIRBASE%\settings
rem see https://github.com/winpython/winpython/issues/839
rem set USERPROFILE=%HOME%
set JUPYTER_DATA_DIR=%HOME%
set JUPYTER_CONFIG_DIR=%WINPYDIR%\etc\jupyter
set JUPYTER_CONFIG_PATH=%WINPYDIR%\etc\jupyter
set FINDDIR=%WINDIR%\system32

rem Remove all double quotes
set PATH_CLEANED=%PATH:"=%
echo ";%PATH_CLEANED%;" | %FINDDIR%\find.exe /C /I ";%WINPYDIR%\;" >nul
if %ERRORLEVEL% NEQ 0 (
   set "PATH={full_path_env_var}"
   cd .
)
set PATH_CLEANED=

rem force default pyqt5 kit for Spyder if PyQt5 module is there
if exist "%WINPYDIR%\Lib\site-packages\PyQt5\__init__.py" set QT_API=pyqt5
