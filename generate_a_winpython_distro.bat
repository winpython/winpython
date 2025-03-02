rem  to launch from a winpython package directory, where 'make.py' is
@echo on

rem *****************************
rem 2020-07-05: install msvc_runtime before packages that may want to compile
rem 2020-12-05 : add a constraints.txt file from a recent pip list
rem 2021-03-20 : track successes packages combination are archived for future contraint update
rem 2021-04-22 : path PyPy3 (as we don't try to copy PyPy3.exe to Python.exe) 
rem 2023-08-21a: add a pre_step with my_requirements_pre.txt + my_find_links_pre
rem 2024-05-12a: use python -m pip instead of pip , and remove --upgrade %new_resolver%
rem 2024-09-15a: compactify for lisiblity
rem 2025-03-02 : remove step 2.3 (pre-build), and 2.8 (post-patch) as we simplify to only wheels
rem *****************************

rem algorithm:
rem 0.0 Initialize variables  
rem 1.0 Do 2021-04-22 : patch PyPy3 (as we don't try to copy PyPy3.exe to Python.exe) 
rem 2 a Pre-clear of previous build infrastructure
rem 2.0 Create a new build
rem   2.1 Create basic build infrastructure 
rem   2.2 check infrastructure is in place
rem   2.4 add packages pre_requirements (if any)
rem   2.5 add requirement packages
rem   2.9 archive success
rem 3.0 Generate Changelog and binaries

rem "my_release_level" is optionaly set per the calling program *********************************************
rem set my_release_level=

rem ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! =

if "%my_release_level%"=="" set my_release_level=

rem ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! = ! =

rem "my_create_installer" is optionaly set per the calling program
if "%my_create_installer%"=="" set my_create_installer=True


rem this is pre-initialised per the program calling this .bat
rem  set my_original_path=%path%
rem  set my_root_dir_for_builds=D:\WinP

rem  set my_python_target=34
rem  set my_pyver=3.4
rem  set my_flavor=slim
rem  set my_release=84

rem  set my_find_link=C:\WinP\packages.srcreq

rem  set my_arch=64
rem  set my_preclear_build_directory=Yes

rem  set my_requirements_pre=C:\WinP\bd311\requirements_mkl_pre.txt
rem  set my_find_links_pre=C:\WinP\packages_mkl.srcreq

rem  set my_requirements=C:\Winpents=d:\my_req1.txt

rem  set my_source_dirs=D:\WinPython\bd34\packages.src D:\WinPython\bd34\packages.win32.Slim
rem  set my_toolsdirs=D:\WinPython\bd34\Tools.Slim
rem  set my_docsdirs=D:\WinPython\bd34\docs.Slim



echo ----------------------------------------
echo 0.0 (%date% %time%) Initialize variables  
echo ----------------------------------------


set my_basedir=%my_root_dir_for_builds%\bd%my_python_target%

rem a building env need is a Python with packages: WinPython + build + flit + packaging + mkshim400.py
set my_buildenv=C:\WinPdev\WPy64-310111

if "%my_constraints%"=="" set my_constraints=C:\WinP\constraints.txt

rem  2021-04-22 : path PyPy3 (as we don't try to copy PyPy3.exe to Python.exe) 
if "%target_python_exe%"=="" set target_python_exe=python.exe


if %my_python_target%==310 (
   set my_python_target_release=31011
   set my_release=2
)

if %my_python_target%==311 (
   set my_python_target_release=3119
   set my_release=1
)

if %my_python_target%==312 (
   set my_python_target_release=3129
   set my_release=1
)

if %my_python_target%==313 (
   set my_python_target_release=3132
   set my_release=1
)
if %my_python_target%==314 (
   set my_python_target_release=3140
   set my_release=0
)


rem  set my_install_options=--no-index --pre

set my_day=%date:/=-%
set my_time=%time:~0,5%
set my_time=%my_time::=_%
set my_time=%my_time: =0%

set my_archive_dir=%~dp0WinPython_build_logs
if not exist %my_archive_dir% mkdir %my_archive_dir%

set my_archive_log=%my_archive_dir%\build_%my_pyver%._.%my_release%%my_flavor%_%my_release_level%_of_%my_day%_at_%my_time%.txt


echo ----------------------------------------
echo preparing winPython for %my_pyver% (%my_python_target%)release %my_release%%my_flavor% (%my_release_level%) *** %my_arch% bit *** 
echo ----------------------------------------
echo ---------------------------------------- >>%my_archive_log%
echo  (%date% %time%) preparing winPython for %my_pyver% (%my_python_target%)release %my_release%%my_flavor% (%my_release_level%) *** %my_arch% bit ***>>%my_archive_log%
echo ---------------------------------------- >>%my_archive_log%


if not "%my_preclear_build_directory%"=="Yes" goto no_preclear


echo ----------------------------------------
echo 1.0 (%date% %time%) Do a Pre-clear of previous build infrastructure  
echo ----------------------------------------
echo ---------------------------------------- >>%my_archive_log%
echo 1.0 (%date% %time%) Do a Pre-clear of previous build infrastructure>>%my_archive_log%
echo ---------------------------------------- >>%my_archive_log%

rem 2019-05-10 PATCH for build problem (asking permission to overwrite the file)
del -y %userprofile%\.jupyter\jupyter_notebook_config.py

cd /D  %my_root_dir_for_builds%\bd%my_python_target%

set build_det=\%my_flavor%
if "%my_flavor%"=="" set build_det=

dir %build_det%

rem 2021-02-13 workaround to hard to remove json files
echo ren bu%my_flavor% bu%my_flavor%_old
ren bu%my_flavor% bu%my_flavor%_old

rem pause
start rmdir /S /Q bu%my_flavor%_old


echo rmdir /S /Q bu%my_flavor%
rem pause
rmdir /S /Q bu%my_flavor%
rmdir /S /Q bu%my_flavor%
rmdir /S /Q bu%my_flavor%
rmdir /S /Q bu%my_flavor%
rmdir /S /Q bu%my_flavor%
rmdir /S /Q dist

echo %date% %time%
echo %date% %time%>>%my_archive_log%

:no_preclear


echo ---------------------------------------- 
echo 2.0 (%date% %time%) Create a new build 
echo ---------------------------------------- >>%my_archive_log%
echo 2.0 (%date% %time%) Create a new build>>%my_archive_log%
echo ---------------------------------------- >>%my_archive_log%


echo cd /D %~dp0>>%my_archive_log%
cd /D %~dp0

echo set path=%my_original_path%>>%my_archive_log%
set path=%my_original_path%

echo call %my_buildenv%\scripts\env.bat>>%my_archive_log%
call %my_buildenv%\scripts\env.bat

echo ---------------------------------------- 
echo   2.1 (%date% %time%) Create basic build infrastructure 
echo ----------------------------------------
echo ---------------------------------------- >>%my_archive_log%
echo   2.1 (%date% %time%) Create basic build infrastructure>>%my_archive_log%
echo ---------------------------------------- >>%my_archive_log%

rem at First step 2.1
rem   we don't use any %my_requirements% 
rem   we don't create installer
rem   we use legacy python build cd /D %~dp0

set my_buildenv_path=%path%

echo python.exe  -c "from make import *;make_all(%my_release%, '%my_release_level%', pyver='%my_pyver%', basedir=r'%my_basedir%', verbose=True, architecture=%my_arch%, flavor='%my_flavor%', install_options=r'%my_install_options%', find_links=r'%my_find_links%', source_dirs=r'%my_source_dirs%', toolsdirs=r'%my_toolsdirs%', docsdirs=r'%my_docsdirs%', create_installer='False', python_target_release='%my_python_target_release%')">>%my_archive_log%

echo python.exe  -c "from make import *;make_all(%my_release%, '%my_release_level%', pyver='%my_pyver%', basedir=r'%my_basedir%', verbose=True, architecture=%my_arch%, flavor='%my_flavor%', install_options=r'%my_install_options%', find_links=r'%my_find_links%', source_dirs=r'%my_source_dirs%', toolsdirs=r'%my_toolsdirs%', docsdirs=r'%my_docsdirs%', create_installer='False', python_target_release='%my_python_target_release%')"

rem pause

python.exe  -c "from make import *;make_all(%my_release%, '%my_release_level%', pyver='%my_pyver%', basedir=r'%my_basedir%', verbose=True, architecture=%my_arch%, flavor='%my_flavor%', install_options=r'%my_install_options%', find_links=r'%my_find_links%', source_dirs=r'%my_source_dirs%', toolsdirs=r'%my_toolsdirs%', docsdirs=r'%my_docsdirs%', create_installer='False', python_target_release='%my_python_target_release%')">>%my_archive_log%


echo ----------------------------------------
echo   2.2 (%date% %time%) check infrastructure is in place
echo ---------------------------------------- 
echo ---------------------------------------- >>%my_archive_log%
echo   2.2 (%date% %time%) check infrastructure is in place>>%my_archive_log%
echo ---------------------------------------- >>%my_archive_log%

@echo on
set my_WINPYDIRBASE=%my_root_dir_for_builds%\bd%my_python_target%\bu%my_flavor%\Wpy%my_arch%-%my_python_target_release%%my_release%%my_release_level%

set WINPYDIRBASE=%my_WINPYDIRBASE% 

if not exist %my_WINPYDIRBASE%\scripts\env.bat (
 echo please check and correct my_python_target_release=%my_python_target_release% 
 echo     my_arch=%my_arch%
 echo     my_python_target_release=%my_python_target_release%
 echo     my_release=%my_release%
 echo     my_release_level=%my_release_level%
 echo in generate_a_winpython_distro.bat
 echo as %my_WINPYDIRBASE%\scripts\env.bat doesnt exist
 pause
 exit
)     

rem we use final environment to install requirements
set path=%my_original_path%

call %my_WINPYDIRBASE%\scripts\env.bat
set


echo ----------------------------------------
echo   2.4 (%date% %time%) add  packages pre_requirements (if any)  
echo ----------------------------------------
echo ---------------------------------------- >>%my_archive_log%
echo   2.4 (%date% %time%) add  packages pre_requirements (if any)  
echo ---------------------------------------- >>%my_archive_log%

if not "Z%my_requirements_pre%Z"=="ZZ" (

if "%my_find_links_pre%"=="" set my_find_links_pre=%my_find_links%

echo python -m pip install -r %my_requirements_pre% -c %my_constraints% --pre  --no-index --trusted-host=None --find-links=%my_find_links_pre%  
echo python -m pip install -r %my_requirements_pre% -c %my_constraints%  --pre  --no-index --trusted-host=None --find-links=%my_find_links_pre%  >>%my_archive_log%
echo if pip doesn't work, check the path of %my_WINPYDIRBASE%

python -m pip install -r %my_requirements_pre% -c  %my_constraints%   --pre  --no-index --trusted-host=None --find-links=%my_find_links_pre%  >>%my_archive_log%
) else (
echo no packages pre_requirements   
echo no packages pre_requirements>>%my_archive_log%
)


echo ----------------------------------------
echo   2.5 (%date% %time%) add requirement packages
echo ----------------------------------------
echo ---------------------------------------- >>%my_archive_log%
echo   2.5 (%date% %time%) add requirement packages_versions>>%my_archive_log%
echo ---------------------------------------- >>%my_archive_log%

echo python -m pip install -r %my_requirements% -c %my_constraints% --pre  --no-index --trusted-host=None --find-links=%my_find_links%  
echo python -m pip install -r %my_requirements% -c %my_constraints% --pre  --no-index --trusted-host=None --find-links=%my_find_links%  >>%my_archive_log%
echo if pip doesn't work, check the path of %my_WINPYDIRBASE%

python -m pip install -r %my_requirements% -c %my_constraints% --pre  --no-index --trusted-host=None --find-links=%my_find_links%  >>%my_archive_log%


echo ----------------------------------------
echo   2.9 (%date% %time%) archive success
echo ----------------------------------------
echo ---------------------------------------- >>%my_archive_log%
echo   2.9 (%date% %time%) archive success          >>%my_archive_log%
echo ---------------------------------------- >>%my_archive_log%

echo %target_python_exe% -m pip freeze>%my_archive_log%.packages_versions.txt>>%my_archive_log%
%target_python_exe% -m pip freeze>%my_archive_log%.packages_versions.txt


echo ----------------------------------------
echo 3.0 (%date% %time%) Generate Changelog and binaries
echo ----------------------------------------
echo ---------------------------------------- >>%my_archive_log%
echo 3.0 (%date% %time%) Generate Changelog and binaries >>%my_archive_log%
echo ---------------------------------------- >>%my_archive_log%

rem build final changelog and binaries, using create_installer='%my_create_installer%', remove_existing=False , remove : requirements, toolsdirs and docdirs

set path=%my_original_path%
echo cd /D %~dp0>>%my_archive_log%
cd /D %~dp0

echo call %my_buildenv%\scripts\env.bat>>%my_archive_log%
call %my_buildenv%\scripts\env.bat
set

echo python.exe  -c "from make import *;make_all(%my_release%, '%my_release_level%', pyver='%my_pyver%', basedir=r'%my_basedir%', verbose=True, architecture=%my_arch%, flavor='%my_flavor%', install_options=r'%my_install_options%', find_links=r'%my_find_links%', source_dirs=r'%my_source_dirs%', create_installer='%my_create_installer%', remove_existing=False, python_target_release='%my_python_target_release%')">>%my_archive_log%

echo python.exe  -c "from make import *;make_all(%my_release%, '%my_release_level%', pyver='%my_pyver%', basedir=r'%my_basedir%', verbose=True, architecture=%my_arch%, flavor='%my_flavor%', install_options=r'%my_install_options%', find_links=r'%my_find_links%', source_dirs=r'%my_source_dirs%', create_installer='%my_create_installer%', remove_existing=False, python_target_release='%my_python_target_release%')"

python.exe  -c "from make import *;make_all(%my_release%, '%my_release_level%', pyver='%my_pyver%', basedir=r'%my_basedir%', verbose=True, architecture=%my_arch%, flavor='%my_flavor%', install_options=r'%my_install_options%', find_links=r'%my_find_links%', source_dirs=r'%my_source_dirs%', create_installer='%my_create_installer%', remove_existing=False, python_target_release='%my_python_target_release%')">>%my_archive_log%


echo ----------------------------------------
echo (%date% %time%) END OF creation
echo ----------------------------------------
echo ---------------------------------------- >>%my_archive_log%
echo (%date% %time%) END OF creation>>%my_archive_log%
echo ---------------------------------------- >>%my_archive_log%

rem show logs
start notepad.exe %my_archive_log%

start notepad.exe %my_archive_log%.packages_versions.txt

set path=%my_original_path%
rem pause
