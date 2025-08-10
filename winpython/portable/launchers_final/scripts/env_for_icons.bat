@echo off
call "%~dp0env.bat"

rem you can use winpython.ini to change defaults
FOR /F "delims=" %%i IN ('""%WINPYDIR%\python.exe" "%~dp0WinpythonIni.py"  %*"') DO set winpythontoexec=%%i
%winpythontoexec%set winpythontoexec=

rem Change of directory only if we are in a launcher directory
if  "%__CD__%scripts\"=="%~dp0"  cd/D %WINPYWORKDIR1%
if  "%__CD__%"=="%~dp0"          cd/D %WINPYWORKDIR1%

if not exist "%HOME%\.spyder-py%WINPYVER:~0,1%"  mkdir "%HOME%\.spyder-py%WINPYVER:~0,1%"
if not exist "%HOME%\.spyder-py%WINPYVER:~0,1%\workingdir" echo %HOME%\Notebooks>"%HOME%\.spyder-py%WINPYVER:~0,1%\workingdir"
