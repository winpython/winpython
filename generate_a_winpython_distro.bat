rem  generate_a_winpython_distro.bat: to be launched from a winpython directory, where 'make.py' is
@echo on

REM === Step 01:Set default values if not already defined ===
if not defined my_release_level set "my_release_level=b1"
if not defined my_create_installer set "my_create_installer=True"
if not defined my_constraints set "my_constraints=C:\WinP\constraints.txt"
if not defined target_python_exe set "target_python_exe=python.exe"

REM === Define archive directory ===
set "my_archive_dir=%~dp0WinPython_build_logs"
if not exist "%my_archive_dir%" mkdir "%my_archive_dir%"

REM === Format current time for use in log file ===
set "my_time=%time:~0,5%"
set "my_time=%my_time::=_%"
set "my_time=%my_time: =0%"

REM === Define archive log file path ===
set "my_archive_log=%my_archive_dir%\build_%my_pyver%_%my_release%%my_flavor%_%my_release_level%_of_%date:/=-%at_%my_time%.txt"

REM === Step 02:Set Python version and release ===
if "%my_python_target%"=="311" (
    set "my_python_target_release=3119"
    set "my_release=2"
) else if "%my_python_target%"=="312" (
    set "my_python_target_release=31210"
    set "my_release=2"
) else if "%my_python_target%"=="313" (
    set "my_python_target_release=3135"
    set "my_release=1"
) else if "%my_python_target%"=="314" (
    set "my_python_target_release=3140"
    set "my_release=1"
)

REM === Step 03:Define base build and distribution paths ===
set "my_basedir=%my_root_dir_for_builds%\bd%my_python_target%"
set "my_WINPYDIRBASE=%my_basedir%\bu%my_flavor%\WPy%my_arch%-%my_python_target_release%%my_release%%my_release_level%"


rem a building env need is a Python with packages: WinPython + build + flit + packaging + mkshim400.py
set my_buildenv=C:\WinPdev\WPy64-310111

call :log_section preparing winPython for %my_pyver% (%my_python_target%)release %my_release%%my_flavor% (%my_release_level%) *** %my_arch% bit ***

REM === Step 04: Pre-clear previous build infrastructure ===
if /i "%my_preclear_build_directory%"=="Yes" (
    call :log_section Pre-clear previous build infrastructure

    REM Delete Jupyter config if it exists
    if exist "%userprofile%\.jupyter\jupyter_notebook_config.py" (
        del /f /q "%userprofile%\.jupyter\jupyter_notebook_config.py"
    )

    REM Navigate to build directory
    cd /D "%my_root_dir_for_builds%\bd%my_python_target%"

    REM Rename previous build folder if it exists
    if exist "bu%my_flavor%" (
        ren "bu%my_flavor%" "bu%my_flavor%_old"
        rmdir /s /q "bu%my_flavor%_old"
    )
)

REM === Step 05: Create new build ===
call :log_section Create a new build

REM Activate base build environment
cd /D "%~dp0"
set "path=%my_original_path%"
call "%my_buildenv%\scripts\env.bat"

REM Call make_all to create basic infrastructure
call :log_section  Create basic build infrastructure
python.exe -c "from make import make_all; make_all(%my_release%, '%my_release_level%', basedir_wpy=r'%my_WINPYDIRBASE%', verbose=True, flavor='%my_flavor%', source_dirs=r'%my_source_dirs%', toolsdirs=r'%my_toolsdirs%')" >>"%my_archive_log%"


REM === Check infrastructure exists ===
call :log_section  Check infrastructure

set "WINPYDIRBASE=%my_WINPYDIRBASE%"

if not exist "%WINPYDIRBASE%\scripts\env.bat" (
    echo ERROR: %WINPYDIRBASE%\scripts\env.bat does not exist
    echo Please verify:
    echo     my_arch=%my_arch%
    echo     my_python_target_release=%my_python_target_release%
    echo     my_release=%my_release%
    echo     my_release_level=%my_release_level%
    pause
    exit /b 1
)

REM === Step 06: Add pre-requisite packages ===
call :log_section Add pre-requisite packages

set "path=%my_original_path%"
call "%my_WINPYDIRBASE%\scripts\env.bat"

rem python -m ensurepip
REM Upgrade essential pip tools
python -m pip install --upgrade pip setuptools wheel wppm  -c "%my_constraints%" --pre --no-index --trusted-host=None --find-links="%my_find_links%" >>"%my_archive_log%"

REM Install additional pre-requirements if specified
if defined my_requirements_pre (
    if not defined my_find_links_pre set "my_find_links_pre=%my_find_links%"
    python -m pip install -r "%my_requirements_pre%" -c "%my_constraints%" --pre --no-index --trusted-host=None --find-links="%my_find_links_pre%" >>"%my_archive_log%"
) else (
    echo No pre-requisite packages specified >>"%my_archive_log%"
)

REM === Step 07: Install main requirement packages ===
call :log_section  Add main requirement packages
python -m pip install -r "%my_requirements%" -c "%my_constraints%" --pre --no-index --trusted-host=None --find-links="%my_find_links%" >>"%my_archive_log%"

REM Patch installed packages to be portable (WinPython style)
python -c "from wppm import wppm;dist=wppm.Distribution(r'%WINPYDIR%');dist.patch_standard_packages('', to_movable=True)"

REM === Step 08: Define lockfile paths for included wheels ===
set "WINPYVERLOCK=%WINPYVER2:.=_%"
set "LOCKDIR=%WINPYDIRBASE%\..\"

set "pip_lock_includedlocal=%LOCKDIR%pylock.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%_wheelslocal.toml"
set "pip_lock_includedweb=%LOCKDIR%pylock.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%_wheels.toml"
set "req_lock_includedlocal=%LOCKDIR%requir.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%_wheelslocal.txt"
set "req_lock_includedweb=%LOCKDIR%requir.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%_wheels.txt"

REM === Step 09: Add lockfile wheels for the Wheelhouse (optional) ===
if defined wheelhousereq if exist "%wheelhousereq%" (
    call :log_section Add wheels for the Wheelhouse

    REM Generate pylock from wheelhousereq
    python -m pip lock --no-index --trusted-host=None --find-links="%my_find_links%" -c "%my_constraints%" -r "%wheelhousereq%" -o "%pip_lock_includedlocal%"

    REM Convert pylock to requirement file with hashes
    python -c "from wppm import wheelhouse as wh; wh.pylock_to_req(r'%pip_lock_includedlocal%', r'%req_lock_includedlocal%')"

    REM Freeze lock again from local hashes
    python -m pip lock --no-deps --require-hashes -c "%my_constraints%" -r "%req_lock_includedlocal%" -o "%pip_lock_includedweb%"

    REM Use wppm to install from lock
    "%my_WINPYDIRBASE%\python\scripts\wppm.exe" "%pip_lock_includedweb%" -ws "%my_find_links%" -wd "%my_WINPYDIRBASE%\wheelhouse\included.wheels"
)

rem set path=%my_original_path%
rem call %my_WINPYDIRBASE%\scripts\env.bat


REM === Step 10: Freeze environment and generate final lockfiles ===
call :log_section Freeze environment and generate lockfiles

set "req=%LOCKDIR%requirement.%my_flavor%-%WINPYARCH%bit-%WINPYVERLOCK%_raw.txt"
set "wanted_req=%LOCKDIR%requirement.%my_flavor%-%WINPYARCH%bit-%WINPYVERLOCK%.txt"

set "pip_lock_web=%LOCKDIR%pylock.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%.toml"
set "pip_lock_local=%LOCKDIR%pylock.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%_local.toml"
set "req_lock_web=%LOCKDIR%requir.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%.txt"
set "req_lock_local=%LOCKDIR%requir.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%_local.txt"
 
REM Archive paths
set "my_archive_lockfile=%my_archive_dir%\pylock.%my_flavor%-%WINPYARCH%bit-%WINPYVERLOCK%_%date:/=-%at_%my_time%.toml"
set "my_changelog_lockfile=%~dp0changelogs\pylock.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%.toml"
set "my_changelog_reqfile=%~dp0changelogs\requir.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%.txt"

REM Freeze full environment (excluding winpython)
python -m pip freeze > "%req%"
findstr /v "winpython" "%req%" > "%wanted_req%"

REM Lock from PyPI
python -m pip lock --no-deps -c "%my_constraints%" -r "%wanted_req%" -o "%pip_lock_web%"

REM Lock from local wheelhouse
python -m pip lock --no-deps --no-index --trusted-host=None --find-links="%my_find_links%" -c "%my_constraints%" -r "%wanted_req%" -o "%pip_lock_local%"

REM Convert both locks to requirement.txt with hash256
python -c "from wppm import wheelhouse as wh; wh.pylock_to_req(r'%pip_lock_web%', r'%req_lock_web%')"
python -c "from wppm import wheelhouse as wh; wh.pylock_to_req(r'%pip_lock_local%', r'%req_lock_local%')"

REM Compare for reproducibility check
fc "%req_lock_web%" "%req_lock_local%"
@echo off

REM Archive generated lockfile
copy /Y "%pip_lock_web%" "%my_archive_lockfile%"
copy /Y "%pip_lock_web%" "%my_changelog_lockfile%"
copy /Y "%req_lock_web%" "%my_changelog_reqfile%"

call :log_section  Archive success

REM === Step 11: Generate changelog and binaries ===
call :log_section Generate changelog and binaries

REM Define markdown changelog filenames
set "mdn=WinPython%my_flavor%-%my_arch%bit-%WINPYVER2%.md"
set "out=WinPython%my_flavor%-%my_arch%bit-%WINPYVER2%_History.md"

REM Create markdown package list
%target_python_exe% -m wppm -md > "%my_WINPYDIRBASE%\..\%mdn%"
copy /Y "%my_WINPYDIRBASE%\..\%mdn%" "%~dp0changelogs\%mdn%"

REM Generate historical diff
%target_python_exe% -c "from wppm import diff; result = diff.compare_package_indexes('%WINPYVER2%', searchdir=r'%~dp0changelogs', flavor=r'%my_flavor%', architecture=%my_arch%); open(r'%my_WINPYDIRBASE%\..\%out%', 'w', encoding='utf-8').write(result)"
copy /Y "%my_WINPYDIRBASE%\..\%out%" "%~dp0changelogs\%out%"

REM === Step 13b: Compress distribution to .7z or installer ===
set "stem=WinPython%my_arch%-%WINPYVER2%%my_flavor%%my_release_level%"
%target_python_exe% -c "from wppm import utils; utils.command_installer_7zip(r'%my_WINPYDIRBASE%', r'%my_WINPYDIRBASE%\..', r'%stem%', r'%my_create_installer%')"

REM === Step 12: Final logs and cleanup ===
call :log_section Final logs and cleanup

REM Restore environment
set "path=%my_original_path%"
call "%my_WINPYDIRBASE%\scripts\env.bat"

REM Freeze final package versions to archive
%target_python_exe% -m pip freeze > "%my_archive_log%.packages_versions.txt"

call :log_section END OF CREATION

REM Open log files in Notepad for review
start notepad.exe "%my_archive_log%"
start notepad.exe "%my_archive_log%.packages_versions.txt"

REM Restore path again (in case env.bat changed it)
set "path=%my_original_path%"
pause
exit

:log_section
echo. >>%my_archive_log%
echo -------------------------------------- >>%my_archive_log%
echo (%date% %time%) %* >>%my_archive_log%
echo (%date% %time%) %*
echo -------------------------------------- >>%my_archive_log%
echo. >>%my_archive_log%
exit /b
