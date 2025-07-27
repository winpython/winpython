rem build launchers in WINDOWS and CONSOLE version
rem tweaked from @datalab-winpython provided code in \launchers_src
rem  @datalab-winpython licence is in \launchers_src\LICENCE
@echo off

set VCVARS_PATH="C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

rem pick the right ones and rename them in launchers_final
set do_launcher=%~dp0launchers_src\build_one_launcher.bat
set do_launcher_original=%~dp0launchers_src_original\build_one_launcher.bat


echo displace this pause if you want to re-build more
pause
rem exit


:: WINDOWS launchers with Drag & Drop
call %do_launcher%  "python.ico" "winidle.bat" "IDLE (Python GUI)" WINDOWS proposed
call %do_launcher%  "spyder.ico" "winspyder.bat" "Spyder" WINDOWS proposed

:: CONSOLE launchers with Drag & Drop
call %do_launcher%  "jupyter.ico" "winipython_notebook.bat" "Jupyter Notebook" CONSOLE proposed
call %do_launcher%  "jupyter.ico" "winjupyter_lab.bat" "Jupyter Lab" CONSOLE proposed
call %do_launcher%  "winpython.ico" "wpcp.bat" "WinPython Control Panel" CONSOLE proposed

:: WINDOWS launchers with no Drag & Drop
call %do_launcher_original% "powershell.ico" "cmd_ps.bat" "WinPython Powershell Prompt" WINDOWS proposed
call %do_launcher_original%  "spyder_reset.ico" "spyder_reset.bat" "Spyder reset" WINDOWS proposed
call %do_launcher_original%  "code.ico" "winvscode.bat" "VS Code" WINDOWS proposed

:: CONSOLE launchers with no Drag & Drop
call %do_launcher_original%  "cmd.ico" "cmd.bat" "WinPython Command Prompt" CONSOLE proposed
call %do_launcher_original%  "python.ico" "winpython.bat" "WinPython Interpreter" CONSOLE proposed

pause

