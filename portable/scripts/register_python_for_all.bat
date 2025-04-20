@echo off
call "%~dp0env.bat"
"%WINPYDIR%\python.exe" "%WINPYDIR%\Lib\site-packages\winpython\associate.py" --all
