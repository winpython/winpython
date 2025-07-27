rem  generate_a_winpython_distropy.bat: to be launched with a winpython sub-directory
rem   where 'build_winpython.py' and 'make.py' are 
@echo on

REM === Initialize default values ===
if not defined my_release_level set "my_release_level=b1"
if not defined my_create_installer set "my_create_installer=True"
if not defined my_constraints set "my_constraints=C:\WinP\constraints.txt"
if not defined target_python_exe set "target_python_exe=python.exe"
if not defined mandatory_requirements set "mandatory_requirements=%~dp0mandatory_requirements.txt"

set "my_archive_dir=%~dp0WinPython_build_logs"
if not exist "%my_archive_dir%" mkdir "%my_archive_dir%"

REM === Format log timestamp ===
set "my_time=%time:~0,5%"
set "my_time=%my_time::=_%"
set "my_time=%my_time: =0%"

set "my_archive_log=%my_archive_dir%\build_%my_pyver%_%my_release%%my_flavor%_%my_release_level%_of_%date:/=-%at_%my_time%.txt"

REM === Define base build and distribution paths ===
set "my_basedir=%my_root_dir_for_builds%\bd%my_python_target%"
set "my_WINPYDIRBASE=%my_basedir%\bu%my_flavor%\WPy%my_arch%-%my_python_target_release%%my_release%%my_release_level%"

rem a building env need is a Python with packages: WinPython + build + flit + packaging + mkshim400.py
set "my_buildenv=C:\WinPdev\WPy64-310111"
set "my_buildenvi=C:\WinPdev\WPy64-310111\python-3.10.11.amd64"
set "my_python_exe=C:\WinPdev\WPy64-310111\python-3.10.11.amd64\python.exe"

if "%my_requirements_pre%" == "" set "my_requirements_pre=%mandatory_requirements%" 
set "my_requirements_pre=%mandatory_requirements%"   

cd/d %~dp0
echo %my_python_exe% -m winpython.build_winpython --buildenv %my_buildenvi% --python-target %my_python_target% --release %my_release% --release-level %my_release_level% --winpydirbase  %my_WINPYDIRBASE%   --flavor %my_flavor% --source_dirs %my_source_dirs%  --tools_dirs %my_toolsdirs% --log-dir %~dp0WinPython_build_logs --mandatory-req %mandatory_requirements% --pre-req %my_requirements_pre% --requirements %my_requirements% --constraints %my_constraints% --find-links %my_find_links%  --wheelhousereq "%wheelhousereq%" --create-installer "%my_create_installer%"
%my_python_exe% -m winpython.build_winpython  --buildenv %my_buildenvi%  --python-target %my_python_target%  --release %my_release% --release-level %my_release_level% --winpydirbase  %my_WINPYDIRBASE%   --flavor %my_flavor% --source_dirs %my_source_dirs%  --tools_dirs %my_toolsdirs% --log-dir %~dp0WinPython_build_logs --mandatory-req %mandatory_requirements% --pre-req %my_requirements_pre%  --requirements %my_requirements% --constraints %my_constraints% --find-links %my_find_links%  --wheelhousereq "%wheelhousereq%" --create-installer "%my_create_installer%"
pause
exit
