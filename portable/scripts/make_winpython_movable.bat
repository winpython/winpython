@echo off
call "%~dp0env.bat"
echo patch pip and current launchers for move

"%WINPYDIR%\python.exe" -c "from winpython import wppm;dist=wppm.Distribution(r'%WINPYDIR%');dist.patch_standard_packages('pip', to_movable=True)"
pause