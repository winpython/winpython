@echo off
call "%~dp0env_for_icons.bat" %*
rem "%WINPYDIR%\python.exe" "%WINPYDIR%\Lib\idlelib\idle.pyw" %*
"%WINPYDIR%\python.exe" -m idlelib %*