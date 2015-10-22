/*

WinPython launcher template script

Copyright © 2012 Pierre Raybaut
Licensed under the terms of the MIT License
(see winpython/__init__.py for details)
 
*/

;================================================================
; These lines are automatically replaced when creating launchers:
; (see winpython/make.py)
!addincludedir ""
!define WINPYDIR ""
!define WINPYVER ""
;  Addition for R_HOME
!define R_HOME ""
;  Addition for JULIA_HOME and JULIA
!define JULIA_HOME ""
!define JULIA ""
;  Addition for JULIA_PKGDIR
!define JULIA_PKGDIR ""

!define COMMAND ""
!define PARAMETERS ""
!define WORKDIR ""
!define PREPATH ""
!define POSTPATH ""
!define SETTINGSDIR ""
!define SETTINGSNAME ""

; prefered command (if it is a file)
!define BETTERCOMMAND ""
!define BETTERWORKDIR ""
!define BETTERPARAMETERS ""

; jupyter workaround to stay in one directory
!define JUPYTER_DATA_DIR ""

Icon ""
OutFile ""
;================================================================

# Standard NSIS plugins
!include "WordFunc.nsh"
!include "FileFunc.nsh"
!include "TextReplace.nsh"

# Custom NSIS plugins
!include "ReplaceInFileWithTextReplace.nsh"
!include "EnumIni.nsh"

SilentInstall silent
AutoCloseWindow true
ShowInstDetails nevershow
RequestExecutionLevel user

Section ""
Call Execute
SectionEnd

Function Execute

; prefered command (if it is a file)
StrCmp "${BETTERCOMMAND}" "" no_better_workdir
StrCpy $R8 "${BETTERCOMMAND}"
IfFileExists $R8 do_better_workdircheck
Goto no_better_workdir

do_better_workdircheck:
StrCpy $R8 "${BETTERWORKDIR}"
IfFileExists $R8 do_better_workdir
Goto no_better_workdir

do_better_workdir:
StrCmp ${BETTERWORKDIR} "" 0 betterworkdir
System::Call "kernel32::GetCurrentDirectory(i ${NSIS_MAX_STRLEN}, t .r0)"
SetOutPath $0
Goto end_workdir
betterworkdir:
SetOutPath "${BETTERWORKDIR}"
Goto end_workdir

no_better_workdir:
;normal workdir
StrCmp ${WORKDIR} "" 0 workdir
System::Call "kernel32::GetCurrentDirectory(i ${NSIS_MAX_STRLEN}, t .r0)"
SetOutPath $0
Goto end_workdir
workdir:
SetOutPath "${WORKDIR}"
end_workdir:

System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("WINPYDIR", "${WINPYDIR}").r0'
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("WINPYVER", "${WINPYVER}").r0'

; Addition of R_HOME Environment Variable if %R_Home%\bin exists
StrCmp "${R_HOME}" "" end_Rsettings
IfFileExists "${R_HOME}\bin\*.*" 0 end_Rsettings

System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("R_HOME", "${R_HOME}").r0'

end_Rsettings:

; Addition of JULIA and JULIA_HOME Environment Variable if %JULIA% program exists
StrCmp "${JULIA}" "" end_Julia_settings
IfFileExists "${JULIA}" 0 end_Julia_settings

System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("JULIA", "${JULIA}").r0'

StrCmp "${JULIA_HOME}" "" end_Julia_settings
IfFileExists "${JULIA_HOME}\*.*" 0 end_Julia_settings
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("JULIA_HOME", "${JULIA_HOME}").r0'

;  Addition for JULIA_PKGDIR
StrCmp "${JULIA_PKGDIR}" "" end_Julia_settings
IfFileExists "${JULIA_PKGDIR}\*.*" 0 end_Julia_settings
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("JULIA_PKGDIR", "${JULIA_PKGDIR}").r0'

end_Julia_settings:


;  Addition for QT_API=pyqt5 if Qt5 detected
IfFileExists "${WINPYDIR}\Lib\site-packages\PyQt5\*.*" 0 end_QT_API_settings
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("QT_API", "pyqt5").r0'

end_QT_API_settings:

; jupyter
StrCmp "${JUPYTER_DATA_DIR}" "" end_jupyter_data_setting
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("JUPYTER_DATA_DIR", "${JUPYTER_DATA_DIR}").r0'

end_jupyter_data_setting:

;================================================================
; Settings directory
IfFileExists "$EXEDIR\settings\*.*" 0 end_settings
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("HOME", "$EXEDIR\settings").r0'
StrCmp "${SETTINGSDIR}" "" end_settings
CreateDirectory "$EXEDIR\settings\${SETTINGSDIR}"
; Handle portability in Spyder's settings
StrCpy $R5 "$EXEDIR\settings\${SETTINGSDIR}\${SETTINGSNAME}"
ReadINIStr $0 $R5 "main" last_drive
${GetRoot} $EXEDIR $1
StrCmp $0 "" write_settings
StrCmp $0 $1 end_settings
${ReplaceInFile} $R5 "$0\\" "$1\\"
write_settings:
WriteINIStr $R5 "main" last_drive $1
end_settings:
;================================================================


; WinPython settings
IfFileExists "$EXEDIR\settings\*.*" 0 winpython_settings_profile
StrCpy $R6 "$EXEDIR\settings\winpython.ini"
Goto winpython_settings_continue
winpython_settings_profile:
StrCpy $R6 "$PROFILE\winpython.ini"
winpython_settings_continue:
IfFileExists $R6 winpython_settings_done
ClearErrors
FileOpen $0 $R6 w
IfErrors winpython_settings_done
FileWrite $0 "[debug]$\r$\nstate = disabled"
FileWrite $0 "$\r$\n"
FileWrite $0 "$\r$\n[environment]"
FileWrite $0 "$\r$\n## <?> Uncomment lines to override environment variables"
FileWrite $0 "$\r$\n#PATH = "
FileWrite $0 "$\r$\n#PYTHONPATH = "
FileWrite $0 "$\r$\n#PYTHONSTARTUP = "
FileClose $0
winpython_settings_done:


; Debug state
IfFileExists $R6 0 no_debug
ReadINIStr $R7 $R6 "debug" "state"
StrCmp $R7 "" no_debug
StrCmp $R7 "disabled" no_debug
StrCpy $R7 "enabled"
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("WINPYDEBUG", "True").r0'
no_debug:


;================================================================
; Environment variables
ReadEnvStr $R0 "PATH"

IfFileExists $R6 0 envvar_done
StrCpy $R9 0
envvar_loop:
    ${EnumIniValue} $1 $R6 "environment" $R9
    StrCmp $1 "" envvar_done
    IntOp $R9 $R9 + 1
    ReadINIStr $2 $R6 "environment" $1

    ${StrFilter} $1 "+" "" " " $1 ; Upper case + remove trailing spaces
    StrCmp $1 "PATH" found_path
    System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("$1", "$2").r0'
    Goto end_found_path

    found_path:
    StrCpy $R0 $2
    StrCmp $R7 "disabled" end_found_path
    MessageBox MB_OK|MB_ICONINFORMATION "Found PATH=$2"
    end_found_path:

    StrCmp $R7 "disabled" envvar_loop
    MessageBox MB_YESNO|MB_ICONQUESTION "$R9: Name='$1'$\nValue='$2'$\n$\n$\nMore?" IDYES envvar_loop
envvar_done:

StrCpy $R0 "${PREPATH};$R0;${POSTPATH}"
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("PATH", R0).r0'
;================================================================




; prefered command (if it is a file)
StrCmp "${BETTERCOMMAND}" "" no_better_command
StrCpy $R8 "${BETTERCOMMAND}"
IfFileExists $R8 do_better_commandcheck
Goto no_better_command

do_better_commandcheck:
StrCmp "${BETTERWORKDIR}" "" no_better_command
StrCpy $R8 "${BETTERWORKDIR}"
IfFileExists $R8 do_better_command
Goto no_better_command

do_better_command:
; Command line parameters
${GetParameters} $R1
StrCmp "${BETTERPARAMETERS}" "" end_betterparam 0
StrCpy $R1 "${BETTERPARAMETERS} $R1"
end_betterparam:
Exec '"${BETTERCOMMAND}" $R1'
Goto end_of_command

no_better_command:
; Command line parameters
${GetParameters} $R1
StrCmp "${PARAMETERS}" "" end_param 0
StrCpy $R1 "${PARAMETERS} $R1"
end_param:
Exec '"${COMMAND}" $R1'

end_of_command:
FunctionEnd