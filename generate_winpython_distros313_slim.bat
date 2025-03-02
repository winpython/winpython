rem  this replace running manually from spyder the make.py 
rem  to launch from a winpython module 'make' directory 

set my_original_path=%path%

set my_root_dir_for_builds=C:\Winp
set my_python_target=313
set my_pyver=3.13

set my_flavor=slim

set my_release=

set my_release_level=

rem set my_create_installer=False
set my_create_installer=nsis.zip
set my_create_installer=.7z
set my_create_installer=7zip

rem 2024-07-14: ask both the 7zip auto executable and the .7z simple archive
rem set my_create_installer=False
set my_create_installer=7zip.7z

set my_arch=64
set my_preclear_build_directory=Yes

set tmp_reqdir=%my_root_dir_for_builds%\bd%my_python_target%

rem ****** THREADING
rem 20240629: handle cython-3.23 as a pre-requirement

rem set my_requirements_pre=C:\WinP\bd313\requirements_pre.txt
rem set my_find_links_pre=C:\WinP\bd313\packages.win-amd64

rem ***** THREADING

set my_requirements=C:\Winp\bd313\requirements64_slim.txt

set my_find_links=C:\Winp\packages.srcreq

set my_source_dirs=C:\Winp\bd313\packages.win-amd64

set my_toolsdirs=C:\Winp\bdTools\Tools.dot

REM 2024-07-13:put back pandoc (so from 598Mo to 518Mo?)
set my_toolsdirs=C:\WinP\bdTools\tools64_pandoc_alone

set my_docsdirs=C:\WinP\bdDocs\docs.dot

set my_install_options=--no-index --pre --trusted-host=None

call %~dp0\generate_a_winpython_distro.bat


set my_arch=32
set my_preclear_build_directory=No

set my_source_dirs=C:\Winp\bd313\packages.win32

rem call %~dp0\generate_a_winpython_distro.bat


pause