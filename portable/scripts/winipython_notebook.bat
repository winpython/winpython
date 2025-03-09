@echo off
call "%~dp0env_for_icons.bat" %*
"%WINPYDIR%\scripts\jupyter-notebook.exe" %*