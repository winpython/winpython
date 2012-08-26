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
CreateDirectory "$EXEDIR\settings"
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("HOME", "$EXEDIR\settings").r0'
ReadEnvStr $R0 "PATH"
StrCpy $R0 "${PREPATH};$R0;${POSTPATH}"
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("PATH", R0).r0'

StrCmp "${SETTINGSDIR}" "" end_settings
CreateDirectory "$EXEDIR\settings\${SETTINGSDIR}"
StrCpy $R5 "$EXEDIR\settings\${SETTINGSDIR}\${SETTINGSNAME}"
ReadINIStr $0 $R5 "main" last_drive
${GetRoot} $EXEDIR $1
StrCmp $0 "" write_settings
StrCmp $0 $1 end_settings
${ReplaceInFile} $R5 "$0\\" "$1\\"
write_settings:
WriteINIStr $R5 "main" last_drive $1
end_settings:

StrCmp "${PARAMETERS}" "" 0 param
${GetParameters} $R1
Goto end_param
param:
StrCpy $R1 "${PARAMETERS}"
end_param:

Exec '"${COMMAND}" $R1'
FunctionEnd