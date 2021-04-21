call C:\WinPython-64bit-3.6.8.0\scripts\env.bat

cd %~dp0

rem echo %date% %time%>>gdc_counting.txt
python hash.py %1 >>hash_counting_%date:/=_%.txt

start notepad.exe hash_counting_%date:/=_%.txt
