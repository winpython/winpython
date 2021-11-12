rem first line check
echo  keep me in ansi =utf-8 without BOM  (notepad plus plus or win10 screwing up for compatibility)

rem 2020-09-26 Jupyterlab-3 simplification
rem 2020-09-27 Jupyterlab-3 5S (looking for missing detail) 
rem 2020-10-25no_more_needed "nbextension enable" no more needed for bqplot, ipyleaflet, ipympl
rem 2021-01-30: jupyterlab2 final stuff removal
rem 2021-03-13: notebook classic stuff removal
rem 2021-05-23: use "%PYTHON%" for the executable instead of "%WINPYDIR%\python.exe"
rem 2021-11-12: patch numba restrictor


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


rem * ==================
echo finish install of bqplot (for VSCode 2021-03-13)
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\bqplot" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix bqplot

						 
rem * ==================
echo finish install of nteract_on_jupyter (2018-12-27)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\nteract_on_jupyter" "%WINPYDIR%\Scripts\jupyter.exe" serverextension enable nteract_on_jupyter


rem * ==================
echo finish install of Voila (2019-07-21)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\voila" "%WINPYDIR%\Scripts\jupyter.exe" serverextension enable voila --sys-prefix


rem * =================
echo finish install seaborn iris example
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\seaborn" "%PYTHON%" -c "import seaborn as sns;sns.set();sns.load_dataset('iris')"


rem  ** Active patchs**
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
rem 2021-11-12: patch numba-0.54.1 restrictor
rem * ===========================
set qt56p=%WINPYDIR%\Lib\site-packages\numba
if exist  "%qt56p%" (
  "%PYTHON%" -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%WINPYDIR%\Lib\site-packages\numba\__init__.py', 'numpy_version > (1, 20):', 'numpy_version > (1, 21):  # stonebig relax patch' )"
  echo "DID I patch numba%??"
) else (
  echo "I DIDN'T patch of numba !"
)

rem * ===========================
rem 2020-05-15 patch statsmodels-0.12.2 for PyPi
rem * ===========================
if exist  "%WINPYDIR%\site-packages\statsmodels-0.12.2.dist-info" (
   echo "coucou PyPy"
   copy/Y "C:\WinP\tempo_fixes\statsmodels\tools\docstring.py" "%WINPYDIR%\site-packages\statsmodels\tools\docstring.py"
   copy/Y "C:\WinP\tempo_fixes\statsmodels\tsa\forecasting\stl.py" "%WINPYDIR%\site-packages\statsmodels\tsa\forecasting\stl.py"
   copy/Y "C:\WinP\tempo_fixes\statsmodels\tsa\vector_ar\api.py" "%WINPYDIR%\site-packages\statsmodels\tsa\vector_ar\api.py"

)


rem  ** Example of live file replacement (not active)**
rem * ===========================
rem 2020-05-15 patch jedi-0.17.0
rem * ===========================
																															
if exist  "%WINPYDIR%\Lib\site-packages\jedi-0.17.0.dist-info" copy/Y "C:\WinP\tempo_fixes\Jedi-0.17.0\api\__init__.py" "%WINPYDIR%\Lib\site-packages\Jedi-0.17.0\api\__init__.py"

rem  ** Example of live source patch (not active)***
rem * =================
rem echo tornado Python-3.8.0  fix 2019-06-28  https://github.com/tornadoweb/tornado/issues/2656#issuecomment-491400255
rem * ==================

rem KEEP as example for next time needed

set qt56p=%WINPYDIR%\Lib\site-packages\tornado-6.0.3.dist-info
if exist  "%qt56p%" (
  "%PYTHON%" -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%WINPYDIR%\Lib\site-packages\tornado\platform\asyncio.py', 'import asyncio', 'import asyncio;asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # python-3.8.0' )"
  rem echo "DID I patch   %qt56p% ??"
) else (
  rem echo "I DIDN'T patch of %qt56p% !"
)

echo JUPYTERLAB_DIR=%JUPYTERLAB_DIR%  default is ~/.jupyter/lab
echo JUPYTERLAB_SETTINGS_DIR=%JUPYTERLAB_SETTINGS_DIR% , default is ~/.jupyter/lab/user-settings/
echo JUPYTERLAB_WORKSPACES_DIR=%JUPYTERLAB_WORKSPACES_DIR% , default is ~/.jupyter/lab/workspaces/

%WINPYDIR%\Scripts\jupyter.exe" lab path


rem jupyter labextension update --all  (will rebuild if needed)
rem 2020-12-31 tweaks
rem see https://jupyter.readthedocs.io/en/latest/use/jupyter-directories.html
if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab" (
"%WINPYDIR%\Scripts\jupyter.exe"jupyter labextension list
"%WINPYDIR%\Scripts\jupyter.exe"jupyter  --paths  
)

if exist  "%WINPYDIR%\Lib\site-packages\notebook" "%WINPYDIR%\Scripts\jupyter.exe" nbextension list


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


rem * ====================
echo patch spyder update reflex (2019-05-18 : spyder, not spyderlib !)
rem * ====================
"%PYTHON%" -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%WINPYDIR%\Lib\site-packages\spyder\config\main.py', ' '+chr(39)+'check_updates_on_startup'+chr(39)+': True', ' '+chr(39)+'check_updates_on_startup'+chr(39)+': False' )"

rem * ====================
echo summary 20202-04-11
rem * ====================
pip check
if exist  "%WINPYDIR%\Lib\site-packages\pipdeptree" pipdeptree


@echo on
goto the_end


:the_end