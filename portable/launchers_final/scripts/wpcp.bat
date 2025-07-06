@echo off
call "%~dp0env_for_icons.bat" %*
rem cmd.exe /k "echo wppm & wppm" %*
cmd.exe /k "echo wppm & python -m wppm" %*