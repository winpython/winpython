rem this replace running manually from spyder the make.py 
rem to launch from a winpython module 'make' directory 

set my_original_path=%path%
set my_buildenv=D:\WinPython-64bit-3.4.3.3_b0

set my_root_dir_for_builds=D:\Winpython
set my_python_target=34
set my_pyver=3.4
set my_release=6
set my_flavor=

set my_arch=64
set my_preclear_build_directory=Yes
 
call %~dp0\generate_a_winpython_distro.bat

set my_arch=32
set my_preclear_build_directory=No
call %~dp0\generate_a_winpython_distro.bat


pause