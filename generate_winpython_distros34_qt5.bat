rem  this replace running manually from spyder the make.py 
rem  to launch from a winpython module 'make' directory 

set my_original_path=%path%
set my_buildenv=C:\winpython-64bit-3.4.3.7Qt5

set my_root_dir_for_builds=C:\Winpython
set my_python_target=34
set my_pyver=3.4

set my_release=2

set my_release_level=

set my_flavor=Qt5


set my_arch=32
set my_preclear_build_directory=Yes

set tmp_reqdir=%my_root_dir_for_builds%\basedir%my_python_target%
rem set my_requirements=%tmp_reqdir%\Qt5_requirements.txt %tmp_reqdir%\Qt5_requirements2.txt %tmp_reqdir%\Qt5_requirements3.txt
set my_requirements=%tmp_reqdir%\Qt5_requirements.txt

set my_find_links=C:\WinPython\packages.srcreq

set my_source_dirs=C:\WinPython\basedir34\packages.win32.Qt5
set my_toolsdirs=C:\WinPython\basedir34\tools
set my_docsdirs=C:\WinPython\basedir34\docs


set my_install_options=--no-index --pre --trusted-host=None

call %~dp0\generate_a_winpython_distro.bat

set my_arch=64
set my_preclear_build_directory=No


set my_source_dirs=C:\WinPython\basedir34\packages.win-amd64.Qt5
set my_toolsdirs=C:\WinPython\basedir34\tools



call %~dp0\generate_a_winpython_distro.bat


pause