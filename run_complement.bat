echo rem labextendion 2019-06-28 test
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


rem * ==========================
rem * configure ipython-parallel
rem * ==========================
@echo off
if exist  "%WINPYDIR%\Lib\site-packages\IPython"  "%WINPYDIR%\Scripts\jupyter-notebook.exe" --generate-config

rem starting Jupyter 5+, use ipcluster
if exist "%WINPYDIR%\Scripts\ipcluster.exe" "%WINPYDIR%\Scripts\ipcluster.exe" nbextension enable

rem 2018-03-10
if exist "%WINPYDIR%\Scripts\ipcluster.exe" jupyter nbextension install --sys-prefix --py ipyparallel
if exist "%WINPYDIR%\Scripts\ipcluster.exe" jupyter nbextension enable --sys-prefix --py ipyparallel
 
rem    if not exist "ipcluster.exe" echo c.NotebookApp.server_extensions.append('ipyparallel.nbextension')>>"%winpydir%\..\settings\.jupyter\jupyter_notebook_config.py"

@echo off
rem * ===========================
echo finish install of jupyterlab
rem * ===========================

rem other suggestion from https://github.com/nteract/nteract
rem npm install -g --production windows-build-tools

rem 2018-01-15 node-gyp experience 2018-01-19removetest
rem npm config set python "C:/WinPython/basedir27/buildZero/winpython-32bit-2.7.x.2/python-2.7.13/python.exe"
rem npm config set PYTHON "C:/WinP/bd27/buildZero/winpython-32bit-2.7.x.2/python-2.7.13/python.exe"
                                                
rem "%WINPYDIR%\..\tools\n\node_modules\npm\bin\node-gyp-bin\node-gyp.cmd" configure --msvs_version=2015
rem if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab" "%WINPYDIR%\Scripts\jupyter.exe" serverextension enable --py  jupyterlab --sys-prefix 

@echo on
rem * ===================
echo jupyterlab manager (if npm there)
rem * ==================
@echo off
rem jupyter lab clean
rem jupyter labextension list
rem jupyter labextension disable bqplot    jupyter-leaflet  jupyter-matplotlib  jupyter-threejs   jupyterlab-datawidgets   jupyterlab_bokeh

rem 2018-07-07 for jupyterlab-0.32.x: https://www.npmjs.com/package/@jupyter-widgets/jupyterlab-manager
if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab"  "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build @jupyter-widgets/jupyterlab-manager


rem * ==================
echo finish install of bqplot
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\bqplot" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix bqplot
rem labextendion2
if exist  "%WINPYDIR%\Lib\site-packages\bqplot" "%WINPYDIR%\Scripts\jupyter.exe"  labextension install --no-build bqplot


rem * ==================
echo finish install of bokeh for jupyterlab (2017-09-16)
rem * ================= 
rem labextendion if exist  "%WINPYDIR%\Lib\site-packages\bokeh" "%WINPYDIR%\Scripts\jupyter.exe"  labextension install --no-build jupyterlab_bokeh


rem * ==================
echo finish install of ipydatawidgets (2018-03-10)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\ipydatawidgets" "%WINPYDIR%\Scripts\jupyter.exe" nbextension install --py --sys-prefix  ipydatawidgets
if exist  "%WINPYDIR%\Lib\site-packages\ipydatawidgets" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  ipydatawidgets
rem labextendion 
rem no need: included per default in jlab-1 
if exist  "%WINPYDIR%\Lib\site-packages\ipydatawidgets" "%WINPYDIR%\Scripts\jupyter.exe"  labextension install --no-build       jupyterlab-datawidgets


rem * ==================
echo finish install of ipyleaflet
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\ipyleaflet" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix  ipyleaflet
rem labextendion 
rem jupyter-leaflet-0.10.7 not ok with jupyterlab-1 (but doesn't work ?)
rem labextendion3 2017-07-02
if exist  "%WINPYDIR%\Lib\site-packages\ipyleaflet" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build jupyter-leaflet


rem * ==================
echo finish install of pythreejs
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\pythreejs" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  pythreejs
rem labextendion
if exist  "%WINPYDIR%\Lib\site-packages\pythreejs" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build jupyter-threejs


rem * ==================
echo finish install of ipyvolume / ipywebrtc
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\ipywebrtc" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  ipywebrtc
if exist  "%WINPYDIR%\Lib\site-packages\ipyvolume" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  ipyvolume


rem * ==================
echo finish install of ipyvolume / ipywebrtc
rem * =================
rem labextendion if exist  "%WINPYDIR%\Lib\site-packages\ipywebrtc" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build jupyter-webrtc
rem labextendion if exist  "%WINPYDIR%\Lib\site-packages\ipywebrtc" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build ipyvolume


rem * ==================
echo finish install of pdvega
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\vega3" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix vega3

rem 2019-03-30 workaround altair-3
rem no need: included per default in jlab-1 
if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab"  "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build @jupyterlab/vega3-extension

rem * ==================
echo finish install of rise
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\rise" "%WINPYDIR%\Scripts\jupyter.exe" nbextension install rise --py --sys-prefix
if exist  "%WINPYDIR%\Lib\site-packages\rise" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix rise 


rem * ==================
echo finish install of ipympl (2017-10-29)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\ipympl" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix ipympl
rem labextendion4
rem no need: included per default in jlab-1 
if exist  "%WINPYDIR%\Lib\site-packages\ipympl" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build jupyter-matplotlib


rem * =================
echo finish install of holoviews jupyterlab 2018-02-27 
rem * =================

rem if exist  "%WINPYDIR%\Lib\site-packages\holoviews" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build @pyviz/jupyterlab_pyviz

rem jupyterlan-1.0.0rc0 tempo patch
echo finish install of holoviews jupyterlab 2018-06-28
rem labextendion2
if exist  "%WINPYDIR%\Lib\site-packages\holoviews" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build @pyviz/jupyterlab_pyviz


rem * ==================
echo finish install of nteract_on_jupyter (2018-12-27)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\nteract_on_jupyter" "%WINPYDIR%\Scripts\jupyter.exe" serverextension enable nteract_on_jupyter


rem * ==================
echo finish install of Qgrid(2019-04-26)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\qgrid" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix qgrid
rem labextendion if exist  "%WINPYDIR%\Lib\site-packages\qgrid" "%WINPYDIR%\Scripts\jupyter.exe"  labextension install --no-build  qgrid  

rem * ==================
echo finish install of Jupyterlab-sql
rem * ==================
rem 2019-06-30 20190706
if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab_sql" "%WINPYDIR%\Scripts\jupyter.exe" serverextension enable jupyterlab_sql --py --sys-prefix
rem labextendion if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab_sql" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build @jupyterlab-sql 
rem requires jupyter lab build after

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
rem echo sqlalchemy Python-3.8.0b1 fix 2019-06-16
rem * ==================
rem set qt56p=%WINPYDIR%\Lib\site-packages\SQLAlchemy-1.3.4.dist-info
rem if exist  "%qt56p%" copy "C:\WinP\bd38\compat.py" "%WINPYDIR%\Lib\site-packages\sqlalchemy\util\compat.py"


rem * =================
echo tornado Python-3.8.0  fix 2019-06-28  https://github.com/tornadoweb/tornado/issues/2656#issuecomment-491400255
rem * ==================
set qt56p=%WINPYDIR%\Lib\site-packages\tornado-6.0.3.dist-info
if exist  "%qt56p%" (
   %WINPYDIR%\python.exe -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%WINPYDIR%\Lib\site-packages\tornado\platform\asyncio.py', 'import asyncio', 'import asyncio;asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # python-3.8.0' )"
)

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
echo patch spyder keep default white theme (2019-05-18)
rem * ====================
%WINPYDIR%\python.exe -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%WINPYDIR%\Lib\site-packages\spyder\config\main.py', 'selected'+chr(39)+': '+chr(39)+'spyder/dark'+chr(39) , 'selected'+chr(39)+': '+chr(39)+'spyder'+chr(39) )"



rem * ===================
echo 2018-03-25 Jupyterlab simplified wrap-up (https://github.com/jupyter/notebook/pull/3116#issuecomment-355672998)
rem * ===================
rem reduce time by building only once
rem at each extension do:
rem   "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build 
rem at the end:
if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab"  "%WINPYDIR%\Scripts\jupyter.exe" lab build
if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab" jupyter labextension list


rem 2018-01-15 node-gyp experience
rem npm config set python "C:\WinPython\bd27\buildZero\winpython-32bit-2.7.x.2\python-2.7.13"
rem npm config delete python 


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