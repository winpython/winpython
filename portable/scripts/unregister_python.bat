@echo off
call "%~dp0env_for_icons.bat"
"%WINPYDIR%\python.exe" "%WINPYDIR%\Lib\site-packages\winpython\associate.py"  --unregister
