@echo off
call "%~dp0env_for_icons.bat" %*
rem "%WINPYDIR%\scripts\jupyter-notebook.exe" %*
"%WINPYDIR%\python.exe" -m jupyter notebook %*