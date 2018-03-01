rem  this replace running manually from spyder the make.py 
rem  to launch from a winpython module 'make' directory 

set my_original_path=%path%
set my_buildenv=C:\winpython-64bit-3.4.3.7Qt5

set my_root_dir_for_builds=C:\Winp
set my_python_target=35
set my_pyver=3.5

set my_flavor=Qt5

set my_release=3
set my_release_level=

set my_install_options=--no-index --pre --trusted-host=None
set my_find_links=C:\Winp\packages.srcreq
set my_docsdirs=C:\Winp\bd35\docs

set my_arch=32

set tmp_reqdir=%my_root_dir_for_builds%\bd%my_python_target%

set my_requirements=%tmp_reqdir%\Qt5_requirements.txt


set my_source_dirs=C:\Winp\bd35\packages.win32.Qt5
set my_toolsdirs=C:\Winp\bd35\tools


set my_preclear_build_directory=Yes
call %~dp0\generate_a_winpython_distro.bat

set my_arch=64
set my_requirements=%tmp_reqdir%\Qt5_requirements64.txt
set my_source_dirs=C:\Winp\bd35\packages.win-amd64.Qt5
set my_toolsdirs=C:\Winp\bd35\tools64

set my_preclear_build_directory=No


call %~dp0\generate_a_winpython_distro.bat


pause