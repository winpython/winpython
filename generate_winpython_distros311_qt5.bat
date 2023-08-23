rem  this replace running manually from spyder the make.py 
rem  to launch from a winpython module 'make' directory 

set my_original_path=%path%

set my_root_dir_for_builds=C:\WinP
set my_python_target=311
set my_pyver=3.11

set my_flavor=

set my_release=0

set my_release_level=

rem set my_create_installer=False
set my_create_installer=nsis.zip
set my_create_installer=7zip

set my_arch=64
set my_preclear_build_directory=Yes

set tmp_reqdir=%my_root_dir_for_builds%\bd%my_python_target%

set my_requirements=C:\WinP\bd311\Qt5_requirements64.txt

set my_find_links=C:\WinP\packages.srcreq

set my_source_dirs=C:\WinP\bd311\packages.win-amd64
set my_toolsdirs=C:\WinP\bdTools\tools64
set my_docsdirs=C:\WinP\bdDocs\docs
set my_install_options=--no-index --pre --trusted-host=None

call %~dp0\generate_a_winpython_distro.bat


pause