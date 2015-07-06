rem this replace running manually from spyder the make.py 
rem to launch from a winpython module 'make' directory  

set my_original_path_one=%path%
 
call %~dp0\generate_winpython_distros34.bat

set path=%my_original_path_one%


call %~dp0\generate_winpython_distros27.bat


pause