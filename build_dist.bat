rmdir /S /Q build
rmdir /S /Q dist
python setup.py build bdist_wininst --plat-name=win32
python setup.py build bdist_wininst --plat-name=win-amd64
del %WINPYTHONBASEDIR%\packages.win32\winpython-*.exe
del %WINPYTHONBASEDIR%\packages.win-amd64\winpython-*.exe
move dist\winpython-*.win-amd64.exe %WINPYTHONBASEDIR%\packages.win-amd64
move dist\winpython-*.win32.exe %WINPYTHONBASEDIR%\packages.win32
pause