@echo off
call "%~dp0env_for_icons.bat" %*
rem "%WINPYDIR%\scripts\jupyter-lab.exe" %*
"%WINPYDIR%\python.exe" -m jupyter lab %*