rem first line check
echo  keep me in ansi =utf-8 without BOM  (notepad plus plus or win10 screwing up for compatibility)

rem *****************************
rem 2021-05-23: use "%PYTHON%" for the executable instead of "%WINPYDIR%\python.exe"
rem 2022-10-19 patch cpython bug https://github.com/winpython/winpython/issues/1121
rem 2024-09-15a: compactify for lisiblity
rem *****************************

rem algorithm:
rem 0.0 Initialize target environment  
rem 1.0 Do cosmetic complements
rem 2.0 Do active patches 
rem 3.0 Don't do patches in reserve (examples)
rem 3.0 clean-ups (to move to upper stage)
rem 4.0 summary of packages

@echo off 
echo ----------------------------------------
echo 0.0 (%date% %time%) Initialize variables  
echo ----------------------------------------

rem %1 is the WINPYDIRBASE being prepared, (names winpydir of python build batch) (like "...bd37\buPyPy\WPy64-37100b2")
rem this .bat is placed at root (buildir34, buildir34\FlavorJulia, ...)
set origin=%~dp0
set new_winpydir=%1

echo new_winpydir=%new_winpydir%
cd /d %new_winpydir%

call scripts\env.bat
@echo off

echo ----------------------------------------
echo 1.0 (%date% %time%) Do cosmetic complements 
echo ----------------------------------------

echo finish install seaborn iris example
rem ----------------------------------------
if exist  "%WINPYDIR%\Lib\site-packages\seaborn" "%PYTHON%" -c "import seaborn as sns;sns.set();sns.load_dataset('iris')"


echo ----------------------------------------
echo 2.0 (%date% %time%) Do Active patchs
echo ----------------------------------------



rem 2022-10-19 patch cpython bug https://github.com/winpython/winpython/issues/1121

set qt56p=%WINPYDIR%\Lib\idlelib\macosx.py
if exist  "%qt56p%" (
  "%PYTHON%" -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%WINPYDIR%\Lib\idlelib\macosx.py', 'from test.support ', '#stonebig  patch cpython/pull/98313/files:  from test.support' )"
  echo "DID I patch numba%??"
) else (
  echo "I DIDN'T patch of numba !"
)


goto the_end

echo ----------------------------------------
echo 2.0 (%date% %time%) not active patchs example (reserve)
echo ----------------------------------------



rem ----------------------------------------
echo 2021-04-17 patch jupyter_lsp-1.1.4
rem see https://github.com/krassowski/jupyterlab-lsp/pull/580/files

rem in DOS, the variable must be set befor the parenthesis block....
set this_source='%WINPYDIR%\Lib\site-packages\jupyter_lsp\virtual_documents_shadow.py'
if exist  "%WINPYDIR%\Lib\site-packages\jupyter_lsp-1.1.4.dist-info" (
   echo "**%this_source%**"
   "%PYTHON%" -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r%this_source%, 'read_text()', 'read_text(encoding='+chr(39)+'utf-8'+chr(39)+')' )"
   "%PYTHON%" -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r%this_source%, 'join(self.lines))', 'join(self.lines), encoding='+chr(39)+'utf-8'+chr(39)+')' )"
) 

rem ----------------------------------------
rem 2020-05-15 patch jedi-0.17.0
																															
if exist  "%WINPYDIR%\Lib\site-packages\jedi-0.17.0.dist-info" copy/Y "C:\WinP\tempo_fixes\Jedi-0.17.0\api\__init__.py" "%WINPYDIR%\Lib\site-packages\Jedi-0.17.0\api\__init__.py"

rem ----------------------------------------





echo 2019-10-22 Spyder tweaks moved at the end as suspicion of problem creating (on Python-3.8)
rem ----------------------------------------
echo .spyder3\temp.py suspected of creating issue east of Italia
echo see https://groups.google.com/forum/#!topic/spyderlib/dH5VXlTc30s

if  exist "%WINPYDIR%\..\settings\.spyder-py3\temp.py" del  "%WINPYDIR%\..\settings\.spyder-py3\temp.py"

rem ----------------------------------------
rem 2023-02-12: paching pip-23.0.0 pip\_vend_r\rich patch cpython bug https://github.com/pypa/pip/issues/11798

if exist  "%WINPYDIR%\Lib\site-packages\pip-23.0.dist-info" (
   echo "coucou Pip-23.0 crashing  _vendor/rich"
   copy/Y "C:\WinP\tempo_fixes\pip\_vendor\rich\_win32_console.py" "%WINPYDIR%\site-packages\pip\_vendor\rich\_win32_console.py"
)

:the_end

echo ----------------------------------------
rem 3.0 (%date% %time%) clean-ups (to move to upper stage)
echo ----------------------------------------

echo JUPYTERLAB_DIR=%JUPYTERLAB_DIR%  default is ~/.jupyter/lab
echo JUPYTERLAB_SETTINGS_DIR=%JUPYTERLAB_SETTINGS_DIR% , default is ~/.jupyter/lab/user-settings/
echo JUPYTERLAB_WORKSPACES_DIR=%JUPYTERLAB_WORKSPACES_DIR% , default is ~/.jupyter/lab/workspaces/

"%WINPYDIR%\Scripts\jupyter.exe" lab path

rem ----------------------------------------
echo clear jupyterlab staging (2018-03-09)

if exist "%WINPYDIR%\share\jupyter\lab\staging" rmdir /S /Q "%WINPYDIR%\share\jupyter\lab\staging"
rem if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab"  "%WINPYDIR%\Scripts\jupyter.exe" lab clean



rem see https://jupyter.readthedocs.io/en/latest/use/jupyter-directories.html
if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab" (
"%WINPYDIR%\Scripts\jupyter.exe" labextension list
"%WINPYDIR%\Scripts\jupyter.exe"  --paths  
)


echo ----------------------------------------
echo 4.0 (%date% %time%) Summary of packages 
echo ----------------------------------------


pip check



