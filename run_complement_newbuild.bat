rem first line check
echo  keep me in ansi =utf-8 without BOM  (notepad plus plus or win10 screwing up for compatibility)

rem 2020-09-26 Jupyterlab-3 simplification
rem 2020-09-27 Jupyterlab-3 5S (looking for missing detail) 

rem use this in case we go back to jupyterlab-2
set jupyterlab2=1
echo jupyterlab2=%jupyterlab2%
if  %jupyterlab2%==1 then echo "do jupyterlab2 %jupyterlab2% stuff"
rem if build error, launch "WinPython Command Prompt.exe" dos ico, then try manual install of requirements.txt 
rem that is:  pip install --pre  --no-index --trusted-host=None  --find-links=C:\WinP\packages.srcreq --use-feature=2020-resolver -r c:\....\requirements.txt 
rem           ( drag & drop "requirements.txt" file in the dos window a the end of the line, to get full path)
rem then drag & drop "run_complement_newbuild.bat" file in the dos window and launch it

@echo off 
rem %1 is WINPYDIR being prepared
rem this .bat is placed at root (buildir34, buildir34\FlavorJulia, ...)
set origin=%~dp0
set new_winpydir=%1

cd /d %new_winpydir%

call scripts\env.bat
@echo off


rem * ===========================
rem 2020-05-15 patch jedi-0.17.0
rem * ===========================
rem if exist  "%WINPYDIR%\Lib\site-packages\jedi-0.17.0.dist-info" copy/Y "C:\WinP\tempo_fixes\Jedi-0.17.0\api\__init__.py" "%WINPYDIR%\Lib\site-packages\Jedi-0.17.0\api\__init__.py"


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

rem if %jupyterlab2%==1 if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab" "%WINPYDIR%\Scripts\jupyter.exe" serverextension enable --py  jupyterlab --sys-prefix 

@echo on
rem * ===================
echo jupyterlab manager (if npm there)
rem * ==================
@echo off
rem 2019-11-02 pre-clean
rem if %jupyterlab2%==1 if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab"  "%WINPYDIR%\Scripts\jupyter.exe" lab clean

rem jupyter labextension list

rem if %jupyterlab2%==1 if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab"  "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build @jupyter-widgets/jupyterlab-manager


rem * ==================
echo finish install of bqplot
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\bqplot" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix bqplot

rem if %jupyterlab2%==1  if exist  "%WINPYDIR%\Lib\site-packages\bqplot" "%WINPYDIR%\Scripts\jupyter.exe"  labextension install --no-build bqplot


rem * ==================
echo finish install of bokeh for jupyterlab (2019-08-10)
rem * ================= 

rem if %jupyterlab2%==1  if exist  "%WINPYDIR%\Lib\site-packages\bokeh" "%WINPYDIR%\Scripts\jupyter.exe"  labextension install --no-build @bokeh/jupyter_bokeh


rem * ==================
echo finish install of ipydatawidgets (2018-03-10)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\ipydatawidgets" "%WINPYDIR%\Scripts\jupyter.exe" nbextension install --py --sys-prefix  ipydatawidgets
if exist  "%WINPYDIR%\Lib\site-packages\ipydatawidgets" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  ipydatawidgets

rem if %jupyterlab2%==1 if exist  "%WINPYDIR%\Lib\site-packages\ipydatawidgets" "%WINPYDIR%\Scripts\jupyter.exe"  labextension install --no-build       jupyterlab-datawidgets


rem * ==================
echo finish install of ipyleaflet
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\ipyleaflet" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix  ipyleaflet

rem if %jupyterlab2%==1  if exist  "%WINPYDIR%\Lib\site-packages\ipyleaflet" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build jupyter-leaflet


rem * ==================
echo finish install of pythreejs
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\pythreejs" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  pythreejs

rem if %jupyterlab2%==1   if exist  "%WINPYDIR%\Lib\site-packages\pythreejs" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build jupyter-threejs


rem * ==================
echo finish install of ipyvolume / ipywebrtc
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\ipywebrtc" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  ipywebrtc
if exist  "%WINPYDIR%\Lib\site-packages\ipyvolume" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  ipyvolume


rem * ==================
echo finish install of ipyvolume / ipywebrtc
rem * =================

rem if %jupyterlab2%==1  if exist  "%WINPYDIR%\Lib\site-packages\ipywebrtc" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build jupyter-webrtc
rem if %jupyterlab2%==1  if exist  "%WINPYDIR%\Lib\site-packages\ipywebrtc" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build ipyvolume


rem * ==================
echo finish install of pdvega
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\vega3" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix vega3

rem if %jupyterlab2%==1  if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab"  "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build @jupyterlab/vega3-extension

rem * ==================
echo finish install of rise
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\rise" "%WINPYDIR%\Scripts\jupyter.exe" nbextension install rise --py --sys-prefix
if exist  "%WINPYDIR%\Lib\site-packages\rise" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix rise 


rem * ==================
echo finish install of ipympl (2017-10-29)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\ipympl" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix ipympl

rem if %jupyterlab2%==1  if exist  "%WINPYDIR%\Lib\site-packages\ipympl" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build jupyter-matplotlib

rem * =================
echo finish install of holoviews jupyterlab 2018-02-27 
rem * =================

rem if %jupyterlab2%==1   if exist  "%WINPYDIR%\Lib\site-packages\holoviews" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build @pyviz/jupyterlab_pyviz


rem * ==================
echo finish install of nteract_on_jupyter (2018-12-27)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\nteract_on_jupyter" "%WINPYDIR%\Scripts\jupyter.exe" serverextension enable nteract_on_jupyter


rem * ==================
echo finish install of Qgrid(2020-03-10)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\qgrid" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix qgrid

rem if %jupyterlab2%==1  if exist  "%WINPYDIR%\Lib\site-packages\qgrid" "%WINPYDIR%\Scripts\jupyter.exe"  labextension install --no-build  qgrid2  

rem * ==================
echo finish install of Jupyterlab-sql
rem * ==================

rem if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab_sql" "%WINPYDIR%\Scripts\jupyter.exe" serverextension enable jupyterlab_sql --py --sys-prefix
rem if %jupyterlab2%==1  if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab_sql" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build @jupyterlab-sql 


rem * ==================
echo finish install of Voila (2019-07-21)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\voila" "%WINPYDIR%\Scripts\jupyter.exe" serverextension enable voila --sys-prefix

rem if %jupyterlab2%==1  if exist  "%WINPYDIR%\Lib\site-packages\voila" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build @jupyter-voila/jupyterlab-preview

rem * ==================
echo  install of dataregistry (2019-07-28)(no more 2020-07-27)
rem * ================= 
rem 2020-07-27 if %jupyterlab2%==1  if exist  "%WINPYDIR%\Lib\site-packages\voila" "%WINPYDIR%\Scripts\jupyter.exe" labextension install @jupyterlab/dataregistry-extension


rem * ==================
echo  install of pydeck (2020-02-02)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\pydeck" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix pydeck
rem 2020-09-26 Jupyterlab-3 simplification if exist  "%WINPYDIR%\Lib\site-packages\pydeck" "%WINPYDIR%\Scripts\jupyter.exe" labextension  install --no-build @deck.gl/jupyter-widget

rem * ==================
echo  install of labextension install dask-labextension (2020-02-05)
rem * ================= 
rem if %jupyterlab2%==1  if exist  "%WINPYDIR%\Lib\site-packages\dask_labextension" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build dask-labextension
if exist  "%WINPYDIR%\Lib\site-packages\dask_labextension" "%WINPYDIR%\Scripts\jupyter.exe" serverextension enable dask_labextension

rem * =================
echo finish install seaborn iris example
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\seaborn" "%WINPYDIR%\python.exe" -c "import seaborn as sns;sns.set();sns.load_dataset('iris')"

rem * =================
echo finish install PyQtdoc
rem * =================
if exist  "%WINPYDIR%\Scripts\PyQtdoc_win_post_install.bat" "%WINPYDIR%\Scripts\PyQtdoc_win_post_install.bat" "-install"


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


rem * =================
echo tornado Python-3.8.0  fix 2019-06-28  https://github.com/tornadoweb/tornado/issues/2656#issuecomment-491400255
rem * ==================
set qt56p=%WINPYDIR%\Lib\site-packages\tornado-6.0.3.dist-info
if exist  "%qt56p%" (
   %WINPYDIR%\python.exe -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%WINPYDIR%\Lib\site-packages\tornado\platform\asyncio.py', 'import asyncio', 'import asyncio;asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # python-3.8.0' )"
   echo "DID I patch   %qt56p% ??"
   rem pause
) else (
   echo "I DIDN'T patch of %qt56p% !"
   rem pause
)



rem * ===================
echo 2018-03-25 Jupyterlab simplified wrap-up (https://github.com/jupyter/notebook/pull/3116#issuecomment-355672998)
rem * ===================
rem reduce time by building only once
rem at each extension do:
rem   "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build 
rem at the end:

rem 2019-08-28 : 32 bit sos "--minimize=False"
rem FAILED: if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab"  "%WINPYDIR%\Scripts\jupyter.exe" lab build --minimize=False
rem trying the memory 3000 instead of 4096 for %WINPYARCH=%WIN32

rem set qt56p=%WINPYDIR%\Lib\jupyterlab\staging\package.json
rem if exist  "%qt56p%"  (
rem if "%WINPYARCH%"=="WIN32"  %WINPYDIR%\python.exe -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%qt56p%', 'max_old_space_size=4096 ', 'max_old_space_size=3000 ' )"
rem )
rem if exist  "%qt56p%"  (
rem if not "%WINPYARCH%"=="WIN32"  %WINPYDIR%\python.exe -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%qt56p%', 'max_old_space_size=3000 ', 'max_old_space_size=4096 ' )"
rem )

rem 2019-08_31 patch
rem if not "%WINPYARCH%"=="WIN32" if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab" (
rem if "%WINPYARCH%"=="WIN32" "%WINPYDIR%\Scripts\jupyter.exe" lab build --minimize=False
rem if not "%WINPYARCH%"=="WIN32" "%WINPYDIR%\Scripts\jupyter.exe" lab build
rem jupyter labextension list
rem )

echo JUPYTERLAB_DIR=%JUPYTERLAB_DIR%  default is ~/.jupyter/lab
echo JUPYTERLAB_SETTINGS_DIR=%JUPYTERLAB_SETTINGS_DIR% , default is ~/.jupyter/lab/user-settings/
echo JUPYTERLAB_WORKSPACES_DIR=%JUPYTERLAB_WORKSPACES_DIR% , default is ~/.jupyter/lab/workspaces/

%WINPYDIR%\Scripts\jupyter.exe" lab path

rem 2019-10-22: in any case Jupytrelab want to build with
rem jupyter-matplotlib
rem jupyter-threejs
rem jupyter-datawidgets

rem if %jupyterlab2%==1   if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab" (
rem "%WINPYDIR%\Scripts\jupyter.exe" lab build
rem jupyter labextension list
rem )

rem jupyter labextension update --all  (will rebuild if needed)




rem * ===================
echo remove enum34 from Tensorfow (2017-12-22)
rem * ===================
if exist  "%WINPYDIR%\Lib\site-packages\enum" "%WINPYDIR%\scripts\pip.exe" uninstall -y enum34


rem * ===================
echo remove typing from altair (2018-11-01)
rem * ===================
if exist  "%WINPYDIR%\Lib\site-packages\typing.py" "%WINPYDIR%\scripts\pip.exe" uninstall -y typing


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

rem ====================
rem installation via requirements.txt, requirements2.txt and requirements3.txt files
rem ====================

rem pip install cvxpy --no-index --find-links=C:\WinPython\packages.srcreq --trusted-host=None

set link_srcreq=--find-links=%origin%packages.srcreq

set my_req=%origin%requirements.txt
if exist %my_req% pip install -r %my_req% --no-index %link_srcreq% --trusted-host=None

set my_req=%origin%requirements2.txt
if exist %my_req% pip install -r %my_req% --no-index %link_srcreq% --trusted-host=None

set my_req=%origin%requirements3.txt
if exist %my_req% pip install -r %my_req% --no-index %link_srcreq% --trusted-host=None

:the_end