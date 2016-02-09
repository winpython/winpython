rem  this replace running manually from spyder the make.py 
rem  to launch from a winpython module 'make' directory 

set my_original_path=%path%
set my_buildenv=D:\winpython-64bit-3.4.3.7Qt5

set my_root_dir_for_builds=D:\Winpython
set my_python_target=34
set my_pyver=3.4

set my_release=1

set my_release_level=build3

set my_flavor=

set my_arch=64
set my_preclear_build_directory=Yes


set tmp_reqdir=%my_root_dir_for_builds%\basedir%my_python_target%
set my_requirements=%tmp_reqdir%\requirements.txt %tmp_reqdir%\requirements2.txt %tmp_reqdir%\requirements3.txt

set my_find_links=D:\WinPython\packages.srcreq

set my_install_options=--no-index --pre --trusted-host=None
 
call %~dp0\generate_a_winpython_distro.bat

set my_arch=32
set my_preclear_build_directory=No
call %~dp0\generate_a_winpython_distro.bat


pause