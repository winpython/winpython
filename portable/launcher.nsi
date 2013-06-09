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
!define COMMAND ""
!define PARAMETERS ""
!define WORKDIR ""
!define PREPATH ""
!define POSTPATH ""
!define SETTINGSDIR ""
!define SETTINGSNAME ""
Icon ""
OutFile ""
;================================================================

# Standard NSIS plugins
!include "FileFunc.nsh"
!include "TextReplace.nsh"

# Custom NSIS plugins
!include "ReplaceInFileWithTextReplace.nsh"

SilentInstall silent
AutoCloseWindow true
ShowInstDetails nevershow
RequestExecutionLevel user

Section ""
Call Execute
SectionEnd

Function Execute
StrCmp ${WORKDIR} "" 0 workdir
System::Call "kernel32::GetCurrentDirectory(i ${NSIS_MAX_STRLEN}, t .r0)"
SetOutPath $0
Goto end_workdir
workdir:
SetOutPath "${WORKDIR}"
end_workdir:

System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("WINPYDIR", "${WINPYDIR}").r0'
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("WINPYVER", "${WINPYVER}").r0'

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
StrCpy $R6 "$EXEDIR\settings\winpython.ini"
IfFileExists $R6 winpython_settings_done
ClearErrors
FileOpen $0 $R6 w
IfErrors winpython_settings_done
FileWrite $0 "$\r$\n[environment]"
FileWrite $0 "$\r$\n## Uncomment following lines to override environment variables"
FileWrite $0 "$\r$\n#path = "
FileWrite $0 "$\r$\n#pythonpath = "
FileWrite $0 "$\r$\n#pythonstartup = "
FileClose $0
winpython_settings_done:


; PATH
IfFileExists $R6 0 no_path_replacement
ReadINIStr $0 $R6 "environment" path
IfErrors no_path_replacement
StrCpy $R0 $0
Goto set_path
no_path_replacement:
ReadEnvStr $R0 "PATH"
set_path:
StrCpy $R0 "${PREPATH};$R0;${POSTPATH}"
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("PATH", R0).r0'

; PYTHONPATH
IfFileExists $R6 0 no_pythonpath_replacement
ReadINIStr $R0 $R6 "environment" pythonpath
IfErrors no_pythonpath_replacement
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("PYTHONPATH", R0).r0'
no_pythonpath_replacement:

; PYTHONSTARTUP
IfFileExists $R6 0 no_pythonstartup_replacement
ReadINIStr $R0 $R6 "environment" pythonstartup
IfErrors no_pythonstartup_replacement
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("PYTHONSTARTUP", R0).r0'
no_pythonstartup_replacement:


; Command line parameters
${GetParameters} $R1
StrCmp "${PARAMETERS}" "" end_param 0
StrCpy $R1 "${PARAMETERS} $R1"
end_param:

Exec '"${COMMAND}" $R1'
FunctionEnd