call C:\WinPdev\WPy64-310111\scripts\env.bat

cd %~dp0

rem echo %date% %time%>>gdc_counting.txt
python -c "import sys;from winpython import hash; hash.print_hashes(sys.argv[1:])" %* >>hash_counting_%date:/=_%.txt
rem python hash.py %* >>hash_counting_%date:/=_%.txt

start notepad.exe hash_counting_%date:/=_%.txt
 