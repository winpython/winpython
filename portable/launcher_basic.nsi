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

;================================================================
; Settings directory HOME (will affect $PROFILE)
IfFileExists "$EXEDIR\settings\*.*" 0 end_settings
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("HOME", "$EXEDIR\settings").r0'
StrCmp "${SETTINGSDIR}" "" end_settings
CreateDirectory "$EXEDIR\settings\${SETTINGSDIR}"

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
; NO PATH Environment variables
ReadEnvStr $R0 "PATH"

;================================================================


; Command line parameters
${GetParameters} $R1
StrCmp "${PARAMETERS}" "" end_param 0
StrCpy $R1 "${PARAMETERS} $R1"
end_param:

; prefered command (if it is a file)
StrCmp "${BETTERCOMMAND}" "" no_better_command
StrCpy $R8 "${BETTERCOMMAND}"
IfFileExists $R8 do_better_command
Goto no_better_command

do_better_command:
Exec '"${BETTERCOMMAND}" $R1'
Goto end_of_command

no_better_command:
Exec '"${COMMAND}" $R1'

end_of_command:
FunctionEnd