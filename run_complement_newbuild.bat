rem first line check
echo  keep me in ansi =utf-8 without BOM  (notepad plus plus or win10 screwing up for compatibility)

rem 2021-05-23: use "%PYTHON%" for the executable instead of "%WINPYDIR%\python.exe"
rem 2022-10-19 patch cpython bug https://github.com/winpython/winpython/issues/1121
 
rem if build error, launch "WinPython Command Prompt.exe" dos ico, then try manual install of requirements.txt 
rem that is:  pip install --pre  --no-index --trusted-host=None --find-links=C:\WinP\packages.srcreq -c C:\WinP\constraints.txt -r   C:\WinP\bd39\requirements_test.txt Qt5_requirements64.txt Cod_requirements64.txt
rem python -m pip freeze>C:\WinP\bd39\req_test150.txt between intermediate steps
rem 
rem           ( drag & drop "requirements.txt" file in the dos window a the end of the line, to get full path)
rem then drag & drop "run_complement_newbuild.bat" file in the dos window and launch it

@echo off 
rem %1 is WINPYDIRBASE being prepared, (names winpydir of python build batch) (like "...bd37\buPyPy\WPy64-37100b2")
rem this .bat is placed at root (buildir34, buildir34\FlavorJulia, ...)
set origin=%~dp0
set new_winpydir=%1

echo new_winpydir= ********%new_winpydir%***********************************************************
cd /d %new_winpydir%

call scripts\env.bat
@echo off

rem  * ==========================
echo * When Python has no mingwpy
rem  * ==========================
if not exist "%WINPYDIR%\Lib\site-packages\mingwpy" set pydistutils_cfg=%WINPYDIR%\..\settings\pydistutils.cfg
if not exist "%WINPYDIR%\Lib\site-packages\mingwpy" echo [config]>%pydistutils_cfg%



rem * =================
echo finish install seaborn iris example
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\seaborn" "%PYTHON%" -c "import seaborn as sns;sns.set();sns.load_dataset('iris')"


rem  ** Active patchs*************************************************************************************************



rem * ===========================
rem 2022-10-19 patch cpython bug https://github.com/winpython/winpython/issues/1121
rem * ===========================
set qt56p=%WINPYDIR%\Lib\idlelib\macosx.py
if exist  "%qt56p%" (
  "%PYTHON%" -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%WINPYDIR%\Lib\idlelib\macosx.py', 'from test.support ', '#stonebig  patch cpython/pull/98313/files:  from test.support' )"
  echo "DID I patch numba%??"
) else (
  echo "I DIDN'T patch of numba !"
)


rem  ** Example of live file replacement (not active)***********************************************************************************************

rem * ===========================
echo 2021-04-17 patch jupyter_lsp-1.1.4
rem see https://github.com/krassowski/jupyterlab-lsp/pull/580/files
rem * ===========================

rem in DOS, the variable must be set befor the parenthesis block....
set this_source='%WINPYDIR%\Lib\site-packages\jupyter_lsp\virtual_documents_shadow.py'
if exist  "%WINPYDIR%\Lib\site-packages\jupyter_lsp-1.1.4.dist-info" (
   echo "**%this_source%**"
   "%PYTHON%" -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r%this_source%, 'read_text()', 'read_text(encoding='+chr(39)+'utf-8'+chr(39)+')' )"
   "%PYTHON%" -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r%this_source%, 'join(self.lines))', 'join(self.lines), encoding='+chr(39)+'utf-8'+chr(39)+')' )"
) 

rem * ===========================
rem 2020-05-15 patch jedi-0.17.0
rem * ===========================
																															
if exist  "%WINPYDIR%\Lib\site-packages\jedi-0.17.0.dist-info" copy/Y "C:\WinP\tempo_fixes\Jedi-0.17.0\api\__init__.py" "%WINPYDIR%\Lib\site-packages\Jedi-0.17.0\api\__init__.py"

rem * =================


echo JUPYTERLAB_DIR=%JUPYTERLAB_DIR%  default is ~/.jupyter/lab
echo JUPYTERLAB_SETTINGS_DIR=%JUPYTERLAB_SETTINGS_DIR% , default is ~/.jupyter/lab/user-settings/
echo JUPYTERLAB_WORKSPACES_DIR=%JUPYTERLAB_WORKSPACES_DIR% , default is ~/.jupyter/lab/workspaces/

"%WINPYDIR%\Scripts\jupyter.exe" lab path


rem jupyter labextension update --all  (will rebuild if needed)
rem 2020-12-31 tweaks
rem see https://jupyter.readthedocs.io/en/latest/use/jupyter-directories.html
if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab" (
"%WINPYDIR%\Scripts\jupyter.exe" labextension list
"%WINPYDIR%\Scripts\jupyter.exe"  --paths  
)

REM 2023-10-15: 'nbextension' was Jupyter3 days
rem if exist  "%WINPYDIR%\Lib\site-packages\notebook" "%WINPYDIR%\Scripts\jupyter.exe" nbextension list


rem * ===================
echo clear jupyterlab staging (2018-03-09)
rem * ===================
if exist "%WINPYDIR%\share\jupyter\lab\staging" rmdir /S /Q "%WINPYDIR%\share\jupyter\lab\staging"
rem if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab"  "%WINPYDIR%\Scripts\jupyter.exe" lab clean


echo 2019-10-22 Spyder tweaks moved at the end as suspicion of problem creating (on Python-3.8)
rem * ============================
echo .spyder3\temp.py suspected of creating issue east of Italia
echo see https://groups.google.com/forum/#!topic/spyderlib/dH5VXlTc30s
rem * ============================
if  exist "%WINPYDIR%\..\settings\.spyder-py3\temp.py" del  "%WINPYDIR%\..\settings\.spyder-py3\temp.py"

rem * ============================
rem 2023-02-12: paching pip-23.0.0 pip\_vend_r\rich patch cpython bug https://github.com/pypa/pip/issues/11798
rem * ============================
if exist  "%WINPYDIR%\Lib\site-packages\pip-23.0.dist-info" (
   echo "coucou Pip-23.0 crashing  _vendor/rich"
   copy/Y "C:\WinP\tempo_fixes\pip\_vendor\rich\_win32_console.py" "%WINPYDIR%\site-packages\pip\_vendor\rich\_win32_console.py"
)

rem * ====================
echo summary 20202-04-11
rem * ====================
pip check


@echo on
goto the_end


:the_end