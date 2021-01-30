rem first line check
echo  keep me in ansi =utf-8 without BOM  (notepad plus plus or win10 screwing up for compatibility)

rem 2020-09-26 Jupyterlab-3 simplification
rem 2020-09-27 Jupyterlab-3 5S (looking for missing detail) 
rem 2020-10-25no_more_needed "nbextension enable" no more needed for bqplot, ipyleaflet, ipympl
rem 2021-01-30: jupyterlab2 final stuff removal


rem if build error, launch "WinPython Command Prompt.exe" dos ico, then try manual install of requirements.txt 
rem that is:  pip install --pre  --no-index --trusted-host=None --log C:\WinP\log.txt  --find-links=C:\WinP\packages.srcreq -c C:\WinP\constraints.txt -r   c:\....\requirements.txt 
rem           ( drag & drop "requirements.txt" file in the dos window a the end of the line, to get full path)
rem if issue, search "ERROR:" in --log C:\WinP\log.txt
rem then drag & drop "run_complement_newbuild.bat" file in the dos window and launch it

@echo off 
rem %1 is WINPYDIR being prepared
rem this .bat is placed at root (buildir34, buildir34\FlavorJulia, ...)
set origin=%~dp0
set new_winpydir=%1

cd /d %new_winpydir%

call scripts\env.bat
@echo off

rem * ==========================
rem * When Python has no mingwpy
rem * ==========================
if not exist "%WINPYDIR%\Lib\site-packages\mingwpy" set pydistutils_cfg=%WINPYDIR%\..\settings\pydistutils.cfg
if not exist "%WINPYDIR%\Lib\site-packages\mingwpy" echo [config]>%pydistutils_cfg%



@echo off
rem * ===========================
echo finish install of jupyterlab
rem * ===========================

rem 2020-04-10 security
rem if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab"  "%WINPYDIR%\..\n\npm" config set ignore-scripts true

rem other suggestion from https://github.com/nteract/nteract
rem npm install -g --production windows-build-tools


@echo on
rem * ===================
echo jupyterlab pre-clean meaningless in 3.0
rem * ==================
@echo off
rem pre-clean Whatever jupyterlab version
rem if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab"  "%WINPYDIR%\Scripts\jupyter.exe" lab clean


rem * ==================
echo finish install of ipydatawidgets (2018-03-10)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\ipydatawidgets" "%WINPYDIR%\Scripts\jupyter.exe" nbextension install --py --sys-prefix  ipydatawidgets
if exist  "%WINPYDIR%\Lib\site-packages\ipydatawidgets" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  ipydatawidgets


rem * ==================
echo finish install of ipyvolume / ipywebrtc
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\ipywebrtc" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  ipywebrtc
if exist  "%WINPYDIR%\Lib\site-packages\ipyvolume" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  ipyvolume


rem * ==================
echo finish install of pdvega
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\vega3" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix vega3


rem * ==================
echo finish install of rise
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\rise" "%WINPYDIR%\Scripts\jupyter.exe" nbextension install rise --py --sys-prefix
if exist  "%WINPYDIR%\Lib\site-packages\rise" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix rise 


rem * ==================
echo finish install of nteract_on_jupyter (2018-12-27)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\nteract_on_jupyter" "%WINPYDIR%\Scripts\jupyter.exe" serverextension enable nteract_on_jupyter


rem * ==================
echo finish install of Voila (2019-07-21)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\voila" "%WINPYDIR%\Scripts\jupyter.exe" serverextension enable voila --sys-prefix


rem * ==================
echo  install of pydeck (2020-02-02)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\pydeck" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix pydeck


rem * ==================
echo  install of labextension install dask-labextension (2020-02-05)
rem * ================= 
rem no more if exist  "%WINPYDIR%\Lib\site-packages\dask_labextension" "%WINPYDIR%\Scripts\jupyter.exe" serverextension enable dask_labextension 


rem * ==================
echo finish install of ipygany (2020-12-29)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\ipygany" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix ipygany

rem * =================
echo finish install seaborn iris example
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\seaborn" "%WINPYDIR%\python.exe" -c "import seaborn as sns;sns.set();sns.load_dataset('iris')"


rem * =================
echo opengl PyQt5 patch 2018-01-06
rem * ==================
set qt56p=%WINPYDIR%\Lib\site-packages\PyQt5\Qt\bin
set qt56dest=%WINPYDIR%\Lib\site-packages\PyQt5\Qt\bin\opengl32sw.dll
if exist  "%qt56p%" if not exist "%qt56dest%" ( 
if "%WINPYARCH%"=="WIN32" copy "C:\WinPython\bd35\patch_qt570\opengl32sw-32\opengl32sw.dll" "%WINPYDIR%\Lib\site-packages\PyQt5\Qt\bin\opengl32sw.dll"
)
if not "%WINPYARCH%"=="WIN32" copy "C:\WinPython\bd35\patch_qt570\opengl32sw-64\opengl32sw.dll" "%WINPYDIR%\Lib\site-packages\PyQt5\Qt\bin\opengl32sw.dll"
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
  %WINPYDIR%\python.exe -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%WINPYDIR%\Lib\site-packages\tornado\platform\asyncio.py', 'import asyncio', 'import asyncio;asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # python-3.8.0' )"
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


rem * ===================
echo clear Pyside2 QML (2018-04-29 : it's too big)
rem * ===================
rem 20181222
rem if exist  "%WINPYDIR%\Lib\site-packages\PySide2\qml"  rmdir /S /Q "%WINPYDIR%\Lib\site-packages\PySide2\qml"

@echo on

echo 2019-10-22 Spyder tweaks moved at the end as suspicion of problem creating (on Python-3.8)
rem * ============================
echo .spyder3\temp.py suspected of creating issue east of Italia
echo see https://groups.google.com/forum/#!topic/spyderlib/dH5VXlTc30s
rem * ============================
if  exist "%WINPYDIR%\..\settings\.spyder-py3\temp.py" del  "%WINPYDIR%\..\settings\.spyder-py3\temp.py"


rem * ====================
echo patch spyder update reflex (2019-05-18 : spyder, not spyderlib !)
rem * ====================
%WINPYDIR%\python.exe -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%WINPYDIR%\Lib\site-packages\spyder\config\main.py', ' '+chr(39)+'check_updates_on_startup'+chr(39)+': True', ' '+chr(39)+'check_updates_on_startup'+chr(39)+': False' )"

rem * ====================
echo summary 20202-04-11
rem * ====================
pip check
if exist  "%WINPYDIR%\Lib\site-packages\pipdeptree" pipdeptree


@echo on
goto the_end



:the_end