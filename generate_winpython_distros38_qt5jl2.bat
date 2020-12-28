rem  this replace running manually from spyder the make.py 
rem  to launch from a winpython module 'make' directory 

set my_original_path=%path%
set my_buildenv=C:\winpython-64bit-3.4.3.7Qt5

set my_root_dir_for_builds=C:\Winp
set my_python_target=38
set my_pyver=3.8

set my_flavor=

set my_release=0

set my_release_level=

rem set my_create_installer=False
set my_create_installer=nsis.zip
set my_create_installer=7zip

set my_install_options=--no-index --pre --trusted-host=None
set my_find_links=C:\Winp\packages.srcreq
set my_docsdirs=C:\WinP\bdDocs\docs

set my_arch=32

set tmp_reqdir=%my_root_dir_for_builds%\bd%my_python_target%

set my_requirements=C:\Winp\bd38\Qt5_requirements.txt


set my_source_dirs=C:\Winp\bd38\packages.win32
set my_toolsdirs=C:\Winp\bdTools\Tools

rem set my_preclear_build_directory=Yes
rem call %~dp0\generate_a_winpython_distro.bat

set my_arch=64
set my_requirements=C:\Winp\bd38\Qt5_requirements64jl2.txt
set jupyterlab2=1
set my_source_dirs=C:\Winp\bd38\packages.win-amd64
set my_toolsdirs=C:\Winp\bdTools\Tools64

set my_preclear_build_directory=Yes


call %~dp0\generate_a_winpython_distro.bat


pause