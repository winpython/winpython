@echo off
call "%~dp0env_for_icons.bat" %*
rem backward compatibility for non-ptpython users
if exist "%WINPYDIR%\Lib\site-packages\ptpython" (
    "%WINPYDIR%\python.exe" -m ptpython %*
) else (
    "%WINPYDIR%\python.exe"  %*
)