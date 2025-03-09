rem  this replace running manually from spyder the make.py 
rem  to launch from a winpython module 'make' directory 

set my_original_path=%path%

set my_root_dir_for_builds=C:\Winp
set my_python_target=313
set my_pyver=3.13
set my_flavor=dot
set my_arch=64

rem settings delegated to generate_a_winpython_distro.bat
set my_release=
set my_release_level=

rem list of installers to create separated per dot: False=none, .zip=zip, .7z=.7z, 7zip=auto-extractible 7z
set my_create_installer=7zip.7z.zip

set my_preclear_build_directory=Yes

set tmp_reqdir=%my_root_dir_for_builds%\bd%my_python_target%

set my_requirements=C:\Winp\bd313\dot_requirements.txt
set my_source_dirs=C:\Winp\bd313\packages.win-amd64

set my_find_links=C:\Winp\packages.srcreq
set my_toolsdirs=C:\Winp\bdTools\Tools.dot
set my_docsdirs=C:\WinP\bdDocs\docs.dot

set my_install_options=--no-index --pre --trusted-host=None

call %~dp0\generate_a_winpython_distro.bat


pause