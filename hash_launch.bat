call C:\WPy64-3890\scripts\env.bat

cd %~dp0

rem echo %date% %time%>>gdc_counting.txt
python hash.py %1 >>hash_counting_%date:/=_%.txt

start notepad.exe hash_counting_%date:/=_%.txt
