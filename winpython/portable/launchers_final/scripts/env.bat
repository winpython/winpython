@echo off
rem read init variables
FOR /F "usebackq tokens=1,2 delims==" %%G IN ("%~dp0env.ini") DO (set %%G=%%H) 

set WINPYDIRBASE=%~dp0..

rem get a normalized path
set WINPYDIRBASETMP=%~dp0..
pushd %WINPYDIRBASETMP%
set WINPYDIRBASE=%__CD__%
if "%WINPYDIRBASE:~-1%"=="\" set WINPYDIRBASE=%WINPYDIRBASE:~0,-1%
set WINPYDIRBASETMP=
popd

set WINPYDIR=%WINPYDIRBASE%\python
set PYTHON=%WINPYDIR%\python.exe

set PYTHONIOENCODING=utf-8
set HOME=%WINPYDIRBASE%\settings

rem Remove all double quotes
set PATH_CLEANED=%PATH:"=%
echo ";%PATH_CLEANED%;" | %WINDIR%\system32\find.exe /C /I ";%WINPYDIR%\;" >nul
if %ERRORLEVEL% NEQ 0 set "PATH=%WINPYDIR%\;%WINPYDIR%\Scripts;%WINPYDIR%\..\t;%WINPYDIR%\..\n;%PATH%"

set PATH_CLEANED=
