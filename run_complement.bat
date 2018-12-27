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

rem 2018-07-07 for jupyterlab-0.32.x: https://www.npmjs.com/package/@jupyter-widgets/jupyterlab-manager
if exist  "%WINPYDIR%\Lib\site-packages\jupyterlab"  "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build @jupyter-widgets/jupyterlab-manager


rem * ==================
echo finish install of bqplot
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\bqplot" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix bqplot
if exist  "%WINPYDIR%\Lib\site-packages\bqplot" "%WINPYDIR%\Scripts\jupyter.exe"  labextension install --no-build bqplot


rem * ==================
echo finish install of bokeh for jupyterlab (2017-09-16)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\bokeh" "%WINPYDIR%\Scripts\jupyter.exe"  labextension install --no-build jupyterlab_bokeh


rem * ==================
echo finish install of ipydatawidgets (2018-03-10)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\ipydatawidgets" "%WINPYDIR%\Scripts\jupyter.exe" nbextension install --py --sys-prefix  ipydatawidgets
if exist  "%WINPYDIR%\Lib\site-packages\ipydatawidgets" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  ipydatawidgets
if exist  "%WINPYDIR%\Lib\site-packages\ipydatawidgets" "%WINPYDIR%\Scripts\jupyter.exe"  labextension install --no-build       jupyterlab-datawidgets


rem * ==================
echo finish install of ipyleaflet
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\ipyleaflet" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix  ipyleaflet
if exist  "%WINPYDIR%\Lib\site-packages\ipyleaflet" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build jupyter-leaflet


rem * ==================
echo finish install of pythreejs
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\pythreejs" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  pythreejs
if exist  "%WINPYDIR%\Lib\site-packages\pythreejs" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build jupyter-threejs


rem * ==================
echo finish install of ipyvolume / ipywebrtc
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\ipywebrtc" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  ipywebrtc
if exist  "%WINPYDIR%\Lib\site-packages\ipyvolume" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py  --sys-prefix  ipyvolume


rem * ==================
echo finish install of ipyvolume / ipywebrtc
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\ipywebrtc" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build jupyter-webrtc
if exist  "%WINPYDIR%\Lib\site-packages\ipywebrtc" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build ipyvolume


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
echo finish install of ipympl (2017-10-29)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\ipympl" "%WINPYDIR%\Scripts\jupyter.exe" nbextension enable --py --sys-prefix ipympl
if exist  "%WINPYDIR%\Lib\site-packages\ipympl" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build jupyter-matplotlib


rem * =================
echo finish install of holoviews jupyterlab 2018-02-27 
rem * =================
if exist  "%WINPYDIR%\Lib\site-packages\holoviews" "%WINPYDIR%\Scripts\jupyter.exe" labextension install --no-build @pyviz/jupyterlab_pyviz


rem * ==================
echo finish install of nteract_on_jupyter (2018-12-27)
rem * ================= 
if exist  "%WINPYDIR%\Lib\site-packages\nteract_on_jupyter" "%WINPYDIR%\Scripts\jupyter.exe" serverextension enable nteract_on_jupyter


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


rem * ============================
echo .spyder3\temp.py suspected of creating issue east of Italia
echo see https://groups.google.com/forum/#!topic/spyderlib/dH5VXlTc30s
rem * ============================
if  exist "%WINPYDIR%\..\settings\.spyder-py3\temp.py" del  "%WINPYDIR%\..\settings\.spyder-py3\temp.py"


rem * ====================
echo patch spyder update reflex (2017-03-25)
rem * ====================
%WINPYDIR%\python.exe -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%WINPYDIR%\Lib\site-packages\spyderlib\config\main.py', ' '+chr(39)+'check_updates_on_startup'+chr(39)+': True', ' '+chr(39)+'check_updates_on_startup'+chr(39)+': False' )"


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