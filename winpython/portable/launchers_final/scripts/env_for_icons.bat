@echo off
call "%~dp0env.bat"
setlocal enabledelayedexpansion
rem you can use winpython.ini to change defaults
for /f "tokens=1,* delims==" %%A in (
    'cmd /c ""%~dp0..\python\python.exe" "%~dp0WinpythonIni.py" %*"'
) do (
    set "key=%%A"
    set "value=%%B"
    set "!key!=!value!"
)

rem Change of directory only if we are in a launcher directory
if  "%__CD__%scripts\"=="%~dp0"  cd/D %WINPYWORKDIR1%
if  "%__CD__%"=="%~dp0"          cd/D %WINPYWORKDIR1%
