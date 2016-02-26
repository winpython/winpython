call D:\WinPython-64bit-3.4.3.7Qt5\scripts\env.bat

cd %~dp0

echo %date% %time%>>gdc_counting.txt
python hash.py %1 >>hash_counting_%date:/=_%.txt

start notepad.exe hash_counting_%date:/=_%.txt
