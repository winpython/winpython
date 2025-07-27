@echo off
call "%~dp0env.bat"

rem default is as before: Winpython ..\Notebooks
set WINPYWORKDIR=%WINPYDIRBASE%\Notebooks
set WINPYWORKDIR1=%WINPYWORKDIR%

rem if we have a file or directory in %1 parameter, we use that directory to define WINPYWORKDIR1
if not "%~1"=="" (
   if exist "%~1" (
      if exist "%~1\" (
         rem echo it is a directory %~1
	     set WINPYWORKDIR1=%~1
	  ) else (
	  rem echo  it is a file %~1, so we take the directory %~dp1
	  set WINPYWORKDIR1=%~dp1
	  )
   )
) else (
rem if it is launched from another directory than icon origin , we keep it that one echo %__CD__%
if not "%__CD__%"=="%~dp0" if not "%__CD__%scripts\"=="%~dp0" set  WINPYWORKDIR1="%__CD__%"
)
rem remove potential doublequote
set WINPYWORKDIR1=%WINPYWORKDIR1:"=%
rem remove some potential last \
if "%WINPYWORKDIR1:~-1%"=="\" set WINPYWORKDIR1=%WINPYWORKDIR1:~0,-1%

rem you can use winpython.ini to change defaults
FOR /F "delims=" %%i IN ('""%WINPYDIR%\python.exe" "%~dp0WinpythonIni.py""') DO set winpythontoexec=%%i
%winpythontoexec%set winpythontoexec=


rem Preventive Working Directories creation if needed
if not "%WINPYWORKDIR%"=="" if not exist "%WINPYWORKDIR%" mkdir "%WINPYWORKDIR%"
if not "%WINPYWORKDIR1%"=="" if not exist "%WINPYWORKDIR1%" mkdir "%WINPYWORKDIR1%"

rem Change of directory only if we are in a launcher directory
if  "%__CD__%scripts\"=="%~dp0"  cd/D %WINPYWORKDIR1%
if  "%__CD__%"=="%~dp0"          cd/D %WINPYWORKDIR1%

if not exist "%HOME%\.spyder-py%WINPYVER:~0,1%"  mkdir "%HOME%\.spyder-py%WINPYVER:~0,1%"
if not exist "%HOME%\.spyder-py%WINPYVER:~0,1%\workingdir" echo %HOME%\Notebooks>"%HOME%\.spyder-py%WINPYVER:~0,1%\workingdir"
