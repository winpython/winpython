rem  this replace running manually from spyder the make.py 
rem  to launch from a winpython module 'make' directory 

set my_original_path=%path%

set my_root_dir_for_builds=C:\Winp
set my_python_target=313
set my_pyver=3.13
set my_flavor=slim
set my_arch=64

rem settings delegated to generate_a_winpython_distro.bat
set my_release=
set my_release_level=

rem list of installers to create separated per dot: False=none, .zip=zip, .7z=.7z, 7zip=auto-extractible 7z
rem set my_create_installer=7zip.7z.zip
set my_create_installer=7zip.7z

set my_preclear_build_directory=Yes

set tmp_reqdir=%my_root_dir_for_builds%\bd%my_python_target%

set my_requirements=C:\Winp\bd313\requirements64_slim.txt
set my_source_dirs=C:\Winp\bd313\packages.win-amd64

set my_find_links=C:\Winp\packages.srcreq
set my_toolsdirs=C:\Winp\bdTools\Tools.dot

REM 2024-07-13:put back pandoc (so from 598Mo to 518Mo?)
set my_toolsdirs=C:\WinP\bdTools\tools64_pandoc_alone

set my_install_options=--no-index --pre --trusted-host=None

rem call %~dp0\generate_a_winpython_distro.bat
call %~dp0\generate_a_winpython_distropy.bat

pause