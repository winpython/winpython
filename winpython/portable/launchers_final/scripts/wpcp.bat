@echo off
call "%~dp0env_for_icons.bat" %*
cmd.exe /k "echo wppm & "%WINPYDIR%\python.exe" -m wppm" %*