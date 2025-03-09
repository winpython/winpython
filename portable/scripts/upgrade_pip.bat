@echo off
call "%~dp0env.bat"
echo this will upgrade pip with latest version, then patch it for WinPython portability ok ?
pause
"%WINPYDIR%\python.exe" -m pip install --upgrade pip
"%WINPYDIR%\python.exe" -c "from winpython import wppm;dist=wppm.Distribution(r'%WINPYDIR%');dist.patch_standard_packages('pip', to_movable=True)
pause