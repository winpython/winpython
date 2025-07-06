rem  generate_a_winpython_distro.bat: to be launched from a winpython directory, where 'make.py' is
@echo on

REM Initialize variables
if "%my_release_level%"=="" set my_release_level=
if "%my_create_installer%"=="" set my_create_installer=True

rem Set archive directory and log file
set my_archive_dir=%~dp0WinPython_build_logs
if not exist %my_archive_dir% mkdir %my_archive_dir%

set my_time=%time:~0,5%
set my_time=%my_time::=_%
set my_time=%my_time: =0%
set my_archive_log=%my_archive_dir%\build_%my_pyver%._.%my_release%%my_flavor%_%my_release_level%_of_%date:/=-%at_%my_time%.txt

set my_basedir=%my_root_dir_for_builds%\bd%my_python_target%

rem a building env need is a Python with packages: WinPython + build + flit + packaging + mkshim400.py
set my_buildenv=C:\WinPdev\WPy64-310111

if "%my_constraints%"=="" set my_constraints=C:\WinP\constraints.txt

rem  2021-04-22 : path PyPy3 (as we don't try to copy PyPy3.exe to Python.exe) 
if "%target_python_exe%"=="" set target_python_exe=python.exe

rem Set Python target release based on my_python_target
if %my_python_target%==311 set my_python_target_release=3119& set my_release=2
if %my_python_target%==312 set my_python_target_release=31210& set my_release=2
if %my_python_target%==313 set my_python_target_release=3135& set my_release=1
if %my_python_target%==314 set my_python_target_release=3140& set my_release=1

set my_WINPYDIRBASE=%my_basedir%\bu%my_flavor%\WPy%my_arch%-%my_python_target_release%%my_release%%my_release_level%

echo -------------------------------------- >>%my_archive_log%
echo (%date% %time%) preparing winPython for %my_pyver% (%my_python_target%)release %my_release%%my_flavor% (%my_release_level%) *** %my_arch% bit ***>>%my_archive_log%
echo -------------------------------------- >>%my_archive_log%

rem Pre-clear previous build infrastructure
if "%my_preclear_build_directory%"=="Yes" (
    echo "(%date% %time%) Pre-clear previous build infrastructure">>%my_archive_log%
    del -y %userprofile%\.jupyter\jupyter_notebook_config.py
    cd /D %my_root_dir_for_builds%\bd%my_python_target%
    set build_det=\%my_flavor%
    if "%my_flavor%"=="" set build_det=
    dir %build_det%
    ren bu%my_flavor% bu%my_flavor%_old
    start rmdir /S /Q bu%my_flavor%_old
    rmdir /S /Q bu%my_flavor%
    rmdir /S /Q dist
)

REM Create a new build
echo -------------------------------------- >>%my_archive_log%
echo "(%date% %time%) Create a new build">>%my_archive_log%
echo -------------------------------------- >>%my_archive_log%
cd /D %~dp0
set path=%my_original_path%
call %my_buildenv%\scripts\env.bat
@echo on

REM Create basic build infrastructure
echo "(%date% %time%) Create basic build infrastructure">>%my_archive_log%
python.exe -c "from make import *;make_all(%my_release%, '%my_release_level%', basedir_wpy=r'%my_WINPYDIRBASE%', verbose=True, flavor='%my_flavor%', install_options=r'%my_install_options%', find_links=r'%my_find_links%', source_dirs=r'%my_source_dirs%', toolsdirs=r'%my_toolsdirs%', create_installer='False')">>%my_archive_log%

REM Check infrastructure is in place
echo "(%date% %time%) Check infrastructure">>%my_archive_log%
set WINPYDIRBASE=%my_WINPYDIRBASE% 

if not exist %my_WINPYDIRBASE%\scripts\env.bat (
 @echo off
 echo as %my_WINPYDIRBASE%\scripts\env.bat does not exist
 echo please check and correct:
 echo     my_arch=%my_arch%
 echo     my_python_target_release=%my_python_target_release%
 echo     my_release=%my_release%
 echo     my_release_level=%my_release_level%
 pause
 exit
)

REM Add pre-requisite packages
echo -------------------------------------- >>%my_archive_log%
echo "(%date% %time%) Add pre-requisite packages">>%my_archive_log%
echo -------------------------------------- >>%my_archive_log%

set path=%my_original_path%
call %my_WINPYDIRBASE%\scripts\env.bat

rem Install pre-requirements if any
if not "Z%my_requirements_pre%Z"=="ZZ" (
    if "%my_find_links_pre%"=="" set my_find_links_pre=%my_find_links%
    python -m pip install -r %my_requirements_pre% -c %my_constraints% --pre --no-index --trusted-host=None --find-links=%my_find_links_pre% >> %my_archive_log%
) else (
    echo "No pre-requisite packages">>%my_archive_log%
)

REM Add requirement packages
echo -------------------------------------- >>%my_archive_log%
echo "(%date% %time%) Add requirement packages">>%my_archive_log%
echo -------------------------------------- >>%my_archive_log%
python -m pip install -r %my_requirements% -c %my_constraints% --pre --no-index --trusted-host=None --find-links=%my_find_links% >>%my_archive_log%
python -c "from wppm import wppm;dist=wppm.Distribution(r'%WINPYDIR%');dist.patch_standard_packages('spyder', to_movable=True)"

REM Add Wheelhouse (to replace per pip lock direct ? would allow paralellism)
echo -------------------------------------- >>%my_archive_log%
echo "(%date% %time%) Add lockfile wheels">>%my_archive_log%
echo -------------------------------------- >>%my_archive_log%
set path=%my_original_path%
@echo on
call %my_WINPYDIRBASE%\scripts\env.bat
@echo on
set WINPYVERLOCK=%WINPYVER2:.=_%
set pylockinclude=%my_root_dir_for_builds%\bd%my_python_target%\bu%addlockfile%\pylock.%addlockfile%-%WINPYARCH%bit-%WINPYVERLOCK%.toml
echo pylockinclude="%pylockinclude%"
if not "Z%addlockfile%Z"=="ZZ" if exist "%pylockinclude%" (
echo %my_WINPYDIRBASE%\python\scripts\wppm.exe "%pylockinclude%" -ws  "%my_find_links%"  -wd "%my_WINPYDIRBASE%\wheelhouse\included.wheels">>%my_archive_log%
%my_WINPYDIRBASE%\python\scripts\wppm.exe "%pylockinclude%" -ws  "%my_find_links%"  -wd "%my_WINPYDIRBASE%\wheelhouse\included.wheels"
)

@echo on
echo wheelhousereq=%wheelhousereq%
set LOCKDIR=%WINPYDIRBASE%\..\
set pip_lock_includedlocal=%LOCKDIR%pylock.%my_flavor%-%WINPYARCH%bit-%WINPYVERLOCK%_includedwheelslocal.toml
set pip_lock_includedweb=%LOCKDIR%pylock.%my_flavor%-%WINPYARCH%bit-%WINPYVERLOCK%_includedwheels.toml
set req_lock_includedlocal=%LOCKDIR%requirement.%my_flavor%-%WINPYARCH%bit-%WINPYVERLOCK%_includedwheelslocal.txt
set req_lock_includedweb=%LOCKDIR%requirement.%my_flavor%-%WINPYARCH%bit-%WINPYVERLOCK%_includedwheels.txt

set pip_lock_includedlocal=%LOCKDIR%pylock.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%_wheelslocal.toml
set pip_lock_includedweb=%LOCKDIR%pylock.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%_wheels.toml
set req_lock_includedlocal=%LOCKDIR%requir.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%_wheelslocal.txt
set req_lock_includedweb=%LOCKDIR%requir.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%_wheels.txt


if not "Z%wheelhousereq%Z"=="ZZ" if exist "%wheelhousereq%" (
echo JOYYYwheelhousereq=%wheelhousereq%
echo  z%pip_lock_includedlocal%z=%pip_lock_includedlocal% 
rem no winpython in it naturally, with deps
python.exe -m pip lock --no-index --trusted-host=None  --find-links=%my_find_links%  -c C:\WinP\constraints.txt -r  "%wheelhousereq%" -o %pip_lock_includedlocal% 
rem generating also classic requirement with hash-256, from obtained pylock.toml
python.exe -c "from wppm import wheelhouse as wh;wh.pylock_to_req(r'%pip_lock_includedlocal%', r'%req_lock_includedlocal%')"

rem same with frozen web from local
python.exe -m pip lock --no-deps --require-hashes    -c C:\WinP\constraints.txt -r  "%req_lock_includedlocal%" -o %pip_lock_includedweb%

echo %my_WINPYDIRBASE%\python\scripts\wppm.exe "%pip_lock_includedweb%" -ws  "%my_find_links%"  -wd "%my_WINPYDIRBASE%\wheelhouse\included.wheels">>%my_archive_log%
%my_WINPYDIRBASE%\python\scripts\wppm.exe "%pip_lock_includedweb%" -ws  "%my_find_links%"  -wd "%my_WINPYDIRBASE%\wheelhouse\included.wheels"
)

echo -------------------------------------- >>%my_archive_log%;
echo "(%date% %time%) generate pylock.toml files and requirement.txt with hash files">>%my_archive_log%
echo -------------------------------------- >>%my_archive_log%

set path=%my_original_path%
call %my_WINPYDIRBASE%\scripts\env.bat

rem generate pip freeze requirements
echo %date% %time%
set LOCKDIR=%WINPYDIRBASE%\..\

set WINPYVERLOCK=%WINPYVER2:.=_%
set req=%LOCKDIR%requirement.%my_flavor%-%WINPYARCH%bit-%WINPYVERLOCK%_raw.txt
set wanted_req=%LOCKDIR%requirement.%my_flavor%-%WINPYARCH%bit-%WINPYVERLOCK%.txt

set pip_lock_web=%LOCKDIR%pylock.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%.toml
set pip_lock_local=%LOCKDIR%pylock.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%_local.toml
set req_lock_web=%LOCKDIR%requir.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%.txt
set req_lock_local=%LOCKDIR%requir.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%_local.txt


set my_archive_lockfile=%my_archive_dir%\pylock.%my_flavor%-%WINPYARCH%bit-%WINPYVERLOCK%_%date:/=-%at_%my_time%.toml
set my_archive_lockfile_local=%my_archive_dir%\pylock.%my_flavor%-%WINPYARCH%bit-%WINPYVERLOCK%_%date:/=-%at_%my_time%.local.toml
set my_changelog_lockfile=%~dp0changelogs\pylock.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%.toml
set my_changelog_reqfile=%~dp0changelogs\requir.%WINPYARCH%-%WINPYVERLOCK%%my_flavor%%my_release_level%.txt

python.exe -m pip freeze>%req%
findstr /v "winpython" %req% > %wanted_req%


rem pip lock from pypi, from the frozen req
python.exe -m pip lock --no-deps  -c C:\WinP\constraints.txt -r "%wanted_req%" -o %pip_lock_web%

rem pip lock from local WheelHouse, from the frozen req
python.exe -m pip lock --no-deps --no-index --trusted-host=None  --find-links=C:\WinP\packages.srcreq -c C:\WinP\constraints.txt -r  "%wanted_req%" -o %pip_lock_local%

rem generating also classic requirement with hash-256, from obtained pylock.toml
python.exe -c "from wppm import wheelhouse as wh;wh.pylock_to_req(r'%pip_lock_web%', r'%req_lock_web%')"
python.exe -c "from wppm import wheelhouse as wh;wh.pylock_to_req(r'%pip_lock_local%', r'%req_lock_local%')"

rem compare the two (result from pypi and local Wheelhouse must be equal)
fc  "%req_lock_web%" "%req_lock_local%"

copy/Y %pip_lock_web% %my_archive_lockfile%
copy/Y %pip_lock_web% %my_changelog_lockfile%
copy/Y %req_lock_web% %my_changelog_reqfile%


REM Archive success
echo -------------------------------------- >>%my_archive_log%
echo "(%date% %time%) Archive success">>%my_archive_log%
echo -------------------------------------- >>%my_archive_log%
set path=%my_original_path%
call %my_WINPYDIRBASE%\scripts\env.bat

%target_python_exe% -m pip freeze > %my_archive_log%.packages_versions.txt

REM Generate changelog and binaries
echo "(%date% %time%) Generate changelog and binaries">>%my_archive_log%

rem markdowm and markdown diff
set mdn=WinPython%my_flavor%-%my_arch%bit-%WINPYVER2%.md
%target_python_exe% -m wppm -md>%my_basedir%\bu%my_flavor%\%mdn%
copy/y %my_basedir%\bu%my_flavor%\%mdn% %~dp0changelogs\%mdn%

set out=WinPython%my_flavor%-%my_arch%bit-%WINPYVER2%_History.md
%target_python_exe% -c "from wppm import diff ;a=(diff.compare_package_indexes(r'%WINPYVER2%', searchdir=r'%~dp0changelogs',flavor=r'%my_flavor%',architecture=%my_arch%));f=open(r'%my_basedir%\bu%my_flavor%\%out%','w', encoding='utf-8');f.write(a);f.close()" 
copy/y %my_basedir%\bu%my_flavor%\%out% %~dp0changelogs\%out%

rem compress
set stem=WinPython%my_arch%-%WINPYVER2%%my_flavor%
%target_python_exe% -c "from wppm import utils;utils.command_installer_7zip(r'%my_WINPYDIRBASE%', r'%my_WINPYDIRBASE%\..',r'%stem%', r'%my_create_installer%')" 

echo -------------------------------------- >>%my_archive_log%
echo "(%date% %time%) END OF CREATION">>%my_archive_log%
echo -------------------------------------- >>%my_archive_log%
start notepad.exe %my_archive_log%
start notepad.exe %my_archive_log%.packages_versions.txt

set path=%my_original_path%