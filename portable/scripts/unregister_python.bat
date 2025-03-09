@echo off
call "%~dp0env_for_icons.bat"
cd /D "%WINPYDIR%\Scripts"
"%WINPYDIR%\python.exe" "%WINPYDIR%\Lib\site-packages\winpython\unregister_python.py" %*