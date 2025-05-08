rem build launchers in WINDOWS and CONSOLE version
rem tweaked from @datalab-winpython provided code in \launchers_src
rem  @datalab-winpython licence is in \launchers_src\LICENCE
@echo off

set VCVARS_PATH="C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

rem pick the right ones and rename them in launchers_final
set do_launcher=%~dp0launchers_src\build_one_launcher.bat
set do_launcher_original=%~dp0launchers_src_original\build_one_launcher.bat

::WINDOWS launchers
call %do_launcher%  "python.ico" "winidle.bat" "IDLE (Python GUI)" WINDOWS

echo displace this pause if you want to re-build more
pause
exit


call %do_launcher% "powershell.ico" "cmd_ps.bat" "WinPython Powershell Prompt" WINDOWS
call %do_launcher%  "spyder.ico" "winspyder.bat" "Spyder" WINDOWS
call %do_launcher%  "spyder_reset.ico" "spyder_reset.bat" "Spyder reset" WINDOWS
call %do_launcher%  "code.ico" "winvscode.bat" "VS Code" WINDOWS

:: CONSOLE launchers
call %do_launcher%  "cmd.ico" "cmd.bat" "WinPython Command Prompt" CONSOLE
call %do_launcher%  "python.ico" "winpython.bat" "WinPython Interpreter" CONSOLE
call %do_launcher%  "jupyter.ico" "winipython_notebook.bat" "Jupyter Notebook" CONSOLE
call %do_launcher%  "jupyter.ico" "winjupyter_lab.bat" "Jupyter Lab" CONSOLE
call %do_launcher%  "winpython.ico" "wpcp.bat" "WinPython Control Panel" CONSOLE
pause

