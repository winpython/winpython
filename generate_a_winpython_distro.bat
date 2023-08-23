rem  to launch from a winpython package directory, where 'make.py' is
@echo on

rem *****************************
rem 2020-07-05: install msvc_runtime before packages that may want to compile
rem 2020-12-05 : add a constrints.txt file from a recent pip list
rem 2021-03-20 : track successes packages combination are archived for future contraint update
rem 2021-04-22 : path PyPy3 (as we don't try to copy PyPy3.exe to Python.exe) 
rem 2023-08-21a: add a pre_step with my_requirements_pre.txt + my_find_links_pre
rem *****************************

rem algorithm:
rem 0.0 Initialize variables  
rem 1.0 Do 2021-04-22 : patch PyPy3 (as we don't try to copy PyPy3.exe to Python.exe) 
rem 2021-04-22b: Patch PyPy3, give '%my_python_target_release%' to make (otherwise known only after unzip)
rem 2 a Pre-clear of previous build infrastructure
rem 2.0 Create a new build
rem   2.1 Create basic build infrastructure 
rem   2.2 check infrastructure is in place
rem   2.3 add mandatory packages for build
rem   2.4 add packages pre_requirements (if any)
rem   2.5 add requirement packages
rem   2.8 post-build (if specific workarounds)
rem   2.9 archive success
rem 3.0 Generate Changelog and binaries



rem  this is pre-initialised per the program calling this .bat
rem  set my_original_path=%path%
rem  set my_root_dir_for_builds=D:\WinP

rem  set my_python_target=34
rem  set my_pyver=3.4
rem  set my_flavor=mkl
rem  set my_release=84


rem set my_find_link=C:\WinP\packages.srcreq

rem this is optionaly pre-initialised per the calling program (simpler to manage here)
rem set my_release_level=


echo ------------------
echo 0.0 Initialize variables  
echo ------------------

if "%my_release_level%"=="" set my_release_level=b4

set my_basedir=%my_root_dir_for_builds%\bd%my_python_target%

set my_buildenv=C:\WinPdev\WPy64-3890

if "%my_constraints%"=="" set my_constraints=C:\WinP\constraints.txt

rem  2021-04-22 : path PyPy3 (as we don't try to copy PyPy3.exe to Python.exe) 
if "%target_python_exe%"=="" set target_python_exe=python.exe


if %my_python_target%==37 (
   set my_python_target_release=3712
   set my_release=1
)
if %my_python_target%==38 (
   set my_python_target_release=3812
   set my_release=1
)
if %my_python_target%==39 (
   set my_python_target_release=3915
   set my_release=1
)

if %my_python_target%==310 (
   set my_python_target_release=31011
   set my_release=2
)


if %my_python_target%==311 (
   set my_python_target_release=3114
   set my_release=1
)


if %my_python_target%==312 (
   set my_python_target_release=3120
   set my_release=0
)



rem **** 2018-10-30 create_installer **
if "%my_create_installer%"=="" set my_create_installer=True

rem  set my_flavor=Slim

rem  set my_arch=32
rem  set my_preclear_build_directory=Yes

rem 20230821 add a requirement_pre.txt + 
rem set my_requirements_pre=C:\WinP\bd311\requirements_mkl_pre.txt
rem set my_find_links_pre=C:\WinP\packages_mkl.srcreq

rem  set my_requirements=C:\Winpents=d:\my_req1.txt
rem  set my_find_links=D:\WinPython\packages.srcreq

rem  set my_source_dirs=D:\WinPython\bd34\packages.src D:\WinPython\bd34\packages.win32.Slim
rem  set my_toolsdirs=D:\WinPython\bd34\Tools.Slim
rem  set my_docsdirs=D:\WinPython\bd34\docs.Slim

rem  set my_install_options=--no-index --pre

set my_day=%date:/=-%
set my_time=%time:~0,5%
set my_time=%my_time::=_%

rem  was the bug 
set my_time=%my_time: =0%

set my_archive_dir=%~dp0WinPython_build_logs
if not exist %my_archive_dir% mkdir %my_archive_dir%

set my_archive_log=%my_archive_dir%\build_%my_pyver%._.%my_release%%my_flavor%_%my_release_level%_of_%my_day%_at_%my_time%.txt


echo ===============
echo preparing winPython for %my_pyver% (%my_python_target%)release %my_release%%my_flavor% (%my_release_level%) *** %my_arch% bit *** 
echo %date% %time%
echo ===============
echo ===============>>%my_archive_log%
echo preparing winPython for %my_pyver% (%my_python_target%)release %my_release%%my_flavor% (%my_release_level%) *** %my_arch% bit ***>>%my_archive_log%
echo %date% %time%>>%my_archive_log%
echo ===============>>%my_archive_log%


if not "%my_preclear_build_directory%"=="Yes" goto no_preclear


echo ------------------
echo 1.0 Do a Pre-clear of previous build infrastructure  
echo ------------------
echo ------------------>>%my_archive_log%
echo 1.0 Do a Pre-clear of previous build infrastructure>>%my_archive_log%
echo %date% %time%     >>%my_archive_log%
echo ------------------>>%my_archive_log%

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

e

echo ----------------------------- 
echo 2.0 Create a new build 
echo ---------------------------- >>%my_archive_log%
echo 2.0 Create a new build>>%my_archive_log%
echo %date% %time%     >>%my_archive_log%
echo ---------------------------- >>%my_archive_log%


echo cd /D %~dp0>>%my_archive_log%
cd /D %~dp0

echo set path=%my_original_path%>>%my_archive_log%
set path=%my_original_path%

echo call %my_buildenv%\scripts\env.bat>>%my_archive_log%
call %my_buildenv%\scripts\env.bat

echo ----------------------------- 
echo   2.1 Create basic build infrastructure 
echo   %date% %time%                
echo -----------------------------
echo ----------------------------->>%my_archive_log%
echo   2.1 Create basic build infrastructure>>%my_archive_log%
echo   %date% %time%                >>%my_archive_log%
echo ----------------------------->>%my_archive_log%

rem 2019-10-22 new age step1
rem we don't use requirements 
rem we don't create installer at first path
rem we use legacy python build cd /D %~dp0

set my_buildenv_path=%path%

echo python.exe  -c "from make import *;make_all(%my_release%, '%my_release_level%', pyver='%my_pyver%', basedir=r'%my_basedir%', verbose=True, architecture=%my_arch%, flavor='%my_flavor%', install_options=r'%my_install_options%', find_links=r'%my_find_links%', source_dirs=r'%my_source_dirs%', toolsdirs=r'%my_toolsdirs%', docsdirs=r'%my_docsdirs%', create_installer='False', python_target_release='%my_python_target_release%')">>%my_archive_log%
echo python.exe  -c "from make import *;make_all(%my_release%, '%my_release_level%', pyver='%my_pyver%', basedir=r'%my_basedir%', verbose=True, architecture=%my_arch%, flavor='%my_flavor%', install_options=r'%my_install_options%', find_links=r'%my_find_links%', source_dirs=r'%my_source_dirs%', toolsdirs=r'%my_toolsdirs%', docsdirs=r'%my_docsdirs%', create_installer='False', python_target_release='%my_python_target_release%')"
rem pause
python.exe  -c "from make import *;make_all(%my_release%, '%my_release_level%', pyver='%my_pyver%', basedir=r'%my_basedir%', verbose=True, architecture=%my_arch%, flavor='%my_flavor%', install_options=r'%my_install_options%', find_links=r'%my_find_links%', source_dirs=r'%my_source_dirs%', toolsdirs=r'%my_toolsdirs%', docsdirs=r'%my_docsdirs%', create_installer='False', python_target_release='%my_python_target_release%')">>%my_archive_log%

rem old one
rem echo python.exe  -c "from make import *;make_all(%my_release%, '%my_release_level%', pyver='%my_pyver%', basedir=r'%my_basedir%', verbose=True, architecture=%my_arch%, flavor='%my_flavor%', requirements=r'%my_requirements%', install_options=r'%my_install_options%', find_links=r'%my_find_links%', source_dirs=r'%my_source_dirs%', toolsdirs=r'%my_toolsdirs%', docsdirs=r'%my_docsdirs%', create_installer='%my_create_installer%')">>%my_archive_log%


echo -----------------------------
echo   2.2 check infrastructure is in place
echo   %date% %time%                
echo ----------------------------- 
echo ----------------------------->>%my_archive_log%
echo   2.2 check infrastructure is in place>>%my_archive_log%
echo   %date% %time%                >>%my_archive_log%
echo ----------------------------->>%my_archive_log%
rem 2019-10-22 new age step2
rem we use final environment to install requirements
set path=%my_original_path%

@echo on
set my_WINPYDIRBASE=%my_root_dir_for_builds%\bd%my_python_target%\bu%my_flavor%\Wpy%my_arch%-%my_python_target_release%%my_release%%my_release_level%

set WINPYDIRBASE=%my_WINPYDIRBASE% 

rem D/2020-07-04: poka-yoke
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
rem F/2020-07-04: poka-yoke

call %my_WINPYDIRBASE%\scripts\env.bat
set
echo beg of step 2/3
rem ok no pause 

echo -----------------------------
echo 2.3 add mandatory packages for build
echo %date% %time%                
echo -----------------------------
echo ----------------------------->>%my_archive_log%
echo 2.3 add mandatory packages for build>>%my_archive_log%
echo %date% %time%                >>%my_archive_log%
echo ----------------------------->>%my_archive_log%
rem D/2020-07-05: install msvc_runtime before packages that may want to compile
echo pip install msvc_runtime --pre  --no-index --trusted-host=None  --find-links=%my_find_links%  --upgrade
echo pip install msvc_runtime --pre  --no-index --trusted-host=None  --find-links=%my_find_links%  --upgrade>>%my_archive_log%
pip install msvc_runtime --pre  --no-index --trusted-host=None  --find-links=%my_find_links%  --upgrade
rem F/2020-07-05: install msvc_runtime before packages that may want to compile


rem D/2023-08-21a: add a pre_step with my_requirements_pre.txt + my_find_links_pre

echo -----------------------------
echo   2.4 add  packages pre_requirements (if any)  
echo   %date% %time%                
echo -----------------------------
echo ----------------------------->>%my_archive_log%
echo   2.4 add  packages pre_requirements (if any)  
echo   %date% %time%                >>%my_archive_log%
echo ----------------------------->>%my_archive_log%rem F/20230821 add a pre_step with my_requirements_pre.txt + my_find_links_pre

if not "Z%my_requirements_pre%Z"=="ZZ" (

   rem 2023-08-21a: add a pre_step with my_requirements_pre.txt + my_find_links_pre
if "%my_find_links_pre%"=="" set my_find_links_pre=%my_find_links%

echo pip install -r %my_requirements_pre% -c %my_constraints% --pre  --no-index --trusted-host=None --find-links=%my_find_links_pre%  --upgrade %new_resolver%
echo pip install -r %my_requirements_pre% -c %my_constraints%  --pre  --no-index --trusted-host=None --find-links=%my_find_links_pre%  --upgrade %new_resolver%>>%my_archive_log%
echo if pip doesn't work, check the path of %my_WINPYDIRBASE%

pip install -r %my_requirements_pre% -c  %my_constraints%   --pre  --no-index --trusted-host=None --find-links=%my_find_links_pre%  --upgrade %new_resolver%>>%my_archive_log%
)
else
(
echo no packages pre_requirements   
echo no packages pre_requirements>>%my_archive_log%
)
rem F/2023-08-21a: add a pre_step with my_requirements_pre.txt + my_find_links_pre

echo -----------------------------
echo   2.5 add requirement packages
echo   %date% %time%                
echo -----------------------------
echo ----------------------------->>%my_archive_log%
echo   2.5 add requirement packages_versions>>%my_archive_log%
echo   %date% %time%                >>%my_archive_log%
echo ----------------------------->>%my_archive_log%

echo pip install -r %my_requirements% -c %my_constraints% --pre  --no-index --trusted-host=None --find-links=%my_find_links%  --upgrade %new_resolver%
echo pip install -r %my_requirements% -c %my_constraints% --pre  --no-index --trusted-host=None --find-links=%my_find_links%  --upgrade %new_resolver%>>%my_archive_log%
echo if pip doesn't work, check the path of %my_WINPYDIRBASE%


rem 2020-12-05 : add a constraints.txt file from a recent pip list
pip install -r %my_requirements% -c %my_constraints% --pre  --no-index --trusted-host=None --find-links=%my_find_links%  --upgrade %new_resolver%>>%my_archive_log%

echo mid of step 2/3

echo -----------------------------
echo   2.8 post-build (if specific workarounds)
echo   %date% %time%                
echo -----------------------------
echo ----------------------------->>%my_archive_log%
echo   2.8 post-build (if specific workarounds)>>%my_archive_log%
echo   %date% %time%                >>%my_archive_log%
echo ----------------------------->>%my_archive_log%
rem finalize
@echo on
call  %my_basedir%\run_complement_newbuild.bat %my_WINPYDIRBASE%
echo end of step 2/3
echo end of step 2/3>>%my_archive_log%
rem pause

rem *****************************
rem 2021-03-20 : track successes packages combination are archived for future contraint update
rem *****************************
echo   -----------------------------
echo   2.9 archive success
echo   %date% %time%                
echo -----------------------------
echo ----------------------------->>%my_archive_log%
echo   2.9 archive success          >>%my_archive_log%
echo   %date% %time%                >>%my_archive_log%
echo ----------------------------->>%my_archive_log%
echo %target_python_exe% -m pip freeze>%my_archive_log%.packages_versions.txt>>%my_archive_log%

%target_python_exe% -m pip freeze>%my_archive_log%.packages_versions.txt


echo -----------------------------
echo 3.0 Generate Changelog and binaries
echo -----------------------------
echo ----------------------------->>%my_archive_log%
echo 3.0 Generate Changelog and binaries >>%my_archive_log%
echo %date% %time%                >>%my_archive_log%
echo ----------------------------->>%my_archive_log%

rem build final changelog and binaries, using create_installer='%my_create_installer%', remove_existing=False , remove : requirements, toolsdirs and docdirs

set path=%my_original_path%
echo cd /D %~dp0>>%my_archive_log%
cd /D %~dp0

echo call %my_buildenv%\scripts\env.bat>>%my_archive_log%
call %my_buildenv%\scripts\env.bat
set

echo python.exe  -c "from make import *;make_all(%my_release%, '%my_release_level%', pyver='%my_pyver%', basedir=r'%my_basedir%', verbose=True, architecture=%my_arch%, flavor='%my_flavor%', install_options=r'%my_install_options%', find_links=r'%my_find_links%', source_dirs=r'%my_source_dirs%', create_installer='%my_create_installer%', remove_existing=False, python_target_release='%my_python_target_release%')">>%my_archive_log%
echo python.exe  -c "from make import *;make_all(%my_release%, '%my_release_level%', pyver='%my_pyver%', basedir=r'%my_basedir%', verbose=True, architecture=%my_arch%, flavor='%my_flavor%', install_options=r'%my_install_options%', find_links=r'%my_find_links%', source_dirs=r'%my_source_dirs%', create_installer='%my_create_installer%', remove_existing=False, python_target_release='%my_python_target_release%')"
rem pause
python.exe  -c "from make import *;make_all(%my_release%, '%my_release_level%', pyver='%my_pyver%', basedir=r'%my_basedir%', verbose=True, architecture=%my_arch%, flavor='%my_flavor%', install_options=r'%my_install_options%', find_links=r'%my_find_links%', source_dirs=r'%my_source_dirs%', create_installer='%my_create_installer%', remove_existing=False, python_target_release='%my_python_target_release%')">>%my_archive_log%

echo ===============
echo END OF creation
echo ===============
echo ===============>>%my_archive_log%
echo END OF creation>>%my_archive_log%
echo %date% %time%  >>%my_archive_log%
echo ===============>>%my_archive_log%

rem show logs
start notepad.exe %my_archive_log%

rem 2021-03-20 : track successes packages combination are archived for future contraint update
start notepad.exe %my_archive_log%.packages_versions.txt

set path=%my_original_path%
rem pause