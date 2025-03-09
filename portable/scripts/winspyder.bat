@echo off
call "%~dp0env_for_icons.bat" %*
"%WINPYDIR%\scripts\spyder.exe" %* -w "%WINPYWORKDIR1%" 